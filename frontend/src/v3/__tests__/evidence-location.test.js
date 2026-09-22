// frontend/src/v3/__tests__/evidence-location.test.js
// Shared Source Evidence Viewer — location presentation + evidence handoff
// (PO authorization, 2026-09-22).
//
// The backend is the only authority on source location: these helpers map what it
// verified onto labels and build the one shared viewer route. An evidence ordinal
// is never turned into a page or a physical row, and a reference without an
// authoritative evidence line has no handoff at all.
import {
  LOCATION_VIEW,
  evidenceViewerPath,
  evidenceViewerPathForReference,
  hasExactLocation,
  locationRows,
  locationView,
} from '../evidence/evidenceLocation';

describe('authoritative location presentation', () => {
  test('a verified page is an exact location', () => {
    const view = locationView({
      kind: 'page',
      page: 2,
      page_state: 'verified',
      line_number: 3,
      display: 'Source page 2.',
    });
    expect(view.state).toBe(LOCATION_VIEW.EXACT);
    expect(view.label).toBe('Source page 2');
    expect(hasExactLocation({ kind: 'page', page: 2 })).toBe(true);
  });

  test('sheet + row and row-only locations are exact and labelled distinctly', () => {
    expect(locationView({ kind: 'sheet_row', sheet: 'Data', row: 7 }).label).toBe(
      'Sheet Data · row 7',
    );
    expect(locationView({ kind: 'row', row: 5 }).label).toBe('Source row 5');
  });

  test('an unavailable location is never dressed up as exact', () => {
    const view = locationView({ kind: 'unavailable', line_number: 4, display: 'Exact source location is not available for this line.' });
    expect(view.state).toBe(LOCATION_VIEW.UNAVAILABLE);
    expect(view.exact).toBe(false);
    expect(view.label).toMatch(/unavailable/i);
    expect(hasExactLocation({ kind: 'unavailable' })).toBe(false);
  });

  test('a restricted location (below FULL depth) is its own state', () => {
    const view = locationView({ state: 'restricted', display: 'Exact source location is not available for your access level.' });
    expect(view.state).toBe(LOCATION_VIEW.RESTRICTED);
    expect(view.exact).toBe(false);
    expect(view.detail).toMatch(/access level/i);
  });

  test('a missing location block degrades to unavailable', () => {
    expect(locationView(null).state).toBe(LOCATION_VIEW.UNAVAILABLE);
    expect(locationView(undefined).state).toBe(LOCATION_VIEW.UNAVAILABLE);
  });

  test('the ordinal is reported as a line, never as a page or row', () => {
    const rows = locationRows({ kind: 'unavailable', line_number: 4 });
    expect(rows).toEqual([{ label: 'Evidence line', value: 'Line 4' }]);
    expect(rows.some((r) => r.label === 'Source page' || r.label === 'Source row')).toBe(false);
  });

  test('restricted locations disclose no field rows at all', () => {
    expect(locationRows({ state: 'restricted' })).toEqual([]);
  });

  test('exact locations report only the server-supplied values', () => {
    expect(locationRows({ kind: 'sheet_row', sheet: 'Data', row: 7, line_number: 2 })).toEqual([
      { label: 'Worksheet', value: 'Data' },
      { label: 'Source row', value: '7' },
      { label: 'Evidence line', value: 'Line 2' },
    ]);
  });
});

describe('evidence handoff (Insight explains; the evidence system proves)', () => {
  test('an evidence line item is addressable by the shared viewer', () => {
    expect(evidenceViewerPath('line-1')).toBe('/evidence/line-items/line-1');
    expect(evidenceViewerPathForReference('evidence_line_item', 'line-1')).toBe(
      '/evidence/line-items/line-1',
    );
  });

  test('an id is encoded and a return path is carried', () => {
    expect(evidenceViewerPath('line/1', { from: '/emissions' })).toBe(
      '/evidence/line-items/line%2F1?from=%2Femissions',
    );
  });

  test('a resolved snapshot hands off the line it was calculated from', () => {
    expect(
      evidenceViewerPathForReference('calculation_snapshot', 'snap-1', {
        source_line_item_id: 'line-9',
      }),
    ).toBe('/evidence/line-items/line-9');
  });

  test('no handoff is invented when the evidence line is unknown', () => {
    expect(evidenceViewerPathForReference('report', 'r-1')).toBeNull();
    expect(evidenceViewerPathForReference('report_version', 'v-1', {})).toBeNull();
    expect(
      evidenceViewerPathForReference('calculation_snapshot', 'snap-1', { co2e_kg: '1.0' }),
    ).toBeNull();
    expect(evidenceViewerPathForReference('evidence_line_item', '')).toBeNull();
  });
});
