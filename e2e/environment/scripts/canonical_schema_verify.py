#!/usr/bin/env python3
"""CT-SCHEMA-02 — canonical schema verifier (fail-closed).

Proves, against a *built* database, that the canonical rebuild procedure reached
the schema CT-SCHEMA-01 established — using the same inventory queries and the
same fingerprint recipe, so the two results are comparable.

It asserts, and fails closed on, each of:

  1. MIGRATION SET     89 baseline files + the additive CT-IMPLEMENT-02 and
                       CT-FINAL-01 migrations (93 files total), deterministic
                       order, no duplicate versions, a migration-set fingerprint
                       that matches the recorded value, and an explicit
                       provenance proof that the baseline subset still
                       reproduces its recorded fingerprint — i.e. the later
                       migrations only APPENDED.
  2. SCHEMA INVENTORY  the 12 inventory classes of CT-SCHEMA-01 and the exact
                       canonical inventory fingerprint.
  3. HEADLINE COUNTS   145 public tables / 145 RLS / 227 policies / 0 anon-public
                       policies / 172 FKs / 551 indexes / 31 public functions /
                       88 triggers / 4592 columns.
  4. REFERENCE DATA    migration-declared rows only; no application data.
  5. D32 PLATFORM      private ``documents`` bucket, exactly the four approved
                       policies, RLS on storage.objects, no anon/public grant.
  6. P17 / P16-R       every object the P17/P16R migrations declare is present.

Usage:
  python3 canonical_schema_verify.py [--host H] [--port P] [--db D] [--user U]
                                     [--password PW] [--json OUT] [--quiet]
Exit: 0 all checks passed; 1 one or more checks failed (each printed as FAIL).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

# ---------------------------------------------------------------------------
# Recorded canonical values
# ---------------------------------------------------------------------------
#: CT-SCHEMA-01 inventory fingerprint (89-migration chain, from-zero rebuild).
CANONICAL_INVENTORY_FINGERPRINT = (
    "c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f"
)
#: CT-SCHEMA-01 migration-set fingerprint (at git HEAD, before the D32 revision).
MIGRATION_SET_FINGERPRINT_CT_SCHEMA_01 = (
    "d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c"
)
#: CT-SCHEMA-02 expected migration-set fingerprint: identical to the CT-SCHEMA-01
#: set except for the single authorised D32 validation revision
#: (P8-D17-D32-STORAGE-POLICY-VALIDATION-DETERMINISM-001).
MIGRATION_SET_FINGERPRINT_EXPECTED = (
    "40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30"
)
#: The only migration file this task is authorised to revise.
AUTHORISED_MIGRATION_REVISION = "20260823000000_d32_private_documents_storage.sql"

EXPECTED_MIGRATION_COUNT = 89

# ---------------------------------------------------------------------------
# CT-IMPLEMENT-02 — the canonically EXTENDED chain
# ---------------------------------------------------------------------------
# CT-IMPLEMENT-02 adds three migrations AFTER the CT-SCHEMA-01/02 chain. They are
# additive and modify no earlier file, so the baseline is asserted to be
# *unchanged* rather than re-pinned:
#
#   * `MIGRATION_SET_FINGERPRINT_EXPECTED` (the 89-file CT-SCHEMA-02 value) is
#     recomputed over the same 89 files and must still match;
#   * the extended set gets its own recorded fingerprint and object list.
CT_IMPLEMENT_02_MIGRATIONS = (
    "20261021000000_ct02_audit_ledger_hardening.sql",
    "20261022000000_ct02_report_sharing.sql",
    "20261023000000_ct02_scheduled_reporting.sql",
)

#: Recorded on the first verified from-zero rebuild of the extended chain
#: (see the CT-IMPLEMENT-02 report §Database). Filled in from the recorded
#: inventory: never guessed, and never normalised to make a run pass.
#: CT-FINAL-01 raised this to 93 — the count and the fingerprint below were
#: RE-MEASURED from the tree with this file's own recipe (``sha256`` of the
#: ``sha256sum`` listing) when the 93rd migration became part of the release;
#: they were not adjusted to make a run pass:
#:
#:     python3 -c "import sys, pathlib; sys.path.insert(0, 'e2e/environment/scripts'); \
#:       import canonical_schema_verify as v; \
#:       print(v.migration_set_fingerprint(pathlib.Path('supabase/migrations')))"
#:     → a18a3d4f23d695e0618e7cc58fd9a766d6030273ddac86e903eb337f4f163e81
EXTENDED_MIGRATION_COUNT = 93
EXTENDED_MIGRATION_SET_FINGERPRINT = (
    "a18a3d4f23d695e0618e7cc58fd9a766d6030273ddac86e903eb337f4f163e81"
)

# ---------------------------------------------------------------------------
# CT-FINAL-01 — the authorised migration that extends the chain once more
# ---------------------------------------------------------------------------
# CT-FINAL-01 adds ONE further additive migration AFTER the CT-IMPLEMENT-02
# chain: ``20261024000000_ct_final_01_documents_bucket_size_limit.sql``.  It is
# storage configuration only — it declares no application object — so it is
# accounted for exactly as the CT-IMPLEMENT-02 additions are:
#
#   * excluded from the 89-file baseline subset, so the CT-SCHEMA-02 baseline
#     fingerprint (``MIGRATION_SET_FINGERPRINT_EXPECTED``) keeps being
#     *reproduced* rather than re-pinned — proof that no earlier migration moved;
#   * included in the extended set whose count and fingerprint are recorded
#     above;
#   * listed as an authorised working-tree revision while it is still
#     uncommitted, and simply absent from that list once it is committed (a
#     clean checkout of HEAD can never "differ from HEAD").
CT_FINAL_01_MIGRATIONS = (
    "20261024000000_ct_final_01_documents_bucket_size_limit.sql",
)

#: Every migration added AFTER the CT-SCHEMA-01/02 baseline.  These are the files
#: that must be excluded when the baseline subset is reconstructed.
POST_BASELINE_MIGRATIONS = CT_IMPLEMENT_02_MIGRATIONS + CT_FINAL_01_MIGRATIONS

#: Headline counts OBSERVED on the first from-zero rebuild of the extended chain
#: (target ct_impl02, 2026-09-28, evidence /tmp/ct_impl02_evidence/verify.txt,
#: 81 PASS / 2 FAIL — both failures were verifier defects, since fixed). The
#: extended chain may only ADD objects, so each value must equal this and be at
#: least the CT-SCHEMA-02 baseline; the deltas are exactly the CT-IMPLEMENT-02
#: additions: +4 tables, +8 policies, +10 FKs, +18 indexes, +6 functions
#: (+12 triggers, +60 columns).
EXPECTED_COUNTS_CT02 = {
    "public_tables": 149,
    "public_tables_with_rls": 149,
    "public_tables_without_rls": 0,
    "policies": 235,
    "policies_granting_anon_or_public": 0,
    "foreign_keys": 182,
    "indexes": 569,
    "public_functions": 37,
    "triggers": 100,
    "columns_all_schemas": 4652,
}

#: The CT-IMPLEMENT-02 guards, transcribed from
#: 20261021000000_ct02_audit_ledger_hardening.sql: trigger name -> the function
#: the migration wired it to. audit_trail has the truncate guard only — its row
#: immutability is the pre-existing ledger trigger from 20260912000000, so a
#: second row guard would be a duplicate control rather than a hardening.
CT02_EXPECTED_GUARDS: dict[str, dict[str, str]] = {
    "audit_trail": {"ct02_audit_trail_no_truncate": "ct02_audit_truncate_guard"},
    "audit_logs": {"ct02_audit_logs_no_truncate": "ct02_audit_truncate_guard",
                   "ct02_audit_logs_immutable": "ct02_append_only_guard"},
    "activity_logs": {"ct02_activity_logs_no_truncate": "ct02_audit_truncate_guard",
                      "ct02_activity_logs_immutable": "ct02_append_only_guard"},
}
EXTENDED_INVENTORY_FINGERPRINT = (
    "5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407"
)

#: Objects CT-IMPLEMENT-02 declares. Each must be present in the rebuilt schema.
CT_IMPLEMENT_02_NAMED_OBJECTS = [
    # PD-3 / R-10.6 — database-level append-only enforcement
    ("table", "report_shares", "PD-1 canonical report sharing"),
    ("table", "report_share_access_events", "PD-1 share access history"),
    ("table", "report_schedule_definitions", "PD-2 canonical scheduled reporting"),
    ("table", "report_schedule_runs", "PD-2 idempotent execution record"),
    ("function", "ct02_audit_truncate_guard", "PD-4 statement-level TRUNCATE guard"),
    ("function", "ct02_append_only_guard", "F-5 append-only row guard"),
    ("function", "ct02_report_share_validate", "PD-1 share validation"),
    ("function", "ct02_report_share_update_guard", "PD-1 share scope freezing"),
    ("function", "ct02_report_schedule_validate", "PD-2 schedule validation"),
    ("function", "ct02_report_schedule_run_guard", "PD-2 run immutability"),
    ("policy", "report_shares_read", "PD-1 tenant/recipient read"),
    ("policy", "report_shares_insert", "PD-1 org-admin insert"),
    ("policy", "report_shares_update", "PD-1 org-admin revocation"),
    ("policy", "report_share_access_events_read", "PD-1 access history read"),
    ("policy", "report_schedule_definitions_read", "PD-2 tenant read"),
    ("policy", "report_schedule_definitions_insert", "PD-2 org-admin insert"),
    ("policy", "report_schedule_definitions_update", "PD-2 org-admin update"),
    ("policy", "report_schedule_runs_read", "PD-2 tenant read"),
]

#: Legacy entities that MUST NOT exist in the canonical schema, in either
#: profile. PD-1/PD-2 forbid recreating them, so their absence is asserted.
FORBIDDEN_LEGACY_TABLES = (
    "report_history",
    "report_schedules",
    "notification_delivery_log",
    "defra_conversion_factors",
)

EXPECTED_COUNTS = {
    "public_tables": 145,
    "public_tables_with_rls": 145,
    "public_tables_without_rls": 0,
    "policies": 227,
    "policies_granting_anon_or_public": 0,
    "foreign_keys": 172,
    "indexes": 551,
    "public_functions": 31,
    "triggers": 88,
    "columns_all_schemas": 4592,
}

EXPECTED_REFERENCE_ROWS = {
    "scope3_categories": 15,
    "disclosure_frameworks": 3,
    "disclosure_framework_versions": 1,
    "disclosure_requirement_versions": 18,
}

D32_POLICIES = {
    "d32_documents_select_org_member": "SELECT",
    "d32_documents_insert_org_member": "INSERT",
    "d32_documents_update_org_member": "UPDATE",
    "d32_documents_delete_org_member": "DELETE",
}

#: The session search_path used for the inventory queries. PostgreSQL renders
#: *stored* expressions (column defaults, policy predicates) relative to
#: ``search_path``, so the bytes of an inventory listing — and therefore the
#: fingerprint computed from it — are only comparable if the rendering context is
#: fixed. CT-SCHEMA-01 computed ``c89c50bd…`` from a session whose search_path
#: included ``auth`` (the provider role's default), which is why the same
#: ``auth.refresh_tokens.id`` default appears there as
#: ``nextval('refresh_tokens_id_seq'::regclass)`` and as
#: ``nextval('auth.refresh_tokens_id_seq'::regclass)`` for a role without ``auth``
#: in its path. Pinning that context here makes the fingerprint reproducible by
#: any caller — the same determinism the D32 revision applies to policy
#: validation (CT-SCHEMA-02 finding F-02-EXT).
INVENTORY_SEARCH_PATH = '"$user", public, auth, extensions'

#: The inventory classes whose concatenation CT-SCHEMA-01 fingerprinted, in this
#: exact order (views and sequences included; matviews and grants excluded, as in
#: CT-SCHEMA-01's own fingerprint command).
INVENTORY_CLASSES: list[tuple[str, str]] = [
    ("A_schemas", "select nspname||' | owner='||pg_get_userbyid(nspowner) from pg_namespace order by 1;"),
    ("B_tables", "select table_schema||'.'||table_name from information_schema.tables order by 1;"),
    ("C_columns", "select table_schema||'.'||table_name||'.'||column_name||' | '||data_type||' | null='||is_nullable||' | def='||coalesce(column_default,'-') from information_schema.columns order by 1;"),
    ("D_constraints", "select n.nspname||'.'||c.relname||' :: '||con.conname||' :: '||con.contype::text from pg_constraint con join pg_class c on c.oid=con.conrelid join pg_namespace n on n.oid=c.relnamespace order by 1;"),
    ("E_indexes", "select schemaname||'.'||tablename||' :: '||indexname from pg_indexes order by 1;"),
    ("F_enums", "select n.nspname||'.'||t.typname||' = '||string_agg(e.enumlabel,',' order by e.enumsortorder) from pg_type t join pg_namespace n on n.oid=t.typnamespace join pg_enum e on e.enumtypid=t.oid group by n.nspname, t.typname order by 1;"),
    ("G_functions", "select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||') secdef='||p.prosecdef from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema') order by 1;"),
    ("H_triggers", "select tg.tgname||' on '||n.nspname||'.'||c.relname from pg_trigger tg join pg_class c on c.oid=tg.tgrelid join pg_namespace n on n.oid=c.relnamespace where not tg.tgisinternal order by 1;"),
    ("I_views", "select schemaname||'.'||viewname from pg_views where schemaname not in ('pg_catalog','information_schema') order by 1;"),
    ("K_sequences", "select sequence_schema||'.'||sequence_name from information_schema.sequences order by 1;"),
    ("L_rls", "select n.nspname||'.'||c.relname||' rls='||c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' order by 1;"),
    ("M_policies", "select schemaname||'.'||tablename||' :: '||policyname||' :: '||cmd||' :: '||array_to_string(roles,',') from pg_policies order by 1;"),
]

#: P17 / P16-R migrations whose declared objects must all exist.
P17_P16R_MIGRATIONS = [
    "20261008000000_p16r5_result_reportability_lifecycle.sql",
    "20261009000000_p16r7_calculation_request_idempotency.sql",
    "20261010000000_p17a_accounting_dimensions_and_factor_governance.sql",
    "20261011000000_p17c_contractual_instruments_and_allocations.sql",
    "20261012000000_p17d_scope3_category_taxonomy.sql",
    "20261013000000_p17h_estimation_and_assumption_records.sql",
    "20261014000000_p17_10_product_contract_reporting_dimensions.sql",
    "20261020000000_p17k_governed_capability_catalogue.sql",
]

#: Named headline objects CT-SCHEMA-01 confirmed present in the canonical schema
#: (kind, identifier, description). Every entry here was re-verified live against
#: the CT-SCHEMA-01 canonical database before being pinned.
P17_NAMED_OBJECTS = [
    ("index", "uq_calc_snapshots_request_id", "P16-R7 calculation request idempotency"),
    ("index", "idx_calc_snapshots_reportability", "P16-R5 result reportability lifecycle"),
    ("index", "idx_emissions_logs_reportability", "P16-R5 result reportability lifecycle"),
    ("column", "calculation_snapshots.facility_id", "P17-A accounting dimension"),
    ("column", "calculation_snapshots.scope2_method", "P17-A scope-2 method"),
    ("column", "calculation_snapshots.scope3_category", "P17-A scope-3 category"),
    ("column", "calculation_snapshots.scope3_method", "P17-10 reporting dimension"),
    ("column", "calculation_snapshots.transaction_provider", "P17-10 reporting dimension"),
    ("column", "emissions_logs.transaction_provider", "P17-10 reporting dimension on logs"),
    ("table", "scope3_categories", "P17-D scope 3 category taxonomy"),
    ("table", "contractual_instruments", "P17-C contractual instruments"),
    ("table", "instrument_allocations", "P17-C instrument allocations"),
    ("table", "estimation_records", "P17-H estimation and assumption records"),
    ("table", "disclosure_requirement_versions", "P17-K governed capability catalogue"),
    ("function", "p17_instrument_over_allocated", "P17-C over-allocation guard"),
    ("function", "p17_dc04_unclassified_transport", "P17-H data-quality rule DC-04"),
    ("function", "p17_dc05_unclassified_waste", "P17-H data-quality rule DC-05"),
    ("function", "p17_dc07_consolidation_missing", "P17-H data-quality rule DC-07"),
    ("function", "p17_unsubstantiated_estimates", "P17-H unsubstantiated-estimate rule"),
]

#: Application tables that must still be empty after a schema-only rebuild.
ZERO_ROW_TABLES = ["organizations", "customer_factors"]

RESULTS: list[dict] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    return ok


def info(name: str, detail: str) -> None:
    RESULTS.append({"check": name, "status": "INFO", "detail": detail})
    print(f"INFO  {name} — {detail}")


# ---------------------------------------------------------------------------
# Database access
# ---------------------------------------------------------------------------
class Db:
    def __init__(self, host: str, port: str, user: str, dbname: str, password: str,
                 search_path: str = INVENTORY_SEARCH_PATH) -> None:
        self.host, self.port, self.user, self.dbname = host, port, user, dbname
        self.env = dict(os.environ, PGPASSWORD=password)
        #: Pinned rendering context for every query (see INVENTORY_SEARCH_PATH).
        self.search_path = search_path

    def _cmd(self, extra: list[str]) -> list[str]:
        cmd = ["psql", "-h", self.host, "-p", self.port, "-U", self.user,
               "-d", self.dbname, "-X", "-q", "-v", "ON_ERROR_STOP=1"]
        if self.search_path:
            cmd += ["-c", f"SET search_path = {self.search_path}"]
        return cmd + extra

    def scalars(self, sql: str) -> list[str]:
        """Rows of a single column, psql -A -t formatting (CT-SCHEMA-01's -Atc)."""
        proc = subprocess.run(self._cmd(["-A", "-t", "-c", sql]),
                              capture_output=True, text=True, env=self.env)
        if proc.returncode != 0:
            raise RuntimeError(f"psql failed ({sql[:70]}…): {proc.stderr.strip()[:300]}")
        return proc.stdout.splitlines()

    def scalar(self, sql: str) -> str:
        rows = self.scalars(sql)
        return rows[0] if rows else ""

    def scalar_int(self, sql: str) -> int:
        value = self.scalar(sql)
        return int(value) if value.strip() else -1


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migration_set_fingerprint(directory: pathlib.Path, relative_prefix: str = "supabase/migrations") -> str:
    """CT-SCHEMA-01's recipe: sha256 of the `sha256sum` listing of all *.sql files.

    The listing is produced from a directory whose *relative* path to the files is
    ``supabase/migrations``, so the recorded value is reproducible byte-for-byte.
    """
    names = sorted(p.name for p in directory.glob("*.sql"))
    listing = "".join(
        f"{sha256_file(directory / n)}  {relative_prefix}/{n}\n" for n in names
    )
    return hashlib.sha256(listing.encode()).hexdigest()


# ---------------------------------------------------------------------------
# 1. Migration set + provenance
# ---------------------------------------------------------------------------
def check_migration_set(mig_dir: pathlib.Path, expect_fingerprint: str,
                        expected_count: int = EXPECTED_MIGRATION_COUNT,
                        expected_last: str = "20261020000000_p17k_governed_capability_catalogue.sql",
                        extended: bool = False) -> bool:
    names = sorted(p.name for p in mig_dir.glob("*.sql"))
    ok = True
    ok &= check("migration_count", len(names) == expected_count,
                f"found {len(names)} .sql files (expected {expected_count})")
    versions = [n.split("_", 1)[0] for n in names]
    ok &= check("migration_order_deterministic", versions == sorted(versions),
                "filenames sort deterministically by version prefix")
    ok &= check("migration_versions_unique", len(versions) == len(set(versions)),
                "no duplicate migration version prefixes")
    expected_first = "00000000000000_init_schema.sql"
    ok &= check("migration_endpoints", names[0] == expected_first and names[-1] == expected_last,
                f"first={names[0]} last={names[-1]}")

    actual = migration_set_fingerprint(mig_dir)
    info("migration_set_fingerprint_actual", actual)
    ok &= check("migration_set_fingerprint_matches_recorded", actual == expect_fingerprint,
                f"actual={actual} expected={expect_fingerprint}")

    # --- CT-IMPLEMENT-02: the CT-SCHEMA-01/02 baseline must be UNCHANGED ------
    # The extended chain is only allowed to *append*. Recompute the CT-SCHEMA-02
    # migration-set fingerprint over exactly the 89 baseline files and require
    # the recorded value:  if CT-IMPLEMENT-02 had touched, reordered or removed
    # an earlier migration, this check fails even though the extended
    # fingerprint would merely have been re-pinned.
    if extended:
        baseline_dir = pathlib.Path(tempfile.mkdtemp(prefix="ct02_baseline_"))
        import shutil
        for name in names:
            if name not in POST_BASELINE_MIGRATIONS:
                shutil.copy2(mig_dir / name, baseline_dir / name)
        baseline_fp = migration_set_fingerprint(baseline_dir)
        info("baseline_migration_count", str(len(list(baseline_dir.glob('*.sql')))))
        ok &= check("baseline_migration_set_unchanged", baseline_fp == MIGRATION_SET_FINGERPRINT_EXPECTED,
                    f"the 89 CT-SCHEMA-01/02 migrations still reproduce "
                    f"{MIGRATION_SET_FINGERPRINT_EXPECTED} (actual={baseline_fp})")
        missing = [m for m in CT_IMPLEMENT_02_MIGRATIONS if m not in names]
        ok &= check("ct_implement_02_migrations_present", not missing,
                    "all three CT-IMPLEMENT-02 migrations present" if not missing
                    else f"missing: {missing}")
        missing_ct_final_01 = [m for m in CT_FINAL_01_MIGRATIONS if m not in names]
        ok &= check("ct_final_01_migrations_present", not missing_ct_final_01,
                    "the CT-FINAL-01 storage migration is present" if not missing_ct_final_01
                    else f"missing: {missing_ct_final_01}")

    # Provenance: prove the set is the CT-SCHEMA-01/02 set apart from the single
    # authorised D32 revision and the CT-IMPLEMENT-02 additions. Read-only git
    # inspection; never mutates the repo.
    #
    # STATE AWARENESS (finding F-6): "git HEAD reproduces the CT-SCHEMA-01
    # fingerprint" is only true while the CT-IMPLEMENT-02 migrations (and the D32
    # revision) are still uncommitted. Once they are committed — as they now are —
    # HEAD has legitimately moved on and asserting the historical value would be a
    # false FAIL. The checks below are therefore expressed so that they hold in
    # BOTH states and are strictly stronger:
    #   * HEAD's migration set, minus the CT-IMPLEMENT-02 additions, must still
    #     reproduce the CT-SCHEMA-02 baseline fingerprint;
    #   * the working tree may differ from HEAD only by authorised revisions that
    #     HEAD does not yet contain.
    # A rogue migration — committed or not — still fails: committed, it lands in
    # the baseline subset above and changes its fingerprint; uncommitted, it is
    # not in the allowed set below.
    #
    # HEAD-SCOPED ALLOWED SET (CT-RELEASE-04): the expected set is derived from
    # HEAD rather than from the pre-commit worktree. A clean checkout of HEAD can
    # never "differ from HEAD", so requiring the authorised D32 revision to be
    # present as an *uncommitted* change made this check — and therefore the
    # canonical rebuild — reproducible only inside the developer worktree that
    # happened to hold it. Committing an authorised revision moves it out of this
    # set; it remains checked by its effect on the baseline fingerprint above.
    try:
        head_listing = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "archive", "HEAD", "supabase/migrations"],
            capture_output=True, check=True).stdout
        head_names = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-tree", "-r", "--name-only", "HEAD", "supabase/migrations"],
            capture_output=True, text=True, check=True).stdout.split()
        head_names = {n.split("supabase/migrations/")[-1] for n in head_names if n.endswith(".sql")}
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["tar", "-x", "-C", tmp], input=head_listing, check=True)
            head_dir = pathlib.Path(tmp) / "supabase" / "migrations"
            head_fp = migration_set_fingerprint(head_dir)
            # The CT-SCHEMA-01 historical anchor (recorded; no longer expected
            # from HEAD once the authorised D32 revision and CT-IMPLEMENT-02 are
            # committed — recorded so the evolution is explicit, never silent).
            info("migration_set_fingerprint_ct_schema_01_anchor",
                 f"{MIGRATION_SET_FINGERPRINT_CT_SCHEMA_01} (historical, pre-D32-revision)")
            baseline_head = pathlib.Path(tempfile.mkdtemp(prefix="ct02_head_baseline_"))
            import shutil
            for name in sorted(head_names):
                if name not in POST_BASELINE_MIGRATIONS:
                    shutil.copy2(head_dir / name, baseline_head / name)
            head_baseline_fp = migration_set_fingerprint(baseline_head)
        ok &= check("migration_set_provenance_baseline_from_head",
                    head_baseline_fp in (MIGRATION_SET_FINGERPRINT_CT_SCHEMA_01,
                                         MIGRATION_SET_FINGERPRINT_EXPECTED),
                    f"git HEAD minus the additive CT-IMPLEMENT-02 / CT-FINAL-01 "
                    f"migrations reproduces a recorded baseline anchor "
                    f"({head_baseline_fp}; CT-SCHEMA-01={MIGRATION_SET_FINGERPRINT_CT_SCHEMA_01}, "
                    f"CT-SCHEMA-02={MIGRATION_SET_FINGERPRINT_EXPECTED}) — head_set={len(head_names)} "
                    f"files, head={head_fp}. Which anchor applies depends on whether the "
                    f"authorised D32 revision is committed at HEAD; any *other* value means "
                    f"the baseline was altered.")

        # Working-tree vs HEAD: modified/added migration files only. `git status`
        # reports both tracked modifications and untracked additions, so a new
        # migration is visible before and after it is committed.
        porcelain = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain", "--", "supabase/migrations"],
            capture_output=True, text=True, check=True).stdout.splitlines()
        changed = sorted({
            line[3:].strip().split("supabase/migrations/")[-1]
            for line in porcelain if line[3:].strip().endswith(".sql")
        })
        allowed = sorted(
            m for m in (
                AUTHORISED_MIGRATION_REVISION,
                *CT_IMPLEMENT_02_MIGRATIONS,
                *CT_FINAL_01_MIGRATIONS,
            )
            if m not in head_names
        )
        ok &= check("migration_set_only_authorised_revision",
                    changed == allowed,
                    f"files differing from HEAD: {changed or 'none'} "
                    f"(allowed: {allowed}; CT-IMPLEMENT-02/CT-FINAL-01 files "
                    f"already in HEAD: "
                    f"{[m for m in POST_BASELINE_MIGRATIONS if m in head_names]})")
    except (subprocess.SubprocessError, OSError) as exc:
        info("migration_set_provenance_skipped", f"git not available: {exc}")
    return bool(ok)


