# backend/routes/admin/defra.py
"""Admin factor management on the CANONICAL factor model (PD-3).

CT-FINAL-01 continuation — ratified Product Owner decision PD-3:

    "Admin factor management is part of the first production release."

This module therefore operates on the canonical CarbonTally factor-governance
store ``public.emission_factors``.  The retired DEFRA conversion-factor table is
**not** a dependency of this module and must never be recreated merely to keep
legacy code working (CT-SCHEMA-03 F-01: its recreation is structurally
forbidden).

Surface (paths preserved from the pre-existing implementation):

    GET    /api/admin/defra/factors
    GET    /api/admin/defra/factors/{factor_id}
    POST   /api/admin/defra/factors
    POST   /api/admin/defra/factors/bulk
    PUT    /api/admin/defra/factors/{factor_id}
    DELETE /api/admin/defra/factors/{factor_id}
    GET    /api/admin/defra/years
    GET    /api/admin/defra/activities
    GET    /api/admin/defra/validate

Authorization (PD-3): CarbonTally internal admin authority only
(``Depends(require_admin())``).  Factor governance is PLATFORM-GLOBAL: there is
no tenant scope that could grant access, so a tenant-scoped (customer,
consultant-client or Processing-Entity) identity is simply not an admin and is
denied.  The UI is never the security boundary.

Provenance: every write records the canonical factor provenance columns
(``factor_source``, ``factor_set``, ``country``, ``unit``, ``scope``) and emits a
best-effort append-only entry into the canonical audit ledger
(``public.audit_trail``, ``domain.audit.AuditEntry``) — the single audit system
(CT-AUDIT-01 Tier 1).  No second audit model is introduced.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_admin
from core.logging import get_logger
from database import get_supabase_client
from domain.audit import AuditEntry
from utils.factor_catalogue import (
    CANONICAL_FACTOR_COLUMNS as _FACTOR_COLUMNS,
    CANONICAL_FACTOR_TABLE as _FACTOR_TABLE,
    DEFAULT_COUNTRY as _DEFAULT_COUNTRY,
    NO_SCOPE as _NO_SCOPE,
    NO_UNIT as _NO_UNIT,
    canonical_factor_payload,
    clean as _clean,
    find_canonical_factor,
    is_unique_violation as _is_unique_violation,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/admin/defra", tags=["Admin - Factor Management (canonical)"]
)


def _single_data(result):
    """Read the row from a ``maybe_single().execute()`` result, or ``None``.

    CT-FINAL-01 (D-6): ``postgrest`` returns ``None`` — not a response object —
    when ``maybe_single()`` matches no row (verified against the installed
    ``postgrest`` in ``backend/.venv``).  Reading ``result.data`` off that
    ``None`` raised ``AttributeError`` and the generic handler turned a
    *missing* factor into HTTP 500; a missing factor is a 404.  Older
    ``postgrest`` versions return a response whose ``data`` is ``None``, so both
    shapes are handled here.
    """
    return getattr(result, "data", None)



class DEFRAFactorBase(BaseModel):
    """Canonical factor payload (core identity + provenance).

    ``reporting_year`` / ``activity_type`` / ``co2e_multiplier`` are the
    canonical core columns; ``unit`` / ``scope`` / ``country`` /
    ``factor_source`` / ``factor_set`` are the canonical provenance columns
    (CT-SCHEMA-02 inventory).  The provenance fields are optional so existing
    clients keep working, but when supplied they are persisted verbatim instead
    of being silently dropped.
    """

    reporting_year: int = Field(..., ge=2000, le=2100, description="Reporting year")
    activity_type: str = Field(..., min_length=1, max_length=150, description="Activity type (e.g., Diesel (DERV))")
    co2e_multiplier: float = Field(..., gt=0, description="CO2e multiplier (kg CO2e per unit)")

    unit: Optional[str] = Field(None, max_length=50, description="Canonical factor unit (e.g. litres, kWh)")
    scope: Optional[str] = Field(None, max_length=50, description="Canonical factor scope")
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2 country; defaults to GB")
    factor_source: Optional[str] = Field(None, max_length=100, description="Factor source / publisher")
    factor_set: Optional[str] = Field(None, max_length=100, description="Factor set / publication")

    @field_validator("activity_type", "unit", "scope", "factor_source", "factor_set")
    @classmethod
    def validate_activity_type(cls, v):
        """Ensure textual fields are properly formatted."""
        return _clean(v)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v):
        """A country code is ISO 3166-1 alpha-2 or absent."""
        cleaned = _clean(v)
        if cleaned is None:
            return None
        if not (len(cleaned) == 2 and cleaned.isalpha()):
            raise ValueError("country must be an ISO 3166-1 alpha-2 code")
        return cleaned.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "reporting_year": 2024,
                "activity_type": "Diesel (DERV)",
                "co2e_multiplier": 2.68,
                "unit": "litres",
                "scope": "Scope 1",
                "country": "GB",
            }
        }


class DEFRAFactorCreate(DEFRAFactorBase):
    """Request model for creating a canonical factor."""


class DEFRAFactorUpdate(BaseModel):
    """Request model for updating a canonical factor (all fields optional)."""

    reporting_year: Optional[int] = Field(None, ge=2000, le=2100)
    activity_type: Optional[str] = Field(None, min_length=1, max_length=150)
    co2e_multiplier: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    scope: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=2)
    factor_source: Optional[str] = Field(None, max_length=100)
    factor_set: Optional[str] = Field(None, max_length=100)

    @field_validator("activity_type", "unit", "scope", "factor_source", "factor_set")
    @classmethod
    def validate_activity_type(cls, v):
        """Ensure textual fields are properly formatted."""
        return _clean(v)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v):
        """A country code is ISO 3166-1 alpha-2 or absent."""
        cleaned = _clean(v)
        if cleaned is None:
            return None
        if not (len(cleaned) == 2 and cleaned.isalpha()):
            raise ValueError("country must be an ISO 3166-1 alpha-2 code")
        return cleaned.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "activity_type": "Diesel (DERV) - Updated",
                "co2e_multiplier": 2.75,
            }
        }


class DEFRAFactorBulkCreate(BaseModel):
    """Request model for bulk creating canonical factors."""

    factors: List[DEFRAFactorCreate] = Field(..., min_length=1, description="List of factors to create")
    update_existing: bool = Field(
        False,
        description=(
            "When true, an existing canonical natural key has its multiplier and "
            "provenance refreshed instead of being skipped. Defaults to false so "
            "a bulk create can never silently change a governed factor."
        ),
    )


class DEFRAFactorResponse(BaseModel):
    """Response model for a canonical factor."""

    id: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: float
    unit: Optional[str] = None
    scope: Optional[str] = None
    country: Optional[str] = None
    factor_source: Optional[str] = None
    factor_set: Optional[str] = None
    import_batch_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DEFRAFactorListResponse(BaseModel):
    """Response model for a canonical factor list."""

    factors: List[DEFRAFactorResponse]
    total: int
    years_available: List[int]
    activities_available: List[str]

# ==========================================
# CANONICAL HELPERS
# ==========================================

def _canonical_payload(factor: DEFRAFactorCreate) -> Dict[str, Any]:
    """Map a request model onto the canonical ``emission_factors`` columns.

    Reads and writes use ONE canonical table with ONE canonical column set; a
    legacy factor store is never addressed.
    """
    return canonical_factor_payload(
        reporting_year=factor.reporting_year,
        activity_type=factor.activity_type,
        co2e_multiplier=factor.co2e_multiplier,
        unit=factor.unit,
        scope=factor.scope,
        country=factor.country,
        factor_source=factor.factor_source,
        factor_set=factor.factor_set,
    )


def _find_duplicate(supabase_client, **natural_key) -> Optional[Dict[str, Any]]:
    """Return the existing factor with the same canonical natural key, or None.

    Thin adapter over ``utils.factor_catalogue.find_canonical_factor`` so the
    canonical natural-key rule exists in exactly ONE place.  The write-payload
    keys (multiplier, provenance) are not part of the identity and are ignored.
    """
    return find_canonical_factor(
        supabase_client,
        reporting_year=natural_key["reporting_year"],
        activity_type=natural_key["activity_type"],
        unit=natural_key.get("unit"),
        scope=natural_key.get("scope"),
        country=natural_key.get("country"),
    )


def _factor_response(row: Dict[str, Any]) -> DEFRAFactorResponse:
    """Map one canonical row to the response model (never inventing values)."""
    return DEFRAFactorResponse(
        id=str(row["id"]),
        reporting_year=int(row["reporting_year"]),
        activity_type=str(row["activity_type"]),
        co2e_multiplier=float(row["co2e_multiplier"]),
        unit=row.get("unit"),
        scope=row.get("scope"),
        country=row.get("country"),
        factor_source=row.get("factor_source"),
        factor_set=row.get("factor_set"),
        import_batch_id=row.get("import_batch_id"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


async def _record_factor_audit(
    repos: RepositoryBundle,
    *,
    current_user: AuthUser,
    action: str,
    factor_id: str,
    changed_fields: Dict[str, Any],
) -> None:
    """Append one best-effort entry to the canonical audit ledger (``audit_trail``).

    Audit is append-only and must never break the factor operation; failures are
    logged and swallowed (the same posture as the other canonical writers).
    """
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=f"emission_factor:{factor_id}",
        entity_type="emission_factor",
        entity_id=str(factor_id),
        action=f"factor.{action}",
        actor=str(current_user.user_id),
        occurred_at=datetime.now(timezone.utc),
        changed_fields=changed_fields,
    )
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 - audit must not break factor governance
        logger.exception("factor.%s audit failed for factor %s", action, factor_id)


async def get_available_years(supabase_client) -> List[int]:
    """Get all available reporting years from the canonical factor store."""
    try:
        result = supabase_client.from_(_FACTOR_TABLE) \
            .select("reporting_year") \
            .order("reporting_year", desc=True) \
            .execute()

        years = list(set([f["reporting_year"] for f in result.data])) if result.data else []
        return sorted(years, reverse=True)
    except Exception as e:
        print(f"Error getting available years: {e}")
        return []


async def get_available_activities(supabase_client) -> List[str]:
    """Get all available activity types from the canonical factor store."""
    try:
        result = supabase_client.from_(_FACTOR_TABLE) \
            .select("activity_type") \
            .order("activity_type") \
            .execute()

        activities = list(set([f["activity_type"] for f in result.data])) if result.data else []
        return sorted(activities)
    except Exception as e:
        print(f"Error getting available activities: {e}")
        return []

# ==========================================
# ENDPOINTS
# ==========================================
# Every endpoint on this surface is CarbonTally internal admin authority only
# (PD-3). Factor governance is platform-global, so no organisation/tenant scope
# can grant access to it.

@router.get("/factors")
async def get_admin_defra_factors(
    year: Optional[int] = Query(None, description="Filter by reporting year"),
    activity: Optional[str] = Query(None, description="Filter by activity type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_admin()),
):
    """List canonical factors with filters (admin only)."""
    try:
        supabase = get_supabase_client()

        query = supabase.from_(_FACTOR_TABLE).select(_FACTOR_COLUMNS)
        count_query = supabase.from_(_FACTOR_TABLE).select("id", count="exact")

        if year:
            query = query.eq("reporting_year", year)
            count_query = count_query.eq("reporting_year", year)
        if activity:
            query = query.ilike("activity_type", f"%{activity}%")
            count_query = count_query.ilike("activity_type", f"%{activity}%")

        count_result = count_query.execute()
        total = count_result.count or 0

        result = query.order("reporting_year", desc=True) \
            .order("activity_type") \
            .range(offset, offset + limit - 1) \
            .execute()

        return {
            "success": True,
            "data": result.data or [],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        print(f"Error getting factors: {e}")
        logger.exception("admin factor listing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load factors. Please try again.",
        )


@router.get("/factors/{factor_id}", response_model=DEFRAFactorResponse)
async def get_admin_defra_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_admin()),
):
    """Read one canonical factor by id (admin only)."""
    try:
        supabase = get_supabase_client()

        result = supabase.from_(_FACTOR_TABLE) \
            .select(_FACTOR_COLUMNS) \
            .eq("id", factor_id) \
            .maybe_single() \
            .execute()

        if not _single_data(result):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factor not found",
            )

        return _factor_response(_single_data(result))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting factor: {e}")
        logger.exception("admin factor read failed for %s", factor_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the factor. Please try again.",
        )


@router.post("/factors", response_model=DEFRAFactorResponse)
async def create_defra_factor(
    factor_data: DEFRAFactorCreate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Create a canonical factor (admin only).

    A factor with the same canonical natural key (year, activity, country,
    unit, scope) is reported as a conflict rather than silently duplicated.
    """
    try:
        supabase = get_supabase_client()
        payload = _canonical_payload(factor_data)

        existing = _find_duplicate(supabase, **payload)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Factor already exists for {factor_data.activity_type} "
                    f"in {factor_data.reporting_year}"
                ),
            )

        try:
            result = supabase.from_(_FACTOR_TABLE).insert(payload).execute()
        except Exception as insert_error:
            if _is_unique_violation(insert_error):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Factor already exists for {factor_data.activity_type} "
                        f"in {factor_data.reporting_year}"
                    ),
                )
            raise

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create factor",
            )

        factor = result.data[0]
        await _record_factor_audit(
            repos,
            current_user=current_user,
            action="created",
            factor_id=str(factor["id"]),
            changed_fields=payload,
        )
        return _factor_response(factor)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating factor: {e}")
        logger.exception("admin factor create failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the factor. Please try again.",
        )

