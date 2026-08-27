// frontend/src/v3/components/EvidenceTrail.jsx
// D33/G-P0-5 — universal evidence-trail UI. Renders the evidence chain for any
// number as a timeline (Source → Extraction → Mapping → Factor → Calculation →
// Validation → Review → Approval) with timestamps/actors where available and a
// per-step completeness tone. Never implies independent audit/certification.
//
// Accepts either:
//   * `steps`  — explicit steps [{id, label, detail, value, actor, at, tone}]
//   * `record` — a D33 `evidence_record` (same shape EvidenceRecordPanel uses),
//                converted into steps automatically.
import React from 'react';
import Icon from './ui/Icon';

const TONE_CLASS = {
  complete: 'ct-badge--evidence-complete',
  partial: 'ct-badge--evidence-partial',
  unavailable: 'ct-badge--evidence-unavailable',
};

function toneLabel(tone) {
  if (tone === 'complete') return 'Complete';
  if (tone === 'partial') return 'Partial';
  return 'Unavailable';
}

function formatAt(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString();
}

/** Convert a D33 evidence_record into timeline steps (only steps with data). */
function stepsFromRecord(record) {
  const s = record?.sections || {};
  const completeness = record?.completeness || 'UNAVAILABLE';
  const tone = completeness === 'COMPLETE' ? 'complete' : completeness === 'PARTIAL' ? 'partial' : 'unavailable';
  const steps = [];

  const push = (id, label, section, valueFields) => {
    const sectionData = s[id] || {};
    const values = valueFields
      .map((f) => sectionData?.fields?.[f])
      .filter((v) => v !== undefined && v !== null && v !== '');
    if (values.length === 0) return; // never fabricate a step for absent data
    steps.push({
      id,
      label,
      detail: values.join(' · '),
      value: values.join(' · '),
      actor: sectionData?.actor || sectionData?.by || null,
      at: sectionData?.at || sectionData?.timestamp || null,
      tone,
    });
  };

  push('source_document', 'Source document', 'source_document', ['document_name', 'invoice_reference', 'supplier', 'document_date']);
  push('extraction', 'Extraction', 'extraction', ['activity', 'original_value']);
  push('mapping', 'Mapping', 'mapping', ['mapped_activity', 'activity_type']);
  push('emission_factor', 'Emission factor', 'emission_factor', ['factor_name', 'factor_source', 'factor_value', 'factor_unit', 'reporting_year']);
  push('calculation', 'Calculation', 'calculation', ['formula', 'methodology', 'algorithm_version']);
  push('result', 'Emission result', 'result', ['co2e_kg', 'scope', 'date']);

  return steps;
}

export default function EvidenceTrail({ steps, record, title = 'Evidence trail' }) {
  const resolvedSteps = steps || stepsFromRecord(record || {});

  if (!resolvedSteps || resolvedSteps.length === 0) {
    return (
      <div className="v3-result-card" style={{ marginTop: 12 }}>
        <h3>{title}</h3>
        <p className="v3-muted" style={{ margin: 0 }}>No evidence record is available for this result.</p>
      </div>
    );
  }

  return (
    <section className="ct-card ct-evidence-trail" aria-label={title}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '0 0 14px' }}>
        <Icon name="evidence" size={16} aria-hidden="true" />
        {title}
      </h3>
      <ol style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {resolvedSteps.map((step, i) => {
          const tone = step.tone || 'unavailable';
          const at = formatAt(step.at);
          return (
            <li
              key={step.id || i}
              style={{
                display: 'flex',
                gap: 12,
                paddingBottom: i < resolvedSteps.length - 1 ? 14 : 0,
                marginBottom: i < resolvedSteps.length - 1 ? 14 : 0,
                borderBottom: i < resolvedSteps.length - 1 ? '1px solid var(--ct-color-border)' : 'none',
              }}
            >
              <div style={{ flex: 'none', width: 22, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <span className="ct-badge__dot" aria-hidden="true" />
                {i < resolvedSteps.length - 1 && <span className="ct-evidence-trail__line" aria-hidden="true" />}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <strong style={{ fontSize: 13 }}>{step.label}</strong>
                  <span className={`ct-badge ${TONE_CLASS[tone] || ''}`}>{toneLabel(tone)}</span>
                </div>
                {step.detail && <div style={{ fontSize: 13, color: 'var(--ct-color-text-secondary)', marginTop: 2 }}>{step.detail}</div>}
                {(step.actor || at) && (
                  <div className="v3-muted" style={{ fontSize: 12, marginTop: 2 }}>
                    {step.actor ? `Actor: ${step.actor}` : ''}{step.actor && at ? ' · ' : ''}{at ? `At: ${at}` : ''}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      <p className="v3-muted" style={{ fontSize: 12, margin: '12px 0 0' }}>
        The evidence trail shows how this result was produced from the source record. It is not an independent audit or
        certification.
      </p>
    </section>
  );
}
