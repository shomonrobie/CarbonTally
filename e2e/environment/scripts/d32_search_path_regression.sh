#!/usr/bin/env bash
# ============================================================================
# CT-SCHEMA-02 — D32 validation: search_path regression + non-weakening proof
# ----------------------------------------------------------------------------
# F-02 was: migration 27 validated the *deparsed* predicate text returned by
# ``pg_policies``, which PostgreSQL renders relative to the session
# ``search_path``. The same, unchanged policy therefore deparsed as
# ``auth.uid()`` for the migration role and as ``uid()`` for ``supabase_admin``
# (whose search_path includes ``auth``), and the migration's own text fragments
# were matched as substrings (so ``myauth.uid()`` would have passed).
#
# This script proves, on a disposable canonical target:
#
#   R1  the PRE-REVISION migration FAILS as supabase_admin   (old risk, reproduced)
#   R2  the PRE-REVISION migration PASSES as postgres        (…because of that role's search_path)
#   R3  the REVISED migration PASSES as supabase_admin       (fix: no role dependence)
#   R4  the REVISED migration PASSES with search_path forced to auth,public
#   R5  the REVISED migration PASSES with search_path forced to pg_catalog
#   R6  a policy calling a LOOK-ALIKE myauth.uid() is PASSED by the PRE-REVISION
#       validator and REJECTED by the REVISED one            (no weakening)
#   R7  a policy missing an approved org-scope fragment is REJECTED (drift still caught)
#   R8  the target is restored afterwards (4 policies, 1 private bucket)
#
# MUTATION SCOPE: R6/R7 temporarily replace exactly one of the four approved
# policies on the disposable target and restore it with the operator step. The
# look-alike function lives in a schema created (and dropped) by this script.
# Nothing outside the target is touched; the target guard below refuses
# protected database names.
#
# PRE-REVISION ARTEFACT (CT-RELEASE-04): R1/R2/R6a run the CT-SCHEMA-01-verified
# validator, i.e. the D32 file as it stood BEFORE the
# P8-D17-D32-STORAGE-POLICY-VALIDATION-DETERMINISM-001 revision. That revision is
# now committed, so the artefact is carried as a byte-identical committed fixture
# (``fixtures/d32_pre_revision_ct_schema_01.sql``) with a pinned sha256 and git
# blob hash, instead of being read back from ``git HEAD``. Nothing below depends
# on the state of the worktree or on git history.
#
# Usage: d32_search_path_regression.sh --password <pw> [options]
#   --host/--port/--db   target (defaults E2E_DB_*)
#   --password <pw>      password for both roles (required)
#   --provider-role <r>  default supabase_admin
#   --migration-role <r> default postgres
#   --evidence <dir>     evidence directory (default /tmp/ct_schema02_evidence)
# ============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MIG="$REPO_ROOT/supabase/migrations/20260823000000_d32_private_documents_storage.sql"

HOST="${E2E_DB_HOST:-127.0.0.1}"
PORT="${E2E_DB_PORT:-55326}"
DB="${E2E_DB_NAME:-postgres}"
PROVIDER_ROLE="supabase_admin"
MIGRATION_ROLE="postgres"
PW=""
EVIDENCE="/tmp/ct_schema02_evidence"

while [ $# -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --db)   DB="$2"; shift 2 ;;
    --password) PW="$2"; shift 2 ;;
    --provider-role) PROVIDER_ROLE="$2"; shift 2 ;;
    --migration-role) MIGRATION_ROLE="$2"; shift 2 ;;
    --evidence) EVIDENCE="$2"; shift 2 ;;
    -h|--help) sed -n '2,38p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

[ -n "$PW" ] || { echo "ABORT: --password is required" >&2; exit 2; }
case "$DB" in
  *qa*|*demo*|*investor*|*prod*|*live*|*production*)
    [ "${CT_ALLOW_PROTECTED_TARGET:-0}" = "1" ] || { echo "ABORT: refusing protected target database '$DB'" >&2; exit 2; } ;;
esac

mkdir -p "$EVIDENCE" || exit 2
PASSED=0
FAILED=0

say() { printf '%s\n' "$*"; }
ok()  { PASSED=$((PASSED + 1)); say "PASS  $1"; }
bad() { FAILED=$((FAILED + 1)); say "FAIL  $1"; }

