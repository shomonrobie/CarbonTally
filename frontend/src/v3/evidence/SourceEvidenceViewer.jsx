// frontend/src/v3/evidence/SourceEvidenceViewer.jsx
// CarbonTally shared Source Evidence Viewer (PO authorization, 2026-09-22).
//
// One reusable viewer for every evidence consumer — normal customer evidence
// tracing, report/disclosure evidence and CarbonTally Insight — rather than an
// Insight-specific viewer. It reuses the authoritative records and primitives
// that already exist:
//
//   * evidence line   → GET /api/v3/evidence/line-items/{id} (allowlisted, DM-6
//                       re-authorized on every read);
//   * source document → the existing SecureDocumentViewer signed-URL primitive;
//   * provenance      → the line's own location block + the calculations that
//                       reference it.
//
// There is NO second evidence model and NOTHING is editable here: the left pane
// is the original source document, the right pane is the extracted/mapped
// evidence and its calculation context, linked by an authoritative location when
// one exists. When it does not, the viewer says so instead of manufacturing
// precision.
import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { getEvidenceLine } from '../api';
import SecureDocumentViewer from '../components/workbench/SecureDocumentViewer';
import Button from '../components/ui/Button';
import { hasExactLocation, locationRows, locationView } from './evidenceLocation';
import './evidence-viewer.css';

//: One non-disclosing failure state for every outcome (missing, foreign,
//: denied, failed). It states neither that the evidence exists nor that it does
//: not, so the viewer cannot leak protected-resource existence in either
//: direction.
const UNAVAILABLE = {
  title: 'Source evidence unavailable',
  body: "CarbonTally can't show this source evidence for you. Evidence access is authorized again every time it is opened.",
};

function Field({ label, value }) {
  return (
    <div className="ct-ev__field">
      <div className="ct-ev__field-key">{label}</div>
      <div className="ct-ev__field-value">{value ?? '—'}</div>
    </div>
  );
}

