// frontend/src/v3/components/CapabilityTruthSurface.jsx
// P17-L — the ONE governed capability truth surface, shared by the customer
// product surface and the investor surface (CT-PO-P17-DECISION-03 §6/§14).
//
// Governance this component encodes:
//
//  * It renders ONLY what the canonical projection sent it. It owns no
//    capability fact, no category→status table and no vocabulary of its own
//    (§5: "Do not hardcode the 15 category capability statuses in frontend
//    code"). The governed value is always quoted VERBATIM and is the claim
//    (IV-2); the explanation comes from the payload's glossary (IV-3).
//  * It never renders an Axis-A architecture status. Those tokens are not in
//    the payload at all — the backend projection refuses to emit them — and
//    nothing here fabricates a status token (IV-1, F-3, AG-3).
//  * It never renders a figure, a zero, a placeholder or a total. A requirement
//    with no result renders as an explicit absence statement, never as 0
//    (F-6, S3-5, AG-4).
//  * The Scope 3 summary is the FOUR-WAY rollup, never a coverage percentage
//    and never "all 15 categories" (S3-1, AG-7).
//  * Provenance is always shown, including the explicit unresolved-source
//    marker (AG-8, §12).
//
// This is presentation only; the API remains the authority.
import React from 'react';
import Alert from './ui/Alert';
import Badge from './ui/Badge';
import Icon from './ui/Icon';

// Presentation tone per governed value (D21 status tone). This map is
// PRESENTATION ONLY: it never renames, reorders, promotes or hides a value.
// A limitation is rendered as prominently as a strength (IN-3, F-9), and an
// unrecognised value falls back to a neutral presentation rather than being
// dropped (IV-4: say less, never something invented).
const TONE_BY_CAPABILITY = {
  SUPPORTED: { tone: 'success', icon: 'checkCircle' },
  PARTIALLY_SUPPORTED: { tone: 'warning', icon: 'alert' },
  STRUCTURED_INPUT_REQUIRED: { tone: 'info', icon: 'info' },
  EXTERNAL_INPUT_REQUIRED: { tone: 'info', icon: 'info' },
  MISSING_CAPABILITY: { tone: 'error', icon: 'xCircle' },
  FUTURE: { tone: 'warning', icon: 'clock' },
  NOT_APPLICABLE_TO_PRODUCT: { tone: 'muted', icon: 'info' },
};
const NEUTRAL_TONE = { tone: 'muted', icon: 'info' };

export function capabilityTone(value) {
  return TONE_BY_CAPABILITY[value] || NEUTRAL_TONE;
}

export function Provenance({ provenance }) {
  if (!provenance) return null;
  const unresolved = provenance.identifier_status !== 'RESOLVED';
  return (
    <div className="ct-capability__provenance">
      {provenance.source_locator && (
        <div className="ct-capability__source">{provenance.source_locator}</div>
      )}
      {provenance.source_tier !== null && provenance.source_tier !== undefined && (
        <div className="ct-capability__tier">Source tier {provenance.source_tier}</div>
      )}
      {unresolved && (
        <div className="ct-capability__unresolved">
          Authoritative identifier unresolved: no official identifier is asserted for this
          requirement (authoritative-source limitation).
        </div>
      )}
    </div>
  );
}

export function CapabilityClaim({ requirement }) {
  const { tone, icon } = capabilityTone(requirement.carbontally_capability);
  return (
    <div className="ct-capability__claim">
      <Badge tone={tone} icon={icon}>
        {requirement.carbontally_capability}
      </Badge>
      <p className="ct-capability__explanation">{requirement.capability_explanation}</p>
      {requirement.capability_detail && (
        <p className="ct-capability__detail">{requirement.capability_detail}</p>
      )}
      <Provenance provenance={requirement.provenance} />
    </div>
  );
}