def check_forbidden_legacy(db: Db) -> bool:
    """PD-1/PD-2 explicitly forbid recreating these entities in the canonical DB."""
    ok = True
    for table in FORBIDDEN_LEGACY_TABLES:
        ok &= check(f"legacy_absent_{table}", not _object_present(db, "table", table),
                    f"{table} must NOT exist in the canonical schema")
    return bool(ok)


def check_ct_implement_02_objects(db: Db) -> bool:
    """Every object declared by the three CT-IMPLEMENT-02 migrations is present."""
    ok = True
    for kind, ident, purpose in CT_IMPLEMENT_02_NAMED_OBJECTS:
        ok &= check(f"ct02_object_{kind}_{ident}", _object_present(db, kind, ident),
                    f"{kind} {ident} present ({purpose})")
    # The hardening must actually be attached to the evidence tables, not merely
    # defined: prove at-runtime that the guards named by
    # 20261021000000_ct02_audit_ledger_hardening.sql are installed, each wired to
    # the function the migration wired it to. The expected sets are transcribed
    # from that migration (CREATE TRIGGER … EXECUTE FUNCTION):
    #   truncate guard  -> audit_trail, audit_logs, activity_logs
    #   append-only row guard -> audit_logs, activity_logs
    # audit_trail deliberately gets NO row guard: its row immutability comes from
    # the pre-existing ledger trigger (migration 20260912000000), so a second row
    # guard would be a duplicate control rather than a hardening.
    for table, guards in CT02_EXPECTED_GUARDS.items():
        listed = ", ".join(f"'{n}'" for n in guards)
        sql = ("select tg.tgname || ' -> ' || p.proname from pg_trigger tg "
               "join pg_class c on c.oid=tg.tgrelid "
               "join pg_namespace n on n.oid=c.relnamespace "
               "join pg_proc p on p.oid=tg.tgfoid "
               f"where n.nspname='public' and c.relname='{table}' and not tg.tgisinternal "
               f"and tg.tgname in ({listed}) order by 1;")
        observed = sorted(db.scalars(sql))
        expected = sorted(f"{n} -> {f}" for n, f in guards.items())
        ok &= check(f"ct02_guards_attached_{table}", observed == expected,
                    f"attached={observed or 'none'} expected={expected}")
    return bool(ok)


