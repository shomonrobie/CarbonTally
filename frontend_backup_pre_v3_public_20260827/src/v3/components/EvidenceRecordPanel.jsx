// frontend/src/v3/components/EvidenceRecordPanel.jsx
// D33.1 — authorized, human-readable evidence record for one emission result.
// Distinguishes ORIGINAL source data (from the document) from CarbonTally-derived
// data (mapping, factor, calculation, result), shows an honest evidence-completeness
// badge and source-location precision, and exposes stable record identifiers in a
// "Technical details" expansion. Never fabricates precision.
import React from 'react';

const BADGE = { COMPLETE: 'complete', PARTIAL: 'partial', UNAVAILABLE: 'unavailable' };

export default function EvidenceRecordPanel({ evidence }) {
  const record = evidence?.evidence_record || {};
  const sections = record.sections || {};
  const completeness = record.completeness || 'UNAVAILABLE';
  const badge = BADGE[completeness] || 'unavailable';

  return (
    <div className="v3-result-card" style={{ marginTop: 12 }}>
      <h3>
        Evidence — {evidence?.source_document?.name || 'source document'}
        <span className={`v3-badge v3-badge-${badge}`}>{completeness}</span>
      </h3>
      <p className="v3-muted" style={{ margin: '4px 0' }}>{record.completeness_reason || ''}</p>
      <p className="v3-muted" style={{ margin: '4px 0 10px' }}>
        {record.source_location?.display || 'Source document available; exact source location not available.'}
      </p>

      {/* EMISSION RESULT (derived) */}
      <h4 className="v3-evidence-section">Emission result — CarbonTally</h4>
      <div className="v3-meta-list">
        <div className="v3-meta-item"><div className="k">kg CO₂e</div><div className="v">{sections.result?.fields?.co2e_kg ?? '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Scope</div><div className="v">{sections.result?.fields?.scope || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Period</div><div className="v">{sections.result?.fields?.date || '—'}</div></div>
      </div>

      {/* CALCULATION (derived) */}
      <h4 className="v3-evidence-section">Calculation — CarbonTally</h4>
      <div className="v3-formula">{sections.calculation?.fields?.formula || '—'}</div>
      <div className="v3-meta-list" style={{ marginTop: 8 }}>
        <div className="v3-meta-item"><div className="k">Methodology</div><div className="v">{sections.calculation?.fields?.methodology || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Algorithm version</div><div className="v">{sections.calculation?.fields?.algorithm_version || '—'}</div></div>
      </div>

      {/* EMISSION FACTOR (derived) */}
      <h4 className="v3-evidence-section">Emission factor — CarbonTally</h4>
      <div className="v3-meta-list">
        <div className="v3-meta-item"><div className="k">Factor</div><div className="v">{sections.emission_factor?.fields?.factor_name || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Source</div><div className="v">{sections.emission_factor?.fields?.factor_source || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Set</div><div className="v">{sections.emission_factor?.fields?.factor_set || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Value</div><div className="v">{sections.emission_factor?.fields?.factor_value ?? '—'} {sections.emission_factor?.fields?.factor_unit || ''}</div></div>
        <div className="v3-meta-item"><div className="k">Reporting year</div><div className="v">{sections.emission_factor?.fields?.reporting_year || '—'}</div></div>
      </div>

      {/* MAPPING (derived) */}
      <h4 className="v3-evidence-section">Mapping — CarbonTally</h4>
      <div className="v3-meta-list">
        <div className="v3-meta-item"><div className="k">Mapped activity</div><div className="v">{sections.mapping?.fields?.mapped_activity || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Activity type</div><div className="v">{sections.mapping?.fields?.activity_type || '—'}</div></div>
      </div>

      {/* ORIGINAL SOURCE DATA (original) */}
      <h4 className="v3-evidence-section">Original source data — from the document</h4>
      <div className="v3-meta-list">
        <div className="v3-meta-item"><div className="k">Source document</div><div className="v">{sections.source_document?.fields?.document_name || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Invoice / reference</div><div className="v">{sections.source_document?.fields?.invoice_reference || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Supplier</div><div className="v">{sections.source_document?.fields?.supplier || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Document date</div><div className="v">{sections.source_document?.fields?.document_date || '—'}</div></div>
        <div className="v3-meta-item"><div className="k">Extracted line</div><div className="v">{sections.extraction?.fields?.activity || '—'} — {sections.extraction?.fields?.original_value || '—'}</div></div>
      </div>
      {evidence?.source_document?.signed_url ? (
        <a className="v3-btn" href={evidence.source_document.signed_url} target="_blank" rel="noreferrer">
          Open source document
        </a>
      ) : (
        <p className="v3-muted">No stored source document available.</p>
      )}

      {/* TECHNICAL DETAILS / EVIDENCE RECORD */}
      <details className="v3-evidence-details" style={{ marginTop: 12 }}>
        <summary>Technical details / Evidence record</summary>
        <div className="v3-meta-list" style={{ marginTop: 8 }}>
          <div className="v3-meta-item"><div className="k">Emission log id</div><div className="v v3-mono">{record.technical_details?.emission_log_id || '—'}</div></div>
          <div className="v3-meta-item"><div className="k">Calculation snapshot id</div><div className="v v3-mono">{record.technical_details?.calculation_snapshot_id || '—'}</div></div>
          <div className="v3-meta-item"><div className="k">Extraction item id</div><div className="v v3-mono">{record.technical_details?.manual_extraction_item_id || '—'}</div></div>
          <div className="v3-meta-item"><div className="k">Source file id</div><div className="v v3-mono">{record.technical_details?.organization_file_id || '—'}</div></div>
          <div className="v3-meta-item"><div className="k">Factor id</div><div className="v v3-mono">{record.technical_details?.emission_factor_id || '—'}</div></div>
          {record.technical_details?.source_page != null && (
            <div className="v3-meta-item"><div className="k">Source page</div><div className="v">{record.technical_details.source_page}</div></div>
          )}
        </div>
      </details>
    </div>
  );
}

