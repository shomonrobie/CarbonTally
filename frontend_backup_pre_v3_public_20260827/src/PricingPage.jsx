// frontend/src/PricingPage.jsx
// Pre-launch planned pricing. Reflects the configured D37 commercial model
// (versioned plans, credit bands, assisted pricing). No online checkout —
// CarbonTally is preparing for commercial launch and access is by arrangement.
import React from 'react';
import { Link } from 'react-router-dom';
import PageShell from './public/PageShell';

const PLANS = [
  {
    name: 'Starter',
    price: '£49',
    period: '/ month',
    blurb: 'Entry plan for smaller organisations.',
    features: ['3 team members', '100 credits per month', 'Self-service processing', 'Reports and evidence', 'Standard storage allowance (20 GB)'],
    featured: false,
  },
  {
    name: 'Professional',
    price: '£149',
    period: '/ month',
    blurb: 'Standard plan for growing teams.',
    features: ['Up to 10 team members', '500 credits per month', 'Self-service processing', 'Reports and evidence', 'Larger storage allowance'],
    featured: false,
  },
  {
    name: 'Business',
    price: '£399',
    period: '/ month',
    blurb: 'High-volume plan with managed options.',
    features: ['Up to 25 team members', '2,000 credits per month', 'Assisted and managed processing', 'API access', 'Large storage allowance (500 GB)', 'Dedicated support'],
    featured: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    blurb: 'Custom plan — quoted.',
    features: ['Custom credit bands and volumes', 'Dedicated processing capacity', 'White-label and custom terms'],
    featured: false,
  },
];

const CREDIT_BANDS = [
  { label: 'Simple', detail: 'Standard invoices and utilities', price: '1 credit per unit' },
  { label: 'Standard', detail: 'Typical commercial documents', price: '2 credits per unit' },
  { label: 'Complex', detail: 'Multi-line, mixed-unit documents', price: '4 credits per unit' },
  { label: 'Exceptional', detail: 'Unusual or very complex documents', price: 'Quoted' },
];

export default function PricingPage() {
  return (
    <PageShell
      title="Pricing — CarbonTally"
      description="CarbonTally pricing: Starter, Professional, Business and Enterprise plans with a credit-based processing model. Pricing is subject to final commercial terms."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>Indicative pricing</h1>
          <p>
            CarbonTally is preparing for commercial launch. The plans below are shown for
            evaluation — final terms will be confirmed at launch.
          </p>
          <p className="ct-note" style={{ marginTop: 14 }}>
            No online checkout is available at this stage. Access is by arrangement with
            the CarbonTally team.
          </p>
        </div>
      </section>

      {/* PLANS */}
      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-pricing-grid">
            {PLANS.map((p) => (
              <div className={`ct-plan${p.featured ? ' featured' : ''}`} key={p.name}>
                {p.featured && <span className="ct-plan-badge">Most popular</span>}
                <h3>{p.name}</h3>
                <p className="ct-note" style={{ minHeight: 34 }}>{p.blurb}</p>
                <div className="ct-plan-price">{p.price}</div>
                <div className="ct-plan-period">{p.period}</div>
                <ul>{p.features.map((f) => <li key={f}>{f}</li>)}</ul>
                <Link to="/contact" className="ct-btn ct-btn-secondary">Discuss at launch</Link>
              </div>
            ))}
          </div>
          <p className="ct-note" style={{ marginTop: 24 }}>
            Plan pricing shown here is indicative and is subject to final commercial
            terms. Processing credits, storage and features vary by plan.
          </p>
        </div>
      </section>

      {/* CREDIT MODEL */}
      <section className="ct-section ct-section-alt">
        <div className="ct-container">
          <div className="ct-section-head center">
            <h2>How the credit model works</h2>
            <p>
              Processing is measured in credits. Documents are classified by complexity,
              and each processed unit consumes credits from your monthly allowance.
            </p>
          </div>
          <div className="ct-grid ct-grid-4">
            {CREDIT_BANDS.map((b) => (
              <div className="ct-card" key={b.label}>
                <h3>{b.label}</h3>
                <p>{b.detail}</p>
                <p style={{ marginTop: 10, fontWeight: 600, color: 'var(--ct-ink)' }}>{b.price}</p>
              </div>
            ))}
          </div>
          <p className="ct-note" style={{ marginTop: 20 }}>
            Assisted processing is priced per document band (from £0.99 per unit). Managed
            processing is quoted per engagement.
          </p>
        </div>
      </section>

      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Want to plan your launch subscription?</h2>
          <p>Tell us your volumes and we will map them to the right plan.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}