# Run one migration file under a given role, optionally with a forced search_path.
#   run_migration <label> <role> <search_path|-> <file> <expect: pass|fail> <expected-message>
run_migration() {
  local label="$1" role="$2" sp="$3" file="$4" expect="$5" want_msg="${6:-}"
  local out="$EVIDENCE/regression_${label}.txt"
  local args=(-h "$HOST" -p "$PORT" -U "$role" -d "$DB" -X -q -v ON_ERROR_STOP=1)
  if [ "$sp" != "-" ]; then args+=(-c "SET search_path = $sp"); fi
  args+=(-f "$file")
  PGPASSWORD="$PW" psql "${args[@]}" > "$out" 2>&1
  local rc=$?
  local body; body="$(sed 's/^psql:[^ ]* //' "$out")"
  if [ "$expect" = "pass" ]; then
    if [ "$rc" -eq 0 ]; then ok "$label (rc=0)"; else bad "$label (expected success, rc=$rc): $(printf '%s' "$body" | tail -3 | tr '\n' ' ')"; fi
  else
    if [ "$rc" -eq 0 ]; then
      bad "$label (expected a rejection, but the migration passed)"
    elif [ -n "$want_msg" ] && ! printf '%s' "$body" | grep -qF "$want_msg"; then
      bad "$label (rejected, but not for the expected reason; wanted: $want_msg)"
    else
      ok "$label (rejected: $(printf '%s' "$body" | grep -m1 -o 'D32[^"]*' | head -c 110))"
    fi
  fi
  { printf '%s\n' "--- $label (role=$role search_path=$sp expect=$expect rc=$rc)"; printf '%s\n' "$body"; } >> "$EVIDENCE/regression_all.txt"
}

# Replace one approved policy with a doctored predicate (provider context).
set_policy() {  # $1 policy name, $2 cmd, $3 predicate
  PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 -c \
    "DROP POLICY IF EXISTS $1 ON storage.objects; CREATE POLICY $1 ON storage.objects FOR $2 TO authenticated USING ($3)" \
    >/dev/null 2>&1 || { bad "could not set the doctored policy $1"; return 1; }
}

restore() {  # re-assert the four approved policies
  PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 \
    -f "$SCRIPT_DIR/d32_storage_operator.sql" >/dev/null 2>&1 || { bad "operator step could not restore the approved policies"; return 1; }
}

: > "$EVIDENCE/regression_all.txt"
say "=== CT-SCHEMA-02 D32 search_path regression (target $MIGRATION_ROLE/$PROVIDER_ROLE@$HOST:$PORT/$DB) ==="

# Evidence: the ambient search_path of each role is what triggered F-02.
for role in "$PROVIDER_ROLE" "$MIGRATION_ROLE"; do
  sp="$(PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$role" -d "$DB" -X -q -A -t -c 'show search_path' 2>&1)"
  say "ambient search_path of $role: $sp"
  printf 'ambient search_path %s = %s\n' "$role" "$sp" >> "$EVIDENCE/regression_all.txt"
done

# Pre-revision migration — the CT-SCHEMA-01-verified artefact, carried as a
# committed fixture (CT-RELEASE-04). Identity is asserted here so a modified or
# mistaken copy can never turn R1/R2/R6a into a vacuous pass, and the fixture is
# asserted to differ from the current migration (otherwise the regression would
# compare the revised validator with itself).
PRE_REVISION_SHA256="45d9eb87da8aec7bd824b858d7a55af6c2c6d340da2d8d01e91401c6e5421798"
PRE_REVISION_BLOB="66a8ddf87e9eaca36a2135214fec9c0afd8334bb"
OLD="$SCRIPT_DIR/fixtures/d32_pre_revision_ct_schema_01.sql"
[ -f "$OLD" ] || { echo "ABORT: the pre-revision fixture $OLD is missing" >&2; exit 2; }
if command -v sha256sum >/dev/null 2>&1; then
  old_sha="$(sha256sum "$OLD" | cut -d' ' -f1)"; mig_sha="$(sha256sum "$MIG" | cut -d' ' -f1)"
elif command -v shasum >/dev/null 2>&1; then
  old_sha="$(shasum -a 256 "$OLD" | cut -d' ' -f1)"; mig_sha="$(shasum -a 256 "$MIG" | cut -d' ' -f1)"
else
  echo "ABORT: neither sha256sum nor shasum is available to verify the fixture" >&2; exit 2
fi
[ "$old_sha" = "$PRE_REVISION_SHA256" ] || {
  echo "ABORT: pre-revision fixture sha256=$old_sha does not match the recorded artefact $PRE_REVISION_SHA256" >&2; exit 2; }
[ "$old_sha" != "$mig_sha" ] || {
  echo "ABORT: the pre-revision fixture is identical to the current D32 migration — the regression would prove nothing" >&2; exit 2; }
