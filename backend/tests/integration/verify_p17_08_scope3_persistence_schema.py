"""P17-IMPLEMENT-08 - real PostgreSQL verification of the Scope 3 persistence target.

READ-ONLY probe. Run it with the dedicated integration test database:

    ./.venv/bin/python tests/integration/verify_p17_08_scope3_persistence_schema.py

It never TRUNCATEs and never writes, so it is safe against any reachable
database, but it only *certifies* the dedicated ``carbontally_test`` target
(F-046-1). Confirm the schema the Scope 3 persistence path depends on before
claiming a real-PostgreSQL round-trip.
"""
import asyncio, os, re, sys
import asyncpg

URL = os.environ.get(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test",
)

#: F-046-1 permits exactly two kinds of integration target: the DEDICATED test
#: database (``carbontally_test``) or a DISPOSABLE clone (``ct_*``). Anything whose
#: name matches a protected persistent marker is refused, as are the main
#: application databases. This probe only READS, but it must still only *certify*
#: a target the repository's own integration harness is allowed to treat as
#: disposable.
SAFE_NAME = "carbontally_test"
SAFE_PREFIX = "ct_"
FORBIDDEN_MAIN_DB_NAMES = ("postgres", "supabase_db_carbon_ledger")
PROTECTED_PERSISTENT_MARKERS = ("qa", "demo", "investor", "prod", "live")


def target_is_permitted(name: str) -> bool:
    """True when ``name`` is an F-046-1-permitted integration target."""
    if name in FORBIDDEN_MAIN_DB_NAMES:
        return False
    if any(marker in name.lower() for marker in PROTECTED_PERSISTENT_MARKERS):
        return False
    return name == SAFE_NAME or name.startswith(SAFE_PREFIX)


async def main() -> int:
    print("TARGET", re.sub(r"://[^@]+@", "://***@", URL))
    try:
        conn = await asyncio.wait_for(asyncpg.connect(URL), timeout=8)
    except Exception as exc:
        print("BLOCKED cannot connect:", type(exc).__name__, str(exc)[:160])
        return 2
    try:
        name = await conn.fetchval("select current_database()")
        print("CONNECTED database=", name)
        if not target_is_permitted(name):
            print(
                "REFUSING:",
                name,
                "is not an F-046-1-permitted target "
                f"(expected {SAFE_NAME!r} or a {SAFE_PREFIX!r} disposable clone)",
            )
            return 3
        for table in ("calculation_snapshots", "emissions_logs", "estimation_records",
                      "contractual_instruments", "instrument_allocations",
                      "scope3_categories", "suppliers"):
            ok = await conn.fetchval("select to_regclass($1) is not null", "public." + table)
            print("TABLE", table, "=", "present" if ok else "MISSING")
        snap = {r["column_name"] for r in await conn.fetch(
            "select column_name from information_schema.columns where table_schema='public' and table_name='calculation_snapshots'")}
        for col in ("scope2_method", "scope3_category", "energy_type", "data_quality",
                    "facility_id", "transport_boundary", "waste_origin", "source_snapshot_id",
                    "performed_by_organization_id", "acting_for_organization_id",
                    # P17-IMPLEMENT-10
                    "scope3_method", "transaction_provider"):
            print("COL calculation_snapshots." + col, "=", "present" if col in snap else "MISSING")
        logs = {r["column_name"] for r in await conn.fetch(
            "select column_name from information_schema.columns where table_schema='public' and table_name='emissions_logs'")}
        for col in ("supplier_id", "scope2_method", "scope3_category", "energy_type",
                    "data_quality", "facility_id", "transport_boundary",
                    "waste_origin", "source_snapshot_id",
                    "performed_by_organization_id", "acting_for_organization_id",
                    # P17-IMPLEMENT-10
                    "scope3_method", "transaction_provider"):
            print("COL emissions_logs." + col, "=", "present" if col in logs else "MISSING")
        est = {r["column_name"] for r in await conn.fetch(
            "select column_name from information_schema.columns where table_schema='public' and table_name='estimation_records'")}
        for col in ("organization_id", "calculation_snapshot_id", "estimation_method", "inputs",
                    "assumptions", "scope3_category", "acting_for_organization_id", "actor_organization_id"):
            print("COL estimation_records." + col, "=", "present" if col in est else "MISSING")
        fn = await conn.fetchval("select to_regprocedure('public.p17_instrument_over_allocated(uuid)') is not null")
        print("FUNCTION p17_instrument_over_allocated =", "present" if fn else "MISSING")
        # P17-IMPLEMENT-10 — the product-contract reporting constraints.
        p10 = await conn.fetch(
            "select conname from pg_constraint where conname in ("
            "'calc_snapshots_scope3_method_check',"
            "'calc_snapshots_scope3_method_scope_check',"
            "'calc_snapshots_transaction_provider_check',"
            "'calc_snapshots_data_quality_check',"
            "'emissions_logs_scope3_method_check',"
            "'emissions_logs_scope3_method_scope_check',"
            "'emissions_logs_transaction_provider_check',"
            "'emissions_logs_data_quality_check')")
        names = {r["conname"] for r in p10}
        for expected in (
            "calc_snapshots_scope3_method_check",
            "calc_snapshots_scope3_method_scope_check",
            "calc_snapshots_transaction_provider_check",
            "calc_snapshots_data_quality_check",
            "emissions_logs_scope3_method_check",
            "emissions_logs_scope3_method_scope_check",
            "emissions_logs_transaction_provider_check",
            "emissions_logs_data_quality_check",
        ):
            print("CONSTRAINT", expected, "=", "present" if expected in names else "MISSING")
        # P17-IMPLEMENT-10 — the widened data-quality vocabulary is a strict superset
        # of the P17-A five: a narrower CHECK would invalidate stored rows.
        widened = await conn.fetchval(
            "select pg_get_constraintdef(oid) from pg_constraint "
            "where conname = 'emissions_logs_data_quality_check'")
        for value in ("primary_measured", "primary_supplier", "secondary_estimated",
                      "spend_based_estimated", "modelled", "activity_based",
                      "estimated", "manual", "unresolved"):
            print("DATA_QUALITY_VALUE", value, "=",
                  "allowed" if value in (widened or "") else "MISSING")
        rls = await conn.fetch("select relname, relrowsecurity as rls_on from pg_class where relname in ('estimation_records','contractual_instruments','instrument_allocations','scope3_categories')")
        for r in rls:
            print("RLS", r["relname"], "=", "enabled" if r["rls_on"] else "DISABLED")
        cnt = await conn.fetchrow("select count(*) c from public.estimation_records")
        print("ROWS estimation_records =", cnt["c"])
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