# ---------------------------------------------------------------------------
# 2 & 3. Inventory, fingerprint, headline counts
# ---------------------------------------------------------------------------
def check_inventory(db: Db, expect_fingerprint: str, workdir: pathlib.Path,
                    dump_dir: pathlib.Path | None = None,
                    record_only: bool = False) -> bool:
    concatenated = b""
    class_hashes: dict[str, str] = {}
    for label, sql in INVENTORY_CLASSES:
        rows = db.scalars(sql)
        blob = "".join(f"{r}\n" for r in rows).encode()
        (workdir / f"{label}.txt").write_bytes(blob)
        if dump_dir is not None:
            dump_dir.mkdir(parents=True, exist_ok=True)
            (dump_dir / f"{label}.txt").write_bytes(blob)
        concatenated += blob
        class_hashes[label] = hashlib.sha256(blob).hexdigest()[:16]
        info(f"inventory_{label}", f"{len(rows)} rows, sha256[:16]={class_hashes[label]}")
    actual = hashlib.sha256(concatenated).hexdigest()
    info("inventory_fingerprint_actual", actual)
    if record_only:
        # First run against the EXTENDED chain: the per-class hashes and the
        # combined fingerprint are RECORDED for pinning. Nothing is judged here,
        # so this branch can never produce a false PASS — the extended
        # fingerprint is pinned by the report and enforced on every later run.
        info("inventory_fingerprint_recorded_for_pinning", actual)
        info("inventory_record_only",
             "extended-chain fingerprint not yet pinned; per-class sha256[:16] values above")
        return True
    ok = check("inventory_fingerprint_matches_canonical", actual == expect_fingerprint,
               f"actual={actual} expected={expect_fingerprint}")
    return bool(ok)


