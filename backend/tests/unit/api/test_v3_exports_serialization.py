"""V3 exports serialization regression tests (P1-F1).

``GET /api/v3/exports/emissions.json`` returned HTTP 500 because the exports
repository handed raw asyncpg ``uuid.UUID`` / ``date`` objects to FastAPI's
JSON encoder. The fix coerces database types to JSON-safe primitives at the
repository boundary (``data.exports._jsonable_row``).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from data.exports import _jsonable_row


def test_jsonable_row_coerces_asyncpg_types() -> None:
    row = {
        "id": uuid.UUID("11111111-1111-4111-8111-111111111111"),
        "organization_id": uuid.UUID("11111111-1111-4111-8111-111111111111"),
        "asset_id": uuid.UUID("21111111-1111-4111-8111-111111111111"),
        "emission_factor_id": None,
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 1, 31),
        "raw_quantity": Decimal("12500"),
        "calculated_kg_co2e": Decimal("2212.50"),
        "unit": "kWh",
        "scope": "Scope 2",
        "snapshot_id": uuid.UUID("31111111-1111-4111-8111-111111111111"),
        "created_at": datetime(2025, 2, 1, 12, 0, 0),
    }
    out = _jsonable_row(row)

    # UUIDs → strings, dates/datetimes → ISO-8601, Decimals → floats, scalars
    # untouched.
    assert out["id"] == "11111111-1111-4111-8111-111111111111"
    assert out["organization_id"] == "11111111-1111-4111-8111-111111111111"
    assert out["asset_id"] == "21111111-1111-4111-8111-111111111111"
    assert out["emission_factor_id"] is None
    assert out["start_date"] == "2025-01-01"
    assert out["end_date"] == "2025-01-31"
    assert out["created_at"] == "2025-02-01T12:00:00"
    assert out["snapshot_id"] == "31111111-1111-4111-8111-111111111111"
    assert out["raw_quantity"] == 12500.0
    assert out["calculated_kg_co2e"] == 2212.50
    assert out["unit"] == "kWh"
    assert out["scope"] == "Scope 2"

    # The whole payload must be JSON-serialisable.
    import json

    json.dumps(out)


def test_jsonable_row_handles_empty_and_scalar_rows() -> None:
    assert _jsonable_row({}) == {}
    assert _jsonable_row({"status": "approved", "n": 3}) == {"status": "approved", "n": 3}
