// frontend/src/v3/portal/ClientPortal.jsx
// CT-CONSULTANT-MODEL-IMPLEMENTATION-03 (F-7 / F-8 / PO-8 / PO-9 / PO-10).
//
// Plane C — the CLIENT portal at /portal/:clientId/* (PO-8 A). :clientId is the
// CLIENT ORGANISATION. The authenticated actor is a client user bound to that
// organisation by authorization, NOT by the URL.
//
// This shell grants nothing. Every call it makes is re-authorised server-side
// against the consultant relationship + the CLIENT ACCESS PROFILE, so a deep
// link to a foreign :clientId yields a generic, non-disclosing failure rather
// than data. There is deliberately NO mapping, factor, recalculation, user
// management, branding or billing control anywhere on this plane (PO-9/PO-2/
// PO-3A/PO-5) — those capabilities do not exist client-side.
import React, { useEffect, useState } from 'react';
import { NavLink, Route, Routes, useParams } from 'react-router-dom';
import {
  getPortalContext,
  getPortalOrganization,
  postPortalAnnotation,
  requestPortalRelationshipChange,
} from '../api';
import './portal.css';

const DENIED_MESSAGE = 'Client portal access is not available for this workspace';

function PortalNotice({ title, children }) {
  return (
    <div className="portal-notice">
      <h1>{title}</h1>
      <div>{children}</div>
    </div>
  );
}

function usePortalContext(clientId) {
  const [ctx, setCtx] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setCtx(await getPortalContext(clientId));
    } catch (e) {
      setError(e.message || DENIED_MESSAGE);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId]);

  return { ctx, error, loading, reload: load };
}

export default function ClientPortal() {
  const { clientId } = useParams();
  const { ctx, error, loading } = usePortalContext(clientId);

  if (loading) {
    return (
      <div className="portal-shell">
        <div className="portal-loading" role="status" aria-live="polite">
          Loading your workspace…
        </div>
      </div>
    );
  }

  if (error || !ctx) {
    // §11.4 / AC-F-17 — generic, non-disclosing. The support path is the
    // documented route for a client whose consultant has not given them portal
    // access (OQ-3).
    return (
      <div className="portal-shell">
        <PortalNotice title="This workspace is not available">
          <p>{DENIED_MESSAGE}.</p>
          <p className="portal-muted">
            If you believe you should have access, your consultant manages this
            workspace. For changes to or the end of a consultant relationship you
            can also contact CarbonTally support.
          </p>
        </PortalNotice>
      </div>
    );
  }

  const brand = ctx.brand || {};
  const firmLabel = ctx.consultant?.firm_name || 'Your consultant';
  const brandName = brand.display_name || firmLabel;

  return (
    <div className="portal-shell">
      <header className="portal-header">
        <div className="portal-brand">
          {brand.logo_url ? (
            <img src={brand.logo_url} alt={brandName} className="portal-logo" />
          ) : (
            <span
              className="portal-brand-text"
              style={{ color: brand.primary_color || undefined }}
            >
              {brandName}
            </span>
          )}
          <span className="portal-org">{ctx.organization.name}</span>
        </div>
        <nav className="portal-nav" aria-label="Client portal">
          <NavLink to={`/portal/${clientId}`} end>
            Overview
          </NavLink>
          <NavLink to={`/portal/${clientId}/relationship`}>Consultant relationship</NavLink>
        </nav>
      </header>

      {ctx.state === 'retained_read_only' && (
        <div className="portal-banner portal-banner-retained" role="status">
          Your engagement with {firmLabel} has ended. Your historical data has
          <strong> not </strong>
          been deleted and remains available read-only under our retention policy.
        </div>
      )}

      <main className="portal-main">
        <Routes>
          <Route index element={<PortalOverview clientId={clientId} ctx={ctx} />} />
          <Route
            path="relationship"
            element={<PortalRelationship clientId={clientId} ctx={ctx} />}
          />
          <Route
            path="*"
            element={
              <PortalNotice title="Not available">
                <p>{DENIED_MESSAGE}.</p>
              </PortalNotice>
            }
          />
        </Routes>
      </main>

      <footer className="portal-footer">
        <span className="portal-muted">
          {brand.footer_text || `${brandName} — client workspace`}
        </span>
      </footer>
    </div>
  );
}

function ProfileLabel({ profile }) {
  const labels = {
    off: 'No portal access',
    read_only: 'Read only',
    collaborative: 'Collaborative',
    managed: 'Managed by your consultant',
  };
  return <strong>{labels[profile] || profile}</strong>;
}

