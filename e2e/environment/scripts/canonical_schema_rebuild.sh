#!/usr/bin/env bash
# ============================================================================
# CT-SCHEMA-02 — canonical from-zero schema rebuild (deterministic, fail-closed)
# ----------------------------------------------------------------------------
# Builds the canonical CarbonTally schema on a BRAND-NEW disposable target, using
# the two-layer model CT-SCHEMA-01 established, then verifies the result against
# the CT-SCHEMA-01 canonical inventory and fingerprint.
#
#   LAYER 1  PLATFORM      Supabase Postgres image + the real Storage service
#                          (provisions auth.*, storage.buckets/objects/foldername)
#   LAYER 2  APPLICATION   the canonical migrations + the D32 operator step
#                          (89 files for --profile ct-schema-02, 92 with the
#                          three CT-IMPLEMENT-02 migrations, 93 with
#                          --profile ct-implement-02 — which also carries the
#                          CT-FINAL-01 storage migration)
#
# CANONICAL SEQUENCE (dependency order — F-03):
#
#   PHASE A  platform prerequisites (fail closed if Storage is absent)
#   PHASE B  migrations 1-26          (creates public.organization_members,
#                                      which the D32 predicates reference)
#   PHASE C  D32 operator step        (private documents bucket + the four
#                                      provider-context policies) + behavioural
#                                      policy-semantics proof
#   PHASE D  migrations 27-89         (migration 27 validates what PHASE C created)
#   VERIFY   canonical inventory + fingerprint + migration-set + D32 + P17/P16R
#
# FAIL-CLOSED: any missing platform object, wrong migration count, failed
# migration, unverifiable policy, unexpected fingerprint or anon/public policy
# aborts the run with a non-zero exit. Nothing is downgraded to a warning.
#
# Usage: canonical_schema_rebuild.sh [options]
#   --prefix <name>     container/volume name prefix (default ct_schema02)
#   --port <port>       host port for the target Postgres (default 55460)
#   --profile <p>       ct-schema-02 (default) or ct-implement-02
#   --image <ref>       Postgres image (default the pinned Supabase image)
#   --storage-image <r> Storage image (default the pinned storage-api image)
#   --reuse             use the existing container/volume instead of a new one
#   --destroy           destroy the disposable target at the end (default: keep)
#   --keep-evidence <d> evidence directory (default /tmp/ct_schema02_evidence)
#   --dry-run           print the plan and exit
#
# Environment overrides: CT02_ANON_KEY / CT02_SERVICE_KEY / CT02_JWT_SECRET let a
# non-disposable environment supply its own Storage key material. The default is
# to generate a disposable pair per run: NO key material is stored in this file.
#
# This script only ever creates/modifies labelled disposable infrastructure
# (container/volume it names itself). It never touches a durable environment.
# ============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

PREFIX="${CT_SCHEMA02_PREFIX:-ct_schema02}"
PORT="${CT_SCHEMA02_PORT:-55460}"
PG_IMAGE="${CT_SCHEMA02_PG_IMAGE:-public.ecr.aws/supabase/postgres:17.6.1.159}"
STORAGE_IMAGE="${CT_SCHEMA02_STORAGE_IMAGE:-public.ecr.aws/supabase/storage-api:v1.69.0}"
STORAGE_FREEZE_AT="${CT_SCHEMA02_STORAGE_FREEZE_AT:-optimize-existing-functions-again}"
EVIDENCE="/tmp/ct_schema02_evidence"
REUSE=0
DESTROY=0
DRY_RUN=0
PROVIDER_ROLE="supabase_admin"
MIGRATION_ROLE="postgres"

# ---------------------------------------------------------------------------
# PROFILE — which canonical chain to build and verify
# ---------------------------------------------------------------------------
# ct-schema-02 (default) : the frozen 89-migration CT-SCHEMA-01/02 baseline.
# ct-implement-02        : the same baseline with the three CT-IMPLEMENT-02
#                          migrations appended (92 total). The verifier proves
#                          the baseline itself is unchanged, so extending the
#                          chain can never mask a modification to an earlier
#                          migration.
PROFILE="${CT_SCHEMA02_PROFILE:-ct-schema-02}"

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix)        PREFIX="$2"; shift 2 ;;
    --port)          PORT="$2"; shift 2 ;;
    --image)         PG_IMAGE="$2"; shift 2 ;;
    --storage-image) STORAGE_IMAGE="$2"; shift 2 ;;
    --evidence)      EVIDENCE="$2"; shift 2 ;;
    --profile)       PROFILE="$2"; shift 2 ;;
    --reuse)         REUSE=1; shift ;;
    --destroy)       DESTROY=1; shift ;;
    --dry-run)       DRY_RUN=1; shift ;;
    -h|--help)       sed -n '2,45p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)               echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

