// frontend/src/public/PlatformPage.jsx
// The CarbonTally platform: capabilities with availability labels.
import React from 'react';
import { Link } from 'react-router-dom';
import PageShell from './PageShell';
import FactorMappingDemo from './demos/FactorMappingDemo';
import OrganizationWorkspaceDemo from './demos/OrganizationWorkspaceDemo';

const BADGE = (label, kind) => <span className={`ct-badge ${kind ? `ct-badge-${kind}` : ''}`}>{label}</span>;

const CAPABILITIES = [
  {
    group: 'Collect & store',
    items: [
      { name: 'Document upload (PDF, image, CSV, spreadsheet)', text: 'Source files are stored in private, organisation-scoped storage and accessed only through short-lived signed URLs.', status: ['Available at launch', 'launch'] },
      { name: 'Scanned document processing', text: 'Scanned PDFs and images are accepted as source documents and processed, with human review before anything moves on.' },
      { name: 'Organisations & teams', text: 'Manage organisations and teams with role-based access — owner, admin, member and viewer roles, with team members managed from the organisation workspace.', status: ['Available at launch', 'launch'] },
    ],
  },
  {
    group: 'Process',
    items: [
      { name: 'Human-in-the-loop extraction', text: 'Trained specialists read source documents — including scanned copies — and extract structured activity data, with review checkpoints before anything moves on.', status: ['Available at launch', 'launch'] },
      { name: 'Full processing workflow', text: 'Batches and items move through extraction, mapping, validation, calculation, customer review and approval.', status: ['Available at launch', 'launch'] },
    ],
  },
  {
    group: 'Map & calculate',
    items: [
      { name: 'Emission-factor matching', text: 'Records are matched to validated emission factors from approved factor sets (for example DEFRA, and SEAI for Irish operations), with every candidate and its provenance retained.', status: ['Available at launch', 'launch'] },
      { name: 'Emissions calculation (Scope 1, 2 & 3)', text: 'An authoritative calculation engine produces snapshotted results; scope classification is carried through the pipeline.', status: ['Available at launch', 'launch'] },
    ],
  },
  {
    group: 'Validate & assure',
    items: [
      { name: 'Validation & review', text: 'Validation gates surface blocking and non-blocking findings; customers review extracted and calculated results before approval.', status: ['Available at launch', 'launch'] },
      { name: 'Quality control', text: 'Independent quality-control checks by CarbonTally specialists — an optional additional review after extraction.', status: ['Available at launch', 'launch'] },
      { name: 'Evidence traceability', text: 'Every emission result traces to its source document, page and extraction item, with an append-only access audit.', status: ['Available at launch', 'launch'] },
    ],
  },
  {
    group: 'Report & export',
    items: [
      { name: 'Structured reports', text: 'Versioned reports composed from the verified data — with sections for calculation, validation, benchmarking where data allows, and sources.', status: ['Available at launch', 'launch'] },
      { name: 'Branded PDF reports', text: 'Reports render to PDF for distribution, including consultant white-label branding.', status: ['Available at launch', 'launch'] },
      { name: 'Data exports', text: 'Emissions data and document inventories export as CSV files for use in your own tools and reporting.', status: ['Available at launch', 'launch'] },
    ],
  },
  {
    group: 'Collaborate',
    items: [
      { name: 'Consultant workspace', text: 'Consultants manage multiple client organisations, processing and reporting from one workspace.', status: ['Available at launch', 'launch'] },
      { name: 'Messaging', text: 'Organisations and consultants communicate inside the platform; specialist processing teams engage only through the platform on the work assigned to them.', status: ['Available at launch', 'launch'] },
      { name: 'White-label', text: 'Consultants can brand the experience with their own name, logo and verified sending domains.', status: ['Available at launch', 'launch'] },
    ],
  },
];

export default function PlatformPage() {
  return (
    <PageShell
      title="Platform — CarbonTally"
      description="The CarbonTally platform: document collection, human-in-the-loop processing, emission-factor mapping, calculation, validation, evidence traceability, reporting and exports."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>The CarbonTally platform</h1>
          <p>
            CarbonTally is more than a carbon calculator. It is a data-processing and
            accounting platform that carries emissions data from messy source documents
            to calculated, validated, evidenced and reportable results.
          </p>
        </div>
      </section>

      {/* INTERACTIVE ORGANIZATION DEMO */}
      <section className="ct-section ct-section-accent">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>Explore the platform — live interactive demo</h2>
            <p>
              A product preview of a Customer Organisation workspace. Select a demo
              organisation, open a Processing Work item and trace one result from source
              document to evidence.
            </p>
          </div>
          <OrganizationWorkspaceDemo />
        </div>
      </section>

      {CAPABILITIES.map((group, i) => (
        <section className={i % 2 ? 'ct-section' : 'ct-section ct-section-alt'} key={group.group}>
          <div className="ct-container">
            <div className="ct-section-head">
              <h2>{group.group}</h2>
            </div>
            <div className="ct-grid ct-grid-3">
              {group.items.map((item) => (
                <div className="ct-card" key={item.name}>
                  <h3>{item.name}</h3>
                  <p>{item.text}</p>
                  {item.status ? (
                    <div className="ct-status-row">
                      <span className="ct-status-label">Status</span>
                      {BADGE(item.status[0], item.status[1])}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </section>
      ))}

      <section className="ct-section ct-section-accent">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>See factor mapping in action</h2>
            <p>
              Matching the right emission factor is where most carbon numbers go wrong. CarbonTally
              keeps every candidate and its confidence, so the choice can be explained.
            </p>
          </div>
          <FactorMappingDemo />
        </div>
      </section>

      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Want a guided look at the platform?</h2>
          <p>Launch access is by arrangement while CarbonTally prepares for commercial launch.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
