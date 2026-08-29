// frontend/src/v3/components/ui/DataTable.jsx
// D21.7 — accessible data table primitive: caption, scope'd headers, compact
// mode, scroll wrapper, server-style pagination and optional client sorting
// (CL-58 shared table contract). The component is deliberately "honest": no
// fake totals, no client-side pagination of an over-broad result set.
import React, { useMemo, useState } from 'react';
import './ui.css';

const PAGE_SIZES = [10, 25, 50, 100];

export default function DataTable({
  columns,
  rows,
  caption,
  emptyLabel = 'No rows to display.',
  compact = false,
  rowKey = 'id',
  onRowClick,
  // CL-58 — server-side pagination contract: `total` is the authoritative row
  // count, `limit`/`offset` are the current page window. When `onPage` is given
  // the table renders Prev/Next + page-size controls; otherwise it is a simple
  // read-only list.
  total,
  limit = 25,
  offset = 0,
  onPage,
  pageSizeOptions = PAGE_SIZES,
}) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    const col = (columns || []).find((c) => (c.key || c.accessor) === sortKey);
    if (!col || !col.sortValue) return rows;
    const dir = sortDir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = col.sortValue(a);
      const bv = col.sortValue(b);
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
      return String(av).localeCompare(String(bv)) * dir;
    });
  }, [rows, sortKey, sortDir, columns]);

  if (!columns || columns.length === 0) return null;

  const onSortToggle = (col) => {
    const key = col.key || col.accessor;
    if (sortKey !== key) {
      setSortKey(key);
      setSortDir('asc');
    } else {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    }
  };

  const hasPagination = typeof onPage === 'function' && typeof total === 'number';
  const pageIndex = limit > 0 ? Math.floor(offset / limit) + 1 : 1;
  const pageCount = limit > 0 ? Math.max(1, Math.ceil(total / limit)) : 1;
  const first = total === 0 ? 0 : offset + 1;
  const last = Math.min(total, offset + (sortedRows.length || limit));

  return (
    <div className="ct-table-wrap">
      <table className={`ct-table${compact ? ' ct-table--compact' : ''}`}>
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map((col) => {
              const key = col.key || col.accessor;
              const active = sortKey === key;
              return (
                <th key={key} scope="col">
                  {col.sortable ? (
                    <button
                      type="button"
                      className="ct-table-sort"
                      onClick={() => onSortToggle(col)}
                      aria-sort={active ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                    >
                      {col.header}
                      {active ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ' ⇅'}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sortedRows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>{emptyLabel}</td>
            </tr>
          ) : (
            sortedRows.map((row, i) => (
              <tr
                key={row[rowKey] ?? i}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                style={onRowClick ? { cursor: 'pointer' } : undefined}
              >
                {columns.map((col) => (
                  <td key={col.key || col.accessor} scope={col.isHeader ? 'row' : undefined}>
                    {col.render ? col.render(row) : row[col.accessor]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {hasPagination && pageCount > 1 && (
        <div className="ct-table-pagination">
          <span className="ct-table-pagination-count">
            {total === 0 ? '0 rows' : `${first}–${last} of ${total}`}
          </span>
          <button
            type="button"
            className="v3-btn v3-btn-sm"
            disabled={pageIndex <= 1}
            onClick={() => onPage(offset - limit, limit)}
          >
            ← Prev
          </button>
          <span className="ct-table-pagination-count">Page {pageIndex} of {pageCount}</span>
          <button
            type="button"
            className="v3-btn v3-btn-sm"
            disabled={pageIndex >= pageCount}
            onClick={() => onPage(offset + limit, limit)}
          >
            Next →
          </button>
          <select
            className="ct-table-pagination-select"
            aria-label="Rows per page"
            value={limit}
            onChange={(e) => onPage(0, Number(e.target.value))}
          >
            {pageSizeOptions.map((s) => (
              <option key={s} value={s}>{s} / page</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

