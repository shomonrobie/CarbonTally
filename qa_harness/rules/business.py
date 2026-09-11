"""Business rules — the core outcome contract.

Encodes the primary CarbonTally business expectations as regression targets:
the document → emissions → approval → report chain, consultant operability,
PE boundaries, internal capability boundaries and admin gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BusinessRule:
    id: str
    rule: str
    expected: str
    severity: str = "P1"
    historical: str = ""
    po_decision_required: bool = False


def build_business_rules() -> List[BusinessRule]:
    R = BusinessRule
    return [
        R("BUS-1", "A customer document must become an emissions result end-to-end",
          "upload → storage → file record → processing job → ingestion → extraction → "
          "mapping → validation → calculation → evidence → review → approval → completed → "
          "emissions → reporting. Each stage must persist; no UI animation is acceptable evidence.",
          severity="P1", historical="PRC-1/2/3, DOC-2"),
        R("BUS-2", "Calculation must be server-authoritative",
          "The backend matches factors, computes CO₂e and persists the result; the UI never "
          "computes emissions itself.", severity="P1", historical="CAL-1"),
        R("BUS-3", "The UI must be able to complete calculation",
          "A validated item becomes calculated via the workbench (start('calculation') then "
          "calculate) for operator and PE staff.", severity="P1", historical="PRC-1/CL-2"),
        R("BUS-4", "Unit aliases must resolve",
          "Common abbreviations (L, t, kg, kWh, m³) must match canonical factor units "
          "(litres, tonne, kilograms) — a correctly mapped item must not 422 UNIT_MISMATCH.",
          severity="P1", historical="PRC-2/CL-3"),
        R("BUS-5", "Customer review and approval must work",
          "Owner/admin sees calculated items in /review and can approve; rejection requires a "
          "reason; member/viewer 403.", severity="P1", historical="PRC-3/CUS-1/CL-1"),
        R("BUS-6", "A consultant must be able to operate their customers",
          "Consultant can create a customer, manage it, enter the client workspace, upload "
          "documents, drive processing/mapping/validation/calculation, review, report and "
          "message — all scoped to the active client.", severity="P1", historical="CON-1..3/CL-7"),
        R("BUS-7", "Cross-client isolation must hold for consultants",
          "Active-client A must not read/write client B data through the consultant surface.",
          severity="P0", historical="CON-5"),
        R("BUS-8", "PE users must never access prohibited customer source documents",
          "No download path; file_url empty for PE-facing items; org-scoped queues and docs "
          "denied (403 / no path).", severity="P0", historical="D20, SEC-3, PE-1"),
        R("BUS-9", "PE Manager must see entity-assigned work",
          "The PE manager's batch list and entity performance must render assigned work "
          "(not 403 / empty).", severity="P1", historical="PE-2/CL-13"),
        R("BUS-10", "Internal capability boundaries must hold",
          "Reviewer ≠ admin: reviewer cannot run the operator queue or calculate. Staff cannot "
          "do staff-admin actions. Only approved admin/system-admin capabilities may create "
          "users or manage roles.", severity="P1", historical="OPS-2/3, SEC-14/15"),
        R("BUS-11", "System Admin must reach the admin control plane",
          "system-admin can use retention, commercial and audit surfaces (role mapping).",
          severity="P1", historical="OPS-6/CL-8"),
        R("BUS-12", "Authenticated messaging must work",
          "Conversation creation, participants, messages, realtime delivery, unread state and "
          "notifications all function; the visitor-only assistant is NOT the authenticated "
          "messaging mechanism.", severity="P1", historical="MSG-1/CL-6"),
        R("BUS-13", "Evidence chain must be complete",
          "source → extracted lines → mapped factor → calculation snapshot (with source_item_id) "
          "→ emissions log → report. A document must expose the emissions it produced.",
          severity="P1", historical="ISC-1/EVD-1"),
        R("BUS-14", "Reports must be honest",
          "Ready/Queued/Failed statuses render; failed generation surfaces the real error; "
          "reports are generated from real data with lineage.", severity="P2", historical="RPT-1"),
        R("BUS-15", "Notifications must work for every user",
          "The bell uses the API surface and shows real notifications (not a broken legacy "
          "direct-table query).", severity="P2", historical="NOT-1/MSG-4/CL-11"),
        R("BUS-16", "The Documents UI must emphasize business outcome",
          "Documents show emissions outcome and processing state, not merely file size.",
          severity="P3", historical="DOC-3"),
        R("BUS-17", "Custom-factor approval in single-owner orgs",
          "Who approves an owner-created factor when the org has a single owner?",
          severity="P2", historical="CF-1", po_decision_required=True),
    ]


class BusinessRuleCatalog:
    def __init__(self, rules: Optional[List[BusinessRule]] = None) -> None:
        self.rules = rules or build_business_rules()

    def po_decisions(self) -> List[BusinessRule]:
        return [r for r in self.rules if r.po_decision_required]
