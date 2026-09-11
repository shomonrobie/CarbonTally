// frontend/src/v3/components/ui/DataTable.jsx
// D21.7 — accessible data table primitive: caption, scope'd headers, compact
// mode, scroll wrapper, server-style pagination and optional client sorting
// (CL-58 shared table contract). The component is deliberately "honest": no
// fake totals. `clientPaginate` (BL-2) slices a fully-loaded, bounded
// per-organisation list in memory and always reports the real row count.
import React, { useEffect, useMemo, useState } from 'react';
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
  // BL-2 — client pagination for bounded, fully-loaded per-org lists. Sorting
  // applies to the full `rows` set before slicing, so page + sort stay coherent.
  clientPaginate = false,
  defaultPageSize = 10,
  resetKey,
  // BL-4 — server-side sorting: when `onSortChange` is provided, sorting is
  // delegated to the parent (rows are already server-ordered) and the table
  // becomes a controlled sort header via optional `sortKey`/`sortDir` props.
  onSortChange,
  sortKey: sortKeyProp,
  sortDir: sortDirProp,
}) {
  const [localSortKey, setLocalSortKey] = useState(null);
  const [localSortDir, setLocalSortDir] = useState('asc');
  const sortKey = sortKeyProp !== undefined ? sortKeyProp : localSortKey;
  const sortDir = sortDirProp !== undefined ? sortDirProp : localSortDir;

  const sortedRows = useMemo(() => {
    if (onSortChange || !sortKey) return rows;
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
  }, [rows, sortKey, sortDir, columns, onSortChange]);

  // BL-2 — client pagination state for bounded, fully-loaded per-org lists.
  const [page, setPage] = useState(0);
  const [pageLimit, setPageLimit] = useState(defaultPageSize);
  const clientTotal = clientPaginate && Array.isArray(rows) ? rows.length : 0;
  const clientPageCount = clientPaginate
    ? Math.max(1, Math.ceil(clientTotal / Math.max(1, pageLimit)))
    : 1;

  useEffect(() => {
    if (!clientPaginate) return;
    setPage((current) => Math.min(current, clientPageCount - 1));
  }, [clientPageCount, clientPaginate]);

  useEffect(() => {
    if (clientPaginate && resetKey !== undefined) setPage(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey]);

  const safePage = Math.min(page, clientPageCount - 1);
  const pageRows = clientPaginate
    ? sortedRows.slice(safePage * pageLimit, (safePage + 1) * pageLimit)
    : sortedRows;

  if (!columns || columns.length === 0) return null;

  const onSortToggle = (col) => {
    const key = col.key || col.accessor;
    if (onSortChange) {
      const nextDir = sortKey === key ? (sortDir === 'asc' ? 'desc' : 'asc') : 'asc';
      onSortChange({ key, direction: nextDir });
      return;
    }
    if (localSortKey !== key) {
      setLocalSortKey(key);
      setLocalSortDir('asc');
    } else {
      setLocalSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    }
  };

  const effectiveTotal = clientPaginate ? clientTotal : total;
  const effectiveLimit = clientPaginate ? pageLimit : limit;
  const effectiveOffset = clientPaginate ? safePage * pageLimit : offset;
  const effectiveOnPage = clientPaginate
    ? (nextOffset, nextLimit) => {
        if (typeof nextLimit === 'number' && nextLimit !== pageLimit) {
          setPageLimit(nextLimit);
          setPage(0);
        } else {
          setPage(Math.floor(nextOffset / pageLimit));
        }
      }
    : onPage;

  const hasPagination = typeof effectiveOnPage === 'function' && typeof effectiveTotal === 'number';
  const pageIndex = effectiveLimit > 0 ? Math.floor(effectiveOffset / effectiveLimit) + 1 : 1;
  const pageCount = effectiveLimit > 0 ? Math.max(1, Math.ceil(effectiveTotal / effectiveLimit)) : 1;
  const first = effectiveTotal === 0 ? 0 : effectiveOffset + 1;
  const last = Math.min(effectiveTotal, effectiveOffset + (clientPaginate ? pageRows.length : sortedRows.length));

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
          {pageRows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>{emptyLabel}</td>
            </tr>
          ) : (
            pageRows.map((row, i) => (
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
            {effectiveTotal === 0 ? '0 rows' : `${first}–${last} of ${effectiveTotal}`}
          </span>
          <button
            type="button"
            className="v3-btn v3-btn-sm"
            disabled={pageIndex <= 1}
            onClick={() => effectiveOnPage(effectiveOffset - effectiveLimit, effectiveLimit)}
          >
            ← Prev
          </button>
          <span className="ct-table-pagination-count">Page {pageIndex} of {pageCount}</span>
          <button
            type="button"
            className="v3-btn v3-btn-sm"
            disabled={pageIndex >= pageCount}
            onClick={() => effectiveOnPage(effectiveOffset + effectiveLimit, effectiveLimit)}
          >
            Next →
          </button>
          <select
            className="ct-table-pagination-select"
            aria-label="Rows per page"
            value={effectiveLimit}
            onChange={(e) => effectiveOnPage(0, Number(e.target.value))}
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