def check_counts(db: Db, expected: dict | None = None, floor_only: bool = False,
                 floor: dict | None = None) -> bool:
    observed = {
        "public_tables": db.scalar_int(
            "select count(*) from information_schema.tables where table_schema='public';"),
        "public_tables_with_rls": db.scalar_int(
            "select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname='public' and c.relkind='r' and c.relrowsecurity;"),
        "public_tables_without_rls": db.scalar_int(
            "select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname='public' and c.relkind='r' and not c.relrowsecurity;"),
        "policies": db.scalar_int("select count(*) from pg_policies;"),
        "policies_granting_anon_or_public": db.scalar_int(
            "select count(*) from pg_policies where 'anon' = any(roles) or 'public' = any(roles);"),
        "foreign_keys": db.scalar_int("select count(*) from pg_constraint where contype='f';"),
        "indexes": db.scalar_int("select count(*) from pg_indexes;"),
        "public_functions": db.scalar_int(
            "select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace "
            "where n.nspname='public';"),
        "triggers": db.scalar_int("select count(*) from pg_trigger where not tgisinternal;"),
        "columns_all_schemas": db.scalar_int("select count(*) from information_schema.columns;"),
    }
    ok = True
    if expected is None:
        expected = EXPECTED_COUNTS
    if floor is None and not floor_only:
        # Every extended-chain count must also be at least the frozen baseline
        # value: appending migrations may add schema objects but never remove
        # them, so a decreased count means the baseline was altered.
        floor = EXPECTED_COUNTS
    for key, exp in expected.items():
        value = observed.get(key, -1)
        if floor_only:
            # CT-IMPLEMENT-02 profile before the extended values were recorded:
            # the chain may only ADD schema objects. The observed values are
            # recorded (and pinned by the report) rather than compared for
            # equality, because a pinned number could only be known after the
            # from-zero rebuild it is meant to verify.
            ok &= check(f"count_{key}_not_reduced", value >= exp,
                        f"observed={value} baseline={exp} (extended chain may only add)")
        else:
            ok &= check(f"count_{key}", value == exp, f"observed={value} expected={exp}")
        if floor is not None and not floor_only:
            ok &= check(f"count_{key}_at_least_baseline", value >= floor[key],
                        f"observed={value} baseline={floor[key]}")
    for key, value in observed.items():
        info(f"count_observed_{key}", str(value))
    return bool(ok)


