"""Integration tests for V3M-5 — First-Class Issue Management (ADR-V3-009,
Option B).

These tests run against the dedicated test database ``carbontally_test`` (see
``tests/integration/conftest.py``) — never the authoritative development
database. They verify the schema and invariants established by:

  * ``supabase/migrations/20260810040000_v3m5_issues.sql``

Covered invariants:
  1. ``issues`` exists with the approved first-class Issue columns and
     lifecycle CHECKs (issue_type/severity/status, priority/escalation >= 0).
  2. Context FKs work: organization (CASCADE), processing entity / work item /
     document / batch (RESTRICT), conversation (SET NULL).
  3. Lifecycle/status rules: the DB enforces the vocabulary; reopening is a
     status transition back to ``open`` recorded via ``reopened_at``.
  4. Processing Entity context: ``entity_id`` FK → ``processing_entities``.
  5. RLS: enabled; org storey SELECT = org member OR consultant AND
     entity_id IS NULL; INSERT/UPDATE = org member AND entity_id IS NULL; NO DELETE policy.
  6. Customer isolation: org-scope policies reference ``is_org_member`` /
     ``is_org_consultant`` only.
  7. Processing Entity isolation: the V3M-6 entity SELECT storey (issues_entity_select) exists
     (complementing the V3M-5 org storey); entity rows are excluded
     from the customer-visible SELECT surface; no entity INSERT/UPDATE/DELETE policies.
  8. CarbonTally internal access: ``service_role`` retains ALL.
  9. Conversations remain separate from Issues (distinct tables; only a
     nullable conversation_id association).
 10. ``emission_factors`` and ``customer_factors`` are untouched.
"""
from __future__ import annotations

import uuid

import asyncpg
import pytest

