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
SAFE_NAME = "carbontally_test"


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
        if name != SAFE_NAME:
            print("REFUSING: expected", SAFE_NAME, "got", name)
            return 3
        for table in ("calculation_snapshots", "emissions_logs", "estimation_records",
                      "contractual_instruments", "instrument_allocations", "suppliers"):
            ok = await conn.fetchval("select to_regclass($1) is not null", "public." + table)
            print("TABLE", table, "=", "present" if ok else "MISSING")
        snap = {r["column_name"] for r in await conn.fetch(
            "select column_name from information_schema.columns where table_schema='public' and table_name='calculation_snapshots'")}
        for col in ("scope2_method", "scope3_category", "energy_type", "data_quality",
                    "facility_id", "transport_boundary", "waste_origin", "source_snapshot_id",
                    "performed_by_organization_id", "acting_for_organization_id"):
            print("COL calculation_snapshots." + col, "=", "present" if col in snap else "MISSING")
        logs = {r["column_name"] for r in await conn.fetch(
            "select column_name from information_schema.columns where table_schema='public' and table_name='emissions_logs'")}
        for col in ("supplier_id", "scope3_category", "data_quality", "calculation_snapshot_id"):
            print("COL emissions_logs." + col, "=", "present" if col in logs else "MISSING")
        est = {r["column_name"] for r in await conn.fetch(
            "select column_name from information_schema.columns where table_schema='public' and table_name='estimation_records'")}
        for col in ("organization_id", "calculation_snapshot_id", "estimation_method", "inputs",
                    "assumptions", "scope3_category", "acting_for_organization_id", "actor_organization_id"):
            print("COL estimation_records." + col, "=", "present" if col in est else "MISSING")
        fn = await conn.fetchval("select to_regprocedure('public.p17_instrument_over_allocated(uuid)') is not null")
        print("FUNCTION p17_instrument_over_allocated =", "present" if fn else "MISSING")
        rls = await conn.fetch("select relname, relrowsecurity from pg_class where relname in ('estimation_records','contractual_instruments','instrument_allocations')")
        for r in rls:
            print("RLS", r["relname"], "=", "enabled" if r["rowsecurity"] else "DISABLED")
        cnt = await conn.fetchrow("select count(*) c from public.estimation_records")
        print("ROWS estimation_records =", cnt["c"])
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