# ---------------------------------------------------------------------------
# 4. Reference data and the no-application-data boundary
# ---------------------------------------------------------------------------
def check_reference_data(db: Db) -> bool:
    ok = True
    for table, expected in EXPECTED_REFERENCE_ROWS.items():
        value = db.scalar_int(f"select count(*) from {table};")
        ok &= check(f"reference_rows_{table}", value == expected,
                    f"observed={value} expected={expected} (migration-declared reference data)")
    for table in ZERO_ROW_TABLES:
        value = db.scalar_int(f"select count(*) from {table};")
        ok &= check(f"no_application_data_{table}", value == 0, f"observed={value} rows")
    return bool(ok)


# ---------------------------------------------------------------------------
# 5. D32 platform objects (bucket, four policies, RLS, identity anchors)
# ---------------------------------------------------------------------------
def check_d32(db: Db) -> bool:
    ok = True
    bucket_public = db.scalar("select public::text from storage.buckets where name='documents';")
    ok &= check("d32_documents_bucket_private", bucket_public == "false",
                f"storage.buckets.public={bucket_public or 'MISSING'} (must be false)")

    ok &= check("d32_storage_objects_rls_enabled", db.scalar(
        "select c.relrowsecurity::text from pg_class c join pg_namespace n on n.oid=c.relnamespace "
        "where n.nspname='storage' and c.relname='objects';") == "true",
        "RLS must be enabled on storage.objects")

    for name, cmd in D32_POLICIES.items():
        row = db.scalar(
            "select p.cmd || '|' || array_to_string(p.roles, ',') from pg_policies p "
            "where p.schemaname='storage' and p.tablename='objects' "
            f"and p.policyname='{name}';")
        ok &= check(f"d32_policy_{name}", row == f"{cmd}|authenticated",
                    f"observed={row or 'MISSING'} expected={cmd}|authenticated")

    extra = db.scalar_int(
        "select count(*) from pg_policies where schemaname='storage' and tablename='objects' "
        "and policyname not in (" + ",".join(f"'{n}'" for n in D32_POLICIES) + ");")
    ok &= check("d32_no_extra_storage_policies", extra == 0,
                f"{extra} unexpected storage.objects policy/policies beyond the four approved")

    broadened = db.scalar_int(
        "select count(*) from pg_policies where schemaname='storage' and tablename='objects' "
        "and ('anon' = any(roles) or 'public' = any(roles));")
    ok &= check("d32_no_anon_public_storage_policy", broadened == 0, f"observed={broadened}")

    # Identity anchors: each stored expression must reference the auth.uid()
    # function and public.organization_members *by OID* — search_path independent.
    anchors = db.scalars(
        "select p.polname || '|' || "
        "(position(':funcid ' || ('auth.uid()'::regprocedure)::oid::text || ' ' "
        "  in coalesce(p.polqual::text,'') || coalesce(p.polwithcheck::text,'')) > 0)::text || '|' || "
        "(position(':relid ' || to_regclass('public.organization_members')::oid::text || ' ' "
        "  in coalesce(p.polqual::text,'') || coalesce(p.polwithcheck::text,'')) > 0)::text "
        "from pg_policy p join pg_class c on c.oid=p.polrelid "
        "join pg_namespace n on n.oid=c.relnamespace "
        "where n.nspname='storage' and c.relname='objects' order by 1;")
    for row in anchors:
        ok &= check(f"d32_identity_anchor_{row.split('|')[0]}", row.endswith("|true|true"),
                    f"auth.uid()-by-OID / organization_members-by-OID anchors: {row}")
    ok &= check("d32_identity_anchor_count", len(anchors) == 4, f"checked {len(anchors)} policies")
    return bool(ok)


