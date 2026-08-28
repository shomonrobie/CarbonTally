"""Emission-factors repository (Backend v2.1 §10.1).

Persistence for the RC2 ``emission_factors`` aggregate. ``provider_key`` is not a
column on ``emission_factors`` (the source of truth is ``import_batches``), so
every read joins the owning import batch to populate the domain field.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from data.base import AbstractRepository
from domain.factor import EmissionFactor

#: Explicit factor column list (never ``SELECT *``). Joins the owning import
#: batch so the domain ``provider_key`` field can be populated.
_FACTOR_COLUMNS = """
    ef.id, ef.reporting_year, ef.activity_type, ef.co2e_multiplier,
    ef.unit, ef.scope, ef.factor_source, ef.factor_set, ef.country,
    ef.import_batch_id, ib.provider_key AS provider_key
"""

#: Always used with :data:`_FACTOR_COLUMNS`; LEFT JOIN so pre-existing
#: (batch-less) factors are still returned.
_FACTOR_FROM = """
    FROM public.emission_factors ef
    LEFT JOIN public.import_batches ib ON ib.id = ef.import_batch_id
"""


def _natural_key(
    reporting_year: int,
    activity_type: str,
    country: str,
    unit: Optional[str],
    scope: Optional[str],
) -> tuple[str, ...]:
    """Build the RC2 natural key tuple ``(year, activity, country, unit, scope)``."""
    return (
        str(reporting_year),
        activity_type,
        country or "",
        unit or "",
        scope or "",
    )


def _row_to_factor(row: Any) -> EmissionFactor:
    r = dict(row)
    unit = r.get("unit")
    scope = r.get("scope")
    country = r.get("country") or "GB"
    return EmissionFactor(
        id=str(r["id"]),
        reporting_year=int(r["reporting_year"]),
        activity_type=str(r["activity_type"]),
        co2e_multiplier=Decimal(str(r["co2e_multiplier"])),
        unit=str(unit) if unit is not None else None,
        scope=str(scope) if scope is not None else None,
        factor_source=str(r.get("factor_source") or ""),
        factor_set=str(r.get("factor_set") or ""),
        country=str(country),
        provider_key=str(r.get("provider_key") or ""),
        import_batch_id=str(r["import_batch_id"]) if r.get("import_batch_id") else None,
        natural_key=_natural_key(
            int(r["reporting_year"]),
            str(r["activity_type"]),
            str(country),
            str(unit) if unit is not None else None,
            str(scope) if scope is not None else None,
        ),
    )

class EmissionFactorsRepository(AbstractRepository[EmissionFactor]):
    """CRUD and lookup operations for emission factors."""

    async def get(self, id: str) -> Optional[EmissionFactor]:
        """Return the single factor with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_FACTOR_COLUMNS} {_FACTOR_FROM} WHERE ef.id = $1", id
        )
        return _row_to_factor(row) if row is not None else None

    async def find_by_natural_key(
        self,
        year: int,
        activity_type: str,
        country: str,
        unit: Optional[str],
        scope: Optional[str],
    ) -> Optional[EmissionFactor]:
        """Exact RC2 natural-key lookup.

        The WHERE clause mirrors the ``emission_factors_year_activity_country_uniq``
        unique index so ``NULL`` unit/scope values match exactly.
        """
        row = await self._fetch_one(
            f"""
            SELECT {_FACTOR_COLUMNS} {_FACTOR_FROM}
            WHERE ef.reporting_year = $1
              AND ef.activity_type = $2
              AND COALESCE(ef.country, 'GB') = COALESCE($3, 'GB')
              AND COALESCE(ef.unit, '{{no-unit}}') = COALESCE($4, '{{no-unit}}')
              AND COALESCE(ef.scope, '{{no-scope}}') = COALESCE($5, '{{no-scope}}')
            """,
            year,
            activity_type,
            country,
            unit,
            scope,
        )
        return _row_to_factor(row) if row is not None else None

    async def find_by_activity(
        self,
        activity: str,
        unit: Optional[str] = None,
        year: Optional[int] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 20,
        unit_substring: bool = False,
    ) -> list[EmissionFactor]:
        """Keyword/activity search with optional filters (case-insensitive).

        ``unit_substring`` (D23): match the unit with a substring instead of an
        exact value so a human operator typing "kWh" also finds "kWh (Gross CV)"
        candidates in the extraction mapping picker.

        CL-3/CL-14: the supplied unit is alias-normalised first (``L`` →
        ``litres``, ``m3`` → ``cubic metres`` …) so the search matches the
        canonical factor-unit vocabulary, and results are ordered with exact
        unit matches first so the correct factor surfaces on the first page.
        """
        from core.units import normalize_unit

        clauses = ["ef.activity_type ILIKE '%' || $1 || '%'"]
        params: list[object] = [activity]
        unit_match_clause = "1=1"
        if unit is not None:
            unit_norm = normalize_unit(unit) or unit
            params.append(unit_norm)
            if unit_substring:
                clauses.append(f"ef.unit ILIKE '%' || ${len(params)} || '%'")
            else:
                clauses.append(f"ef.unit = ${len(params)}")
            # Relevance: exact (normalised) unit match first, then activity.
            unit_match_clause = f"(ef.unit = ${len(params)}) DESC"
        if year is not None:
            params.append(year)
            clauses.append(f"ef.reporting_year = ${len(params)}")
        if country is not None:
            params.append(country)
            clauses.append(f"COALESCE(ef.country, 'GB') = ${len(params)}")
        if provider is not None:
            params.append(provider)
            clauses.append(f"ib.provider_key = ${len(params)}")
        params.append(limit)
        query = (
            f"SELECT {_FACTOR_COLUMNS} {_FACTOR_FROM}"
            " WHERE " + " AND ".join(clauses)
            + f" ORDER BY {unit_match_clause}, ef.reporting_year DESC, ef.activity_type"
            + f" LIMIT ${len(params)}"
        )
        rows = await self._fetch_all(query, *params)
        return [_row_to_factor(r) for r in rows]


    async def bulk_upsert(self, factors: list[EmissionFactor]) -> int:
        """Idempotent natural-key upsert; returns the number of inserted rows.

        Existing factors (matched on the RC2 natural-key unique index) are
        updated in place; only genuinely new rows count as inserted.
        """
        if not factors:
            return 0
        async with self._pool.acquire() as conn:
            inserted = 0
            for factor in factors:
                row = await conn.fetchrow(
                    """
                    INSERT INTO public.emission_factors (
                        id, reporting_year, activity_type, co2e_multiplier,
                        unit, scope, factor_source, factor_set, country,
                        import_batch_id, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                    ON CONFLICT (
                        reporting_year, activity_type,
                        COALESCE(country, 'GB'),
                        COALESCE(unit, '{no-unit}'),
                        COALESCE(scope, '{no-scope}')
                    )
                    DO UPDATE SET
                        co2e_multiplier = EXCLUDED.co2e_multiplier,
                        unit = EXCLUDED.unit,
                        scope = EXCLUDED.scope,
                        factor_source = EXCLUDED.factor_source,
                        factor_set = EXCLUDED.factor_set,
                        import_batch_id = EXCLUDED.import_batch_id,
                        updated_at = NOW()
                    RETURNING (xmax = 0) AS inserted
                    """,
                    factor.id,
                    factor.reporting_year,
                    factor.activity_type,
                    factor.co2e_multiplier,
                    factor.unit,
                    factor.scope,
                    factor.factor_source,
                    factor.factor_set,
                    factor.country,
                    factor.import_batch_id,
                )
                if row is not None and row["inserted"]:
                    inserted += 1
            return inserted

    async def get_active_set(self, provider: str, year: int) -> list[EmissionFactor]:
        """Return every factor of the active batch for ``provider`` + ``year``."""
        rows = await self._fetch_all(
            f"""
            SELECT {_FACTOR_COLUMNS} {_FACTOR_FROM}
            WHERE ib.provider_key = $1
              AND ib.reporting_year = $2
              AND ib.is_active = TRUE
            ORDER BY ef.activity_type
            """,
            provider,
            year,
        )
        return [_row_to_factor(r) for r in rows]

    async def deactivate_by_batch(self, batch_id: str) -> int:
        """Detach every factor of ``batch_id`` from its batch; returns count."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.emission_factors
                SET import_batch_id = NULL, updated_at = NOW()
                WHERE import_batch_id = $1
                """,
                batch_id,
            )
            return _rowcount(result)

    async def load_all_for_index(self) -> list[EmissionFactor]:
        """Return every factor (for search-index loading)."""
        rows = await self._fetch_all(
            f"SELECT {_FACTOR_COLUMNS} {_FACTOR_FROM}"
            " ORDER BY ef.reporting_year, ef.activity_type"
        )
        return [_row_to_factor(r) for r in rows]

    async def count_by_provider(self, provider: str) -> int:
        """Return the total factor count for ``provider``."""
        row = await self._fetch_one(
            """
            SELECT COUNT(*) AS count
            FROM public.emission_factors ef
            JOIN public.import_batches ib ON ib.id = ef.import_batch_id
            WHERE ib.provider_key = $1
            """,
            provider,
        )
        return int(row["count"]) if row is not None else 0


    async def save(self, entity: EmissionFactor) -> EmissionFactor:
        """Upsert a single factor by natural key and return the stored state."""
        row = await self._fetch_one(
            """
            INSERT INTO public.emission_factors (
                id, reporting_year, activity_type, co2e_multiplier,
                unit, scope, factor_source, factor_set, country,
                import_batch_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
            ON CONFLICT (
                reporting_year, activity_type,
                COALESCE(country, 'GB'),
                COALESCE(unit, '{no-unit}'),
                COALESCE(scope, '{no-scope}')
            )
            DO UPDATE SET
                co2e_multiplier = EXCLUDED.co2e_multiplier,
                unit = EXCLUDED.unit,
                scope = EXCLUDED.scope,
                factor_source = EXCLUDED.factor_source,
                factor_set = EXCLUDED.factor_set,
                import_batch_id = EXCLUDED.import_batch_id,
                updated_at = NOW()
            RETURNING
                id, reporting_year, activity_type, co2e_multiplier, unit, scope,
                factor_source, factor_set, country, import_batch_id,
                (SELECT provider_key FROM public.import_batches ib
                 WHERE ib.id = emission_factors.import_batch_id) AS provider_key
            """,
            entity.id,
            entity.reporting_year,
            entity.activity_type,
            entity.co2e_multiplier,
            entity.unit,
            entity.scope,
            entity.factor_source,
            entity.factor_set,
            entity.country,
            entity.import_batch_id,
        )
        if row is None:
            raise RuntimeError("factor upsert returned no row")
        return _row_to_factor(row)

    async def delete(self, id: str) -> None:
        """Delete a factor by id (rarely used; factors are deactivated)."""
        await self._execute(
            "DELETE FROM public.emission_factors WHERE id = $1", id
        )


def _rowcount(status: str) -> int:
    """Parse the ``N`` row-count out of an asyncpg command-status string."""
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0

