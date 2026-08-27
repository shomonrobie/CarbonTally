// frontend/src/v3/components/RoleRoute.jsx
// D25 — frontend role-route guards.
//
// The backend/RLS remain the authoritative security boundary; these guards are
// UX/navigation only: they stop an actor from landing on a workspace they do
// not have, and redirect to an appropriate home. Guards never grant access.
//
//   useActorRoles()   — resolves org membership / staff / consultant once
//   RoleRoute         — renders children only when the required role is held
import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { getConsultantProfile, getOpsMe, resolveV3Organization } from '../api';

export function useActorRoles() {
  const [roles, setRoles] = useState({
    org: null,
    isStaff: false,
    isConsultant: false,
    loaded: false,
  });

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      resolveV3Organization(),
      getOpsMe().then(() => true).catch(() => false),
      getConsultantProfile().then(() => true).catch(() => false),
    ]).then(([orgResult, staffResult, consultantResult]) => {
      if (!active) return;
      setRoles({
        org: orgResult.status === 'fulfilled' ? orgResult.value || null : null,
        isStaff: staffResult.status === 'fulfilled' && staffResult.value === true,
        isConsultant: consultantResult.status === 'fulfilled' && consultantResult.value === true,
        loaded: true,
      });
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

  const required = (requireOrg && !roles.org)
    || (requireStaff && !roles.isStaff)
    || (requireConsultant && !roles.isConsultant);

  if (required) {
    return <Navigate to={fallback} replace />;
  }

  return children;
}
