// frontend/src/v3/components/RoleRoute.jsx
// D25 — frontend role-route guards.
//
// The backend/RLS remain the authoritative security boundary; these guards are
// UX/navigation only: they stop an actor from landing on a workspace they do
// not have, and redirect to an appropriate home. Guards never grant access.
//
// Phase 3 / P1-B — actor roles are resolved from the single server-authoritative
// /api/v3/me/context endpoint. A resolution failure is FAIL-CLOSED: the guard
// shows a controlled error/retry state instead of silently redirecting an
// existing user (previously a probe failure could bounce users to the public
// site or organisation onboarding).
import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { getMeContext } from '../api';

export function useActorRoles() {
  const [roles, setRoles] = useState({
    org: null,
    isStaff: false,
    isConsultant: false,
    isNewUser: false,
    loaded: false,
    failed: false,
  });

  useEffect(() => {
    let active = true;
    getMeContext()
      .then((context) => {
        if (!active) return;
        const destination = context.destination || context.primary_workspace;
        setRoles({
          org: context.actor_type === 'customer' ? context.organization || true : null,
          isStaff: context.actor_type === 'staff' || context.actor_type === 'entity_staff',
          isConsultant: context.actor_type === 'consultant',
          isNewUser: destination === '/onboarding',
          loaded: true,
          failed: false,
        });
      })
      .catch(() => {
        if (!active) return;
        setRoles((prev) => ({ ...prev, loaded: true, failed: true }));
      });
    return () => { active = false; };
  }, []);

  return roles;
}

/**
 * Role-gated route wrapper.
 * - `requireOrg`:  caller must be an active organisation member (customer)
 * - `requireStaff`: caller must be an active staff profile
 * - `requireConsultant`: caller must be an active consultant firm member
 * - `fallback`:    where to redirect when the role is missing
 */
export default function RoleRoute({ requireOrg, requireStaff, requireConsultant, fallback = '/', children }) {
  const roles = useActorRoles();

  if (!roles.loaded) {
    return <div className="v3-loading"><div className="spinner" />Checking access…</div>;
  }

  // Fail-closed: resolution failure → controlled error/retry, never a silent
  // redirect (the UI is never the security boundary, but misrouting an
  // existing user to the public site or onboarding is a genuine defect).
  if (roles.failed) {
    return (
      <div className="v3-loading">
        <div role="alert" style={{ color: '#b91c1c', marginBottom: '0.75rem' }}>
          We couldn&apos;t verify your access just now. Please try again.
        </div>
        <button
          type="button"
          onClick={() => window.location.reload()}
          style={{ cursor: 'pointer', padding: '0.4rem 0.9rem', borderRadius: 6, border: '1px solid #94a3b8' }}
        >
          Retry
        </button>
      </div>
    );
  }

  // A genuinely new authenticated user (server-authoritative) must reach
  // self-service onboarding — not a fallback redirect loop to the public site.
  if (roles.isNewUser) {
    return <Navigate to="/onboarding" replace />;
  }

  const required = (requireOrg && !roles.org)
    || (requireStaff && !roles.isStaff)
    || (requireConsultant && !roles.isConsultant);

  if (required) {
    return <Navigate to={fallback} replace />;
  }

  return children;
}