export default function SourceEvidenceViewer() {
  const { lineItemId } = useParams();
  const [params] = useSearchParams();
  const from = params.get('from') || '/emissions';

  const [state, setState] = useState('loading');
  const [evidence, setEvidence] = useState(null);

  const load = useCallback(async () => {
    setState('loading');
    try {
      const payload = await getEvidenceLine(lineItemId);
      setEvidence(payload);
      setState('ready');
    } catch (_error) {
      setEvidence(null);
      setState('unavailable');
    }
  }, [lineItemId]);

  useEffect(() => {
    load();
  }, [load]);

  const line = evidence?.line || {};
  const document = evidence?.document || null;
  const location = evidence?.location || null;
  const view = locationView(location);
  const rows = locationRows(location);
  const calculations = evidence?.calculations || [];

  return (
    <div className="ct-ev">
      <nav className="ct-ev__back" aria-label="Breadcrumb">
        <Link to={from} className="ct-ev__back-link">
          ← Back to evidence
        </Link>
      </nav>

      <header className="ct-ev__head">
        <h1 className="ct-ev__title">Source evidence</h1>
        <p className="ct-ev__subtitle v3-muted">
          The original source document beside the CarbonTally evidence extracted from it.
          This view is read-only.
        </p>
      </header>

      {state === 'loading' && (
        <div className="ct-ev__card" role="status" aria-live="polite">
          Loading source evidence…
        </div>
      )}

      {state === 'unavailable' && (
        <div className="ct-ev__card" data-testid="source-evidence-unavailable" role="alert">
          <h2 className="ct-ev__card-title">{UNAVAILABLE.title}</h2>
          <p className="v3-muted">{UNAVAILABLE.body}</p>
          <Button variant="secondary" size="sm" onClick={load}>
            Try again
          </Button>
        </div>
      )}

      {state === 'ready' && evidence && (
        <div className="ct-ev__grid">
          <section className="ct-ev__pane" aria-labelledby="ct-ev-source-heading">
            <h2 id="ct-ev-source-heading" className="ct-ev__pane-title">
              Original source document
            </h2>
            <p className="ct-ev__pane-sub v3-muted">
              {document?.name || 'Source document'}
              {document?.file_type ? ` · ${document.file_type}` : ''}
            </p>
            {document?.signed_url ? (
              <SecureDocumentViewer
                src={document.signed_url}
                title={document.name || 'Source document'}
                allowDownload={false}
              />
            ) : (
              <div
                className="ct-ev__notice"
                data-testid="source-evidence-document-withheld"
              >
                <strong>Source document view is not available for your access level.</strong>
                <p className="v3-muted">
                  {evidence.document_available
                    ? 'CarbonTally does not issue source-document access below the full drill-down boundary. The extracted evidence beside this notice is authoritative.'
                    : 'No stored source document is linked to this evidence line.'}
                </p>
              </div>
            )}
          </section>

          <section className="ct-ev__pane" aria-labelledby="ct-ev-evidence-heading">
            <h2 id="ct-ev-evidence-heading" className="ct-ev__pane-title">
              Extracted and mapped evidence
            </h2>

            <div
              className={`ct-ev__location ct-ev__location--${view.state}`}
              data-testid="source-evidence-location"
              data-location-state={view.state}
            >
              <span className="ct-ev__location-label">{view.label}</span>
              {view.detail && <p className="ct-ev__location-detail">{view.detail}</p>}
              {location?.ordinal_note && (
                <p className="v3-muted ct-ev__location-note">{location.ordinal_note}</p>
              )}
            </div>

            <h3 className="ct-ev__section-title">Evidence line</h3>
            <div className="ct-ev__fields">
              <Field
                label="Evidence line id"
                value={<span className="v3-mono">{evidence.evidence_line_item_id}</span>}
              />
              <Field
                label="Extracted row"
                value={
                  line.raw_description ||
                  (Array.isArray(line.redacted_fields) &&
                  line.redacted_fields.includes('raw_description')
                    ? 'Not available for your access level'
                    : '—')
                }
              />
              <Field
                label="Quantity extracted"
                value={
                  line.raw_quantity != null
                    ? `${line.raw_quantity} ${line.raw_unit || ''}`.trim()
                    : 'Not available for your access level'
                }
              />
              <Field label="Materialisation" value={evidence.materialisation_kind || '—'} />
              {rows.map((row) => (
                <Field key={row.label} label={row.label} value={row.value} />
              ))}
            </div>

            <h3 className="ct-ev__section-title">Calculation context</h3>
            {calculations.length === 0 ? (
              <p className="v3-muted">No calculation references this evidence line yet.</p>
            ) : (
              <ul className="ct-ev__calc-list">
                {calculations.map((calc) => (
                  <li key={calc.id} className="ct-ev__calc">
                    <div className="ct-ev__calc-head">
                      <strong>{calc.co2e_kg ?? '—'} kg CO₂e</strong>
                      <span className="v3-muted">
                        {calc.activity || calc.activity_type || '—'}
                      </span>
                    </div>
                    <div className="ct-ev__calc-meta v3-muted">
                      {[
                        calc.scope,
                        calc.date,
                        calc.quantity ? `${calc.quantity} ${calc.quantity_unit || ''}` : null,
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </div>
                    <div className="ct-ev__calc-meta v3-muted v3-mono">{calc.id}</div>
                  </li>
                ))}
              </ul>
            )}

            {!hasExactLocation(location) && (
              <p
                className="v3-muted ct-ev__footnote"
                data-testid="source-evidence-location-caveat"
              >
                CarbonTally has not established an exact page, sheet or row for this
                evidence line, so none is shown. The evidence above is the authoritative
                extracted record.
              </p>
            )}

            <details className="ct-ev__access">
              <summary>Access and authorization</summary>
              <div className="ct-ev__fields" style={{ marginTop: 8 }}>
                <Field label="Drill-down depth" value={evidence.access?.drill_down_depth} />
                <Field label="Reason" value={evidence.access?.drill_down_rationale} />
                <Field
                  label="Source-document references"
                  value={
                    evidence.access?.document_references_available
                      ? 'Available'
                      : 'Not available at this depth'
                  }
                />
              </div>
            </details>
          </section>
        </div>
      )}
    </div>
  );
}
