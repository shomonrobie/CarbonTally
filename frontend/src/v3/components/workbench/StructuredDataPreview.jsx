// frontend/src/v3/components/workbench/StructuredDataPreview.jsx
// Step 2C / POD-3 — structured-data preview for CSV/TSV/XLSX source documents.
//
// The workbench viewer used to refuse non-PDF/image files ("Document preview is
// not available for this file type") — the PO-visible symptom that a CSV/Excel
// uploads but the left-side pane shows nothing useful. This preview is
// read-only and bounded (CSV/TSV → table; XLSX → workbook/sheet-aware). The
// authoritative extraction stays server-side and the security boundary stays the
// backend-issued signed URL; no download control is added.
import React, { useEffect, useState } from 'react';
import * as XLSX from 'xlsx';
import Icon from '../ui/Icon';

//: Bounded preview limits — a large export must not freeze the workbench.
export const MAX_PREVIEW_ROWS = 50;
export const MAX_PREVIEW_COLUMNS = 30;
export const MAX_SHEETS_LISTED = 12;

export function previewKind(title, src) {
  const urlName = String(src || '').split('?')[0].split('#')[0].toLowerCase();
  const name = String(title || urlName).toLowerCase();
  if (/\.(xlsx|xls)$/.test(name)) return 'xlsx';
  if (/\.(csv|tsv)$/.test(name)) return 'csv';
  return 'unknown';
}

/** Minimal RFC4180-ish delimited-text parser (quotes + embedded separators). */
export function parseDelimited(text, separator) {
  const rows = [];
  let row = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') { cell += '"'; i += 1; } else { quoted = false; }
      } else {
        cell += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === separator) {
      row.push(cell); cell = '';
    } else if (ch === '\n') {
      row.push(cell); rows.push(row); row = []; cell = '';
    } else if (ch !== '\r') {
      cell += ch;
    }
  }
  if (cell.length || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.some((c) => String(c).trim() !== ''));
}

function toPreview(matrix) {
  const headers = (matrix[0] || []).slice(0, MAX_PREVIEW_COLUMNS).map((c) => String(c ?? ''));
  const body = matrix.slice(1);
  return {
    headers,
    rows: body.slice(0, MAX_PREVIEW_ROWS).map((r) => r.slice(0, MAX_PREVIEW_COLUMNS)),
    total: body.length,
  };
}

export default function StructuredDataPreview({ src, title }) {
  const kind = previewKind(title, src);
  const [state, setState] = useState({ status: 'loading' });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await fetch(src);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        if (kind === 'xlsx') {
          const workbook = XLSX.read(await response.arrayBuffer(), { type: 'array' });
          const names = (workbook.SheetNames || []).slice(0, MAX_SHEETS_LISTED);
          const first = names[0];
          const matrix = first
            ? XLSX.utils.sheet_to_json(workbook.Sheets[first], { header: 1, blankrows: false })
            : [];
          if (active) setState({ status: 'ready', sheets: names, sheet: first, ...toPreview(matrix) });
          return;
        }
        const separator = /\.tsv(\?|$)/i.test(String(title || src)) ? '\t' : ',';
        const preview = toPreview(parseDelimited(await response.text(), separator));
        if (active) setState({ status: 'ready', ...preview });
      } catch (error) {
        if (active) setState({ status: 'error', message: error.message || 'preview unavailable' });
      }
    })();
    return () => { active = false; };
  }, [kind, src, title]);

  if (state.status === 'loading') {
    return (
      <div className="ct-wb-viewer__empty" data-testid="structured-preview-loading">
        <Icon name="documents" size={20} /> Loading {kind === 'xlsx' ? 'workbook' : 'data'} preview…
      </div>
    );
  }
  if (state.status === 'error') {
    return (
      <div className="ct-wb-viewer__empty" data-testid="structured-preview-error">
        <Icon name="lock" size={20} aria-hidden="true" />
        <span style={{ marginLeft: 8 }}>
          Structured preview is not available for this file ({state.message}). The document is still
          registered and server-side extraction is unaffected.
        </span>
      </div>
    );
  }
  const shown = state.rows?.length ?? 0;
  const total = state.total ?? shown;
  if (!state.headers?.length && !shown) {
    return (
      <div className="ct-wb-viewer__empty" data-testid="structured-preview-empty">
        <Icon name="documents" size={20} /> This {kind === 'xlsx' ? 'workbook' : 'file'} contains no
        previewable rows.
      </div>
    );
  }
  const sheetNote = state.sheets?.length > 1
    ? ` · sheets: ${state.sheets.join(', ')} (showing ${state.sheet})`
    : '';
  return (
    <div className="ct-wb-viewer__data-wrap" data-testid="structured-preview">
      <div className="ct-wb-viewer__data-scroll">
        <table className="ct-wb-viewer__data" data-testid="structured-data-table">
          <caption className="ct-wb-viewer__data-caption">
            {kind === 'xlsx' ? 'Workbook' : 'Data'} preview — showing {shown}
            {total > shown ? ` of ${total}` : ''} row{total === 1 ? '' : 's'}{sheetNote}
          </caption>
          <thead>
            <tr>
              {state.headers.map((h, index) => (
                <th key={`h-${index}`} scope="col">{h || `Column ${index + 1}`}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {state.rows.map((row, rIndex) => (
              <tr key={`r-${rIndex}`}>
                {state.headers.map((_h, cIndex) => (
                  <td key={`c-${rIndex}-${cIndex}`}>{String(row[cIndex] ?? '')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