function PortalOverview({ clientId, ctx }) {
  const [org, setOrg] = useState(null);
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    getPortalOrganization(clientId)
      .then((data) => setOrg(data.organization))
      .catch(() => setOrg(null));
  }, [clientId]);

  const canComment = Boolean(ctx.capabilities?.comment);

  const submitAnnotation = async () => {
    if (!message.trim()) return;
    setStatus('Sending…');
    try {
      await postPortalAnnotation(clientId, message.trim());
      setMessage('');
      setStatus('Your comment has been sent to your consultant.');
    } catch (e) {
      setStatus(e.message || 'Unable to send your comment.');
    }
  };

  return (
    <div>
      <h1>{ctx.organization.name}</h1>
      <p className="portal-muted">
        Managed by {ctx.consultant.firm_name}. Your access profile is{' '}
        <ProfileLabel profile={ctx.profile} />.
      </p>

      <div className="portal-card">
        <h2>Organisation</h2>
        {org ? (
          <dl className="portal-dl">
            <dt>Name</dt>
            <dd>{org.name}</dd>
            <dt>Country</dt>
            <dd>{org.country || '—'}</dd>
            <dt>Status</dt>
            <dd>{org.is_active ? 'Active' : 'Inactive'}</dd>
          </dl>
        ) : (
          <p className="portal-muted">Organisation details are unavailable.</p>
        )}
      </div>

      <div className="portal-card">
        <h2>Comments and queries</h2>
        {canComment ? (
          <>
            <label htmlFor="portal-comment">Send a comment to your consultant</label>
            <textarea
              id="portal-comment"
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <div className="portal-actions">
              <button className="v3-btn primary" onClick={submitAnnotation} disabled={!message.trim()}>
                Send comment
              </button>
            </div>
            {status && <p className="portal-muted">{status}</p>}
          </>
        ) : (
          <p className="portal-muted">
            Commenting is not available for this workspace
            {ctx.state === 'retained_read_only' ? ' after the engagement has ended' : ''}.
          </p>
        )}
      </div>

      <div className="portal-card portal-muted">
        <h2>What you cannot do here</h2>
        <p>
          For data integrity and provenance, client users never map emission
          factors, edit mappings or trigger recalculations. Your consultant
          performs those steps. If you need a change, send a comment above.
        </p>
      </div>
    </div>
  );
}

function PortalRelationship({ clientId, ctx }) {
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);

  const request = async (requestType, label) => {
    // OQ-1 / T-1 — an explicit confirmation is required; the action creates a
    // REQUEST and never destroys the relationship.
    // eslint-disable-next-line no-alert
    if (!window.confirm(
      `${label}? This sends a request to CarbonTally. Your data is not deleted and your consultant relationship is not changed until the request is confirmed.`
    )) return;
    setBusy(true);
    setStatus('');
    try {
      await requestPortalRelationshipChange(clientId, requestType, null);
      setStatus(
        'Your request has been submitted to CarbonTally. You will be contacted to confirm it.'
      );
    } catch (e) {
      setStatus(e.message || 'Unable to submit your request.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h1>Consultant relationship</h1>
      <div className="portal-card">
        <dl className="portal-dl">
          <dt>Consultant firm</dt>
          <dd>{ctx.consultant.firm_name}</dd>
          <dt>Relationship status</dt>
          <dd>{ctx.state === 'retained_read_only' ? 'Ended (retained read-only)' : 'Active'}</dd>
          <dt>Your access profile</dt>
          <dd><ProfileLabel profile={ctx.profile} /></dd>
          <dt>Workspace</dt>
          <dd>{ctx.organization.name}</dd>
        </dl>
      </div>

      {ctx.state === 'retained_read_only' ? (
        <div className="portal-card">
          <p className="portal-muted">
            This engagement has ended. Your historical data has not been deleted.
            To reconnect with a consultant, contact CarbonTally support.
          </p>
        </div>
      ) : (
        <div className="portal-card">
          <h2>Request a change</h2>
          <p className="portal-muted">
            These actions create a request. Nothing is changed until the request
            is confirmed.
          </p>
          <div className="portal-actions">
            <button
              className="v3-btn"
              onClick={() => request('change_consultant', 'Request a change of consultant')}
              disabled={busy}
            >
              Request change of consultant
            </button>
            <button
              className="v3-btn"
              onClick={() => request('end_relationship', 'Request to end the consultant relationship')}
              disabled={busy}
            >
              Request to end consultant relationship
            </button>
          </div>
          {status && <p className="portal-muted" role="status">{status}</p>}
        </div>
      )}
    </div>
  );
}
