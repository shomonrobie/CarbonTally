// frontend/src/v3/components/ui/DataTable.jsx
// D21.7 — accessible data table primitive: caption, scope'd headers, compact
// mode and a scroll wrapper (no horizontal overflow on narrow viewports).
import React from 'react';
import './ui.css';

export default function DataTable({ columns, rows, caption, emptyLabel = 'No rows to display.', compact = false, rowKey = 'id', onRowClick }) {
  if (!columns || columns.length === 0) return null;

  return (
    <div className="ct-table-wrap">
      <table className={`ct-table${compact ? ' ct-table--compact' : ''}`}>
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key || col.accessor} scope="col">{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>{emptyLabel}</td>
            </tr>
          ) : (
            rows.map((row, i) => (
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
    </div>
  );
}
