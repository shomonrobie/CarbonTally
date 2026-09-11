"""P6-2B-4 — manual/automatic processing-mode containment (Phase-6 control).

The PO rule: work whose extraction OR mapping was performed manually by an
authorized human actor must pass the mandatory CarbonTally CT-QC gate before it
can reach Customer Review/Approval; automatically extracted/mapped work does
NOT require routine human CT-QC.

This module implements the agreed **P1 containment** classification — it is a
DELIBERATELY DERIVED, temporary predicate, NOT the final provenance
architecture (deferred to the P2/D7 provenance workstream). P1 classifies an
item as AUTOMATIC only when a durable automatic-processing job exists for it AND
the machine actually produced output (the job's write-once
``automation_extracted_data``, or the machine zero-UUID ``extracted_by`` marker
on the item). Everything else is MANUAL.

Deliberate limitation (documented, not solved here): mixed/corrected automatic
work (a human correcting an automatically extracted value, or changing a
mapping/factor) is not distinguishable by P1 and remains a future provenance
concern. The predicate is fail-closed: any item it cannot positively recognise
as automatic is treated as MANUAL and must pass CT-QC.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException

#: The machine/system extractor marker stamped by the automatic worker
#: (``services.automatic_processing._SYSTEM_ACTOR`` /
#: ``api.audit_helpers.MACHINE_EXTRACTOR``).
MACHINE_EXTRACTOR = "00000000-0000-0000-0000-000000000000"

#: Item statuses that already represent a completed CarbonTally CT-QC pass (or
#: the canonical post-CT-QC customer hand-off derived from it).
CT_QC_SATISFIED_STATUSES: tuple[str, ...] = ("ct_qc_approved", "customer_review")


async def item_is_automatic(repos: Any, item: Any) -> bool:
    """P1 containment: True only for durably automatic-processed work.

    Requires (a) a durable automatic-processing job for the item and (b) machine
    production evidence. A freshly-attached / pending job with no machine output
    is NOT automatic (closes the "attach a job to fake automatic" window), and a
    failed automatic run that a human completed manually stays MANUAL.
    """
    getter = getattr(getattr(repos, "processing", None), "get_by_item", None)
    if getter is None:
        return False
    job = await getter(str(getattr(item, "id", "") or ""))
    if job is None:
        return False
    if getattr(job, "automation_extracted_data", None) is not None:
        return True
    return str(getattr(item, "extracted_by", "") or "") == MACHINE_EXTRACTOR


async def ensure_manual_ct_qc_prerequisite(
    repos: Any, item: Any, *, action: str
) -> None:
    """Deny a customer-facing action for MANUAL work that has not passed CT-QC.

    Automatic work (P1 predicate) and work already at ``ct_qc_approved`` /
    ``customer_review`` proceed unchanged. Raises 403 before any mutation or
    billing side effect.
    """
    if await item_is_automatic(repos, item):
        return
    if (getattr(item, "status", None) or "") in CT_QC_SATISFIED_STATUSES:
        return
    raise HTTPException(
        status_code=403,
        detail=(
            "CarbonTally QC (ct_qc_approved) is required before "
            f"{action} for manually processed work"
        ),
    )
