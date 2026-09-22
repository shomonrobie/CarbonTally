// frontend/src/v3/insight/InsightReferences.jsx
// CarbonTally Insight I6 — evidence/provenance reference presentation.
//
// References are rendered as **locators** (PO I6-4). The UI makes no access
// decision: opening a reference calls the ratified I3 read-only tool surface,
// which re-authorizes the caller against the resolved object. Success renders
// the backend's allowlisted projection; every other outcome (and any thrown
// error) renders one non-disclosing state that reveals nothing about whether
// the protected resource exists.
import React, { useState } from 'react';
import Button from '../components/ui/Button';
import Icon from '../components/ui/Icon';
import { invokeInsightTool } from '../api';
import {
  REFERENCE_UNAVAILABLE,
  REFERENCE_UNRESOLVABLE,
  projectEvidenceRows,
  referenceKindLabel,
  referenceLabel,
  referenceResolver,
  resolutionPresentation,
  shortReferenceId,
} from './references';
import './insight.css';

const IDLE = 'idle';

/**
 * One reference locator plus its (re-authorized) resolution.
 *
 * Exported for direct testing of the non-disclosing states.
 */
export function InsightReference({ reference, organizationId }) {
  const [state, setState] = useState(IDLE);
  const [result, setResult] = useState(null);

  if (!reference || !reference.id) return null;

  const kind = reference.kind;
  const id = reference.id;
  const kindLabel = referenceKindLabel(kind);
  const resolver = referenceResolver(kind, id);

  const open = async () => {
    if (!resolver) return;
    setState('loading');
    setResult(null);
    try {
      const response = await invokeInsightTool(organizationId, resolver.tool, resolver.input);
      // `no_data` / `not_authorized` / `invalid_input` / `provider_unavailable` /
      // `error` all collapse into one non-disclosing state (never "it exists" /
      // "it doesn't") through the shared mapping.
      if (resolutionPresentation(response) === null) {
        setResult(response);
        setState('resolved');
      } else {
        setState('unavailable');
      }
    } catch (_error) {
      // A 404 for a foreign resource is a non-disclosing answer by design.
      setState('unavailable');
    }
  };

  const projection = result ? projectEvidenceRows(result.data) : { rows: [], collections: [] };

  return (
    <li className="ct-insight-ref" data-testid="insight-reference" data-reference-kind={kind}>
      <div className="ct-insight-ref__locator">
        <Icon name="tag" size={14} aria-hidden="true" />
        <span className="ct-insight-ref__kind">{kindLabel}</span>
        <code className="ct-insight-ref__id" title={id}>{shortReferenceId(id)}</code>
      </div>

      {resolver ? (
        <Button
          size="sm"
          variant="ghost"
          onClick={open}
          loading={state === 'loading'}
          aria-label={`Open ${referenceLabel(reference)}`}
        >
          Open reference
        </Button>
      ) : (
        <div className="ct-insight-ref__note" data-testid="insight-reference-unresolvable">
          <span className="ct-insight-ref__note-title">{REFERENCE_UNRESOLVABLE.title}.</span>{' '}
          {REFERENCE_UNRESOLVABLE.body}
        </div>
      )}

      {state === 'unavailable' && (
        <div className="ct-insight-ref__note" data-testid="insight-reference-unavailable">
          <span className="ct-insight-ref__note-title">{REFERENCE_UNAVAILABLE.title}.</span>{' '}
          {REFERENCE_UNAVAILABLE.body}
        </div>
      )}

      {state === 'resolved' && (
        <div className="ct-insight-ref__resolved" data-testid="insight-reference-resolved">
          {projection.rows.length > 0 && (
            <dl className="ct-insight-ref__rows">
              {projection.rows.map((row) => (
                <React.Fragment key={row.key}>
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </React.Fragment>
              ))}
            </dl>
          )}
          {projection.collections.length > 0 && (
            <ul className="ct-insight-ref__counts">
              {projection.collections.map((collection) => (
                <li key={collection.key}>
                  {collection.label}: {collection.detail || `${collection.count}`}
                </li>
              ))}
            </ul>
          )}
          {projection.rows.length === 0 && projection.collections.length === 0 && (
            <p className="v3-muted">CarbonTally returned no displayable fields for this reference.</p>
          )}
        </div>
      )}
    </li>
  );
}

export default function InsightReferences({ references = [], organizationId, headingId }) {
  if (!references.length) return null;

  return (
    <section className="ct-insight-refs" aria-labelledby={headingId}>
      <h4 id={headingId} className="ct-insight-refs__title">
        <Icon name="evidence" size={15} aria-hidden="true" />
        {`Provenance references (${references.length})`}
      </h4>
      <p className="v3-muted ct-insight-refs__note">
        These identify the CarbonTally records behind the answer. They are locators, not access:
        CarbonTally authorizes each one again whenever it is opened.
      </p>
      <ul className="ct-insight-refs__list">
        {references.map((reference, index) => (
          <InsightReference
            key={`${reference && reference.kind}:${reference && reference.id}:${index}`}
            reference={reference}
            organizationId={organizationId}
          />
        ))}
      </ul>
    </section>
  );
}