@router.post("/factors/bulk")
async def create_defra_factors_bulk(
    bulk_data: DEFRAFactorBulkCreate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Bulk create / refresh canonical factors (admin only).

    Existing canonical natural keys are SKIPPED by default (never overwritten),
    so a bulk create cannot silently change a governed factor's multiplier.  The
    caller may opt in to refreshing them with ``update_existing`` (the admin
    import surface does), and every write is recorded in the canonical audit
    ledger.
    """
    try:
        supabase = get_supabase_client()

        created = 0
        updated = 0
        skipped = 0
        created_ids: List[str] = []
        updated_ids: List[str] = []
        errors: List[str] = []

        for factor in bulk_data.factors:
            payload = _canonical_payload(factor)
            try:
                existing = _find_duplicate(supabase, **payload)
                if existing:
                    if not bulk_data.update_existing:
                        skipped += 1
                        continue
                    supabase.from_(_FACTOR_TABLE) \
                        .update({
                            "co2e_multiplier": payload["co2e_multiplier"],
                            "unit": payload["unit"],
                            "scope": payload["scope"],
                            "country": payload["country"],
                            "factor_source": payload["factor_source"],
                            "factor_set": payload["factor_set"],
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }) \
                        .eq("id", existing["id"]) \
                        .execute()
                    updated += 1
                    updated_ids.append(str(existing["id"]))
                    continue

                result = supabase.from_(_FACTOR_TABLE).insert(payload).execute()
                if result.data:
                    created += 1
                    created_ids.append(str(result.data[0]["id"]))
                else:
                    errors.append(
                        f"Failed to create {factor.activity_type} ({factor.reporting_year})"
                    )
            except Exception as e:
                if _is_unique_violation(e):
                    skipped += 1
                    continue
                errors.append(
                    f"Error creating {factor.activity_type} "
                    f"({factor.reporting_year}): {e}"
                )

        if created_ids or updated_ids:
            await _record_factor_audit(
                repos,
                current_user=current_user,
                action="bulk_written",
                factor_id=(created_ids or updated_ids)[0],
                changed_fields={
                    "created": created,
                    "updated": updated,
                    "factor_ids": created_ids + updated_ids,
                },
            )

        return {
            "success": True,
            "message": (
                f"Created {created} factors, refreshed {updated} existing, "
                f"skipped {skipped}"
            ),
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors if errors else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error bulk creating factors: {e}")
        logger.exception("admin bulk factor create failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the factors. Please try again.",
        )


@router.put("/factors/{factor_id}", response_model=DEFRAFactorResponse)
async def update_defra_factor(
    factor_id: str,
    update_data: DEFRAFactorUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Update a canonical factor (admin only).

    If the update changes the canonical natural key, an existing factor on the
    target key is a conflict.  The change is recorded in the canonical audit
    ledger so factor governance stays traceable.
    """
    try:
        supabase = get_supabase_client()

        existing = supabase.from_(_FACTOR_TABLE) \
            .select("id, reporting_year, activity_type, unit, scope, country") \
            .eq("id", factor_id) \
            .maybe_single() \
            .execute()

        existing_row = _single_data(existing)
        if not existing_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factor not found",
            )

        current = existing_row
        update_dict: Dict[str, Any] = {}
        for field in (
            "activity_type",
            "co2e_multiplier",
            "reporting_year",
            "unit",
            "scope",
            "country",
            "factor_source",
            "factor_set",
        ):
            value = getattr(update_data, field)
            if value is not None:
                update_dict[field] = value

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        new_year = update_dict.get("reporting_year", current["reporting_year"])
        new_activity = update_dict.get("activity_type", current["activity_type"])
        new_unit = update_dict.get("unit", current.get("unit"))
        new_scope = update_dict.get("scope", current.get("scope"))
        new_country = update_dict.get("country", current.get("country"))
        key_changed = (
            str(new_year) != str(current["reporting_year"])
            or str(new_activity) != str(current["activity_type"])
            or (new_unit or _NO_UNIT) != (current.get("unit") or _NO_UNIT)
            or (new_scope or _NO_SCOPE) != (current.get("scope") or _NO_SCOPE)
            or (new_country or _DEFAULT_COUNTRY)
            != (current.get("country") or _DEFAULT_COUNTRY)
        )

        if key_changed:
            duplicate = _find_duplicate(
                supabase,
                reporting_year=new_year,
                activity_type=new_activity,
                unit=new_unit,
                scope=new_scope,
                country=new_country,
            )
            if duplicate and str(duplicate["id"]) != str(factor_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Factor already exists for {new_activity} in {new_year}",
                )

        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            result = supabase.from_(_FACTOR_TABLE) \
                .update(update_dict) \
                .eq("id", factor_id) \
                .execute()
        except Exception as update_error:
            if _is_unique_violation(update_error):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Factor already exists for {new_activity} in {new_year}",
                )
            raise

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update factor",
            )

        factor = result.data[0]
        await _record_factor_audit(
            repos,
            current_user=current_user,
            action="updated",
            factor_id=str(factor_id),
            changed_fields={
                "changed": sorted(k for k in update_dict if k != "updated_at"),
                "before": {
                    "reporting_year": current["reporting_year"],
                    "activity_type": current["activity_type"],
                    "unit": current.get("unit"),
                    "scope": current.get("scope"),
                    "country": current.get("country"),
                },
            },
        )
        return _factor_response(factor)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating factor: {e}")
        logger.exception("admin factor update failed for %s", factor_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the factor. Please try again.",
        )

