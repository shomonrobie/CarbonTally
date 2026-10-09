// frontend/src/v3/customer/ManualProcessingPage.jsx
// CT-MP-SUB-004 — Customer Manual Processing service state (CT-UX-MP-SUB-003 §3, §7).
//
// The customer sees their OWN organisation's effective service state — never the
// consultant's purchased capacity, another client, an allocation id or an
// internal routing id (§3, §6 Visibility, §10 criterion 11).
//
// The organisation id is resolved server-side (resolveV3Organization) and the
// endpoint re-enforces exact-tenant scope (require_org_member), so this page
// cannot be pointed at another organisation from the browser.
//
// Commercial entitlement stays SEPARATE from operational readiness (§1/§10
// criteria 12/13): an entitled-but-not-yet-configured customer must never be
// shown as "not subscribed".
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyManualProcessing, resolveV3Organization } from '../api';
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-09/UX-13) — when this page is
// rendered inside the consultant CLIENT OPERATING PLANE the same component must
// keep the user in the consultant FIRM commercial context, not the client's.
import { useConsultantClientContext } from '../consultant/ConsultantClientContext';
import Badge from '../components/ui/Badge';
import Alert from '../components/ui/Alert';
import { Card } from '../components/ui/Card';
import { ErrorState, LoadingState } from '../components/ui/StateViews';

const SOURCE_LABEL = {
  direct: 'Direct subscription',
  sponsored: 'Consultant-sponsored coverage',
};

