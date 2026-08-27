// frontend/src/AboutUs.jsx
// Pre-launch about page. Evidence-based: what CarbonTally is, why it exists,
// the problem it addresses and its intended market. No fictional team,
// fabricated customer numbers, funding or certification claims.
import React from 'react';
import { Link } from 'react-router-dom';
import PageShell from './public/PageShell';

const PRINCIPLES = [
  {
    title: 'Data first',
    text: 'Carbon accounting should start from the source data — invoices, PDFs, spreadsheets — not from assumptions entered into a calculator.',
  },
  {
    title: 'Evidence is non-negotiable',
    text: 'Every number should be traceable to a defensible source document. Evidence traceability is built into the pipeline, not bolted on.',
  },
  {
    title: 'Humans in the loop',
    text: 'Messy data needs judgment. CarbonTally combines structured processing with trained people — reviewers, consultants and specialist processing teams — behind quality gates.',
  },
  {
    title: 'Automation with human review',
    text: 'Automation is built around human review: every result passes validation, customer review and quality control before it is used.',
  },
];

export default function AboutUs() {
  return (
    <PageShell
      title="About — CarbonTally"
      description="CarbonTally is a carbon data processing and accounting platform preparing for commercial launch. Learn what CarbonTally is, why it exists and who it serves."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>About CarbonTally</h1>
          <p>
            CarbonTally is building the data-processing infrastructure that sits between
            the messy source documents organisations already have and the emissions
            numbers they need to trust.
          </p>
        </div>
      </section>

      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Why CarbonTally exists</h2>
            <p>
              Organisations preparing carbon disclosures face a familiar problem: the
              calculation is the easy part. The hard part is gathering invoices, PDFs,
              spreadsheets and scans, cleaning and normalising them, choosing defensible
              emission factors, and keeping the evidence trail that makes the final number
              credible to a regulator or auditor.
            </p>
            <p style={{ marginTop: 14 }}>
              CarbonTally is a carbon accounting and data-processing platform that performs
              that work — with human-in-the-loop processing, end-to-end evidence
              traceability, and consultant and human processing services around it.
            </p>
          </div>
        </div>
      </section>

      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>How we build it</h2>
          </div>
          <div className="ct-grid ct-grid-2">
            {PRINCIPLES.map((p) => (
              <div className="ct-card" key={p.title}>
                <h3>{p.title}</h3>
                <p>{p.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Who CarbonTally serves</h2>
            <p>
              Individuals and small businesses getting a first structured footprint; organisations
              preparing defensible emissions data; consultants delivering carbon accounting to
              multiple clients; and specialist processing teams performing extraction work under
              controlled, isolated access.
            </p>
          </div>
          <div className="ct-grid ct-grid-3">
            <div className="ct-card"><h3>Individuals &amp; small businesses</h3><p>Sole traders and growing teams that need a structured, calculated footprint without a data team — on plans that scale by team size.</p></div>
            <div className="ct-card"><h3>Organisations</h3><p>UK, Irish and European businesses preparing emissions inventories, SECR-style reporting and reduction planning.</p></div>
            <div className="ct-card"><h3>Consultants &amp; advisers</h3><p>Carbon consultants and advisory firms delivering client work through one controlled workspace, with white-label options.</p></div>
          </div>
        </div>
      </section>

      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>CarbonTally is preparing for launch</h2>
          <p>Commercial launch access is by arrangement with the team. Get in touch to be part of it.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
