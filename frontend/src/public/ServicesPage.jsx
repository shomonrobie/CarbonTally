// frontend/src/public/ServicesPage.jsx
// The complete CarbonTally service catalogue, organised by category with
// availability labels. Software, processing services, consultant workflows and
// human processing services are kept clearly separate.
import React from 'react';
import { Link } from 'react-router-dom';
import PageShell from './PageShell';
import HumanReviewDemo from './demos/HumanReviewDemo';

const BADGE = (label, kind) => <span className={`ct-badge ${kind ? `ct-badge-${kind}` : ''}`}>{label}</span>;

const CATEGORIES = [
  {
    title: 'Platform software',
    intro: 'The CarbonTally software platform. You (or a consultant) operate it; CarbonTally provides the technology.',
    services: [
      {
        name: 'Carbon data platform',
        what: 'A web platform to collect source documents, drive processing, map factors, calculate emissions, validate, evidence and report.',
        for: 'Organisations and consultants preparing emissions inventories.',
        why: 'Replaces the spreadsheet-and-inbox workflow with a controlled, auditable pipeline.',
        how: 'Upload documents → processing pipeline → calculation → review → reports and exports.',
        get: 'A structured, traceable, exportable emissions data set.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
      {
        name: 'Evidence & traceability',
        what: 'Every calculated result is linked to the source document, page and extraction item that produced it.',
        for: 'Teams that must defend their numbers to regulators, auditors or clients.',
        why: '“Where did this number come from?” is answered in seconds, not weeks.',
        how: 'Source references are captured at extraction and carried through mapping, calculation and reporting, with an append-only access audit.',
        get: 'An evidence record for every emission result.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
      {
        name: 'Reporting & exports',
        what: 'Versioned structured reports and branded PDFs, plus CSV data exports.',
        for: 'Organisations and consultants preparing disclosures and internal reporting.',
        why: 'Reporting is generated from the verified, evidenced data set — not re-keyed.',
        how: 'The report engine composes sections from the approved calculations and validation results.',
        get: 'A report you can distribute, and data you can take anywhere.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
      {
        name: 'Consultant workspace & white-label',
        what: 'A workspace for firms serving multiple client organisations, with optional white-label branding.',
        for: 'Carbon consultants and advisory firms.',
        why: 'One controlled workspace across all clients, with branding that is yours.',
        how: 'Consultants manage client access, processing, reporting and messaging; white-label applies branding and verified sending domains.',
        get: 'A repeatable client delivery workflow.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
    ],
  },
  {
    title: 'Processing services',
    intro: 'Services CarbonTally performs. Choose how much of the work we do — the pricing model reflects that choice.',
    services: [
      {
        name: 'Self-service processing',
        what: 'Your team drives processing inside the platform; CarbonTally provides the pipeline.',
        for: 'Organisations with internal capacity to manage the workflow.',
        why: 'Full control with platform-grade mapping, calculation and evidence.',
        how: 'You create batches, upload documents and drive items through the workflow; factors, calculation and reports are platform-provided.',
        get: 'A controlled, evidenced processing pipeline for your team.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
      {
        name: 'Assisted processing',
        what: 'CarbonTally performs extraction and preparation work on your documents, with review checkpoints.',
        for: 'Organisations that want the data prepared for them and final sign-off kept in-house.',
        why: 'Offloads the operational grind while keeping control of the result.',
        how: 'You approve an estimate, CarbonTally processes the documents, and results are presented for review and approval.',
        get: 'Prepared, mapped and calculated data with human oversight.',
        when: 'Available at launch (plan-gated).',
        badge: ['Available at launch', 'launch'],
      },
      {
        name: 'Managed processing',
        what: 'CarbonTally runs the end-to-end workflow as a managed service.',
        for: 'Organisations with large or complex backlogs and limited internal capacity.',
        why: 'A complete processing outcome without building a processing team.',
        how: 'CarbonTally manages collection, extraction, mapping, calculation, validation and reporting against agreed terms.',
        get: 'A finished, evidenced, reportable emissions data set.',
        when: 'Available at launch (plan-gated).',
        badge: ['Available at launch', 'launch'],
      },
    ],
  },
  {
    title: 'Human processing services',
    intro: 'The people behind assisted and managed processing — specialists who can prepare, extract, structure and review emissions data when you need extra hands-on support.',
    services: [
      {
        name: 'Consultant support',
        what: 'Independent carbon consultants and firms operating CarbonTally for their clients.',
        for: 'Consultants who need one controlled workspace across many clients.',
        why: 'Consultants can deliver processing, calculation and reporting without rebuilding infrastructure.',
        how: 'Consultant firms manage client organisations, processing, reporting, messaging and white-label branding.',
        get: 'A professional delivery surface for client work.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
      {
        name: 'Specialist processing teams',
        what: 'Vetted human teams that perform document extraction and preparation work for assisted and managed processing.',
        for: 'Customers who want CarbonTally (or its specialist teams) to do the extraction work for them.',
        why: 'Human-in-the-loop quality when you need hands-on support — without exposing your data to untracked channels.',
        how: 'Work is assigned through the platform, reviews are recorded, and customers never share documents directly with individual operators.',
        get: 'Quality extraction capacity with controlled access and a full audit trail.',
        when: 'Available at launch.',
        badge: ['Available at launch', 'launch'],
      },
    ],
  },
  {
    title: 'Commercial services',
    intro: 'How CarbonTally will be sold and delivered. Indicative pricing is subject to final commercial terms.',
    services: [
      {
        name: 'Plans & credits',
        what: 'Four subscription plans (Starter, Professional, Business, Enterprise) with a credit-based processing model.',
        for: 'All customers.',
        why: 'Predictable pricing tied to the work actually performed.',
        how: 'Plans include monthly credits, storage and team limits; processing complexity consumes credits on a published band.',
        get: 'A transparent commercial model.',
        when: 'At launch. Pricing is subject to final commercial terms.',
        badge: ['At launch', 'launch'],
      },
      {
        name: 'Online payments',
        what: 'Online checkout and card payment for subscriptions and orders.',
        for: 'Customers who prefer to pay online.',
        why: 'Pay for subscriptions and orders without a manual step.',
        how: 'Subscriptions and orders are arranged directly with the CarbonTally team.',
        get: 'Simple, direct commercial arrangements with the CarbonTally team.',
        when: 'Arranged directly with the CarbonTally team.',
      },
    ],
  },
];

export default function ServicesPage() {
  return (
    <PageShell
      title="Services — CarbonTally"
      description="The CarbonTally service catalogue: platform software, self-service/assisted/managed processing, consultant workflows, human processing services and the commercial model."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>Services</h1>
          <p>
            CarbonTally provides software, performs processing services, and works with
            consultants and specialist processing teams. Each capability below answers what it
            is, who it is for, how it works and when it is available.
          </p>
        </div>
      </section>

      {/* Service hierarchy: platform + processing are primary (more space),
          human processing services are supporting, commercial services are
          subordinate (muted background, concise). */}
      {CATEGORIES.map((cat, i) => {
        const bg = ['ct-section', 'ct-section ct-section-alt', 'ct-section', 'ct-section ct-section-muted'][i] || 'ct-section';
        return (
        <section className={bg} key={cat.title}>
          <div className="ct-container">
            <div className="ct-section-head">
              <h2>{cat.title}</h2>
              <p>{cat.intro}</p>
            </div>
            <div className="ct-grid ct-grid-2">
              {cat.services.map((s) => (
                <div className="ct-card" key={s.name}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                    <h3 style={{ margin: 0 }}>{s.name}</h3>
                    {s.badge ? BADGE(s.badge[0], s.badge[1]) : null}
                  </div>
                  <dl style={{ margin: '16px 0 0' }}>
                    <dt style={{ fontWeight: 600, fontSize: 13, color: '#0f766e', marginTop: 12 }}>What is it?</dt>
                    <dd style={{ margin: '2px 0 0', fontSize: 14.5, color: '#334155' }}>{s.what}</dd>
                    <dt style={{ fontWeight: 600, fontSize: 13, color: '#0f766e', marginTop: 12 }}>Who is it for?</dt>
                    <dd style={{ margin: '2px 0 0', fontSize: 14.5, color: '#334155' }}>{s.for}</dd>
                    <dt style={{ fontWeight: 600, fontSize: 13, color: '#0f766e', marginTop: 12 }}>Why does it matter?</dt>
                    <dd style={{ margin: '2px 0 0', fontSize: 14.5, color: '#334155' }}>{s.why}</dd>
                    <dt style={{ fontWeight: 600, fontSize: 13, color: '#0f766e', marginTop: 12 }}>How does it work?</dt>
                    <dd style={{ margin: '2px 0 0', fontSize: 14.5, color: '#334155' }}>{s.how}</dd>
                    <dt style={{ fontWeight: 600, fontSize: 13, color: '#0f766e', marginTop: 12 }}>What does the customer get?</dt>
                    <dd style={{ margin: '2px 0 0', fontSize: 14.5, color: '#334155' }}>{s.get}</dd>
                    <dt style={{ fontWeight: 600, fontSize: 13, color: '#0f766e', marginTop: 12 }}>When is it available?</dt>
                    <dd style={{ margin: '2px 0 0', fontSize: 14.5, color: '#334155' }}>{s.when}</dd>
                  </dl>
                </div>
              ))}
            </div>
          </div>
        </section>
        );
      })}

      <section className="ct-section ct-section-accent">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>Human processing services, explained</h2>
            <p>
              Specialist teams can help prepare, extract, structure and review emissions data when
              you need additional hands-on support — with review checkpoints before anything is final.
            </p>
          </div>
          <HumanReviewDemo />
        </div>
      </section>

      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Questions about the service model?</h2>
          <p>CarbonTally is preparing for commercial launch — the team can walk you through the services.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
