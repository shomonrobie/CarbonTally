// frontend/src/v3/__tests__/useClientTablePage.test.js
// BL-2 — client-side pagination state shared by the customer operational
// tables (documents, processing, reports). Pure hook tests: slicing, page
// clamping when the row set shrinks, and page-size reset.
import { renderHook, act } from '@testing-library/react';
import { useClientTablePage } from '../components/ui/hooks';

const makeRows = (n) => Array.from({ length: n }, (_, i) => ({ id: `r${i}`, n: i }));

describe('useClientTablePage (BL-2)', () => {
  test('slices the first page with the default limit', () => {
    const { result } = renderHook(() => useClientTablePage(makeRows(25), 10));
    expect(result.current.total).toBe(25);
    expect(result.current.page).toBe(0);
    expect(result.current.pageCount).toBe(3);
    expect(result.current.pageRows).toHaveLength(10);
    expect(result.current.pageRows[0].n).toBe(0);
  });

  test('paginates forward and backward', () => {
    const { result } = renderHook(() => useClientTablePage(makeRows(25), 10));
    act(() => result.current.onPage(1));
    expect(result.current.page).toBe(1);
    expect(result.current.pageRows[0].n).toBe(10);
    act(() => result.current.onPage(0));
    expect(result.current.page).toBe(0);
    expect(result.current.pageRows[0].n).toBe(0);
  });

  test('clamps the page when the row set shrinks', () => {
    const { result, rerender } = renderHook(
      ({ rows }) => useClientTablePage(rows, 10),
      { initialProps: { rows: makeRows(25) } },
    );
    act(() => result.current.onPage(2));
    expect(result.current.page).toBe(2);
    rerender({ rows: makeRows(5) });
    expect(result.current.total).toBe(5);
    expect(result.current.pageCount).toBe(1);
    expect(result.current.page).toBe(0);
  });

  test('page-size change resets to page 0 and shows everything', () => {
    const { result } = renderHook(() => useClientTablePage(makeRows(25), 10));
    act(() => result.current.onPage(1));
    act(() => result.current.onLimitChange(25));
    expect(result.current.limit).toBe(25);
    expect(result.current.page).toBe(0);
    expect(result.current.pageRows).toHaveLength(25);
  });

  test('ignores out-of-range page targets', () => {
    const { result } = renderHook(() => useClientTablePage(makeRows(12), 10));
    act(() => result.current.onPage(99));
    expect(result.current.page).toBe(1);
    act(() => result.current.onPage(-5));
    expect(result.current.page).toBe(0);
  });

  test('empty rows yield a single empty page', () => {
    const { result } = renderHook(() => useClientTablePage([], 10));
    expect(result.current.total).toBe(0);
    expect(result.current.pageRows).toEqual([]);
    expect(result.current.pageCount).toBe(1);
  });
});
