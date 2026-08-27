// frontend/src/public/ContactPage.jsx
// Pre-launch contact page. CarbonTally is not accepting customers yet, so
// there is no signup or waitlist form. The contact path is a real mailto
// link with a structured subject/body — a functioning mechanism with no
// backend dependency. No submissions are silently discarded.
import React from 'react';
import PageShell from './PageShell';

const EMAIL = 'hello@carbontally.co.uk';

function buildMailto(subject, body) {
  return `mailto:${EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

const TOPICS = [
  {
    title: 'Launch access & pilots',
    subject: 'Launch access enquiry — CarbonTally',
    body: 'Hello CarbonTally team,\n\nI would like to learn more about launch access and pilot programmes for my organisation.\n\nOrganisation:\nSector:\nWhat we need help with:',
  },
  {
    title: 'Consultant onboarding',
    subject: 'Consultant onboarding enquiry — CarbonTally',
    body: 'Hello CarbonTally team,\n\nI am a carbon consultant and would like to understand how CarbonTally supports consultant firms.\n\nFirm:\nNumber of clients:',
  },
  {
    title: 'General enquiry',
    subject: 'Enquiry — CarbonTally',
    body: 'Hello CarbonTally team,\n\nWrite your message here.',
  },
];

export default function ContactPage() {
  return (
    <PageShell
      title="Contact — CarbonTally"
      description="Contact CarbonTally about launch access, pilot programmes, consultant onboarding and the commercial model."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>Contact CarbonTally</h1>
          <p>
            CarbonTally is preparing for commercial launch. There is no open signup at
            this stage — the fastest way to reach the team is email.
          </p>
        </div>
      </section>

      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-section-head">
            <h2>Start an email with the right template</h2>
            <p>Clicking a card opens your email client with the message pre-filled. Nothing is submitted to a form — nothing is lost.</p>
          </div>
          <div className="ct-grid ct-grid-3">
            {TOPICS.map((t) => (
              <a
                key={t.title}
                href={buildMailto(t.subject, t.body)}
                className="ct-card"
                style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}
              >
                <h3>{t.title}</h3>
                <p style={{ marginTop: 8, fontSize: 14 }}>Opens your email client addressed to {EMAIL}.</p>
              </a>
            ))}
          </div>

          <div style={{ marginTop: 40, border: '1px solid var(--ct-line)', borderRadius: 14, padding: 28 }}>
            <h3 style={{ margin: '0 0 10px' }}>Prefer to write directly?</h3>
            <p style={{ fontSize: 15, color: 'var(--ct-ink-soft)', margin: '0 0 8px' }}>
              Email <a href={`mailto:${EMAIL}`}>{EMAIL}</a> — we aim to respond within a few working days.
            </p>
            <p className="ct-note" style={{ marginTop: 12 }}>
              Launch pricing, timing and availability are subject to final commercial terms and will be
              confirmed with you directly.
            </p>
          </div>
        </div>
      </section>
    </PageShell>
  );
}
