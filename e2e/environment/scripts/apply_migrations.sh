#!/usr/bin/env bash
# ============================================================================
# CT-SCHEMA-02 — CANONICAL migration runner (LAYER 2 of the two-layer model)
# ----------------------------------------------------------------------------
# Applies the canonical CarbonTally migration set deterministically and
# fail-closed, and records an independent apply ledger.
#
# CHANGED IN CT-SCHEMA-02 (and why):
#   * SOURCE : ``<repo>/supabase/migrations`` (89 files) is the canonical set.
#     The old helper read a 53-file *copy* under ``e2e/environment/supabase/
#     migrations`` that had drifted from canonical (including a pre-revision
#     D32). That copy is now a symlink to the canonical directory.
#   * ROLE   : ``postgres`` — CarbonTally's ordinary migration role. The old
#     helper prescribed ``supabase_admin`` for the D32 migration, which
#     contradicted PO decision Route C (the migration role must not own, or be
#     granted, a provider-managed relation) and is stale: the current D32
#     revision issues no ownership-sensitive DDL, it only validates. Provider
#     privilege belongs to the D32 *operator* step (d32_storage_operator.sql).
#   * CONTEXT: every migration runs with an EXPLICIT pinned ``search_path`` and
#     the pin is verified before the first file runs. Unqualified references in
#     a migration could otherwise resolve differently per ambient session state,
#     and PostgreSQL renders policy expressions relative to ``search_path``
#     (the F-02 defect). A run can no longer succeed merely because the machine
#     happened to have a favourable ``search_path``.
#   * ORDER  : ``--from``/``--to`` exist so the canonical sequence (migrations
#     1-26 -> D32 operator step -> migrations 27-89) can be driven by
#     ``canonical_schema_rebuild.sh`` without editing any migration file.
#
# GUARDRAILS
#   * aborts on the first non-zero exit (never continues, never fixes forward);
#   * refuses a protected target database name (qa/demo/investor/prod/live)
#     unless CT_ALLOW_PROTECTED_TARGET=1 is set explicitly;
#   * refuses a source set with duplicate migration versions;
#   * ``--require-storage`` fails closed when the Supabase Storage platform
#     layer is absent (F-01 diagnostic) instead of failing 27 files later.
#
# Usage: apply_migrations.sh [options] [<start-filename>]
#   --source <dir>        migration dir (default <repo>/supabase/migrations)
#   --role <role>         apply role (default postgres)
#   --host|--port|--db    target (defaults E2E_DB_HOST/PORT/NAME)
#   --from <name|seq>     first migration to apply, inclusive (1-based)
#   --to <name|seq>       last migration to apply, inclusive
#   --ledger <path>       ledger file (default <logs>/apply_ledger.tsv)
#   --logs <dir>          per-migration output (default /tmp/ct_apply_logs)
#   --expect-count <n>    fail unless the selected set has exactly <n> files
#   --search-path <v>     pinned session search_path (default migration role's)
#   --require-storage     fail closed unless the platform storage layer exists
#   --dry-run             print the selected set and exit
# ============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

SOURCE_DIR="$REPO_ROOT/supabase/migrations"
ROLE="${E2E_DB_USER:-postgres}"
HOST="${E2E_DB_HOST:-127.0.0.1}"
PORT="${E2E_DB_PORT:-55326}"
DB="${E2E_DB_NAME:-postgres}"
export PGPASSWORD="${E2E_DB_PASSWORD:-postgres}"

FROM_SEL=""
TO_SEL=""
LEDGER=""
LOGS=""
EXPECT_COUNT=""
REQUIRE_STORAGE=0
DRY_RUN=0
#: The canonical migration role's search_path (pg_roles.rolconfig for `postgres`
#: on the Supabase platform image). `auth` and `storage` are deliberately absent.
PINNED_SEARCH_PATH='"$user", public, extensions'

while [ $# -gt 0 ]; do
  case "$1" in
    --source)          SOURCE_DIR="$2"; shift 2 ;;
    --role)            ROLE="$2"; shift 2 ;;
    --host)            HOST="$2"; shift 2 ;;
    --port)            PORT="$2"; shift 2 ;;
    --db)              DB="$2"; shift 2 ;;
    --from)            FROM_SEL="$2"; shift 2 ;;
    --to)              TO_SEL="$2"; shift 2 ;;
    --ledger)          LEDGER="$2"; shift 2 ;;
    --logs)            LOGS="$2"; shift 2 ;;
    --expect-count)    EXPECT_COUNT="$2"; shift 2 ;;
    --search-path)     PINNED_SEARCH_PATH="$2"; shift 2 ;;
    --require-storage) REQUIRE_STORAGE=1; shift ;;
    --dry-run)         DRY_RUN=1; shift ;;
    -h|--help)         sed -n '2,58p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)                echo "apply_migrations.sh: unknown option: $1" >&2; exit 2 ;;
    *)                 FROM_SEL="$1"; shift ;;   # deprecated positional form
  esac
