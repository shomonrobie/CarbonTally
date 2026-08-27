"""Organisation-scoped search repository (G-P1-1).

A minimal, safe full-text-ish search over the organisation's OWN rows. The
backend is the search boundary: the query is always bound to ``organization_id``
and every result row belongs to that organisation (no cross-org leakage). The
UI (nav search box) is presentation only.

Searchable surfaces (all org-scoped by the query):
* documents  -> ``organization_files.name``
* items      -> ``manual_extraction_items.file_name`` (via batch org)
* issues     -> ``issues.title`` / ``issues.description``
* suppliers  -> ``suppliers.name``
* facilities -> ``facilities.name``
* vehicles   -> ``vehicles.name`` / ``vehicles.registration``
* reports    -> ``report_versions.report_name``
"""

from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository


class SearchRepository(AbstractRepository[dict]):
    """Org-scoped keyword search across the organisation's master and work data."""

    async def search_org(
        self, org_id: str, query: str, limit: int = 20
    ) -> list[dict]:
        q = f"%{query.strip()}%"
        results: list[dict] = []

        def add(kind: str, rows: list[Any], label: str) -> None:
            for r in rows:
                results.append(
                    {
                        "type": kind,
                        "id": str(r["id"]),
                        "label": label,
                    }
                )

        # Documents
        docs = await self._fetch_all(
            "SELECT id, name FROM public.organization_files "
            "WHERE organization_id = $1 AND deleted_at IS NULL AND name ILIKE $2 "
            "ORDER BY name LIMIT $3",
            org_id, q, limit,
        )
        add("document", docs, [str(r["name"]) for r in docs])

        # Extraction items (via batch org)
        items = await self._fetch_all(
            """
            SELECT i.id, i.file_name FROM public.manual_extraction_items i
            JOIN public.manual_extraction_batches b ON b.id = i.batch_id
            WHERE b.organization_id = $1 AND i.file_name ILIKE $2
            ORDER BY i.file_name LIMIT $3
            """,
            org_id, q, limit,
        )
        add("item", items, [str(r["file_name"]) for r in items])

        # Issues (customer-facing, org-scoped)
        issues = await self._fetch_all(
            "SELECT id, title FROM public.issues "
            "WHERE organization_id = $1 AND entity_id IS NULL "
            "AND (title ILIKE $2 OR description ILIKE $2) "
            "ORDER BY created_at DESC LIMIT $3",
            org_id, q, limit,
        )
        add("issue", issues, [str(r["title"]) for r in issues])

        # Suppliers
        suppliers = await self._fetch_all(
            "SELECT id, name FROM public.suppliers "
            "WHERE organization_id = $1 AND name ILIKE $2 "
            "ORDER BY name LIMIT $3",
            org_id, q, limit,
        )
        add("supplier", suppliers, [str(r["name"]) for r in suppliers])

        # Facilities
        facilities = await self._fetch_all(
            "SELECT id, name FROM public.facilities "
            "WHERE organization_id = $1 AND name ILIKE $2 "
            "ORDER BY name LIMIT $3",
            org_id, q, limit,
        )
        add("facility", facilities, [str(r["name"]) for r in facilities])

        # Vehicles (D17)
        vehicles = await self._fetch_all(
            "SELECT id, name FROM public.vehicles "
            "WHERE organization_id = $1 "
            "AND (name ILIKE $2 OR COALESCE(registration, '') ILIKE $2) "
            "ORDER BY name LIMIT $3",
            org_id, q, limit,
        )
        add("vehicle", vehicles, [str(r["name"]) for r in vehicles])

        # Reports
        reports = await self._fetch_all(
            "SELECT id, report_name FROM public.report_versions "
            "WHERE organization_id = $1 AND report_name ILIKE $2 "
            "ORDER BY created_at DESC LIMIT $3",
            org_id, q, limit,
        )
        add("report", reports, [str(r["report_name"]) for r in reports])

        return results[:limit]

    # AbstractRepository contract (method-driven).
    async def get(self, id: str) -> Optional[dict]:
        return None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None
