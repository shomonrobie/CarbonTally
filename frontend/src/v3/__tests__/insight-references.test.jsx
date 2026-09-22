// frontend/src/v3/__tests__/insight-references.test.jsx
// I6 — evidence/provenance reference presentation (PO I6-4).
//
// References are locators, never authorization grants:
//   * the UI performs no access decision and holds no reference→access mapping;
//   * resolution always goes back to the backend (the ratified I3 read-only tool
//     surface), which re-authorizes the caller against the resolved object;
//   * every non-success outcome — unauthorized, absent, invalid, failed, or a
//     thrown 404 — renders ONE non-disclosing state that says nothing about
//     whether the protected resource exists.
import React from 'react';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

jest.mock('../api', () => ({ invokeInsightTool: jest.fn() }));

import InsightReferences from '../insight/InsightReferences';
import {
  REFERENCE_KIND_LABELS,
  REFERENCE_UNAVAILABLE,
  projectEvidenceRows,
  referenceKindLabel,
  referenceLabel,
  referenceResolver,
  shortReferenceId,
} from '../insight/references';

const api = jest.requireMock('../api');

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(cleanup);

describe('I3 reference kernel (I6-4)', () => {
  test('only the four ratified reference kinds are labelled', () => {
    expect(Object.keys(REFERENCE_KIND_LABELS).sort()).toEqual([
      'calculation_snapshot',
      'evidence_line_item',
      'report',
      'report_version',
    ]);
  });

  test('resolvable kinds map onto the ratified by-identifier tools', () => {
    expect(referenceResolver('report', 'r-1')).toEqual({
      tool: 'report_lookup',
      input: { report_id: 'r-1' },
    });
    expect(referenceResolver('report_version', 'v-1')).toEqual({
      tool: 'report_version_lookup',
      input: { version_id: 'v-1' },
    });
    expect(referenceResolver('calculation_snapshot', 's-1')).toEqual({
      tool: 'calculation_snapshot_lookup',
      input: { snapshot_id: 's-1' },
    });
  });

  test('evidence_line_item has no ratified by-identifier lookup and is not guessed', () => {
    expect(referenceResolver('evidence_line_item', 'e-1')).toBeNull();
    expect(referenceResolver('report', 'r-1')).not.toBeNull();
  });

  test('an unratified or incomplete reference resolves to nothing', () => {
    expect(referenceResolver('mystery_kind', 'x')).toBeNull();
    expect(referenceResolver('report', '')).toBeNull();
  });

  test('labels and identifiers are presented safely', () => {
    expect(referenceKindLabel('report')).toBe('Report');
    expect(referenceKindLabel('mystery_kind')).toBe('Reference');
    expect(shortReferenceId('abcdefghijklmnop')).toBe('abcdefghij…');
    expect(shortReferenceId('abc')).toBe('abc');
    expect(referenceLabel({ kind: 'report', id: 'r-1' })).toBe('Report r-1');
  });

  test('the allowlisted projection separates scalars from collections', () => {
    const { rows, collections } = projectEvidenceRows({
      report_name: '2025 SECR report',
      reporting_year: 2025,
      is_approved_or_final: true,
      versions: [{ id: 'v1' }, { id: 'v2' }],
      ignored: null,
    });
    expect(rows).toEqual([
      { key: 'report_name', label: 'Report name', value: '2025 SECR report' },
      { key: 'reporting_year', label: 'Reporting year', value: '2025' },
      { key: 'is_approved_or_final', label: 'Approved or final', value: 'Yes' },
    ]);
    expect(collections).toEqual([{ key: 'versions', label: 'Versions', count: 2 }]);
  });
});

describe('InsightReferences renders locators', () => {
  test('nothing is rendered when there are no references', () => {
    const { container } = render(<InsightReferences references={[]} organizationId="org-1" />);
    expect(container).toBeEmptyDOMElement();
  });

  test('references are shown as locators and never as access', () => {
    render(
      <InsightReferences
        references={[{ kind: 'report', id: 'report-abc123456789' }]}
        organizationId="org-1"
      />,
    );

    expect(screen.getByText('Report')).toBeInTheDocument();
    expect(screen.getByText('report-abc…')).toBeInTheDocument();
    expect(screen.getByText(/locators, not access/i)).toBeInTheDocument();
    // No data of the referenced resource is on screen before resolution.
    expect(screen.queryByTestId('insight-reference-resolved')).not.toBeInTheDocument();
  });

  test('an unresolvable kind is offered no client-side route at all', () => {
    render(
      <InsightReferences
        references={[{ kind: 'evidence_line_item', id: 'line-1' }]}
        organizationId="org-1"
      />,
    );

    expect(screen.queryByRole('button', { name: /open/i })).not.toBeInTheDocument();
    expect(screen.getByTestId('insight-reference-unresolvable')).toBeInTheDocument();
    expect(api.invokeInsightTool).not.toHaveBeenCalled();
  });
});