export default function ManualProcessingPage() {
  const [org, setOrg] = useState(null);
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  // true only inside /consultant/clients/:clientId/* (the client plane). Never an
  // authorisation — presentation context used only to choose correct copy/CTA.
  const consultantContext = useConsultantClientContext();
  const inConsultantPlane = !!consultantContext.active;

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const organization = await resolveV3Organization();
      if (!organization) {
        setError('No organisation is linked to this account.');
        setOrg(null);
        setState(null);
        return;
      }
      setOrg(organization);
      const data = await getMyManualProcessing(organization.id);
      setState(data);
    } catch (e) {
      setState(null);
      setError(e.message || 'Unable to load Manual Processing.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, attempt]);

  if (loading) return <LoadingState label="Loading Manual Processing…" />;

  if (error && !state) {
    return <ErrorState message={error} onRetry={() => setAttempt((n) => n + 1)} />;
  }

  if (!state) return null;

  const entitled = !!state.effective_entitled;
  const direct = !!state.direct_entitled;
  const sponsored = !!state.sponsored_entitled;
  const both = direct && sponsored;
  const configured = state.operational_status === 'configured';
  const governanceEnabled = !!(state.governance && state.governance.enabled);
  const consultantName = state.consultant && state.consultant.company_name;
  const outcome = state.effective ? state.effective.outcome : null;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Manual Processing</h1>
      </div>

      <Card
        title="Manual Processing"
        actions={
          <Badge tone={entitled ? 'success' : 'muted'}>
            {entitled ? 'AVAILABLE' : 'NOT INCLUDED'}
          </Badge>
        }
      >
        {!entitled ? (
          <>
            <p>
              Manual Processing is not included in{' '}
              {inConsultantPlane
                ? 'this client’s current commercial coverage.'
                : 'your current commercial coverage.'}
            </p>
            {inConsultantPlane ? (
              <p className="v3-muted">
                Manual Processing for a consultant-managed client is arranged through
                your FIRM&apos;s commercial coverage with CarbonTally, not the client&apos;s
                own subscription. When your firm&apos;s coverage includes this client it
                will appear here.
              </p>
            ) : (
              <p className="v3-muted">
                It is not currently available through your commercial coverage.
                CarbonTally Support can confirm what your plan includes.
              </p>
            )}
            {/* CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-09/UX-13, AC-12/AC-13):
                /billing is an organisation-only route (RoleRoute requireOrg), so a
                consultant who followed the old absolute link was bounced to
                /consultant via the guard's fallback. In the client plane the CTA
                must stay in the consultant FIRM commercial context instead. */}
            <Link
              className="v3-btn v3-btn-primary"
              to={inConsultantPlane ? '/consultant?view=coverage' : '/billing'}
            >
              {inConsultantPlane ? 'View firm coverage & plans' : 'View available plans'}
            </Link>
          </>
        ) : both ? (
          <>
            <p style={{ marginTop: 0 }}>Your coverage includes:</p>
            <ul style={{ marginTop: 4 }}>
              <li>Direct subscription</li>
              <li>Consultant-sponsored coverage</li>
            </ul>
            <table className="v3-table">
              <tbody>
                <tr>
                  <th scope="row">Effective entitlement</th>
                  <td>AVAILABLE</td>
                </tr>
                <tr>
                  <th scope="row">Processing mode</th>
                  <td>Manual Processing</td>
                </tr>
                <tr>
                  <th scope="row">Processing Entity</th>
                  <td>{configured ? 'Configured' : 'Not configured'}</td>
                </tr>
                <tr>
                  <th scope="row">Governance status</th>
                  <td>{governanceEnabled ? 'Active' : 'Inactive'}</td>
                </tr>
              </tbody>
            </table>
            <p className="v3-muted">
              Both commercial paths support one operational Manual Processing
              service, not two.
            </p>
          </>
        ) : (
          <table className="v3-table">
            <tbody>
              <tr>
                <th scope="row">Status</th>
                <td>AVAILABLE</td>
              </tr>
              <tr>
                <th scope="row">Coverage</th>
                <td>
                  {direct
                    ? 'Included in your subscription'
                    : 'Provided through your consultant'}
                </td>
              </tr>
              {sponsored && (
                <tr>
                  <th scope="row">Consultant</th>
                  <td>{consultantName || 'Your consultant'}</td>
                </tr>
              )}
              <tr>
                <th scope="row">Processing mode</th>
                <td>Manual Processing</td>
              </tr>
              <tr>
                <th scope="row">Processing Entity</th>
                <td>
                  {sponsored && !direct
                    ? (configured ? 'Configured separately' : 'Not configured')
                    : (configured ? 'Configured' : 'Not configured')}
                </td>
              </tr>
              <tr>
                <th scope="row">Governance status</th>
                <td>{governanceEnabled ? 'Active' : 'Inactive'}</td>
              </tr>
              {(state.coverage_sources || []).map((source) => (
                <tr key={source}>
                  <th scope="row">Coverage source</th>
                  <td>{SOURCE_LABEL[source] || source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {entitled && !configured && (
        <Alert tone="info" title="Commercially entitled, not yet configured">
          <p style={{ margin: 0 }}>
            Commercial entitlement: <strong>AVAILABLE</strong>
          </p>
          <p style={{ margin: '4px 0 0' }}>
            Operational status: <strong>NOT YET CONFIGURED</strong>
          </p>
          <p style={{ margin: '4px 0 0' }}>
            Processing Entity: <strong>Not configured</strong>
          </p>
          <p style={{ margin: '8px 0 0' }}>
            Your Manual Processing coverage is active, but operational processing
            configuration is not yet complete. This is not the same as not being
            subscribed.
          </p>
        </Alert>
      )}

      {entitled && configured && outcome === 'not_enabled' && (
        <Alert tone="warning" title="Processing not yet enabled">
          Your coverage is active and a Processing Entity is configured, but Manual
          Processing has not been enabled for your organisation yet.
        </Alert>
      )}

      <Card title="What this means">
        <p className="v3-muted" style={{ marginTop: 0 }}>
          Commercial coverage decides whether Manual Processing is available to your
          organisation. Operational configuration — governance, and the Processing
          Entity that performs the work — decides whether it is actually running.
          These are separate.
        </p>
        {!entitled && (
          <p className="v3-muted">
            Coverage for your organisation is a commercial arrangement: if your
            consultant or CarbonTally has arranged Manual Processing for you, it will
            appear here.
          </p>
        )}
        {org && (
          <p className="v3-muted" style={{ marginBottom: 0 }}>
            Organisation: {org.name || org.id}
          </p>
        )}
      </Card>
    </div>
  );
}
