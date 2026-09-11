// frontend/src/v3/__tests__/DataTable.test.jsx
// BL-2/BL-4 — shared DataTable behaviour: client pagination over a bounded
// per-org list, sorting applied to the full set before slicing, page-size
// selection, empty state, and server-side sort delegation (audit console).
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import DataTable from '../components/ui/DataTable';

const columns = [
  {
    key: 'name',
    header: 'Name',
    accessor: 'name',
    sortable: true,
    sortValue: (r) => (r.name || '').toLowerCase(),
    render: (r) => <strong>{r.name}</strong>,
    isHeader: true,
  },
  {
    key: 'value',
    header: 'Value',
    accessor: 'value',
    sortable: true,
    sortValue: (r) => r.value ?? -1,
    render: (r) => r.value,
  },
];

// 25 rows ordered descending by value (row 0 -> value 25, row 24 -> value 1),
// so the first page is NOT sorted until the user clicks a header.
const makeRows = (n) => Array.from(
  { length: n },
  (_, i) => ({ id: `row-${i}`, name: `Item ${String.fromCharCode(90 - (i % 26))}${i}`, value: n - i }),
);

describe('DataTable client pagination (BL-2)', () => {
  test('renders only the current page window with a real total', () => {
    render(<DataTable columns={columns} rows={makeRows(25)} clientPaginate defaultPageSize={10} />);
    // header row + 10 body rows
    expect(screen.getAllByRole('row')).toHaveLength(11);
    expect(screen.getByText('1–10 of 25')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
  });

  test('Next and Prev move between pages', () => {
    render(<DataTable columns={columns} rows={makeRows(25)} clientPaginate defaultPageSize={10} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('11–20 of 25')).toBeInTheDocument();
    expect(screen.getByText('Page 2 of 3')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /prev/i }));
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
  });

  test('changing the page size widens the window', () => {
    render(<DataTable columns={columns} rows={makeRows(25)} clientPaginate defaultPageSize={10} />);
    fireEvent.change(screen.getByLabelText('Rows per page'), { target: { value: '25' } });
    // With a single page the pagination bar hides and every row is shown.
    expect(screen.getAllByRole('row')).toHaveLength(26);
    expect(screen.queryByText('Page 1 of 3')).not.toBeInTheDocument();
  });

  test('sorting applies to the full row set before slicing', () => {
    render(<DataTable columns={columns} rows={makeRows(25)} clientPaginate defaultPageSize={10} />);
    // Initial page contains value 25 down to 16 (unsorted by name).
    fireEvent.click(screen.getByRole('button', { name: /value/i }));
    const firstRow = screen.getAllByRole('row')[1];
    expect(firstRow).toHaveTextContent('Item B24');
    expect(firstRow).toHaveTextContent('1');
  });

  test('empty rows render the empty label', () => {
    render(<DataTable columns={columns} rows={[]} clientPaginate emptyLabel="Nothing here" />);
    expect(screen.getByText('Nothing here')).toBeInTheDocument();
  });

  test('page resets when resetKey changes', () => {
    const { rerender } = render(
      <DataTable columns={columns} rows={makeRows(25)} clientPaginate defaultPageSize={10} resetKey="a" />,
    );
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Page 2 of 3')).toBeInTheDocument();
    rerender(
      <DataTable columns={columns} rows={makeRows(25)} clientPaginate defaultPageSize={10} resetKey="b" />,
    );
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
  });
});

describe('DataTable server-side sort delegation (BL-4)', () => {
  test('calls onSortChange and skips internal re-sorting', () => {
    const onSortChange = jest.fn();
    render(
      <DataTable
        columns={columns}
        rows={makeRows(5)}
        onSortChange={onSortChange}
        sortKey={null}
        sortDir="asc"
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /name/i }));
    expect(onSortChange).toHaveBeenCalledWith({ key: 'name', direction: 'asc' });
    // The server owns ordering: the table must not re-sort client-side.
    expect(screen.getAllByRole('row')[1]).toHaveTextContent('Item Z0');
  });

  test('reflects a controlled sort direction', () => {
    const { rerender } = render(
      <DataTable columns={columns} rows={makeRows(5)} onSortChange={jest.fn()} sortKey="name" sortDir="asc" />,
    );
    const header = screen.getByRole('button', { name: /name/i });
    expect(header).toHaveAttribute('aria-sort', 'ascending');
    fireEvent.click(header);
    rerender(
      <DataTable columns={columns} rows={makeRows(5)} onSortChange={jest.fn()} sortKey="name" sortDir="desc" />,
    );
    expect(screen.getByRole('button', { name: /name/i })).toHaveAttribute('aria-sort', 'descending');
  });
});