done

fail() { echo "ABORT: $*" >&2; exit 1; }
psql_q() { psql -h "$HOST" -p "$PORT" -U "$ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 "$@"; }
psql_scalar() { psql -h "$HOST" -p "$PORT" -U "$ROLE" -d "$DB" -X -q -A -t -c "$1"; }

# ---------------------------------------------------------------------------
# Target guard (AGENTS.md §55.1 convention): a destructive runner must refuse a
# target whose database name looks like a persistent / authoritative environment.
# ---------------------------------------------------------------------------
case "$DB" in
  *qa*|*demo*|*investor*|*prod*|*live*|*production*)
    if [ "${CT_ALLOW_PROTECTED_TARGET:-0}" != "1" ]; then
      fail "refusing target database '$DB' — its name matches a protected-environment pattern (qa/demo/investor/prod/live). Point this at a disposable clone, or set CT_ALLOW_PROTECTED_TARGET=1 only after an explicit documented decision."
    fi
    echo "WARNING: protected-target guard explicitly overridden for '$DB'"
    ;;
esac

# ---------------------------------------------------------------------------
# Migration set: deterministic order, no duplicates, no silent gaps
# ---------------------------------------------------------------------------
[ -d "$SOURCE_DIR" ] || fail "migration source directory not found: $SOURCE_DIR"
MIGRATIONS=()
while IFS= read -r m; do MIGRATIONS+=("$m"); done < <(cd "$SOURCE_DIR" && ls -1 -- *.sql 2>/dev/null | LC_ALL=C sort)
[ "${#MIGRATIONS[@]}" -gt 0 ] || fail "no .sql migrations found in $SOURCE_DIR"

VERSIONS="$(printf '%s\n' "${MIGRATIONS[@]}" | sed 's/_.*//')"
DUPES="$(printf '%s\n' "$VERSIONS" | LC_ALL=C sort | uniq -d | tr '\n' ' ')"
[ -z "${DUPES// /}" ] || fail "duplicate migration versions in $SOURCE_DIR: $DUPES"
UNSORTED="$(printf '%s\n' "$VERSIONS" | LC_ALL=C sort -c 2>&1)" || fail "migration versions are not in deterministic (LC_ALL=C sorted) order: $UNSORTED"

RESOLVED=""
resolve_index() {  # $1 selector  $2 label -> sets $RESOLVED (1-based position)
  local sel="$1" label="$2" i
  RESOLVED=""
  if [[ "$sel" =~ ^[0-9]+$ ]]; then
    [ "$sel" -ge 1 ] && [ "$sel" -le "${#MIGRATIONS[@]}" ] || return 1
    RESOLVED="$sel"; return 0
  fi
  for i in "${!MIGRATIONS[@]}"; do
    if [ "${MIGRATIONS[$i]}" = "$sel" ]; then RESOLVED="$((i + 1))"; return 0; fi
  done
  return 1
}

FIRST=1
LAST="${#MIGRATIONS[@]}"
if [ -n "$FROM_SEL" ]; then
  resolve_index "$FROM_SEL" --from || fail "--from '$FROM_SEL' is not a migration in $SOURCE_DIR"
  FIRST="$RESOLVED"
fi
if [ -n "$TO_SEL" ]; then
  resolve_index "$TO_SEL" --to || fail "--to '$TO_SEL' is not a migration in $SOURCE_DIR"
  LAST="$RESOLVED"
fi
[ "$FIRST" -le "$LAST" ] || fail "--from (position $FIRST) is after --to (position $LAST)"

SELECTED=("${MIGRATIONS[@]:FIRST - 1:LAST - FIRST + 1}")
COUNT="${#SELECTED[@]}"
if [ -n "$EXPECT_COUNT" ] && [ "$EXPECT_COUNT" != "$COUNT" ]; then
  fail "expected $EXPECT_COUNT migration(s) in the selected range, found $COUNT"
fi

LOGS="${LOGS:-/tmp/ct_apply_logs}"
LEDGER="${LEDGER:-$LOGS/apply_ledger.tsv}"
mkdir -p "$LOGS" || fail "cannot create log directory $LOGS"

