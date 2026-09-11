"""Processing-origin vocabulary (V1.2 §9 + CT-QC-004).

CarbonTally work is processed by one of two origins:

* ``CARBONTALLY_INTERNAL`` — CarbonTally's own Data Processing / Extraction
  staff (``manual_extraction_batches.entity_id IS NULL``);
* ``PROCESSING_ENTITY`` — an external Processing Entity to which CarbonTally
  assigned the batch (``manual_extraction_batches.entity_id`` populated).

The origin is preserved as auditable provenance so CarbonTally QC can verify
processed data regardless of origin (CT-QC-002) and so CarbonTally can tell
which upstream controls apply (internal path has no PE Review/PE QC; the PE
path does). This module is pure — no database access.
"""
from __future__ import annotations

from typing import Optional

#: Processing origin values (stable, machine-readable).
ORIGIN_CARBONTALLY_INTERNAL = "CARBONTALLY_INTERNAL"
ORIGIN_PROCESSING_ENTITY = "PROCESSING_ENTITY"

#: Human labels for the same two origins.
ORIGIN_LABELS: dict[str, str] = {
    ORIGIN_CARBONTALLY_INTERNAL: "CarbonTally internal processing",
    ORIGIN_PROCESSING_ENTITY: "Processing Entity processing",
}


def processing_origin_for_batch(entity_id: Optional[str]) -> str:
    """Derive the processing origin from a batch's assignment carrier.

    ``manual_extraction_batches.entity_id`` is the CarbonTally-controlled
    assignment column: NULL = CarbonTally internal processing; populated = the
    Processing Entity performing the work. (Reassignments are recorded by the
    existing assignment audit events; this derives the CURRENT origin.)
    """
    if entity_id:
        return ORIGIN_PROCESSING_ENTITY
    return ORIGIN_CARBONTALLY_INTERNAL


def processing_origin_label(origin: str) -> str:
    """Human-readable label for a processing origin value."""
    return ORIGIN_LABELS.get(origin, origin)
