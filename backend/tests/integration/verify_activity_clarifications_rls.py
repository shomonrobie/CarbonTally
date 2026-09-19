"""CarbonTally — F-039-1 activity_clarifications BEHAVIOURAL RLS verification.

Exercises the frozen tenant matrix against the *real* PostgreSQL RLS engine by
role-playing actual identities (SET LOCAL ROLE + request.jwt.claim.sub) rather than
calling the helpers directly.

TARGET SAFETY (F-046-1): refuses any target that is not disposable. NEVER point this at
a persistent environment, the investor/demo dataset, or production.

    INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test \
        python backend/tests/integration/verify_activity_clarifications_rls.py

Creates its own isolated QA fixtures (labelled 'QA' / 'qa:') and deletes only those rows.
No existing data is truncated, reset or modified.
"""

from __future__ import annotations

import asyncio
import os
import uuid

import asyncpg

FORBIDDEN = ("qa", "demo", "investor", "prod", "live")
# F-063-1 repair: the 055 lifecycle migration made ``adjudication_id`` NOT NULL with no
# default and added ``effective_context_key`` NOT NULL, so a fixture INSERT that omits
# them fails against the shipped schema. ``gen_random_uuid()`` (the table's own ``id``
# default) gives each QA row its own single-version lineage; the QA activity key doubles
# as the bounded context key. No production schema or policy is touched.
INS = (
    "INSERT INTO public.activity_clarifications "
    "(activity_key, organization_id, original_activity, clarification, policy_input, "
    " outcome_status, adjudication_id, effective_context_key) "
    "VALUES ($1,$2,'QA','QA','QA','clarification_required',gen_random_uuid(),$1)"
)
RLSISH = ("row-level security", "permission denied")


def _target() -> str:
    url = os.environ.get("INTEGRATION_DATABASE_URL", "")
    if not url:
        raise SystemExit("F-046-1: INTEGRATION_DATABASE_URL is required (disposable target only)")
    name = url.rsplit("/", 1)[-1].split("?")[0].lower()
    if name in ("postgres", "carbontally") or any(tag == name or tag in name for tag in FORBIDDEN):
        raise SystemExit(f"F-046-1: refusing non-disposable target '{name}'")
    return url


async def _attempt(conn, role: str, sub, query: str, args=()):
    try:
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE " + role)
            if sub:
                await conn.execute("SELECT set_config('request.jwt.claim.sub',$1,true)", str(sub))
            if query.lstrip().upper().startswith("SELECT"):
                return "ok", await conn.fetchval(query, *args)
            return "ok", await conn.execute(query, *args)
    except Exception as exc:  # noqa: BLE001 - the outcome IS the assertion
        return "err", f"{type(exc).__name__}: {exc}"[:80]


def _denied(result) -> bool:
    if result[0] == "ok":
        return result[1] == 0 or str(result[1]).endswith("0")
    return any(k in result[1].lower() for k in RLSISH)