echo "=== canonical migration runner (CT-SCHEMA-02) ==="
echo "  target      : $ROLE@$HOST:$PORT/$DB"
echo "  source      : $SOURCE_DIR"
echo "  migration set: ${#MIGRATIONS[@]} files (${MIGRATIONS[0]} .. ${MIGRATIONS[-1]})"
echo "  selected    : positions $FIRST..$LAST -> $COUNT file(s)"
echo "  range       : ${SELECTED[0]} .. ${SELECTED[-1]}"
echo "  search_path : $PINNED_SEARCH_PATH  (EXPLICIT PIN)"
echo "  ledger      : $LEDGER"

if [ "$DRY_RUN" = "1" ]; then
  printf '%s\n' "${SELECTED[@]}"
  echo "DRY_RUN_SELECTED=$COUNT"
  exit 0
fi

# ---------------------------------------------------------------------------
# Pre-flight: connectivity, pinned context, optional platform prerequisite
# ---------------------------------------------------------------------------
IDENT="$(psql_scalar "select current_user || '@' || current_database() || ' pg=' || current_setting('server_version')" 2>&1)" \
  || fail "cannot connect to $ROLE@$HOST:$PORT/$DB: $IDENT"
echo "  connected   : $IDENT"

PINNED_SCHEMAS="$(psql -h "$HOST" -p "$PORT" -U "$ROLE" -d "$DB" -X -q -A -t \
  -c "SET search_path = $PINNED_SEARCH_PATH" \
  -c "select coalesce(array_to_string(current_schemas(true), ','), '')" 2>&1)" \
  || fail "could not apply the pinned search_path: $PINNED_SCHEMAS"
case ",$PINNED_SCHEMAS," in
  *,auth,*|*,storage,*)
    fail "pinned search_path resolved to '{$PINNED_SCHEMAS}' which includes auth and/or storage. Refusing to run: unqualified names (and PostgreSQL's rendering of policy expressions) would resolve differently from the canonical migration context." ;;
esac
echo "  pinned ctx  : current_schemas(true) = {$PINNED_SCHEMAS}"

if [ "$REQUIRE_STORAGE" = "1" ]; then
  STORAGE_OK="$(psql_scalar "select (to_regclass('storage.buckets') is not null and to_regclass('storage.objects') is not null and to_regprocedure('storage.foldername(text)') is not null)::text" 2>&1)"
  if [ "$STORAGE_OK" != "true" ]; then
    fail "platform prerequisite missing: the Supabase Storage layer (storage.buckets / storage.objects / storage.foldername) is not provisioned in $DB. Provision the platform Storage service first (LAYER 1) — never fabricate platform tables. [F-01]"
  fi
  echo "  storage     : platform Storage layer present"
fi

# ---------------------------------------------------------------------------
# Apply: one file at a time, ascending order, abort on first failure
# ---------------------------------------------------------------------------
printf 'seq\tfile\tsha256_16\trc\tseconds\tstatus\n' > "$LEDGER" || fail "cannot write ledger $LEDGER"

applied=0
n=0
for f in "${SELECTED[@]}"; do
  n=$((n + 1))
  sha="$(sha256sum "$SOURCE_DIR/$f" | cut -c1-16)"
  log="$LOGS/$(printf '%03d' "$n")_$f.log"
  t0="$(date +%s.%N)"
  psql -h "$HOST" -p "$PORT" -U "$ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 \
       -c "SET search_path = $PINNED_SEARCH_PATH" \
       -f "$SOURCE_DIR/$f" > "$log" 2>&1
  rc=$?
  t1="$(date +%s.%N)"
  secs="$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b - a}')"

  if [ "$rc" -eq 0 ]; then
    printf '%03d\t%s\t%s\t%s\t%s\tAPPLIED\n' "$n" "$f" "$sha" "$rc" "$secs" >> "$LEDGER"
    applied=$((applied + 1))
    echo "OK   [$n/$COUNT] $f (${secs}s)"
  else
    printf '%03d\t%s\t%s\t%s\t%s\tFAILED\n' "$n" "$f" "$sha" "$rc" "$secs" >> "$LEDGER"
    echo "FAIL [$n/$COUNT] $f rc=$rc (${secs}s)" >&2
    echo "----- error tail ($log) -----" >&2
    tail -25 "$log" >&2
    echo "----- end -----" >&2
    echo "APPLIED=$applied FAILED_AT=$f LEDGER=$LEDGER" >&2
    exit 1
  fi
done

echo "ALL_APPLIED applied=$applied selected=$COUNT source=$SOURCE_DIR"
echo "LEDGER=$LEDGER"
echo "LEDGER_SHA256=$(sha256sum "$LEDGER" | cut -d' ' -f1)"


