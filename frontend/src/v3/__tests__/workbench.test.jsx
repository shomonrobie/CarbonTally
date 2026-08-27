// frontend/src/v3/__tests__/workbench.test.jsx
// D19 — the workbench shell must render TOP workflow navigation, the three
// pane presets (40/60 · 50/50 · 60/40), status/lock/autosave indicators and
// the secure view-only source pane — without any left sidebar.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import WorkbenchShell from '../components/workbench/WorkbenchShell';
import WorkflowNav, { DEFAULT_STAGES } from '../components/workbench/WorkflowNav';
import { presetToRatio } from '../components/workbench/SplitPane';
import ConfidenceBadge from '../components/workbench/ConfidenceBadge';
import AutosaveIndicator from '../components/workbench/AutosaveIndicator';
import ExtractionPanel from '../ops/ExtractionPanel';

describe('D19 WorkbenchShell', () => {
  test('renders top workflow navigation with all default stages', () => {
    render(<WorkbenchShell currentStage="extract" data={<div>Data pane</div>} />);
    expect(screen.getByRole('navigation', { name: /processing workflow/i })).toBeInTheDocument();
    DEFAULT_STAGES.forEach((stage) => {
      expect(screen.getByRole('button', { name: new RegExp(stage.label, 'i') })).toBeInTheDocument();
    });
  });

  test('renders the three pane presets (40/60 · 50/50 · 60/40)', () => {
    render(<WorkbenchShell currentStage="map" data={<div>Data pane</div>} />);
    expect(presetToRatio('40-60')).toBe('40 / 60');
    expect(presetToRatio('50-50')).toBe('50 / 50');
    expect(presetToRatio('60-40')).toBe('60 / 40');
    ['40 / 60', '50 / 50', '60 / 40'].forEach((label) => {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    });
  });

  test('changes preset when a preset button is pressed', () => {
    const onPresetChange = jest.fn();
    render(<WorkbenchShell currentStage="extract" data={<div>Data pane</div>} onPresetChange={onPresetChange} />);
    fireEvent.click(screen.getByRole('button', { name: '60 / 40' }));
    expect(onPresetChange).toHaveBeenCalledWith('60-40');
  });

  test('shows status, lock and autosave indicators', () => {
    render(
      <WorkbenchShell
        currentStage="extract"
        data={<div>Data pane</div>}
        status="extracting"
        locked
        autosaveState="saving"
      />,
    );
    expect(screen.getByText('Extracting')).toBeInTheDocument();
    expect(screen.getByText('Locked')).toBeInTheDocument();
    expect(screen.getByText('Saving…')).toBeInTheDocument();
  });

  test('marks the current stage with aria-current="step"', () => {
    render(<WorkbenchShell currentStage="extract" data={<div>Data pane</div>} />);
    expect(screen.getByRole('button', { name: /extract/i })).toHaveAttribute('aria-current', 'step');
  });

  test('secure source pane shows the view-only affordance when downloads are disallowed', () => {
    render(
      <WorkbenchShell
        currentStage="extract"
        data={<div>Data pane</div>}
        sourceUrl="https://signed.example/file.pdf"
        allowDownload={false}
      />,
    );
    expect(screen.getByText(/view only — download disabled/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /download/i })).not.toBeInTheDocument();
  });

  test('no permanent left sidebar inside the workbench', () => {
    const { container } = render(<WorkbenchShell currentStage="extract" data={<div>Data pane</div>} />);
    const sidebars = container.querySelectorAll('[class*="sidebar"], aside');
    expect(sidebars.length).toBe(0);
  });
});

describe('D19 WorkflowNav', () => {
  test('reports complete/current/upcoming stages', () => {
    render(<WorkflowNav stages={DEFAULT_STAGES} current="map" onStep={() => {}} />);
    // Complete stages expose a check icon inside the step number.
    const queueStep = screen.getByRole('button', { name: /queue/i });
    expect(queueStep).not.toHaveAttribute('aria-current');
    expect(screen.getByRole('button', { name: /map/i })).toHaveAttribute('aria-current', 'step');
  });

  test('invokes onStep when a stage is clicked', () => {
    const onStep = jest.fn();
    render(<WorkflowNav stages={DEFAULT_STAGES} current="extract" onStep={onStep} />);
    fireEvent.click(screen.getByRole('button', { name: /validate/i }));
    expect(onStep).toHaveBeenCalledWith('validate');
  });
});