if command -v git >/dev/null 2>&1; then
  old_blob="$(git -C "$REPO_ROOT" hash-object "$OLD" 2>/dev/null)"
  [ "$old_blob" = "$PRE_REVISION_BLOB" ] || {
    echo "ABORT: pre-revision fixture blob=$old_blob does not match the recorded CT-SCHEMA-01 blob $PRE_REVISION_BLOB" >&2; exit 2; }
  say "pre-revision artefact: fixture sha256=$old_sha blob=$old_blob (recorded CT-SCHEMA-01 artefact; current=$mig_sha)"
else
  say "pre-revision artefact: fixture sha256=$old_sha (git unavailable — blob identity not re-checked; current=$mig_sha)"
fi

say ""
say "--- reproducing the old risk (pre-revision validator) ---"
run_migration R1_pre_revision_as_provider_role "$PROVIDER_ROLE" -           "$OLD" fail 'missing the approved org-scope fragment "auth.uid()"'
run_migration R2_pre_revision_as_migration_role "$MIGRATION_ROLE" -         "$OLD" pass
run_migration R2b_pre_revision_forced_pg_catalog "$MIGRATION_ROLE" pg_catalog "$OLD" pass

say ""
say "--- the revised validator is search_path independent ---"
run_migration R3_revised_as_provider_role "$PROVIDER_ROLE" -              "$MIG" pass
run_migration R4_revised_forced_auth_public "$MIGRATION_ROLE" 'auth, public' "$MIG" pass
run_migration R5_revised_forced_pg_catalog "$MIGRATION_ROLE" pg_catalog   "$MIG" pass
run_migration R5b_revised_provider_forced_auth "$PROVIDER_ROLE" 'auth, public' "$MIG" pass

say ""
say "--- the validation is not weakened: a look-alike function is rejected ---"
PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 -c \
  "CREATE SCHEMA IF NOT EXISTS myauth; CREATE OR REPLACE FUNCTION myauth.uid() RETURNS uuid LANGUAGE sql STABLE AS \$\$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid \$\$;" \
  >/dev/null 2>&1 || bad "could not create the look-alike myauth.uid() function"

LOOKALIKE="bucket_id = 'documents' AND (storage.foldername(name))[1] = 'uploads' AND (storage.foldername(name))[2]::uuid IN (SELECT organization_id FROM public.organization_members WHERE user_id = myauth.uid() AND is_active = TRUE)"
if set_policy d32_documents_select_org_member SELECT "$LOOKALIKE"; then
  # The old validator matched fragments as substrings, so 'myauth.uid()' satisfied
  # 'auth.uid()' — the wrong function was accepted.
  run_migration R6a_pre_revision_accepts_lookalike_function "$MIGRATION_ROLE" - "$OLD" pass
  run_migration R6b_revised_rejects_lookalike_function "$MIGRATION_ROLE" - "$MIG" fail 'does not call the approved session-identity function'
fi

say ""
say "--- drift is still caught ---"
restore
DRIFT="bucket_id = 'documents' AND (storage.foldername(name))[2]::uuid IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid() AND is_active = TRUE)"
if set_policy d32_documents_select_org_member SELECT "$DRIFT"; then
  run_migration R7_revised_rejects_missing_fragment "$MIGRATION_ROLE" - "$MIG" fail 'missing the approved org-scope fragment'
fi

say ""
say "--- restore and confirm the target is unchanged ---"
restore
POLICIES="$(PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -A -t -c \
  "select count(*) from pg_policies where schemaname='storage' and tablename='objects'" 2>&1)"
BUCKETS="$(PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -A -t -c \
  "select count(*) from storage.buckets where name='documents' and public = false" 2>&1)"
PGPASSWORD="$PW" psql -h "$HOST" -p "$PORT" -U "$PROVIDER_ROLE" -d "$DB" -X -q -v ON_ERROR_STOP=1 \
  -c "DROP SCHEMA IF EXISTS myauth CASCADE;" >/dev/null 2>&1
[ "$POLICIES" = "4" ] && ok "R8 target restored (4 storage.objects policies)" || bad "R8 policy count after restore: $POLICIES (expected 4)"
[ "$BUCKETS" = "1" ] && ok "R8 documents bucket still private and single" || bad "R8 documents bucket check: $BUCKETS (expected 1)"
run_migration R9_revised_final_pass "$MIGRATION_ROLE" - "$MIG" pass

say ""
say "=== RESULT: $PASSED passed, $FAILED failed ==="
[ "$FAILED" -eq 0 ] || exit 1
exit 0

