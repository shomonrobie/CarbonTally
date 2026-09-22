// frontend/src/v3/insight/references.js
// CarbonTally Insight I6 — reference presentation and resolution (presentation
// only; no contract change).
//
// PO decision I6-4 / AGENTS.md §3.3: a reference is a **locator**, never an
// authorization grant. Having an id in the UI grants nothing; resolution always
// goes back through the backend, which re-checks the caller's scope against the
// resolved object. No client-side authorization logic exists here.
//
// The four ratified reference kinds are the I3 contract's
// (`backend/domain/insight_tool.py` → `REFERENCE_KINDS`):
//
//   report · report_version · evidence_line_item · calculation_snapshot
//
// Resolution uses the **ratified I3 read-only tool surface** — the only
// authorized by-identifier path that exists. No new API is created for I6.

export const REFERENCE_KIND_LABELS = {
  report: 'Report',
  report_version: 'Report version',
  evidence_line_item: 'Evidence line item',
  calculation_snapshot: 'Calculation snapshot',
};

/**
 * The identifier → ratified-tool mapping used for resolution.
 *
 * `evidence_line_item` is deliberately **absent**: the four closed I3 tools
 * accept a report id, a report-version id, a report-version id (evidence
 * lookup) and a calculation-snapshot id — none accepts an evidence line-item
 * id. Rather than invent an identifier route (which would require a new tool,
 * i.e. a PO decision), that kind is unresolvable and the UI shows the locator
 * with a non-disclosing state.
 */
const IDENTIFIER_TOOL = {
  report: (id) => ({ tool: 'report_lookup', input: { report_id: id } }),
  report_version: (id) => ({ tool: 'report_version_lookup', input: { version_id: id } }),
  calculation_snapshot: (id) => ({ tool: 'calculation_snapshot_lookup', input: { snapshot_id: id } }),
};

export function referenceKindLabel(kind) {
  if (REFERENCE_KIND_LABELS[kind]) return REFERENCE_KIND_LABELS[kind];
  return 'Reference';
}

/** The tool invocation for a reference, or `null` when it cannot be resolved. */
export function referenceResolver(kind, id) {
  const builder = IDENTIFIER_TOOL[kind];
  if (!builder || !id) return null;
  return builder(id);
}

/** The stable short form of a reference identifier for display. */
export function shortReferenceId(id, head = 10) {
  const value = typeof id === 'string' ? id : '';
  if (!value) return '';
  if (value.length <= head) return value;
  return `${value.slice(0, head)}…`;
}

/** The accessible label for one reference locator. */
export function referenceLabel(reference) {
  const kind = reference && reference.kind;
  const id = reference && reference.id;
  return `${referenceKindLabel(kind)} ${id || ''}`.trim();
}

// ---------------------------------------------------------------------------
// Non-disclosing states (I6-4 / I6-7 / PO §9)
//
// A single message is used for every failure mode — an unresolvable kind, a
// non-success tool status, and a thrown request error. It states neither that
// the resource exists nor that it does not, so the UI cannot leak protected
// resource existence in either direction.
// ---------------------------------------------------------------------------

export const REFERENCE_UNAVAILABLE = {
  tone: 'muted',
  title: "Can't be opened here",
  body:
    "CarbonTally can't open this reference for you. A reference is a locator — it identifies something, it does not grant access to it, and opening it is authorized again on every request.",
};

export const REFERENCE_UNRESOLVABLE = {
  tone: 'muted',
  title: "Can't be opened from Insight",
  body:
    'This reference type has no by-identifier lookup available from Insight. It is shown as a provenance locator only.',
};

/** How a resolution outcome should be presented (never discloses existence). */
export function resolutionPresentation(result) {
  if (result && result.status === 'success') return null;
  return REFERENCE_UNAVAILABLE;
}

// ---------------------------------------------------------------------------
// Resolved-evidence projection (presentation of an allowlisted tool result)
// ---------------------------------------------------------------------------

// Business labels for fields the backend already allows through. Unknown keys
// fall back to a de-underscored form — nothing is added or inferred here.
const EVIDENCE_FIELD_LABELS = {
  id: 'Identifier',
  organization_id: 'Organisation',
  report_id: 'Report',
  report_type: 'Report type',
  report_name: 'Report name',
  reporting_year: 'Reporting year',
  status: 'Status',
  version_number: 'Version',
  is_current: 'Current version',
  is_approved_or_final: 'Approved or final',
  created_at: 'Created',
  completed_at: 'Completed',
  report_organization_id: 'Organisation',
  activity: 'Activity',
  activity_type: 'Activity type',
  quantity: 'Quantity',
  quantity_unit: 'Unit',
  co2e_multiplier: 'Factor value',
  co2e_kg: 'Emissions (kg CO2e)',
  scope: 'Scope',
  date: 'Date',
  methodology: 'Methodology',
  algorithm_version: 'Algorithm version',
  content_hash: 'Content hash',
  factor_id: 'Factor',
  factor_kind: 'Factor kind',
  customer_factor_id: 'Customer factor',
  factor_source: 'Factor source',
  source_item_id: 'Source item',
  source_line_item_id: 'Source line item',
  disclosure_value_id: 'Disclosure value',
  requirement_version_id: 'Requirement version',
  calculation_snapshot_id: 'Calculation snapshot',
  evidence_line_item_id: 'Evidence line item',
  line_number: 'Line',
  materialisation_kind: 'Materialisation',
};

/** Human label for an allowlisted evidence field (fallback: de-underscored). */
export function evidenceFieldLabel(key) {
  if (EVIDENCE_FIELD_LABELS[key]) return EVIDENCE_FIELD_LABELS[key];
  return String(key).replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());
}

const isScalar = (value) => (
  value === null || value === undefined
  || ['string', 'number', 'boolean'].includes(typeof value)
);

const formatScalar = (value) => {
  if (value === true) return 'Yes';
  if (value === false) return 'No';
  return String(value);
};

/**
 * Project an allowlisted tool-result `data` payload into display rows.
 *
 * Scalars become `{label, value}` rows; collections become `{label, count}`
 * summaries so a bounded list never renders as an unreadable wall.
 */
export function projectEvidenceRows(data) {
  if (!data || typeof data !== 'object') return { rows: [], collections: [] };
  const rows = [];
  const collections = [];
  Object.keys(data).forEach((key) => {
    const value = data[key];
    if (value === null || value === undefined) return;
    if (Array.isArray(value)) {
      collections.push({ key, label: evidenceFieldLabel(key), count: value.length });
      return;
    }
    if (isScalar(value)) {
      rows.push({ key, label: evidenceFieldLabel(key), value: formatScalar(value) });
      return;
    }
    if (typeof value === 'object') {
      const label = evidenceFieldLabel(key);
      const parts = [value.id, value.status].filter((part) => part !== undefined && part !== null);
      if (parts.length) collections.push({ key, label, count: 1, detail: parts.join(' · ') });
    }
  });
  return { rows, collections };
}