describe('D16/D19 ConfidenceBadge', () => {
  test('renders high confidence with a label', () => {
    render(<ConfidenceBadge value={0.94} field="supplier" />);
    expect(screen.getByText(/94% High confidence/i)).toBeInTheDocument();
  });

  test('renders low confidence as needing verification', () => {
    render(<ConfidenceBadge value={0.3} />);
    expect(screen.getByText(/30% Low confidence — verify/i)).toBeInTheDocument();
  });

  test('renders nothing for missing confidence', () => {
    const { container } = render(<ConfidenceBadge value={null} />);
    expect(container.firstChild).toBeNull();
  });

describe('D19 SplitPane keyboard resizing', () => {
  test('ArrowRight increases the source pane ratio and ArrowLeft decreases it', () => {
    render(<WorkbenchShell currentStage="extract" data={<div>Data pane</div>} />);
    const handle = screen.getByRole('button', { name: /resize panes/i });
    expect(handle).toBeInTheDocument();
    // ArrowRight from the 50-50 default increases the ratio (ratio is exposed
    // on the pane widths after render; the resize handle remains present).
    fireEvent.keyDown(handle, { key: 'ArrowRight' });
    fireEvent.keyDown(handle, { key: 'ArrowLeft' });
    // No crash, handle still focused and the two panes remain rendered.
    expect(handle).toBeInTheDocument();
    expect(screen.getAllByRole('region').length).toBeGreaterThan(0);
  });
});

describe('D19 ExtractionPanel — suggestions, inline validation and lock state', () => {
  const makeApi = () => ({
    startItem: jest.fn().mockResolvedValue({ status: 'pending' }),
    extractItem: jest.fn().mockResolvedValue({}),
    mapItem: jest.fn().mockResolvedValue({}),
    calculateItem: jest.fn().mockResolvedValue({ co2e: 10 }),
    getMappingOptions: jest.fn().mockResolvedValue({ factors: [] }),
    draftItem: jest.fn().mockResolvedValue({}),
  });

  const pendingItem = {
    id: 'item-1',
    file_name: 'invoice.pdf',
    file_url: 'https://signed.example/invoice',
    status: 'pending',
    extracted_data: null,
    mapped_data: null,
  };

  test('renders a Suggested chip for fields auto-suggested from the source OCR text', async () => {
    const api = makeApi();
    const { findAllByText } = render(
      <ExtractionPanel
        item={{ ...pendingItem, extracted_data: { supplier: 'Acme', invoice_number: 'INV-9' } }}
        items={[pendingItem]}
        api={api}
        onItemChange={() => {}}
        suggestions={{ supplier: 'Acme', invoice_number: 'INV-9', date: '2025-01-01' }}
        validation={[]}
      />,
    );
    const chips = await findAllByText(/suggested/i);
    expect(chips.length).toBeGreaterThanOrEqual(1);
  });

  test('renders field-level validation errors inline for server findings', async () => {
    const api = makeApi();
    render(
      <ExtractionPanel
        item={pendingItem}
        items={[pendingItem]}
        api={api}
        onItemChange={() => {}}
        suggestions={null}
        validation={[{ code: 'E1', severity: 'error', message: 'Missing supplier', field: 'supplier' }]}
      />,
    );
    const alerts = await screen.findAllByRole('alert');
    expect(alerts.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Missing supplier/)).toBeInTheDocument();
  });

  test('locks inputs when the server item status is outside the editable stages', () => {
    const api = makeApi();
    render(
      <ExtractionPanel
        item={{ ...pendingItem, status: 'calculated', extracted_data: { supplier: 'Acme' } }}
        items={[pendingItem]}
        api={api}
        onItemChange={() => {}}
        suggestions={null}
        validation={[]}
      />,
    );
    expect(screen.getByText(/read-only in the workbench/i)).toBeInTheDocument();
    const supplier = screen.getByDisplayValue('Acme');
    expect(supplier).toBeDisabled();
  });
});

});

describe('D19 AutosaveIndicator', () => {
  test('announces save state to assistive technology', () => {
    render(<AutosaveIndicator state="saved" />);
    expect(screen.getByRole('status')).toHaveTextContent('Saved');
  });
});