PG="${PREFIX}_pg"
VOLUME="${PREFIX}_pgdata"
STORAGE="${PREFIX}_storage"
ENVFILE="/tmp/${PREFIX}.env"
DB=postgres

log()  { echo "[$(date +%H:%M:%S)] $*"; }
fail() { echo "ABORT: $*" >&2; exit 1; }

if [ "$DRY_RUN" = "1" ]; then
  cat <<EOF
CANONICAL SCHEMA REBUILD PLAN (dry run)
  target containers : ${PG} (postgres ${PG_IMAGE}), ${STORAGE} (${STORAGE_IMAGE})
  target volume     : ${VOLUME}
  host port         : 127.0.0.1:${PORT}
  database          : ${DB}
  provider role     : ${PROVIDER_ROLE}   (D32 operator step only — provider privilege)
  migration role    : ${MIGRATION_ROLE}  (migrations 1-26 and 27-89, pinned search_path)
  phases            : A platform -> B migrations 1-26 -> C D32 operator (+semantics)
                      -> D migrations 27-89 -> VERIFY canonical inventory/fingerprint
  evidence dir      : ${EVIDENCE}
EOF
  exit 0
fi

mkdir -p "$EVIDENCE" || fail "cannot create evidence directory $EVIDENCE"

psql_provider() { PGPASSWORD="$PW" psql -h 127.0.0.1 -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 "$@"; }
scalar_provider() { PGPASSWORD="$PW" psql -h 127.0.0.1 -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -A -t -c "$1"; }

# ===========================================================================
# PHASE A — platform prerequisites (LAYER 1)
# ===========================================================================
log "PHASE A — provisioning a brand-new disposable target"

if [ "$REUSE" = "1" ]; then
  [ -f "$ENVFILE" ] || fail "--reuse given but $ENVFILE (holding the target password) is absent"
  # shellcheck disable=SC1090
  . "$ENVFILE"
  PW="${CT02_PW:-}"
  [ -n "$PW" ] || fail "$ENVFILE does not define CT02_PW"
  log "reusing the existing target $PG (credentials read from $ENVFILE)"
else
  if docker ps -a --format '{{.Names}}' | grep -qx "$PG"; then
    fail "container $PG already exists — refusing to adopt it implicitly (use --reuse, or another --prefix)"
  fi
  if docker volume ls --format '{{.Name}}' | grep -qx "$VOLUME"; then
    fail "volume $VOLUME already exists — refusing to adopt it implicitly (use --reuse, or another --prefix)"
  fi

  PW="$(openssl rand -hex 16)"
  umask 077
  printf "export CT02_PW='%s'\n" "$PW" > "$ENVFILE"
  chmod 600 "$ENVFILE"

  log "creating volume $VOLUME and container $PG (image $PG_IMAGE)"
  docker volume create "$VOLUME" >/dev/null || fail "could not create volume $VOLUME"
  docker run -d --name "$PG" \
    --label ct.schema02.task=CT-SCHEMA-02-20260927 \
    --label ct.schema02.disposable=true \
    -e POSTGRES_PASSWORD="$PW" -e POSTGRES_USER="$PROVIDER_ROLE" -e POSTGRES_DB="$DB" \
    -p "127.0.0.1:$PORT:5432" -v "$VOLUME":/var/lib/postgresql/data "$PG_IMAGE" >/dev/null \
    || fail "could not start container $PG"
fi

# Readiness: the Supabase image restarts the server during initialisation, so a
# successful `pg_isready` (or even a single query) can land inside that restart
# window. Require two consecutive successful in-container queries instead.
log "waiting for PostgreSQL readiness (max 300s)"
ready=0
for _ in $(seq 1 150); do
  if docker exec "$PG" psql -U "$PROVIDER_ROLE" -d "$DB" -Atc "select 1" >/dev/null 2>&1; then
    sleep 3
    if docker exec "$PG" psql -U "$PROVIDER_ROLE" -d "$DB" -Atc "select 1" >/dev/null 2>&1; then
      ready=1
      break
    fi
  fi
  sleep 2
done
[ "$ready" = "1" ] || fail "PostgreSQL in $PG did not become ready"

