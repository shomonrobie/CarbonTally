// frontend/src/LandingPage.jsx
// Pre-launch commercial homepage. Replaces the beta/waitlist landing page.
import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import PageShell from './public/PageShell';
import EvidenceJourneyDemo from './public/demos/EvidenceJourneyDemo';
import DataToEmissionsDemo from './public/demos/DataToEmissionsDemo';
import EvidenceTraceabilityDemo from './public/demos/EvidenceTraceabilityDemo';
import DashboardDemo from './public/demos/DashboardDemo';

// Reveals the processing journey when it scrolls into view. Falls back to
// visible immediately for reduced-motion users and non-IntersectionObserver
// environments, so content is never gated on animation.
function useStageReveal() {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (
      typeof IntersectionObserver === 'undefined' ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      setInView(true);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setInView(true);
          io.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -48px 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return [ref, inView];
}

// Inline stroke icons for the five processing stages (lucide-style, 24px grid).
const STAGE_ICONS = {
  Collect: <path d="M3 13.5V19a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5.5M12 3v10m0 0 3.5-3.5M12 13 8.5 9.5" />,
  Extract: <path d="M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 16h6M10 10h1" />,
  Map: <><circle cx="6" cy="19" r="2" /><circle cx="18" cy="5" r="2" /><path d="M8 19h6c2 0 3-1 3-3s-1-3-3-3h-4c-2 0-3-1-3-3s1-3 3-3h6" /></>,
  Calculate: <><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01" /></>,
  'Validate & report': <><path d="M12 3l7 3v5c0 5-3 7.5-7 10-4-2.5-7-5-7-10V6z" /><path d="M9 12l2 2 4-4" /></>,
};

const StageIcon = ({ name }) => (
  <svg
    viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true" focusable="false"
  >
    {STAGE_ICONS[name]}
  </svg>
);

const BADGE = (label, kind) => <span className={`ct-badge ${kind ? `ct-badge-${kind}` : ''}`}>{label}</span>;

const PIPELINE = [
  { name: 'Collect', desc: 'Upload PDFs, images, CSVs and spreadsheets. Source files stay in private, org-scoped storage.' },
  { name: 'Extract', desc: 'Data is read from source documents — by you, by CarbonTally specialists, or with AI-assisted help — and reviewed by people before it moves on.' },
  { name: 'Map', desc: 'Records are matched to validated emission factors (e.g. DEFRA), with every candidate kept on the record.' },
  { name: 'Calculate', desc: 'Emissions are calculated by an authoritative engine; every result is snapshotted and traceable.' },
  { name: 'Validate & report', desc: 'Validation, customer review and quality-control checks precede structured reports and exports.' },
];

const PROBLEMS = [
  { icon: '🗂️', title: 'Messy source data', text: 'Invoices, PDFs, spreadsheets and scanned documents in different formats, units and levels of completeness.' },
  { icon: '🧮', title: 'Factor selection', text: 'Choosing and justifying the right emission factors across activities, fuels and supply chains.' },
  { icon: '🧾', title: 'Evidence burden', text: 'Regulators and auditors expect every number to trace back to a defensible source document.' },
  { icon: '⏱️', title: 'Operational grind', text: 'Manual data cleaning, mapping and calculation consumes the time that should go into reduction.' },
];

const SERVICES = [
  { title: 'Platform software', to: '/platform', text: 'The data-processing and accounting platform: collection, mapping, calculation, validation, evidence, reporting.' },
  { title: 'Processing services', to: '/processing-services', text: 'Self-service, assisted and managed processing options — choose how much of the work CarbonTally performs.' },
  { title: 'Consultant workflows', to: '/consultants', text: 'A dedicated workspace for consultants serving multiple client organisations, with white-label options.' },
  { title: 'Human processing services', to: '/processing-services', text: 'Specialist teams can help prepare, extract, structure and review emissions data when you need extra hands-on support.' },
];

const AUDIENCES = [
  { icon: '👤', title: 'Individuals & sole traders', text: 'A one-person business with fuel bills, mileage or utility data can get a structured, calculated footprint on a small plan — without a data team.' },
  { icon: '📈', title: 'Small & growing businesses', text: 'Teams that are outgrowing spreadsheets can collect source documents, map them to factors and produce traceable reports as they scale.' },
  { icon: '🏢', title: 'Organisations', text: 'Businesses that need to turn messy emissions data into calculated, evidenced, reportable results across sites and supply chains.' },
  { icon: '🤝', title: 'Consultants & advisers', text: 'Firms and individuals managing carbon data for multiple client organisations from one controlled workspace, with white-label options.' },
];

const PRICING_PREVIEW = [
  { name: 'Starter', price: '£49', per: '/ month', feat: ['3 team members', '100 credits / month', 'Self-service processing', 'Reports & evidence'] },
  { name: 'Professional', price: '£149', per: '/ month', feat: ['Up to 10 team members', '500 credits / month', 'Self-service processing', 'Everything in Starter'] },
  { name: 'Business', price: '£399', per: '/ month', feat: ['Up to 25 team members', '2,000 credits / month', 'Assisted + managed processing', 'API access', 'Everything in Professional'] },
  { name: 'Enterprise', price: 'Custom', per: '', feat: ['Custom volumes & credit bands', 'Dedicated processing capacity', 'White-label & custom terms'] },
];

export default function LandingPage() {
  const [stageRef, stageInView] = useStageReveal();

  return (
    <PageShell
      title="CarbonTally — Carbon Data Processing & Emissions Management Platform"
      description="CarbonTally turns messy carbon source data into structured, mapped, calculated and traceable emissions. A carbon data processing platform preparing for commercial launch."
    >
      {/* HERO */}
      <section className="ct-hero">
        <div className="ct-container ct-hero-grid">
          <div>
            <span className="ct-eyebrow">Carbon data processing infrastructure</span>
            <h1>Turn messy carbon data into <span className="ct-underline">traceable emissions.</span></h1>
            <p className="ct-lead">
              CarbonTally is a carbon accounting and data-processing platform that takes
              invoices, PDFs, spreadsheets and raw records — and turns them into mapped,
              calculated, validated and fully evidenced emissions data.
            </p>
            <div className="ct-hero-actions">
              <Link to="/contact" className="ct-btn ct-btn-primary">Request launch information</Link>
              <Link to="/platform" className="ct-btn ct-btn-secondary">Explore the platform</Link>
            </div>
            <p className="ct-hero-note">
              CarbonTally is preparing for commercial launch. Launch access is by arrangement
              with the CarbonTally team.
            </p>
          </div>

          <div className="ct-hero-visual">
            <p className="ct-visual-title">A single record, fully evidenced</p>
            <EvidenceJourneyDemo />
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Why emissions data is so hard to process</h2>
            <p>
              Most of the effort in carbon accounting is not calculation — it is the
              unglamorous work of getting messy, incomplete, inconsistent data into a
              form you can trust.
            </p>
          </div>
          <div className="ct-grid ct-grid-4">
            {PROBLEMS.map((p) => (
              <div className="ct-card" key={p.title}>
                <span className="ct-icon">{p.icon}</span>
                <h3>{p.title}</h3>
                <p>{p.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PROCESSING JOURNEY */}
      <section className="ct-section ct-section-journey">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>From source document to evidenced result</h2>
            <p>
              CarbonTally combines structured processing, human-in-the-loop review and
              end-to-end evidence traceability — so the number you report is the number
              you can prove.
            </p>
          </div>

          <div className={`ct-journey-stage${stageInView ? ' ct-inview' : ''}`} ref={stageRef}>
            <div className="ct-journey-track">
              {PIPELINE.map((s, i) => (
                <div className="ct-journey-step" key={s.name} style={{ '--i': i }}>
                  <span className="ct-journey-icon"><StageIcon name={s.name} /></span>
                  <span className="ct-journey-num">{String(i + 1).padStart(2, '0')}</span>
                  <h3>{s.name}</h3>
                  <p>{s.desc}</p>
                </div>
              ))}
            </div>

            <div className="ct-journey-divider">See it happen — one messy line, end to end</div>
            <DataToEmissionsDemo />
          </div>
        </div>
      </section>

      {/* SERVICES */}
      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>A complete service ecosystem</h2>
            <p>CarbonTally is software, processing services and an expert ecosystem — clearly separated so you know what you are buying.</p>
          </div>
          <div className="ct-grid ct-grid-2">
            {SERVICES.map((s) => (
              <div className="ct-card" key={s.title}>
                <h3><Link to={s.to}>{s.title} →</Link></h3>
                <p>{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PROCESSING OPTIONS */}
      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>Choose how much processing CarbonTally performs</h2>
          </div>
          <div className="ct-grid ct-grid-3">
            <div className="ct-card">
              <h3>Self-service</h3>
              <p>Your team uploads documents and drives processing inside the platform. Factor mapping, calculation, validation and reporting are handled by the platform.</p>
              <div className="ct-status-row">{BADGE('Available at launch', 'launch')}</div>
            </div>
            <div className="ct-card">
              <h3>Assisted processing</h3>
              <p>CarbonTally performs the extraction and preparation work on your behalf, with review checkpoints before results are finalised.</p>
              <div className="ct-status-row">{BADGE('Available at launch', 'launch')}</div>
            </div>
            <div className="ct-card">
              <h3>Managed processing</h3>
              <p>CarbonTally runs the end-to-end workflow — collection, extraction, mapping, calculation and reporting — as a managed service.</p>
              <div className="ct-status-row">{BADGE('Available at launch', 'launch')}</div>
            </div>
          </div>
          <p className="ct-note" style={{ marginTop: 20, textAlign: 'center' }}>
            Availability of assisted and managed processing depends on the subscription plan. See <Link to="/pricing">pricing</Link>.
          </p>
        </div>
      </section>

      {/* AUDIENCES */}
      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Built for everyone in the middle of carbon data</h2>
            <p>
              From a sole trader with a fuel card to an enterprise with fifty sites — the plans scale
              by team size and volume. Individual users and small businesses fit the smaller plans;
              consultants and managed-service customers add dedicated workflows.
            </p>
          </div>
          <div className="ct-grid ct-grid-4">
            {AUDIENCES.map((a) => (
              <div className="ct-card" key={a.title}>
                <span className="ct-icon">{a.icon}</span>
                <h3>{a.title}</h3>
                <p>{a.text}</p>
              </div>
            ))}
          </div>
          <p className="ct-note" style={{ marginTop: 20, textAlign: 'center' }}>
            Eligibility and plan limits follow the commercial model — see <Link to="/pricing">pricing</Link>.
          </p>
        </div>
      </section>

      {/* TRUST */}
      <section className="ct-section ct-section-accent">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>Evidence and security by design</h2>
            <p>Only factual claims — the properties built into the platform.</p>
          </div>
          <div className="ct-grid ct-grid-3">
            <div className="ct-card">
              <h3>End-to-end traceability</h3>
              <p>Every emission result can be traced to its source document, page and extraction item — with an append-only access audit trail.</p>
            </div>
            <div className="ct-card">
              <h3>Isolated data</h3>
              <p>Customer, consultant and specialist processing teams are kept fully separate, and documents are stored in private, organisation-scoped storage with short-lived access links.</p>
            </div>
            <div className="ct-card">
              <h3>Human-in-the-loop control</h3>
              <p>Processing passes through validation, customer review and quality-control gates before anything is presented as final.</p>
            </div>
          </div>

          <div className="ct-section-head center" style={{ marginTop: 36 }}>
            <h3 style={{ fontSize: '1.35rem', marginBottom: 2 }}>Trace one number back to its source</h3>
            <p>Every result can answer: where did this come from?</p>
          </div>
          <EvidenceTraceabilityDemo />
        </div>
      </section>

      {/* REPORTING RESULT */}
      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>From processed records to a reportable result</h2>
            <p>
              Approved records roll up into a footprint by scope, category and month — ready for
              reports, exports and the questions your stakeholders ask.
            </p>
          </div>
          <DashboardDemo />
          <p className="ct-note" style={{ marginTop: 16, textAlign: 'center' }}>
            Same sample dataset, one narrative: the invoice you saw processed earlier feeds the
            diesel line in this dashboard. Explore the <Link to="/platform">platform</Link> or{' '}
            <Link to="/processing-services">processing services</Link> for the steps in between.
          </p>
        </div>
      </section>

      {/* PRICING PREVIEW */}
      <section className="ct-section ct-section-muted">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>Indicative pricing</h2>
            <p>Four plans, one credit-based processing model. Indicative pricing is subject to final commercial terms.</p>
          </div>
          <div className="ct-pricing-grid">
            {PRICING_PREVIEW.map((p, i) => (
              <div className={`ct-plan${i === 2 ? ' featured' : ''}`} key={p.name}>
                {i === 2 && <span className="ct-plan-badge">Most popular</span>}
                <h3>{p.name}</h3>
                <div className="ct-plan-price">{p.price}</div>
                <div className="ct-plan-period">{p.per}</div>
                <ul>{p.feat.map((f) => <li key={f}>{f}</li>)}</ul>
                <Link to="/pricing" className="ct-btn ct-btn-secondary">View details</Link>
              </div>
            ))}
          </div>
          <p className="ct-note" style={{ marginTop: 24 }}>
            Indicative pricing shown for evaluation. There is no online checkout at this stage —
            launch access is by arrangement with the CarbonTally team. See <Link to="/pricing">full pricing</Link>.
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Preparing for commercial launch</h2>
          <p>
            Speak to the CarbonTally team about launch access, pilot programmes and the
            commercial model.
          </p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