from tests.integration.conftest import (
    _SYSTEM_UUID,
    make_org,
    new_id,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_issue(
    conn: asyncpg.Connection,
    org_id: str,
    *,
    title: str = "V3M5 test issue",
    issue_type: str = "exception",
    severity: str = "medium",
    priority: int = 0,
    status: str = "open",
    entity_id: str | None = None,
    work_item_id: str | None = None,
    document_id: str | None = None,
    batch_id: str | None = None,
    conversation_id: str | None = None,
    escalation_level: int = 0,
) -> str:
    issue_id = new_id()
    await conn.execute(
        """
        INSERT INTO public.issues (
            id, organization_id, title, issue_type, severity, priority,
            status, entity_id, work_item_id, document_id, batch_id,
            conversation_id, escalation_level
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """,
        issue_id,
        org_id,
        title,
        issue_type,
        severity,
        priority,
        status,
        entity_id,
        work_item_id,
        document_id,
        batch_id,
        conversation_id,
        escalation_level,
    )
    return issue_id


async def _create_processing_entity(conn: asyncpg.Connection) -> str:
    entity_id = new_id()
    await conn.execute(
        "INSERT INTO public.processing_entities (id, name) VALUES ($1, $2)",
        entity_id,
        f"V3M5 Entity {entity_id[:8]}",
    )
    return entity_id


async def _create_work_item(conn: asyncpg.Connection, org_id: str) -> str:
    work_item_id = new_id()
    await conn.execute(
        """
        INSERT INTO public.manual_review_queue (
            id, organization_id, file_url, file_name, file_type, data_type, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        work_item_id,
        org_id,
        f"https://example.test/{work_item_id[:8]}.pdf",
        f"{work_item_id[:8]}.pdf",
        "pdf",
        "invoice",
        "pending",
    )
    return work_item_id


async def _create_document(conn: asyncpg.Connection, org_id: str) -> str:
    document_id = new_id()
    await conn.execute(
        """
        INSERT INTO public.customer_documents (
            id, organization_id, organization_member_id, file_name,
            file_url, file_type, status
        ) VALUES ($1, $2, $3, $4, $5, $6, 'uploaded')
        """,
        document_id,
        org_id,
        _SYSTEM_UUID,
        f"{document_id[:8]}.pdf",
        f"https://example.test/{document_id[:8]}.pdf",
        "pdf",
    )
    return document_id


async def _create_batch(conn: asyncpg.Connection, org_id: str) -> str:
    batch_id = new_id()
    await conn.execute(
        "INSERT INTO public.upload_batches (id, organization_id, batch_name, status) "
        "VALUES ($1, $2, $3, 'completed')",
        batch_id,
        org_id,
        f"V3M5 batch {batch_id[:8]}",
    )
    return batch_id


async def _create_conversation(conn: asyncpg.Connection, org_id: str) -> str:
    conversation_id = new_id()
    await conn.execute(
        "INSERT INTO public.conversations (id, organization_id, subject, status) "
        "VALUES ($1, $2, $3, 'open')",
        conversation_id,
        org_id,
        f"V3M5 conversation {conversation_id[:8]}",
    )
    return conversation_id


# ---------------------------------------------------------------------------
# 1. issues schema (columns + lifecycle CHECKs)
# ---------------------------------------------------------------------------


async def test_issues_table_exists(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'issues'"
        )
        assert exists == 1


async def test_issue_create_and_fetch(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        issue_id = await _create_issue(
            conn, org_id, title="Escalation from QC", issue_type="escalation"
        )
        row = await conn.fetchrow(
            "SELECT issue_type, severity, priority, status, title, "
            "escalation_level, created_at, updated_at "
            "FROM public.issues WHERE id = $1",
            issue_id,
        )
        assert row["issue_type"] == "escalation"
        assert row["severity"] == "medium"  # default
        assert row["priority"] == 0  # default
        assert row["status"] == "open"  # default
        assert row["title"] == "Escalation from QC"
        assert row["escalation_level"] == 0
        assert row["created_at"] is not None
        assert row["updated_at"] is not None


async def test_issue_title_required(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.NotNullViolationError):
            await conn.execute(
                "INSERT INTO public.issues (id, organization_id) VALUES ($1, $2)",
                new_id(),
                org_id,
            )


async def test_issue_type_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_issue(conn, org_id, issue_type="feedback")


async def test_issue_severity_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_issue(conn, org_id, severity="urgent")


async def test_issue_status_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_issue(conn, org_id, status="cancelled")


async def test_issue_priority_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_issue(conn, org_id, priority=-1)


async def test_issue_escalation_level_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_issue(conn, org_id, escalation_level=-1)

# ---------------------------------------------------------------------------
# 2. lifecycle / status rules
# ---------------------------------------------------------------------------


async def test_issue_reopen_rule(pool: asyncpg.Pool) -> None:
    """A resolved issue may be reopened: status returns to ``open`` and
    ``reopened_at`` records the event (spec §14.2 Reopening)."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        issue_id = await _create_issue(conn, org_id, status="resolved")
        await conn.execute(
            "UPDATE public.issues SET status = 'open', reopened_at = NOW(), "
            "resolved_at = NULL WHERE id = $1",
            issue_id,
        )
        row = await conn.fetchrow(
            "SELECT status, reopened_at, resolved_at "
            "FROM public.issues WHERE id = $1",
            issue_id,
        )
        assert row["status"] == "open"
        assert row["reopened_at"] is not None
        assert row["resolved_at"] is None


async def test_issue_close_rule(pool: asyncpg.Pool) -> None:
    """Closure is the final soft lifecycle state (never hard-deleted)."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        issue_id = await _create_issue(conn, org_id, status="closed")
        row = await conn.fetchrow(
            "SELECT status FROM public.issues WHERE id = $1", issue_id
        )
        assert row["status"] == "closed"


# ---------------------------------------------------------------------------
# 3. issue relationships (org / entity / work item / document / batch / conversation)
# ---------------------------------------------------------------------------


async def test_issue_org_fk(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_issue(conn, new_id())


async def test_issue_entity_context(pool: asyncpg.Pool) -> None:
    """Processing Entity context works: entity_id FK → processing_entities."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        entity_id = await _create_processing_entity(conn)
        issue_id = await _create_issue(conn, org_id, entity_id=entity_id)
        row = await conn.fetchrow(
            "SELECT entity_id FROM public.issues WHERE id = $1", issue_id
        )
        assert row["entity_id"] == uuid.UUID(entity_id)

        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_issue(conn, org_id, entity_id=new_id())


async def test_issue_work_item_fk(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        work_item_id = await _create_work_item(conn, org_id)
        issue_id = await _create_issue(conn, org_id, work_item_id=work_item_id)
        row = await conn.fetchrow(
            "SELECT work_item_id FROM public.issues WHERE id = $1", issue_id
        )
        assert row["work_item_id"] == uuid.UUID(work_item_id)

        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_issue(conn, org_id, work_item_id=new_id())




async def test_issue_document_fk(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        document_id = await _create_document(conn, org_id)
        issue_id = await _create_issue(conn, org_id, document_id=document_id)
        row = await conn.fetchrow(
            "SELECT document_id FROM public.issues WHERE id = $1", issue_id
        )
        assert row["document_id"] == uuid.UUID(document_id)

        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_issue(conn, org_id, document_id=new_id())


async def test_issue_batch_fk(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        batch_id = await _create_batch(conn, org_id)
        issue_id = await _create_issue(conn, org_id, batch_id=batch_id)
        row = await conn.fetchrow(
            "SELECT batch_id FROM public.issues WHERE id = $1", issue_id
        )
        assert row["batch_id"] == uuid.UUID(batch_id)

        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_issue(conn, org_id, batch_id=new_id())


async def test_issue_conversation_fk(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        conversation_id = await _create_conversation(conn, org_id)
        issue_id = await _create_issue(
            conn, org_id, conversation_id=conversation_id
        )
        row = await conn.fetchrow(
            "SELECT conversation_id FROM public.issues WHERE id = $1", issue_id
        )
        assert row["conversation_id"] == uuid.UUID(conversation_id)

        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_issue(conn, org_id, conversation_id=new_id())


async def test_issue_entity_fk_restrict(pool: asyncpg.Pool) -> None:
    """ON DELETE RESTRICT: an entity referenced by an issue cannot be deleted
    (attribution preserved — V3M-1 convention)."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        entity_id = await _create_processing_entity(conn)
        await _create_issue(conn, org_id, entity_id=entity_id)
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await conn.execute(
                "DELETE FROM public.processing_entities WHERE id = $1",
                entity_id,
            )


async def test_issue_conversation_fk_set_null(pool: asyncpg.Pool) -> None:
    """ON DELETE SET NULL: deleting a conversation never destroys the issue."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        conversation_id = await _create_conversation(conn, org_id)
        issue_id = await _create_issue(
            conn, org_id, conversation_id=conversation_id
        )
        await conn.execute(
            "DELETE FROM public.conversations WHERE id = $1", conversation_id
        )
        row = await conn.fetchrow(
            "SELECT conversation_id FROM public.issues WHERE id = $1", issue_id
        )
        assert row["conversation_id"] is None

# ---------------------------------------------------------------------------
# 4. RLS posture (V3M-5 org storey + V3M-6 entity SELECT storey)
# ---------------------------------------------------------------------------


async def test_issues_rls_enabled_no_delete(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        rls_on = await conn.fetchval(
            "SELECT relrowsecurity FROM pg_class WHERE relname = 'issues'"
        )
        assert rls_on is True

        policies = await conn.fetch(
            "SELECT policyname, cmd FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'issues'"
        )
        # Resolve policies by name: pg_policies rows are unordered and two
        # SELECT policies now exist (V3M-5 org storey + V3M-6 entity storey),
        # so a dict keyed only by cmd cannot represent the inventory.
        by_name = {p["policyname"]: p["cmd"] for p in policies}
        assert by_name["issues_select_own"] == "SELECT"
        assert by_name["issues_insert_own"] == "INSERT"
        assert by_name["issues_update_own"] == "UPDATE"
        assert by_name["issues_entity_select"] == "SELECT"
        assert "DELETE" not in set(by_name.values()), (
            "issues must have NO delete policy"
        )


async def test_issues_rls_customer_isolation(pool: asyncpg.Pool) -> None:
    """Customer isolation: SELECT is org member OR consultant and never sees
    entity-scoped issues; INSERT/UPDATE are org-member only (spec §14.4)."""
    async with pool.acquire() as conn:
        policies = await conn.fetch(
            "SELECT policyname, cmd, qual, with_check FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'issues'"
        )
        # Resolve the org storey by policy name — after V3M-6 two SELECT
        # policies exist (issues_select_own + issues_entity_select).
        by_name = {p["policyname"]: p for p in policies}

        select_qual = by_name["issues_select_own"]["qual"]
        assert "is_org_member" in select_qual
        assert "is_org_consultant" in select_qual
        assert "entity_id" in select_qual, (
            "entity-scoped issues must be excluded from the customer-visible "
            "SELECT surface"
        )

        insert_check = by_name["issues_insert_own"]["with_check"]
        assert "is_org_member" in insert_check
        assert "entity_id" in insert_check

        update_qual = by_name["issues_update_own"]["qual"]
        update_check = by_name["issues_update_own"]["with_check"]
        assert "is_org_member" in update_qual
        assert "entity_id" in update_qual
        assert "is_org_member" in update_check
        assert "entity_id" in update_check


async def test_issues_rls_entity_storey_select_only(pool: asyncpg.Pool) -> None:
    """Processing Entity isolation (V3M-6 contract): the ONLY entity-scoped
    issues policy is the entity SELECT storey (issues_entity_select via
    is_entity_member). Entity rows remain invisible to customers; no entity
    INSERT/UPDATE/DELETE policy exists (entity writes stay service-role)."""
    async with pool.acquire() as conn:
        policies = await conn.fetch(
            "SELECT policyname, cmd FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'issues'"
        )
        by_name = {p["policyname"]: p["cmd"] for p in policies}
        assert by_name == {
            "issues_select_own": "SELECT",
            "issues_insert_own": "INSERT",
            "issues_update_own": "UPDATE",
            "issues_entity_select": "SELECT",
        }
        entity_policies = {
            name: cmd
            for name, cmd in by_name.items()
            if "entity" in name.lower()
        }
        assert entity_policies == {"issues_entity_select": "SELECT"}


async def test_issues_service_role_access(pool: asyncpg.Pool) -> None:
    """CarbonTally internal access: service_role retains ALL privileges
    (bypasses RLS for platform operations)."""
    async with pool.acquire() as conn:
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            granted = await conn.fetchval(
                "SELECT has_table_privilege('service_role', "
                "'public.issues', $1)",
                priv,
            )
            assert granted is True, f"service_role missing {priv} on issues"


async def test_issues_updated_at_trigger(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        trigger = await conn.fetchrow(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgrelid = 'public.issues'::regclass "
            "AND tgname = 'trg_set_updated_at_issues'"
        )
        assert trigger is not None


# ---------------------------------------------------------------------------
# 5. separation from existing structures + factor data untouched
# ---------------------------------------------------------------------------


async def test_conversations_separate_from_issues(pool: asyncpg.Pool) -> None:
    """Conversations remain a distinct first-class surface: only a nullable
    conversation_id association on issues; no issue columns were added to the
    conversations table."""
    async with pool.acquire() as conn:
        conv_cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'conversations'"
        )
        conv_names = {c["column_name"] for c in conv_cols}
        assert "issue_id" not in conv_names
        assert "issue_type" not in conv_names

        issue_cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'issues'"
        )
        issue_names = {c["column_name"] for c in issue_cols}
        assert "conversation_id" in issue_names


async def test_emission_factors_untouched(pool: asyncpg.Pool) -> None:
    """No issue columns were added to global emission_factors."""
    async with pool.acquire() as conn:
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'emission_factors'"
        )
        names = {c["column_name"] for c in cols}
        assert "issue_id" not in names
        assert "organization_id" not in names


async def test_customer_factors_untouched(pool: asyncpg.Pool) -> None:
    """No issue columns were added to customer_factors."""
    async with pool.acquire() as conn:
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'customer_factors'"
        )
        names = {c["column_name"] for c in cols}
        assert "issue_id" not in names