{
  echo "=== PHASE A target identity ==="
  docker inspect "$PG" --format 'container={{.Name}} id={{.Id}} image={{.Config.Image}} started={{.State.StartedAt}}'
  docker inspect "$VOLUME" --format 'volume={{.Name}} created={{.CreatedAt}}'
  scalar_provider "select 'postgres_version='||version();"
  scalar_provider "select 'server_version='||current_setting('server_version');"
} | tee "$EVIDENCE/phase_a_identity.txt"

# The migration role needs a usable password on this disposable target (the image
# sets one only for the superuser role that initialises the cluster).
psql_provider -c "ALTER ROLE $MIGRATION_ROLE WITH LOGIN PASSWORD '$PW';" \
  || fail "could not set a password for the migration role $MIGRATION_ROLE"

# A fresh target must contain no CarbonTally application tables.
EMPTY_PUBLIC="$(scalar_provider "select count(*) from information_schema.tables where table_schema='public';")"
log "fresh target public tables: $EMPTY_PUBLIC"
[ "$EMPTY_PUBLIC" = "0" ] || fail "target is not empty ($EMPTY_PUBLIC public objects present); PHASE A requires a brand-new target"

# Platform: the real Supabase Storage service provisions storage.* through its own
# migrations. It is provisioned — never fabricated.
log "starting the platform Storage service ($STORAGE_IMAGE)"
psql_provider -c "GRANT CREATE, USAGE ON SCHEMA storage TO supabase_storage_admin;" \
  || fail "could not grant the storage admin role the privileges the Storage service needs"
docker rm -f "$STORAGE" >/dev/null 2>&1 || true
# Storage credentials for the DISPOSABLE target: generated per run.
# No key material is stored in this script (AGENTS.md §70). The Storage service
# verifies its bearer tokens against AUTH_JWT_SECRET, so a freshly signed
# anon/service_role pair is sufficient for the disposable probe container;
# a non-disposable environment supplies its own material through
# CT02_ANON_KEY / CT02_SERVICE_KEY / CT02_JWT_SECRET.
if [ -n "${CT02_ANON_KEY:-}" ] && [ -n "${CT02_SERVICE_KEY:-}" ] && [ -n "${CT02_JWT_SECRET:-}" ]; then
  ANON_KEY="$CT02_ANON_KEY"; SERVICE_KEY="$CT02_SERVICE_KEY"; AUTH_JWT_SECRET="$CT02_JWT_SECRET"
  log "using caller-supplied Storage key material (CT02_* environment)"
else
  AUTH_JWT_SECRET="$(openssl rand -hex 32)"
  mapfile -t STORAGE_KEYS < <(python3 - "$AUTH_JWT_SECRET" <<'PY_KEYGEN'
import base64, hashlib, hmac, json, sys
secret = sys.argv[1].encode()
b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
def token(role):
    payload = b64(json.dumps({"iss": "supabase-demo", "role": role, "exp": 4102444800},
                             separators=(",", ":")).encode())
    sig = b64(hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"
print(token("anon"))
print(token("service_role"))
PY_KEYGEN
  )
  ANON_KEY="${STORAGE_KEYS[0]:-}"; SERVICE_KEY="${STORAGE_KEYS[1]:-}"
  [ -n "$ANON_KEY" ] && [ -n "$SERVICE_KEY" ] || fail "could not generate Storage key material"
  log "generated per-run Storage key material (nothing key-shaped is stored in this script)"
fi
docker run -d --name "$STORAGE" \
  --label ct.schema02.task=CT-SCHEMA-02-20260927 \
  --label ct.schema02.disposable=true \
  --network "container:$PG" \
  -e DATABASE_URL="postgresql://supabase_storage_admin:$PW@127.0.0.1:5432/$DB" \
  -e VECTOR_DATABASE_URL="postgresql://$PROVIDER_ROLE:$PW@127.0.0.1:5432/$DB" \
  -e ANON_KEY="$ANON_KEY" \
  -e SERVICE_KEY="$SERVICE_KEY" \
  -e AUTH_JWT_SECRET="$AUTH_JWT_SECRET" \
  -e TENANT_ID=stub -e STORAGE_BACKEND=file -e FILE_STORAGE_BACKEND_PATH=/mnt \
  -e STORAGE_S3_REGION=local -e GLOBAL_S3_BUCKET=stub -e FILE_SIZE_LIMIT=52428800 \
  -e ENABLE_IMAGE_TRANSFORMATION=false -e DB_MIGRATIONS_FREEZE_AT="$STORAGE_FREEZE_AT" \
  -e VECTOR_ENABLED=true -e VECTOR_STORE_MIGRATIONS_ENABLED=true \
  "$STORAGE_IMAGE" >/dev/null || fail "could not start the platform Storage service"

log "waiting for the platform Storage layer (max 300s)"
storage_ready=0
for _ in $(seq 1 150); do
  if [ "$(scalar_provider "select count(*) from information_schema.tables where table_schema='storage' and table_name='objects';" 2>/dev/null)" = "1" ]; then
    storage_ready=1; break
  fi
  sleep 2
done
if [ "$storage_ready" != "1" ]; then
  docker logs --tail 25 "$STORAGE" 2>&1 | grep -viE 'jwt|key|secret|token' | tail -25
  fail "platform prerequisite missing: the Supabase Storage layer was not provisioned by the Storage service. The application chain cannot run on a bare Postgres baseline (F-01). Never fabricate platform tables."
fi

PLATFORM_OK="$(scalar_provider "select (to_regclass('storage.buckets') is not null and to_regclass('storage.objects') is not null and to_regprocedure('storage.foldername(text)') is not null and to_regprocedure('auth.uid()') is not null and exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='storage' and c.relname='objects' and c.relrowsecurity))::text")"
[ "$PLATFORM_OK" = "true" ] || fail "platform prerequisite check failed (need storage.buckets, storage.objects, storage.foldername(text), auth.uid(), RLS on storage.objects)"
log "PHASE A complete — platform layer present (storage.buckets, storage.objects, storage.foldername, auth.uid(), RLS on storage.objects)"

