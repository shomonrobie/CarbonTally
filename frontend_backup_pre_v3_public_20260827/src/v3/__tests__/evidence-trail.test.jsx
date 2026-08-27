// frontend/src/v3/__tests__/evidence-trail.test.jsx
// D33/G-P0-5 — universal evidence trail renders the chain with labels, tones
// and actors; never implies independent certification.
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import EvidenceTrail from '../components/EvidenceTrail';

describe('EvidenceTrail (D33 / G-P0-5)', () => {
  test('renders explicit steps with labels and completeness tones', () => {
    const steps = [
      { id: 'source', label: 'Source document', detail: 'invoice.pdf', tone: 'complete' },
      { id: 'factor', label: 'Emission factor', detail: 'DEFRA 2025', tone: 'complete' },
      { id: 'result', label: 'Emission result', detail: '12.3 kg CO₂e', tone: 'partial' },
    ];
    render(<EvidenceTrail steps={steps} />);
    expect(screen.getByText('Source document')).toBeInTheDocument();
    expect(screen.getByText('Emission factor')).toBeInTheDocument();
    expect(screen.getByText('Emission result')).toBeInTheDocument();
    expect(screen.getAllByText(/complete/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/partial/i)).toBeInTheDocument();
  });

  test('renders a D33 evidence_record into steps', () => {
    const record = {
      completeness: 'COMPLETE',
      sections: {
        source_document: { fields: { document_name: 'invoice.pdf', supplier: 'ACME' } },
        calculation: { fields: { formula: 'qty * factor', algorithm_version: 'v1' } },
        result: { fields: { co2e_kg: '12.3', scope: 'Scope 1' } },
      },
    };
    render(<EvidenceTrail record={record} />);
    expect(screen.getByText('Source document')).toBeInTheDocument();
    expect(screen.getByText(/invoice.pdf/)).toBeInTheDocument();
    expect(screen.getByText('Emission result')).toBeInTheDocument();
  });

  test('renders empty state when no evidence is available', () => {
    render(<EvidenceTrail />);
    expect(screen.getByText(/no evidence record/i)).toBeInTheDocument();
  });

  test('never implies independent audit or certification', () => {
    const steps = [{ id: 'source', label: 'Source document', detail: 'invoice.pdf', tone: 'complete' }];
    render(<EvidenceTrail steps={steps} />);
    expect(screen.getByText(/not an independent audit/i)).toBeInTheDocument();
  });
});
