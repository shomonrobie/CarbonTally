// frontend/src/v3/__tests__/report-meta-layout.test.jsx
// F-07 (CSS-01) regression guard — CT-STEP2-FINAL-STABILIZATION-012.
//
// The production defect: `reports/reports.css` overrode the SHARED `.v3-meta-*`
// rules with an UNSCOPED grid, while `.v3-meta-item` stayed a ROW flex and the
// inherited label rule (`width: 190px; flex: none`) ate the grid column — long
// values (an organisation name) collapsed to near-zero width and wrapped
// character-by-character. Because the override was unscoped it also leaked into
// every other `.v3-meta-list` surface once a reports page had loaded.
//
// jsdom does not apply external stylesheets, so this test asserts the CSS contract
// itself (the same approach the project uses for source-level invariants).
import fs from 'fs';
import path from 'path';

const v3Css = fs.readFileSync(path.join(__dirname, '..', 'v3.css'), 'utf8');
const reportsCss = fs.readFileSync(
  path.join(__dirname, '..', 'reports', 'reports.css'),
  'utf8',
);

/** Return the declaration block for a selector (first match, no nesting). */
function block(css, selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  return match ? match[1] : null;
}

test('the shared meta layout is a flex, non-collapsing list (unchanged)', () => {
  expect(block(v3Css, '.v3-meta-list')).toMatch(/display:\s*flex/);
  expect(block(v3Css, '.v3-meta-item')).toMatch(/min-width:\s*0/);
  expect(block(v3Css, '.v3-meta-item .v')).toMatch(/min-width:\s*0/);
  expect(block(v3Css, '.v3-meta-item .v')).toMatch(/overflow-wrap:\s*anywhere/);
});

test('reports.css no longer overrides the shared meta rules unscoped', () => {
  // An unscoped `.v3-meta-list {` / `.v3-meta-item .k {` would leak app-wide again.
  expect(reportsCss).not.toMatch(/^\.v3-meta-list\s*\{/m);
  expect(reportsCss).not.toMatch(/^\.v3-meta-item\s+\.k\s*\{/m);
  expect(reportsCss).not.toMatch(/^\.v3-meta-item\s+\.v\s*\{/m);
});

test('the report surface scopes its meta overrides and cannot collapse values', () => {
  const list = block(reportsCss, '.v3-report-page .v3-meta-list');
  expect(list).toMatch(/display:\s*grid/);
  expect(list).toMatch(/minmax\(\s*2\d\dpx/); // usable minimum column width

  const item = block(reportsCss, '.v3-report-page .v3-meta-item');
  expect(item).toMatch(/flex-direction:\s*column/); // label above value
  expect(item).toMatch(/min-width:\s*0/);

  const label = block(reportsCss, '.v3-report-page .v3-meta-item .k');
  expect(label).toMatch(/width:\s*auto/); // no fixed 190px label eating the column
  expect(label).toMatch(/text-transform:\s*uppercase/); // styling intent preserved

  const value = block(reportsCss, '.v3-report-page .v3-meta-item .v');
  expect(value).toMatch(/min-width:\s*0/);
  expect(value).toMatch(/overflow-wrap:\s*anywhere/);
  expect(value).toMatch(/word-break:\s*break-word/);
});

test('no vertical writing mode is used anywhere in the meta rules', () => {
  expect(`${v3Css}${reportsCss}`.includes('writing-mode')).toBe(false);
});