export function CapabilityRollup({ rollup, basis }) {
  const entries = Object.entries(rollup || {});
  return (
    <section className="ct-capability__rollup" aria-labelledby="ct-capability-rollup-title">
      <h2 id="ct-capability-rollup-title" className="ct-capability__section-title">
        Scope 3 capability — the four-way split
      </h2>
      <p className="ct-capability__rollup-note">{basis}</p>
      <ul className="ct-capability__rollup-list">
        {entries.map(([value, count]) => {
          const { tone, icon } = capabilityTone(value);
          return (
            <li key={value} className="ct-capability__rollup-item">
              <Badge tone={tone} icon={icon}>
                {value}
              </Badge>
              <span className="ct-capability__rollup-count">{count}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function CapabilityGlossary({ glossary, vocabulary }) {
  if (!glossary.length) return null;
  const governed = new Set(vocabulary || []);
  return (
    <section className="ct-capability__glossary" aria-labelledby="ct-capability-glossary-title">
      <h2 id="ct-capability-glossary-title" className="ct-capability__section-title">
        The governed capability vocabulary
      </h2>
      <p className="ct-capability__rollup-note">
        Every capability value on this page is quoted verbatim from this governed vocabulary.
        Explanations accompany a value; they never replace it.
      </p>
      <dl className="ct-capability__glossary-list">
        {glossary.map((entry) => {
          const { tone, icon } = capabilityTone(entry.value);
          return (
            <div key={entry.value} className="ct-capability__glossary-entry">
              <dt>
                <Badge tone={governed.has(entry.value) ? tone : 'error'} icon={icon}>
                  {entry.value}
                </Badge>
              </dt>
              <dd>{entry.explanation}</dd>
            </div>
          );
        })}
      </dl>
    </section>
  );
}

export function Scope3Table({ requirements }) {
  return (
    <section className="ct-capability__scope3" aria-labelledby="ct-capability-scope3-title">
      <h2 id="ct-capability-scope3-title" className="ct-capability__section-title">
        Scope 3 categories 1–15
      </h2>
      <table className="ct-capability__table">
        <caption>
          CarbonTally capability per Scope 3 category. This states what the product supports; it
          is not an applicability or materiality assessment for any organisation.
        </caption>
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">Requirement</th>
            <th scope="col">CarbonTally capability</th>
            <th scope="col">What that means, and what it depends on</th>
            <th scope="col">Provenance</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((item) => {
            const { tone, icon } = capabilityTone(item.carbontally_capability);
            return (
              <tr key={item.requirement_code} data-requirement={item.requirement_code}>
                <th scope="row">{item.scope3_category}</th>
                <td>{item.requirement_name}</td>
                <td>
                  <Badge tone={tone} icon={icon}>
                    {item.carbontally_capability}
                  </Badge>
                </td>
                <td>
                  <p className="ct-capability__explanation">{item.capability_explanation}</p>
                  {item.capability_detail && (
                    <p className="ct-capability__detail">{item.capability_detail}</p>
                  )}
                  <p className="ct-capability__absence">
                    No result is stated here for any organisation.
                  </p>
                </td>
                <td>
                  <Provenance provenance={item.provenance} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}


export function Scope2Panel({ requirements }) {
  if (!requirements.length) return null;
  return (
    <section className="ct-capability__scope2" aria-labelledby="ct-capability-scope2-title">
      <h2 id="ct-capability-scope2-title" className="ct-capability__section-title">
        Scope 2 — by method
      </h2>
      <p className="ct-capability__rollup-note">
        The method is part of a result's identity and is never inferred. Each method is stated
        separately; a method is never implied from another method's support.
      </p>
      <div className="ct-capability__scope2-grid">
        {requirements.map((item) => (
          <article key={item.requirement_code} data-requirement={item.requirement_code}>
            <h3 className="ct-capability__subsection-title">
              {item.scope2_method === 'MARKET_BASED' ? 'Market-based' : 'Location-based'}
            </h3>
            <CapabilityClaim requirement={item} />
            <p className="ct-capability__absence">
              No result is stated here for any organisation.
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function Scope1Panel({ requirements }) {
  if (!requirements.length) return null;
  return (
    <section className="ct-capability__scope1" aria-labelledby="ct-capability-scope1-title">
      <h2 id="ct-capability-scope1-title" className="ct-capability__section-title">
        Scope 1
      </h2>
      {requirements.map((item) => (
        <article key={item.requirement_code} data-requirement={item.requirement_code}>
          <h3 className="ct-capability__subsection-title">{item.requirement_name}</h3>
          <CapabilityClaim requirement={item} />
          <p className="ct-capability__absence">No result is stated here for any organisation.</p>
        </article>
      ))}
    </section>
  );
}

export default function CapabilityTruthSurface({ payload, audience = 'customer' }) {
  const requirements = payload.requirements || [];
  const scope3 = requirements
    .filter((item) => item.scope3_category !== null && item.scope3_category !== undefined)
    .slice()
    .sort((a, b) => a.scope3_category - b.scope3_category);
  const scope2 = requirements.filter((item) => item.scope2_method);
  const scope1 = requirements.filter((item) => item.scope === 'Scope 1');
  const isInvestor = audience === 'investor';

  return (
    <div className="ct-capability" data-audience={audience}>
      <header className="ct-capability__head">
        <h1 className="ct-capability__title">
          {isInvestor ? 'CarbonTally product capabilities' : 'What CarbonTally supports'}
        </h1>
        <p className="ct-capability__subtitle">
          Product-level capability for{' '}
          <strong>{(payload.framework && payload.framework.name) || 'the governed framework'}</strong>
          {payload.framework_version && payload.framework_version.version_label ? (
            <>
              {' '}
              — {payload.framework_version.version_label} (
              {payload.framework_version.status})
            </>
          ) : null}
          . These are facts about the product: they are not statements about any organisation,
          and not a statement about which requirements apply to anyone.
        </p>
        {payload.framework_version && payload.framework_version.source_url && (
          <p className="ct-capability__framework-source">
            Authority source:{' '}
            <a href={payload.framework_version.source_url} target="_blank" rel="noreferrer noopener">
              {payload.framework_version.source_url}
              <Icon name="external" size={12} aria-hidden="true" />
            </a>
            {payload.framework_version.source_tier !== null &&
              payload.framework_version.source_tier !== undefined && (
                <> (source tier {payload.framework_version.source_tier})</>
              )}
          </p>
        )}
      </header>

      <Alert tone="info" title="Capability is not a result">
        {payload.result_presence_note}
      </Alert>

      {!isInvestor && (
        <p className="ct-capability__where">
          Your own calculated results live on your <a href="/emissions">Emissions</a> and{' '}
          <a href="/reports">Reports</a> pages. This page never states a result for your
          organisation, so a requirement listed here without a result of yours is not an
          unsupported requirement.
        </p>
      )}

      <CapabilityRollup
        rollup={payload.scope3_capability_rollup}
        basis={payload.scope3_rollup_basis}
      />
      <Scope1Panel requirements={scope1} />
      <Scope2Panel requirements={scope2} />
      <Scope3Table requirements={scope3} />
      <CapabilityGlossary
        glossary={payload.capability_glossary || []}
        vocabulary={payload.capability_vocabulary || []}
      />

      <p className="ct-capability__footnote">
        Nothing on this page is a compliance conclusion, a materiality assessment or a coverage
        figure, and no figure on this page is an emissions result.
      </p>
    </div>
  );
}