@router.delete("/factors/{factor_id}")
async def delete_defra_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Delete a canonical factor (admin only).

    A factor referenced by any persisted emissions record is NOT deletable: the
    provenance link must survive (AGENTS.md §17).  The canonical reference column
    is ``emissions_logs.emission_factor_id``.
    """
    try:
        supabase = get_supabase_client()

        existing = supabase.from_(_FACTOR_TABLE) \
            .select("id, activity_type, reporting_year") \
            .eq("id", factor_id) \
            .maybe_single() \
            .execute()

        existing_row = _single_data(existing)
        if not existing_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factor not found",
            )

        emissions_usage = supabase.from_("emissions_logs") \
            .select("id", count="exact") \
            .eq("emission_factor_id", factor_id) \
            .execute()

        if emissions_usage.count and emissions_usage.count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cannot delete factor that is used in "
                    f"{emissions_usage.count} emissions records"
                ),
            )

        supabase.from_(_FACTOR_TABLE).delete().eq("id", factor_id).execute()

        await _record_factor_audit(
            repos,
            current_user=current_user,
            action="deleted",
            factor_id=str(factor_id),
            changed_fields={
                "activity_type": existing_row["activity_type"],
                "reporting_year": existing_row["reporting_year"],
            },
        )

        return {
            "success": True,
            "message": (
                f"Factor '{existing_row['activity_type']}' "
                f"({existing_row['reporting_year']}) deleted successfully"
            ),
            "factor_id": factor_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting factor: {e}")
        logger.exception("admin factor delete failed for %s", factor_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the factor. Please try again.",
        )


@router.get("/years")
async def get_defra_years(
    current_user: AuthUser = Depends(require_admin()),
):
    """Get all available reporting years (canonical store, admin only)."""
    try:
        supabase = get_supabase_client()
        years = await get_available_years(supabase)
        return {"years": years, "total": len(years)}

    except Exception as e:
        print(f"Error getting factor years: {e}")
        logger.exception("admin factor years failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load reporting years. Please try again.",
        )


@router.get("/activities")
async def get_defra_activities(
    reporting_year: Optional[int] = Query(None, description="Filter by reporting year"),
    current_user: AuthUser = Depends(require_admin()),
):
    """Get all available activity types (canonical store, admin only)."""
    try:
        supabase = get_supabase_client()

        query = supabase.from_(_FACTOR_TABLE).select("activity_type")
        if reporting_year:
            query = query.eq("reporting_year", reporting_year)

        result = query.order("activity_type").execute()
        activities = list(set([f["activity_type"] for f in result.data])) if result.data else []

        return {"activities": sorted(activities), "total": len(activities)}

    except Exception as e:
        print(f"Error getting factor activities: {e}")
        logger.exception("admin factor activities failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load activity types. Please try again.",
        )


@router.get("/validate")
async def validate_defra_factor(
    reporting_year: int = Query(..., description="Reporting year to validate"),
    activity_type: str = Query(..., description="Activity type to validate"),
    unit: Optional[str] = Query(None, description="Optional canonical unit"),
    scope: Optional[str] = Query(None, description="Optional canonical scope"),
    country: Optional[str] = Query(None, description="Optional ISO 3166-1 alpha-2 country"),
    current_user: AuthUser = Depends(require_admin()),
):
    """Validate whether a canonical factor exists for the given natural key.

    The lookup is exact on the canonical natural key; a caller may narrow it
    with the optional provenance dimensions.
    """
    try:
        supabase = get_supabase_client()

        match = _find_duplicate(
            supabase,
            reporting_year=reporting_year,
            activity_type=activity_type,
            unit=_clean(unit),
            scope=_clean(scope),
            country=_clean(country).upper() if _clean(country) else None,
        )

        if match:
            detailed = supabase.from_(_FACTOR_TABLE) \
                .select(_FACTOR_COLUMNS) \
                .eq("id", match["id"]) \
                .maybe_single() \
                .execute()
            row = _single_data(detailed) or match
            return {
                "exists": True,
                "factor_id": str(row["id"]),
                "co2e_multiplier": float(row["co2e_multiplier"]),
                "reporting_year": reporting_year,
                "activity_type": activity_type,
                "unit": row.get("unit"),
                "scope": row.get("scope"),
                "country": row.get("country"),
            }

        return {
            "exists": False,
            "reporting_year": reporting_year,
            "activity_type": activity_type,
            "message": f"No factor found for {activity_type} in {reporting_year}",
        }

    except Exception as e:
        print(f"Error validating factor: {e}")
        logger.exception("admin factor validation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to validate the factor. Please try again.",
        )