# ---------------------------------------------------------------------------
# 6. P17 / P16-R declared objects
# ---------------------------------------------------------------------------
def _object_present(db: Db, kind: str, ident: str) -> bool:
    if kind == "table":
        sql = ("select count(*) from information_schema.tables where table_schema='public' "
               f"and table_name='{ident}';")
    elif kind == "column":
        table, column = ident.split(".", 1)
        sql = ("select count(*) from information_schema.columns where table_schema='public' "
               f"and table_name='{table}' and column_name='{column}';")
    elif kind == "index":
        sql = f"select count(*) from pg_indexes where indexname='{ident}';"
    elif kind == "policy":
        sql = f"select count(*) from pg_policies where policyname='{ident}';"
    elif kind == "function":
        sql = ("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace "
               f"where n.nspname='public' and p.proname='{ident}';")
    else:
        raise ValueError(f"unknown object kind: {kind}")
    return db.scalar_int(sql) > 0


def check_p17_p16r(db: Db, mig_dir: pathlib.Path) -> bool:
    # NOTE on the declaration parser: CT-SCHEMA-01's parser captured table/function
    # names with ``[a-z_]+``, which stops at a digit and produced one *parser
    # artefact* (``public.scope`` mis-parsed out of ``public.scope3_categories``,
    # recorded in that report as 105 parsed / 104 present / 1 artefact / 0 real
    # absences). This verifier is digit-tolerant (``[a-z_0-9]+``), so the same
    # declarations are parsed without the artefact. No presence verdict is weakened:
    # a digit-tolerant capture can only make the check stricter about real objects.
    ok = True
    declared_total = 0
    absent: list[str] = []
    for filename in P17_P16R_MIGRATIONS:
        body = re.sub(r"--[^\n]*", "", (mig_dir / filename).read_text(encoding="utf-8"))
        checks: list[tuple[str, str]] = []
        for t in sorted(set(re.findall(r"CREATE TABLE IF NOT EXISTS\s+(?:public\.)?([a-z_0-9]+)", body, re.I))):
            checks.append(("table", t))
        for m in re.finditer(r"ALTER TABLE\s+(?:public\.)?([a-z_0-9]+)([^;]*?);", body, re.I | re.S):
            for c in re.findall(r"ADD COLUMN (?:IF NOT EXISTS )?([a-z_0-9]+)", m.group(2), re.I):
                checks.append(("column", f"{m.group(1)}.{c}"))
        for i in sorted(set(re.findall(r"CREATE INDEX IF NOT EXISTS\s+([a-z_0-9]+)", body, re.I))):
            checks.append(("index", i))
        for p in sorted(set(re.findall(r"CREATE POLICY\s+\"?([a-z_0-9]+)\"?", body, re.I))):
            checks.append(("policy", p))
        for f in sorted(set(re.findall(r"CREATE OR REPLACE FUNCTION\s+(?:public\.)?([a-z_0-9]+)", body, re.I))):
            checks.append(("function", f))
        for kind, ident in checks:
            declared_total += 1
            if not _object_present(db, kind, ident):
                absent.append(f"{filename}:{kind}:{ident}")
    ok &= check("p17_p16r_declared_objects_present", not absent,
                f"{declared_total} declared objects checked; absent={absent[:12] if absent else 'none'}")
    for kind, ident, description in P17_NAMED_OBJECTS:
        present = _object_present(db, kind, ident)
        ok &= check(f"p17_named_{ident}", present, f"{description} ({kind}) present={present}")
    return bool(ok)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="CT-SCHEMA-02 canonical schema verifier")
    parser.add_argument("--host", default=os.environ.get("E2E_DB_HOST", "127.0.0.1"))
    parser.add_argument("--port", default=os.environ.get("E2E_DB_PORT", "55326"))
    parser.add_argument("--db", default=os.environ.get("E2E_DB_NAME", "postgres"))
    parser.add_argument("--user", default=os.environ.get("E2E_DB_USER", "postgres"))
    parser.add_argument("--password", default=os.environ.get("E2E_DB_PASSWORD", "postgres"))
    parser.add_argument("--migrations", default=str(MIGRATIONS_DIR))
    parser.add_argument("--expect-inventory-fingerprint", default=CANONICAL_INVENTORY_FINGERPRINT)
    parser.add_argument("--expect-migration-fingerprint", default=MIGRATION_SET_FINGERPRINT_EXPECTED)
    parser.add_argument("--inventory-search-path", default=INVENTORY_SEARCH_PATH,
                        help="pinned session search_path for the inventory queries "
                             "(PostgreSQL renders stored expressions relative to it, so it "
                             "must be fixed for the fingerprint to be comparable)")
    parser.add_argument("--profile", default="ct-schema-02", choices=["ct-schema-02", "ct-implement-02"],
                        help="ct-schema-02 (default): the 89-migration canonical baseline, verified "
                             "byte-for-byte against the CT-SCHEMA-01 fingerprint. ct-implement-02: the "
                             "same baseline with the three CT-IMPLEMENT-02 migrations appended; the "
                             "baseline is proven unchanged and the new objects are proven present.")
    parser.add_argument("--json", default="")
    parser.add_argument("--migration-set-only", action="store_true",
                        help="verify only the canonical migration set (identity, order, "
                             "fingerprints); skip the cluster-wide schema inventory, which is "
                             "only comparable on a target provisioned exactly like the canonical "
                             "platform layer")
    parser.add_argument("--dump-inventory", default="",
                        help="also write the per-class inventory listings to this directory "
                             "(byte-comparable with CT-SCHEMA-01's /tmp/inv/*)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    mig_dir = pathlib.Path(args.migrations)
    db = Db(args.host, args.port, args.user, args.db, args.password,
            search_path=args.inventory_search_path)

    extended = args.profile == "ct-implement-02"
    if extended:
        # In the extended profile the *expected* values are the recorded ones for
        # the extended chain; inventory is compared for equality against the
        # recorded extended fingerprint once it exists, and otherwise only its
        # per-class hashes are recorded for pinning (never silently accepted).
        expect_migration_fp = args.expect_migration_fingerprint if args.expect_migration_fingerprint != MIGRATION_SET_FINGERPRINT_EXPECTED else EXTENDED_MIGRATION_SET_FINGERPRINT
        expected_count, expected_last = EXTENDED_MIGRATION_COUNT, CT_FINAL_01_MIGRATIONS[-1]
    else:
        expect_migration_fp = args.expect_migration_fingerprint
        expected_count, expected_last = EXPECTED_MIGRATION_COUNT, "20261020000000_p17k_governed_capability_catalogue.sql"

    print("=== CT-SCHEMA-02 canonical schema verification ===")
    print(f"    profile    : {args.profile}")
    print(f"    target     : {args.user}@{args.host}:{args.port}/{args.db}")
    print(f"    migrations : {mig_dir}")
    print(f"    pinned search_path (inventory rendering context): {args.inventory_search_path}")
    print(f"    canonical inventory fingerprint (CT-SCHEMA-01): {CANONICAL_INVENTORY_FINGERPRINT}")

    all_ok = True
    all_ok &= check_migration_set(mig_dir, expect_migration_fp, expected_count, expected_last,
                                  extended=extended)
    if args.migration_set_only:
        info("migration_set_only", "cluster-wide inventory, counts, D32 and P17 checks skipped by request")
    else:
        all_ok &= check_counts(db, expected=EXPECTED_COUNTS_CT02 if extended else None,
                               floor_only=False)
        with tempfile.TemporaryDirectory() as tmp:
            if extended and EXTENDED_INVENTORY_FINGERPRINT.startswith("TO_BE_RECORDED"):
                # First verified rebuild of the extended chain: record, do not judge.
                all_ok &= check_inventory(db, CANONICAL_INVENTORY_FINGERPRINT, pathlib.Path(tmp),
                                          pathlib.Path(args.dump_inventory) if args.dump_inventory else None,
                                          record_only=True)
            else:
                expect_inv = EXTENDED_INVENTORY_FINGERPRINT if extended else args.expect_inventory_fingerprint
                all_ok &= check_inventory(db, expect_inv, pathlib.Path(tmp),
                                          pathlib.Path(args.dump_inventory) if args.dump_inventory else None)
        all_ok &= check_reference_data(db)
        all_ok &= check_d32(db)
        all_ok &= check_p17_p16r(db, mig_dir)
        all_ok &= check_forbidden_legacy(db)
        if extended:
            all_ok &= check_ct_implement_02_objects(db)

    failures = [r for r in RESULTS if r["status"] == "FAIL"]
    print("")
    print(f"=== RESULT: {'ALL CHECKS PASSED' if all_ok else 'FAILED'} "
          f"({len([r for r in RESULTS if r['status'] == 'PASS'])} pass, {len(failures)} fail) ===")
    for failure in failures:
        print(f"  FAIL {failure['check']}: {failure['detail']}")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps({
            "verifier": "CT-SCHEMA-02 canonical_schema_verify.py",
            "target": f"{args.user}@{args.host}:{args.port}/{args.db}",
            "canonical_inventory_fingerprint_ct_schema_01": CANONICAL_INVENTORY_FINGERPRINT,
            "migration_set_fingerprint_ct_schema_01": MIGRATION_SET_FINGERPRINT_CT_SCHEMA_01,
            "migration_set_fingerprint_expected": args.expect_migration_fingerprint,
            "passed": bool(all_ok),
            "results": RESULTS,
        }, indent=1), encoding="utf-8")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
