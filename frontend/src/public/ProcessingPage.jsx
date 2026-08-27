// frontend/src/public/ProcessingPage.jsx
// Processing services: self-service / assisted / managed, human processing
// services, and the automation position. Customer-friendly language; internal
// terminology translated.
import React from 'react';
import { Link } from 'react-router-dom';
import PageShell from './PageShell';
import DocumentExtractionDemo from './demos/DocumentExtractionDemo';

const BADGE = (label, kind) => <span className={`ct-badge ${kind ? `ct-badge-${kind}` : ''}`}>{label}</span>;

const OPTIONS = [
  {
    name: 'Self-service',
    who: 'Your team',
    does: 'Your team uploads documents, creates processing batches and drives items through the workflow in the platform.',
    reviews: 'You review and approve results before they are final.',
    receives: 'A controlled pipeline with platform-grade factor mapping, calculation, evidence and reporting.',
    status: 'Available at launch',
    badge: ['Available at launch', 'launch'],
  },
  {
    name: 'Assisted',
    who: 'CarbonTally (with you)',
    does: 'CarbonTally performs extraction and preparation work on your documents against an approved estimate.',
    reviews: 'Results are presented to you for review and approval before finalisation.',
    receives: 'Prepared, mapped and calculated data with your sign-off retained.',
    status: 'Available at launch (plan-gated)',
    badge: ['Available at launch', 'launch'],
  },
  {
    name: 'Managed',
    who: 'CarbonTally',
    does: 'CarbonTally runs the end-to-end workflow — collection, extraction, mapping, calculation, validation and reporting.',
    reviews: 'Quality gates and reporting checkpoints are built into the engagement terms.',
    receives: 'A finished, evidenced, reportable emissions data set.',
    status: 'Available at launch (plan-gated)',
    badge: ['Available at launch', 'launch'],
  },
];

export default function ProcessingPage() {
  return (
    <PageShell
      title="Processing Services — CarbonTally"
      description="Self-service, assisted and managed emissions data processing, plus specialist human processing teams. Choose how much processing CarbonTally performs."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>Processing services</h1>
          <p>
            The same pipeline, three ways to run it. CarbonTally is software that
            performs processing — you choose how much of the work we do.
          </p>
        </div>
      </section>

      {/* OPTIONS */}
      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Choose your processing model</h2>
          </div>
          <div className="ct-table-wrap">
            <table className="ct-table">
              <thead>
                <tr>
                  <th style={{ width: '14%' }}>Model</th>
                  <th>Who performs the work</th>
                  <th>What happens</th>
                  <th>Who reviews</th>
                  <th>What you receive</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {OPTIONS.map((o) => (
                  <tr key={o.name}>
                    <td style={{ fontWeight: 600 }}>{o.name}</td>
                    <td>{o.who}</td>
                    <td>{o.does}</td>
                    <td>{o.reviews}</td>
                    <td>{o.receives}</td>
                    <td>{BADGE(o.badge[0], o.badge[1])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="ct-note" style={{ marginTop: 16 }}>
            Assisted and managed availability depends on the subscription plan — see{' '}
            <Link to="/pricing">pricing</Link>.
          </p>
        </div>
      </section>

      {/* HOW DATA MOVES */}
      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>What happens to your data</h2>
            <p>One controlled path from source document to defensible result.</p>
          </div>
          <div className="ct-steps">
            <div className="ct-step"><span className="n">1</span><h3>You provide the source data</h3><p>PDFs, scans, CSVs and spreadsheets — uploaded to private, organisation-scoped storage.</p></div>
            <div className="ct-step"><span className="n">2</span><h3>Processing is performed</h3><p>By your team, by CarbonTally, or by specialist processing teams under controlled access.</p></div>
            <div className="ct-step"><span className="n">3</span><h3>Data is mapped &amp; calculated</h3><p>Records are matched to emission factors, units are checked, and emissions are calculated with full provenance.</p></div>
            <div className="ct-step"><span className="n">4</span><h3>You review &amp; approve</h3><p>Validation findings and results are presented for customer review before approval.</p></div>
            <div className="ct-step"><span className="n">5</span><h3>You report &amp; export</h3><p>Structured reports, branded PDFs and CSV data exports are generated from the approved data.</p></div>
          </div>
        </div>
      </section>

      {/* HUMAN PROCESSING SERVICES */}
      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Human processing services</h2>
            <p>
              Behind assisted and managed processing are specialist teams that can help
              prepare, extract, structure and review emissions data when you need
              additional hands-on support.
            </p>
          </div>
          <div className="ct-grid ct-grid-3">
            <div className="ct-card">
              <h3>Controlled access</h3>
              <p>Each team sees only the work assigned to it. Customer organisations, consultants and processing teams are fully isolated from one another.</p>
            </div>
            <div className="ct-card">
              <h3>Structured communication</h3>
              <p>Questions about your documents are routed through the platform as structured clarifications — never through untracked personal channels.</p>
            </div>
            <div className="ct-card">
              <h3>Human quality, controlled</h3>
              <p>Specialist teams perform extraction and preparation; validation, customer review and CarbonTally quality-control checks sit on top before anything is final.</p>
            </div>
          </div>
          <div className="ct-status-row" style={{ marginTop: 20 }}>
            {BADGE('Human processing services available at launch', 'launch')}
          </div>
        </div>
      </section>

      {/* AUTOMATION */}
      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Automation in the pipeline</h2>
            <p>The parts of the workflow that run automatically — with human review around them.</p>
          </div>
          <div className="ct-grid ct-grid-3">
            <div className="ct-card">
              <h3>Scanned document processing</h3>
              <p>Scanned PDFs and images are accepted as source documents and processed, with human review before anything moves on.</p>
            </div>
            <div className="ct-card">
              <h3>Automated mapping &amp; calculation</h3>
              <p>Factor matching and emissions calculation run automatically once data is extracted, with unit checks before anything is calculated.</p>
              <div className="ct-status-row">{BADGE('Available at launch', 'launch')}</div>
            </div>
            <div className="ct-card">
              <h3>Automatic validation checks</h3>
              <p>Validation gates run automatically, surfacing blocking and non-blocking findings that reviewers work through before anything is final.</p>
              <div className="ct-status-row">{BADGE('Available at launch', 'launch')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* EXTRACTION DEMO */}
      <section className="ct-section ct-section-accent">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>See extraction and review in action</h2>
            <p>A source invoice becomes structured, reviewable fields — ready for mapping, calculation and review.</p>
          </div>
          <DocumentExtractionDemo />
        </div>
      </section>

      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Discuss your processing needs</h2>
          <p>CarbonTally is preparing for commercial launch — tell us about your data and we will show you how it would flow.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