export E2E_DB_HOST=127.0.0.1
export E2E_DB_PORT="$PORT"
export E2E_DB_NAME="$DB"
export E2E_DB_PASSWORD="$PW"

# ===========================================================================
# PHASE B — migrations 1-26 (application layer, before the operator step)
# ===========================================================================
log "PHASE B — applying migrations 1-26 as $MIGRATION_ROLE"
E2E_DB_USER="$MIGRATION_ROLE" bash "$SCRIPT_DIR/apply_migrations.sh" \
  --from 1 --to 26 --expect-count 26 --require-storage \
  --ledger "$EVIDENCE/ledger_phase_b.tsv" --logs "$EVIDENCE/logs_phase_b" \
  > "$EVIDENCE/phase_b.txt" 2>&1
rc=$?
tail -6 "$EVIDENCE/phase_b.txt"
[ "$rc" -eq 0 ] || fail "PHASE B failed: migrations 1-26 did not all apply (see $EVIDENCE/phase_b.txt)"

DEP_OK="$(scalar_provider "select (to_regclass('public.organization_members') is not null)::text")"
[ "$DEP_OK" = "true" ] || fail "PHASE C cannot run: public.organization_members is absent after migrations 1-26"
log "PHASE B complete — 26/26 applied; public.organization_members present (D32 dependency satisfied)"

# ===========================================================================
# PHASE C — D32 operator step (provider context) + behavioural semantics proof
# ===========================================================================
log "PHASE C — D32 operator step: private documents bucket + four provider-context policies"
PGPASSWORD="$PW" psql -h 127.0.0.1 -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 \
  -f "$SCRIPT_DIR/d32_storage_operator.sql" > "$EVIDENCE/phase_c_operator.txt" 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then
  cat "$EVIDENCE/phase_c_operator.txt" >&2
  fail "PHASE C failed: the D32 operator step did not complete (see $EVIDENCE/phase_c_operator.txt)"
fi
log "PHASE C — operator step OK; proving policy semantics behaviourally (rolled back)"
PGPASSWORD="$PW" psql -h 127.0.0.1 -p "$PORT" -U "$MIGRATION_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 \
  -f "$SCRIPT_DIR/verify_d32_policy_semantics.sql" > "$EVIDENCE/phase_c_semantics.txt" 2>&1
rc=$?
tail -8 "$EVIDENCE/phase_c_semantics.txt"
[ "$rc" -eq 0 ] || fail "PHASE C failed: the D32 behavioural policy-semantics proof did not pass (see $EVIDENCE/phase_c_semantics.txt)"

# Idempotency: the operator step must converge, not duplicate (RUN 2 against the
# already prepared target), and the behavioural proof must still hold.
log "PHASE C — idempotency re-run of the operator step"
BEFORE="$(scalar_provider "select count(*) from pg_policies where schemaname='storage' and tablename='objects';")"
PGPASSWORD="$PW" psql -h 127.0.0.1 -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 \
  -f "$SCRIPT_DIR/d32_storage_operator.sql" > "$EVIDENCE/phase_c_operator_rerun.txt" 2>&1 \
  || fail "PHASE C idempotency re-run failed (see $EVIDENCE/phase_c_operator_rerun.txt)"
