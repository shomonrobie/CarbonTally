// frontend/src/public/ConsultantsPage.jsx
// The consultant positioning page: multi-client workspace, processing,
// reporting, white-label. Evidence-based — only implemented capabilities.
import React from 'react';
import { Link } from 'react-router-dom';
import PageShell from './PageShell';
import ConsultantWorkspaceDemo from './demos/ConsultantWorkspaceDemo';

const BADGE = (label, kind) => <span className={`ct-badge ${kind ? `ct-badge-${kind}` : ''}`}>{label}</span>;

const FEATURES = [
  {
    title: 'Multiple client organisations',
    text: 'One consultant workspace across every client you serve. Access to each client is controlled by client-grant semantics, and suspended or ended clients lose access immediately.',
  },
  {
    title: 'Client processing',
    text: 'Run document processing, mapping, calculation and validation for each client from your workspace — with per-client isolation.',
  },
  {
    title: 'Reporting for clients',
    text: 'Generate structured reports and branded PDFs per client, from their approved data.',
  },
  {
    title: 'White-label & branding',
    text: 'Apply your own brand — name, logo, colours, verified sending domain — so client-facing output is yours.',
  },
  {
    title: 'Client communication',
    text: 'Message clients inside the platform with a clear audit trail, instead of chasing threads across inboxes.',
  },
  {
    title: 'Client lifecycle',
    text: 'Onboard clients, suspend or end engagements — when an engagement is suspended or closed, access ends immediately.',
  },
];

export default function ConsultantsPage() {
  return (
    <PageShell
      title="For Consultants — CarbonTally"
      description="CarbonTally gives carbon consultants one controlled workspace across multiple client organisations: processing, reporting, messaging and white-label branding."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>Built for carbon consultants</h1>
          <p>
            If you deliver carbon accounting for clients, CarbonTally gives you the
            processing infrastructure — extraction, mapping, calculation, evidence and
            reporting — behind one professional workspace.
          </p>
        </div>
      </section>

      {/* INTERACTIVE CONSULTANT DEMO */}
      <section className="ct-section ct-section-accent">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>One consultant workspace, many client organisations</h2>
            <p>
              A product preview of a consultant workspace. Open a client organisation, review
              its processing status, then switch to another — exactly the switching a
              consultant performs in the platform.
            </p>
          </div>
          <ConsultantWorkspaceDemo />
        </div>
      </section>

      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-grid ct-grid-3">
            {FEATURES.map((f) => (
              <div className="ct-card" key={f.title}>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>How a consultant engagement works</h2>
          </div>
          <div className="ct-steps">
            <div className="ct-step"><span className="n">1</span><h3>Client granted access</h3><p>A client organisation grants your firm access; you work inside the platform, never outside it.</p></div>
            <div className="ct-step"><span className="n">2</span><h3>Collect &amp; process</h3><p>Client documents are uploaded and processed through the pipeline under your control.</p></div>
            <div className="ct-step"><span className="n">3</span><h3>Calculate &amp; validate</h3><p>Emissions are mapped, calculated and validated — with evidence traceability on every result.</p></div>
            <div className="ct-step"><span className="n">4</span><h3>Report &amp; deliver</h3><p>Generate structured reports and branded PDFs for each client from their approved data.</p></div>
          </div>
          <div className="ct-status-row" style={{ justifyContent: 'center', marginTop: 24 }}>
            {BADGE('Consultant workspace available at launch', 'launch')}
          </div>
        </div>
      </section>

      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Preparing to serve your clients with CarbonTally?</h2>
          <p>Consultant onboarding is by arrangement with the CarbonTally team ahead of launch.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