async def main() -> int:
    conn = await asyncpg.connect(_target())
    # F-063-1 repair: resolve the identity pair from the DATA rather than assuming the
    # alphabetically-first organisation happens to own an active member. The matrix needs
    # one organisation with an active member (org A) and a DIFFERENT second organisation
    # (org B); anything else is still reported as an explicit precondition failure.
    member = await conn.fetchrow(
        "SELECT user_id, organization_id FROM public.organization_members "
        "WHERE coalesce(is_active,true) AND user_id IS NOT NULL "
        "ORDER BY organization_id, user_id LIMIT 1"
    )
    second = (
        await conn.fetchval(
            "SELECT id FROM public.organizations WHERE id <> $1 ORDER BY id LIMIT 1",
            member["organization_id"],
        )
        if member is not None
        else None
    )
    if member is None or second is None:
        raise SystemExit("need one existing member in one organisation and a second organisation")

    org_a, org_b, actor = member["organization_id"], second, member["user_id"]
    consult, client, firm = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    checks: list[tuple[str, bool]] = []

    def record(label: str, ok: bool, detail="") -> None:
        checks.append((label, ok))
        print(("PASS" if ok else "FAIL"), "|", label, "|", str(detail)[:80])

    try:
        await conn.execute("INSERT INTO public.users (id,email) VALUES ($1,'qa_cons@qa.local')", consult)
        await conn.execute("INSERT INTO public.users (id,email) VALUES ($1,'qa_client@qa.local')", client)
        await conn.execute(
            "INSERT INTO public.consultant_profiles (id,user_id,company_name,white_label_enabled)"
            " VALUES ($1,$2,'QA Firm',false)", firm, consult)
        await conn.execute(
            "INSERT INTO public.consultant_firm_members (firm_id,user_id,role,is_active)"
            " VALUES ($1,$2,'owner',true)", firm, consult)
        await conn.execute(
            "INSERT INTO public.consultant_clients (consultant_id,organization_id,client_name,status)"
            " VALUES ($1,$2,'QA Client','active')", firm, org_a)
        await conn.execute(
            "INSERT INTO public.organization_members (organization_id,user_id,role,is_active)"
            " VALUES ($1,$2,'member',true)", org_b, client)
        seed_a = await conn.fetchval(INS + " RETURNING id", "qa:rls:seedA", org_a)
        seed_b = await conn.fetchval(INS + " RETURNING id", "qa:rls:seedB", org_b)
        # F-063-1 repair (harness quality): the mutation checks below COMMIT inside their
        # own transaction, so pointing them at the SELECT seed destroyed the very row the
        # later allow-checks needed to observe — several "allow" results were satisfied by
        # "no error" on 0 rows. The destructive checks now use their own row, so every
        # allow-check genuinely sees a row where the policy permits one.
        seed_mut = await conn.fetchval(INS + " RETURNING id", "qa:rls:seedA_mut", org_a)

        async def check(label, role, sub, query, args, expect):
            result = await _attempt(conn, role, sub, query, args)
            record(label, result[0] == "ok" if expect == "allow" else _denied(result), result)

        q_a = "SELECT count(*) FROM public.activity_clarifications WHERE activity_key='qa:rls:seedA'"
        q_b = "SELECT count(*) FROM public.activity_clarifications WHERE activity_key='qa:rls:seedB'"
        upd = "UPDATE public.activity_clarifications SET unit='x' WHERE id=$1"
        dele = "DELETE FROM public.activity_clarifications WHERE id=$1"

        await check("member/own SELECT", "authenticated", actor, q_a, (), "allow")
        await check("member/own INSERT", "authenticated", actor, INS, ("qa:rls:mA", org_a), "allow")
        await check("member/own UPDATE", "authenticated", actor, upd, (seed_mut,), "allow")
        await check("member/own DELETE", "authenticated", actor, dele, (seed_mut,), "allow")
        await check("member A->B SELECT denied", "authenticated", actor, q_b, (), "deny")
        await check("member A->B INSERT denied", "authenticated", actor, INS, ("qa:rls:xB", org_b), "deny")
        await check("member A->B UPDATE denied", "authenticated", actor, upd, (seed_b,), "deny")
        await check("member A->B DELETE denied", "authenticated", actor, dele, (seed_b,), "deny")
        row = await conn.fetchrow("SELECT unit FROM public.activity_clarifications WHERE id=$1", seed_b)
        record("org B row unmodified by org A", row is not None and row["unit"] is None, row)
        await check("consultant/authorised client SELECT", "authenticated", consult, q_a, (), "allow")
        # Row-level proof for the consultant allow-path (an "allow" that sees 0 rows would
        # otherwise be indistinguishable from a denial).
        consultant_view = await _attempt(conn, "authenticated", consult, q_a, ())
        record("consultant SEES the authorised client's row",
               consultant_view[0] == "ok" and consultant_view[1] == 1, consultant_view)
        await check("consultant INSERT denied (member-only)", "authenticated", consult, INS, ("qa:rls:cA", org_a), "deny")
        await check("consultant UPDATE denied", "authenticated", consult, upd, (seed_a,), "deny")
        await check("consultant DELETE denied", "authenticated", consult, dele, (seed_a,), "deny")
        await check("consultant->unauthorised client SELECT denied", "authenticated", consult, q_b, (), "deny")
        await check("consultant->unauthorised client INSERT denied", "authenticated", consult, INS, ("qa:rls:cB", org_b), "deny")
        await check("client/own org SELECT", "authenticated", client, q_b, (), "allow")
        await check("client/own org INSERT", "authenticated", client, INS, ("qa:rls:cliB", org_b), "allow")
        await check("client->other org SELECT denied", "authenticated", client, q_a, (), "deny")
        await check("client->other org INSERT denied", "authenticated", client, INS, ("qa:rls:cliA", org_a), "deny")
        await check("client->other org UPDATE denied", "authenticated", client, upd, (seed_a,), "deny")
        await check("client->other org DELETE denied", "authenticated", client, dele, (seed_a,), "deny")
        await check("anon SELECT denied", "anon", None, q_a, (), "deny")
        await check("anon INSERT denied", "anon", None, INS, ("qa:rls:anon", org_a), "deny")
        await check("anon UPDATE denied", "anon", None, "UPDATE public.activity_clarifications SET unit='a'", (), "deny")
        await check("anon DELETE denied", "anon", None, "DELETE FROM public.activity_clarifications", (), "deny")
        await check("service_role SELECT (BYPASSRLS)", "service_role", None, q_a, (), "allow")
        await check("service_role INSERT", "service_role", None, INS, ("qa:rls:svc", org_b), "allow")
    finally:
        await conn.execute("DELETE FROM public.activity_clarifications WHERE activity_key LIKE 'qa:%'")
        await conn.execute("DELETE FROM public.consultant_clients WHERE consultant_id=$1", firm)
        await conn.execute("DELETE FROM public.consultant_firm_members WHERE firm_id=$1", firm)
        await conn.execute("DELETE FROM public.consultant_profiles WHERE id=$1", firm)
        await conn.execute("DELETE FROM public.organization_members WHERE user_id=$1", client)
        await conn.execute("DELETE FROM public.users WHERE id = ANY($1::uuid[])", [consult, client])
        await conn.close()

    passed = sum(1 for _, ok in checks if ok)
    print(f"=== RLS MATRIX: {passed}/{len(checks)} PASS ===")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