AFTER="$(scalar_provider "select count(*) from pg_policies where schemaname='storage' and tablename='objects';")"
log "storage.objects policies before=$BEFORE after=$AFTER"
[ "$BEFORE" = "4" ] && [ "$AFTER" = "4" ] || fail "D32 operator step is not idempotent: policy count $BEFORE -> $AFTER (must stay 4)"
BUCKETS="$(scalar_provider "select count(*) from storage.buckets where name='documents';")"
[ "$BUCKETS" = "1" ] || fail "D32 operator step duplicated the documents bucket ($BUCKETS rows)"
log "PHASE C complete — operator step idempotent (4 policies, 1 bucket, unchanged on re-run)"

case "$PROFILE" in
  ct-schema-02)    MIG_TO="89"; MIG_EXPECT="63" ;;
  # CT-FINAL-01 extended the canonical chain to 93 files (the CT-FINAL-01
  # documents-bucket storage migration is the 93rd); PHASE D applies 27-93.
  ct-implement-02) MIG_TO="93"; MIG_EXPECT="67" ;;
  *) fail "unknown --profile '$PROFILE' (expected ct-schema-02 or ct-implement-02)" ;;
esac
log "profile=$PROFILE (migrations 27-$MIG_TO in PHASE D, expected $MIG_EXPECT)"

# ===========================================================================
# PHASE D — migrations 27-89 (migration 27 validates what PHASE C created)
# ===========================================================================
log "PHASE D — applying migrations 27-$MIG_TO as $MIGRATION_ROLE"
E2E_DB_USER="$MIGRATION_ROLE" bash "$SCRIPT_DIR/apply_migrations.sh" \
  --from 27 --to "$MIG_TO" --expect-count "$MIG_EXPECT" --require-storage \
  --ledger "$EVIDENCE/ledger_phase_d.tsv" --logs "$EVIDENCE/logs_phase_d" \
  > "$EVIDENCE/phase_d.txt" 2>&1
rc=$?
tail -6 "$EVIDENCE/phase_d.txt"
[ "$rc" -eq 0 ] || fail "PHASE D failed: migrations 27-89 did not all apply (see $EVIDENCE/phase_d.txt)"

# Independent apply ledger over the whole canonical sequence.
{
  head -1 "$EVIDENCE/ledger_phase_b.tsv"
  grep -v '^seq' "$EVIDENCE/ledger_phase_b.tsv"
  grep -v '^seq' "$EVIDENCE/ledger_phase_d.tsv"
} > "$EVIDENCE/ledger_canonical.tsv"
printf 'ledger_rows_excluding_header=%s\n' "$(( $(wc -l < "$EVIDENCE/ledger_canonical.tsv") - 1 ))"
printf 'applied=%s failed=%s\n' \
  "$(grep -c APPLIED "$EVIDENCE/ledger_canonical.tsv")" \
  "$(grep -c FAILED "$EVIDENCE/ledger_canonical.tsv")"
printf 'distinct_files=%s\n' "$(cut -f2 "$EVIDENCE/ledger_canonical.tsv" | grep -v '^file$' | sort -u | wc -l)"
printf 'ledger_sha256=%s\n' "$(sha256sum "$EVIDENCE/ledger_canonical.tsv" | cut -d' ' -f1)"

# ===========================================================================
# VERIFY — canonical inventory, fingerprint, migration set, D32, P17/P16R
# ===========================================================================
log "VERIFY — canonical schema verification"
E2E_DB_USER="$MIGRATION_ROLE" python3 "$SCRIPT_DIR/canonical_schema_verify.py" \
  --profile "$PROFILE" \
  --host 127.0.0.1 --port "$PORT" --db "$DB" --dump-inventory "$EVIDENCE/inventory" \
  --json "$EVIDENCE/verify.json" > "$EVIDENCE/verify.txt" 2>&1
ver=$?
tail -12 "$EVIDENCE/verify.txt"

if [ "$DESTROY" = "1" ]; then
  log "destroying the disposable target ($PG, $STORAGE, $VOLUME)"
  docker rm -f "$STORAGE" >/dev/null 2>&1 || true
  docker rm -f "$PG" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  rm -f "$ENVFILE"
fi

if [ "$ver" -eq 0 ]; then
  log "REBUILD VERIFIED — canonical schema reproduced (see $EVIDENCE)"
  exit 0
fi
fail "REBUILD VERIFICATION FAILED — the rebuilt schema does not match the CT-SCHEMA-01 canonical inventory/fingerprint (see $EVIDENCE/verify.txt). Do not normalise the difference away: determine whether it comes from the implementation, platform provisioning, migration ordering or drift."