describe('reference resolution always goes through the backend', () => {
  test('a successful resolution renders the allowlisted projection only', async () => {
    api.invokeInsightTool.mockResolvedValue({
      tool: 'report_lookup',
      status: 'success',
      contract_version: 'i3-6point-v1',
      data: {
        report_name: '2025 SECR report',
        reporting_year: 2025,
        versions: [{ id: 'v1' }],
      },
      references: [],
      reason: null,
      truncated: false,
    });

    render(
      <InsightReferences
        references={[{ kind: 'report', id: 'report-1' }]}
        organizationId="org-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Open Report report-1' }));

    await waitFor(() => expect(api.invokeInsightTool).toHaveBeenCalledTimes(1));
    expect(api.invokeInsightTool).toHaveBeenCalledWith('org-1', 'report_lookup', {
      report_id: 'report-1',
    });

    const resolved = await screen.findByTestId('insight-reference-resolved');
    expect(resolved).toHaveTextContent('2025 SECR report');
    expect(resolved).toHaveTextContent('Reporting year');
    expect(resolved).toHaveTextContent('Versions: 1');
  });

  test('a saved id alone grants nothing: resolution re-reads through the backend every time', async () => {
    api.invokeInsightTool.mockResolvedValue({ status: 'success', data: { id: 'report-1' } });

    render(
      <InsightReferences
        references={[{ kind: 'report', id: 'report-1' }]}
        organizationId="org-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Open Report report-1' }));
    await screen.findByTestId('insight-reference-resolved');
    expect(api.invokeInsightTool).toHaveBeenCalledTimes(1);

    // Re-opening after a success still asks the backend again (no cached grant).
    fireEvent.click(screen.getByRole('button', { name: 'Open Report report-1' }));
    await waitFor(() => expect(api.invokeInsightTool).toHaveBeenCalledTimes(2));
  });

  test.each(['not_authorized', 'no_data', 'invalid_input', 'error', 'provider_unavailable'])(
    'a %s outcome is non-disclosing',
    async (status) => {
      api.invokeInsightTool.mockResolvedValue({ tool: 'report_lookup', status, data: {} });

      render(
        <InsightReferences
          references={[{ kind: 'report', id: 'report-1' }]}
          organizationId="org-1"
        />,
      );

      fireEvent.click(screen.getByRole('button', { name: 'Open Report report-1' }));

      const unavailable = await screen.findByTestId('insight-reference-unavailable');
      expect(unavailable).toHaveTextContent(REFERENCE_UNAVAILABLE.body);
      // Says neither that the resource exists nor that it does not.
      expect(unavailable.textContent).not.toMatch(/not found|does not exist|no such|denied|forbidden|permission/i);
      expect(screen.queryByTestId('insight-reference-resolved')).not.toBeInTheDocument();
    },
  );

  test('a thrown 404 for a foreign resource is non-disclosing', async () => {
    const notFound = new Error('Reference not found.');
    notFound.status = 404;
    api.invokeInsightTool.mockRejectedValue(notFound);

    render(
      <InsightReferences
        references={[{ kind: 'calculation_snapshot', id: 'snapshot-9' }]}
        organizationId="org-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Open Calculation snapshot snapshot-9' }));

    const unavailable = await screen.findByTestId('insight-reference-unavailable');
    expect(unavailable).toHaveTextContent(REFERENCE_UNAVAILABLE.body);
    // The backend's own 404 wording is not echoed to the user.
    expect(unavailable.textContent).not.toContain('Reference not found.');
  });

  test('a network failure is non-disclosing and does not claim a result', async () => {
    api.invokeInsightTool.mockRejectedValue(new Error('Network error — please check your connection.'));

    render(
      <InsightReferences
        references={[{ kind: 'report_version', id: 'version-3' }]}
        organizationId="org-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Open Report version version-3' }));

    const unavailable = await screen.findByTestId('insight-reference-unavailable');
    expect(unavailable).toHaveTextContent(REFERENCE_UNAVAILABLE.body);
    expect(screen.queryByTestId('insight-reference-resolved')).not.toBeInTheDocument();
  });
});

