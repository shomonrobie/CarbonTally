"""Admin provider endpoints (prep-pack Phase 10.3, providers).

Exposes the provider state already supported by the backend/provider
architecture. Phase 10 does **not** implement EPA/ADEME/IPCC — the catalogue
reports them as ``implemented = false, status = "deferred"`` and never pretends
they are live.

Live database state (active import batches, factor counts) is attached only for
implemented providers, through the existing repositories.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.contracts import (
    ImportBatchOut,
    ProviderListOut,
    ProviderOut,
    import_batch_out,
)
from api.dependencies import RepositoryBundle, get_repositories, require_admin

router = APIRouter(prefix="/api/v2/admin/providers", tags=["Admin Providers"])


def _catalog_entry(
    key: str,
    name: str,
    jurisdiction: str,
    country_codes: tuple[str, ...],
    website: str,
    license: str,
    latest_version: str,
    publisher: str,
    language: str,
    documentation_url: str,
    implemented: bool,
) -> dict[str, Any]:
    return {
        "key": key,
        "name": name,
        "jurisdiction": jurisdiction,
        "country_codes": list(country_codes),
        "website": website,
        "license": license,
        "latest_version": latest_version,
        "publisher": publisher,
        "language": language,
        "documentation_url": documentation_url,
        "implemented": implemented,
        "status": "active" if implemented else "deferred",
    }


#: Known provider catalogue. SEAI and DEFRA are implemented (Phase 5, verified
#: Phase 9D); EPA/ADEME/IPCC remain deferred (Phase 12 scope — not Phase 10).
PROVIDER_CATALOG: tuple[dict[str, Any], ...] = (
    _catalog_entry(
        key="seai",
        name="SEAI Emission Factors",
        jurisdiction="Ireland",
        country_codes=("IE",),
        website="https://www.seai.ie/",
        license="SEAI data — attribution required",
        latest_version="2025",
        publisher="Sustainable Energy Authority of Ireland",
        language="en",
        documentation_url="https://www.seai.ie/data-and-insights/",
        implemented=True,
    ),
    _catalog_entry(
        key="defra",
        name="UK Government GHG Conversion Factors",
        jurisdiction="United Kingdom",
        country_codes=("GB",),
        website="https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting",
        license="Open Government Licence v3.0",
        latest_version="2025",
        publisher="UK Department for Energy Security & Net Zero",
        language="en",
        documentation_url="https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting",
        implemented=True,
    ),
    _catalog_entry(
        key="epa",
        name="EPA (Ireland) Emission Factors",
        jurisdiction="Ireland",
        country_codes=("IE",),
        website="https://www.epa.ie/",
        license="",
        latest_version="",
        publisher="Environmental Protection Agency (Ireland)",
        language="en",
        documentation_url="",
        implemented=False,
    ),
    _catalog_entry(
        key="ademe",
        name="ADEME Base Carbone",
        jurisdiction="France",
        country_codes=("FR",),
        website="https://base-emissions.ademe.fr/",
        license="",
        latest_version="",
        publisher="ADEME",
        language="fr",
        documentation_url="https://base-emissions.ademe.fr/",
        implemented=False,
    ),
    _catalog_entry(
        key="ipcc",
        name="IPCC Emission Factor Database",
        jurisdiction="Global",
        country_codes=("*",),
        website="https://www.ipcc-nggip.iges.or.jp/EFDB/main.php",
        license="",
        latest_version="",
        publisher="IPCC",
        language="en",
        documentation_url="https://www.ipcc-nggip.iges.or.jp/EFDB/main.php",
        implemented=False,
    ),
)

_CATALOG_BY_KEY = {entry["key"]: entry for entry in PROVIDER_CATALOG}


async def _build_provider(entry: dict[str, Any], repos: RepositoryBundle) -> ProviderOut:
    """Attach live repository state for implemented providers only."""
    active_batches: list[ImportBatchOut] = []
    factor_count = 0
    if entry["implemented"]:
        history = await repos.imports.get_history(entry["key"])
        active_batches = [import_batch_out(b) for b in history if b.is_active]
        factor_count = await repos.factors.count_by_provider(entry["key"])
    return ProviderOut(**{k: v for k, v in entry.items()}, active_batches=active_batches, factor_count=factor_count)


@router.get("", response_model=ProviderListOut)
async def list_providers(
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ProviderListOut:
    """List every known provider with implementation state."""
    providers = [await _build_provider(entry, repos) for entry in PROVIDER_CATALOG]
    return ProviderListOut(providers=providers)


@router.get("/{key}", response_model=ProviderOut)
async def get_provider(
    key: str,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ProviderOut:
    """Return one provider's metadata + live state (404 when unknown)."""
    entry = _CATALOG_BY_KEY.get(key)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"provider {key!r} is not registered")
    return await _build_provider(entry, repos)
