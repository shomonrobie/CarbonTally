// frontend/src/v3/evidence/evidenceLocation.js
// Shared Source Evidence Viewer — authoritative location presentation and the
// single evidence handoff used by every caller (customer evidence tracing,
// reports/disclosure, CarbonTally Insight).
//
// PO architecture (2026-09-22): "Insight explains; the evidence system proves."
// A reference is a LOCATOR, never an authorization grant: this module only builds
// a route to the shared viewer, which re-authorizes the caller on every read. No
// page, row, sheet or document is ever inferred or guessed here — the location
// block comes from the backend, which is the only authority on it.

export const LOCATION_VIEW = {
  /** An authoritative page / sheet+row / row exists. */
  EXACT: 'exact',
  /** No authoritative location exists for this line. */
  UNAVAILABLE: 'unavailable',
  /** A location exists but is a document reference withheld below FULL depth. */
  RESTRICTED: 'restricted',
};

export const LOCATION_VIEW_LABELS = {
  [LOCATION_VIEW.EXACT]: 'Exact location',
  [LOCATION_VIEW.UNAVAILABLE]: 'Location unavailable',
  [LOCATION_VIEW.RESTRICTED]: 'Location restricted',
};

/**
 * Map the server's location block to one of the three honest presentation states.
 * Nothing is derived from an ordinal: `line_number` is NEVER treated as a page or
 * a physical file row.
 */
export function locationView(location) {
  if (!location) {
    return {
      state: LOCATION_VIEW.UNAVAILABLE,
      label: LOCATION_VIEW_LABELS[LOCATION_VIEW.UNAVAILABLE],
      detail: 'CarbonTally has no source location recorded for this line.',
      exact: false,
    };
  }
  if (location.state === 'restricted') {
    return {
      state: LOCATION_VIEW.RESTRICTED,
      label: LOCATION_VIEW_LABELS[LOCATION_VIEW.RESTRICTED],
      detail:
        location.display ||
        'Exact source location is not available for your access level.',
      exact: false,
    };
  }
  if (location.kind === 'unavailable' || !location.kind) {
    return {
      state: LOCATION_VIEW.UNAVAILABLE,
      label: LOCATION_VIEW_LABELS[LOCATION_VIEW.UNAVAILABLE],
      detail: location.display || 'Exact source location is not available for this line.',
      exact: false,
    };
  }
  return {
    state: LOCATION_VIEW.EXACT,
    label:
      location.kind === 'page'
        ? `Source page ${location.page}`
        : location.kind === 'sheet_row'
          ? `Sheet ${location.sheet} · row ${location.row}`
          : location.kind === 'row'
            ? `Source row ${location.row}`
            : `Source reference ${location.row_reference}`,
    detail: location.display || '',
    exact: true,
  };
}

/** Whether the backend established an authoritative location for this line. */
export function hasExactLocation(location) {
  return locationView(location).state === LOCATION_VIEW.EXACT;
}

/**
 * Display rows for the location block (server values only; empty when withheld).
 */
export function locationRows(location) {
  const rows = [];
  if (!location || location.state === 'restricted') return rows;
  if (location.kind !== 'unavailable') {
    if (location.page != null) rows.push({ label: 'Source page', value: `${location.page}` });
    if (location.sheet) rows.push({ label: 'Worksheet', value: location.sheet });
    if (location.row != null) rows.push({ label: 'Source row', value: `${location.row}` });
    if (location.row_reference) {
      rows.push({ label: 'Source reference', value: location.row_reference });
    }
  }
  if (location.line_number != null) {
    rows.push({ label: 'Evidence line', value: `Line ${location.line_number}` });
  }
  return rows;
}

/** The shared Source Evidence Viewer route for one evidence line. */
export function evidenceViewerPath(lineItemId, { from } = {}) {
  if (!lineItemId) return null;
  const base = `/evidence/line-items/${encodeURIComponent(lineItemId)}`;
  return from ? `${base}?from=${encodeURIComponent(from)}` : base;
}

/**
 * The handoff path for an I6/I3 provenance reference, or `null` when there is no
 * authoritative evidence line to hand off.
 *
 * `evidence_line_item` references are addressable by the shared viewer; a
 * resolved `calculation_snapshot` carries the line it was calculated from. Any
 * other reference (or an unresolved one) has no handoff — the caller keeps its
 * existing truthful answer state instead of guessing.
 */
export function evidenceViewerPathForReference(kind, id, resolvedData = null) {
  if (!id) return null;
  if (kind === 'evidence_line_item') return evidenceViewerPath(id);
  const lineId =
    resolvedData && typeof resolvedData.source_line_item_id === 'string'
      ? resolvedData.source_line_item_id
      : null;
  return lineId ? evidenceViewerPath(lineId) : null;
}
