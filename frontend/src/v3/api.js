// frontend/src/v3/api.js
// CarbonTally V3 API client — thin fetch wrapper around the authoritative
// /api/v3/* backend. The frontend never calculates or fabricates data: every
// value comes from the V3 backend (engine → persisted rows → API).
import { supabase } from '../supabaseClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getV3Token = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || localStorage.getItem('access_token') || null;
};

// D29/F3 — bounded requests: a hanging request must surface as a usable
// error state instead of an indefinite spinner. 25s is generous for the
// V3 backend's data-heavy aggregates.
const REQUEST_TIMEOUT_MS = 25000;

// Map raw backend errors to concise, user-facing copy while preserving the
// technical detail for developers in the console (raw stays on error.raw).
const friendlyError = (raw, status) => {
  if (status === 401) {
    return 'Please sign in again — your session may have expired.';
  }
  if (status === 403) {
    return "You don't have permission to access this area.";
  }
  // Never surface raw backend/server internals to end users.
  if (status >= 500) {
    return 'Something went wrong on our side. Please try again.';
  }
  return raw || 'Request failed.';
};

export const v3Fetch = async (path, options = {}) => {
  const token = await getV3Token();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers, signal: controller.signal });
  } catch (e) {
    if (e && e.name === 'AbortError') {
      console.error(`[CarbonTally V3] ${options.method || 'GET'} ${path} → timed out after ${REQUEST_TIMEOUT_MS}ms`);
      const err = new Error('The request took too long and timed out. Please try again.');
      err.status = 0;
      err.raw = 'timeout';
      throw err;
    }
    console.error(`[CarbonTally V3] ${options.method || 'GET'} ${path} → network error:`, e);
    const err = new Error('Network error — please check your connection and try again.');
    err.status = 0;
    err.raw = 'network';
    throw err;
  } finally {
    clearTimeout(timeout);
  }
  if (!response.ok) {
    let raw = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      raw = body.detail || body.error?.message || raw;
    } catch (_e) {
      /* non-JSON error body */
    }
    // Keep the real backend message visible to developers (suppressed when the
    // caller explicitly opts into a quiet probe — CL-49: expected 403 role
    // probes must not produce console noise on normal page loads).
    if (!options.quiet) {
      console.error(`[CarbonTally V3] ${options.method || 'GET'} ${path} → ${response.status}:`, raw);
    }
    const error = new Error(friendlyError(raw, response.status));
    error.status = response.status;
    error.raw = raw;
    throw error;
  }
  return response.json();
};

// Resolve the caller's primary organisation using the existing legacy
// membership endpoint (same pattern as the Dashboard) so every V3 request is
// org-scoped and org-isolated.
export const resolveV3Organization = async () => {
  const token = await getV3Token();
  if (!token) return null;
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;
  const response = await fetch(
    `${API_URL}/api/organizations/members/user/${user.id}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) return null;
  const data = await response.json();
  return data?.primary_organization || data?.organization || null;
};

// D29/F5 — resolve the authenticated actor's landing workspace from the SINGLE
// SERVER-AUTHORITATIVE context endpoint (GET /api/v3/me/context).
//
// Phase 3 / P1-B — this replaces the old probe chain (org → staff →
// consultant) which treated ANY failure (500/403/network) as "brand-new
// customer" and misrouted existing users to /onboarding. Fail-closed: on
// failure this THROWS so callers show a controlled error/retry state. An API
// error is never interpreted as "new customer".
export const getMeContext = async () => {
  const data = await v3Fetch('/api/v3/me/context');
  const destination = data && (data.destination || data.primary_workspace);
  if (!destination) {
    console.error('[CarbonTally V3] /api/v3/me/context returned no destination');
    const err = new Error('Unable to resolve your workspace. Please try again.');
    err.status = 0;
    err.raw = 'empty-me-context';
    throw err;
  }
  return data;
};

// D29/F5 — resolve the authenticated actor's landing workspace.
//   org member   -> /home
//   staff/entity -> /ops
//   consultant   -> /consultant
//   no relationship (server decision) -> /onboarding
//   no session   -> /login
// On ANY resolution failure it throws (never /onboarding).
export const resolvePostLoginPath = async () => {
  if (!(await getV3Token())) return '/login';
  const context = await getMeContext();
  return context.destination || context.primary_workspace;
};

// Phase 3 / P1-B — shared post-login navigation helper for login/signup
// callers. On success it navigates to the server-authoritative workspace; on
// failure it THROWS so the caller can render a controlled error/retry state.
// An API/network failure can never be turned into /onboarding here.
export const goToWorkspace = async (navigate) => {
  const path = await resolvePostLoginPath();
  navigate(path, { replace: true });
};


// ---------------------------------------------------------------------------
// Reports API (V3 authoritative surface)
// ---------------------------------------------------------------------------

export const listReports = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  return v3Fetch(`/api/v3/reports?${query.toString()}`);
};

export const getReport = (reportId) => v3Fetch(`/api/v3/reports/${reportId}`);

export const getReportContent = (reportId) =>
  v3Fetch(`/api/v3/reports/${reportId}/content`);

export const getReportVersions = (reportId) =>
  v3Fetch(`/api/v3/reports/${reportId}/versions`);

export const getReportTypes = () => v3Fetch('/api/v3/reports/types');

// --- S6 — report lifecycle (visibility-first) -------------------------------
// Thin wrappers over the existing, already-authorised lifecycle endpoints. The
// server owns the state machine and re-checks authority on every transition;
// these helpers never decide whether an action is legal.
export const submitReportVersion = (reportId, versionNumber) =>
  v3Fetch(`/api/v3/reports/${reportId}/versions/${versionNumber}/submit`, {
    method: 'POST',
  });

export const approveReportVersion = (reportId, versionNumber) =>
  v3Fetch(`/api/v3/reports/${reportId}/versions/${versionNumber}/approve`, {
    method: 'POST',
  });

export const requestChangesReportVersion = (reportId, versionNumber) =>
  v3Fetch(
    `/api/v3/reports/${reportId}/versions/${versionNumber}/request-changes`,
    { method: 'POST' }
  );

export const rejectReportVersion = (reportId, versionNumber) =>
  v3Fetch(`/api/v3/reports/${reportId}/versions/${versionNumber}/reject`, {
    method: 'POST',
  });

export const finalizeReportVersion = (reportId, versionNumber) =>
  v3Fetch(`/api/v3/reports/${reportId}/versions/${versionNumber}/finalize`, {
    method: 'POST',
  });

// The lifecycle action → endpoint map used by the UI. Only actions present in a
// version's server-provided `allowed_actions` are ever offered.
export const REPORT_LIFECYCLE_ACTION_CALLS = {
  submit_review: submitReportVersion,
  approve: approveReportVersion,
  request_changes: requestChangesReportVersion,
  reject: rejectReportVersion,
  finalize: finalizeReportVersion,
};

export const generateReport = (payload) =>
  v3Fetch('/api/v3/reports', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// Download the persisted report content through the authenticated API.
export const downloadReport = async (reportId, fallbackName = 'report.json') => {
  const token = await getV3Token();
  const response = await fetch(`${API_URL}/api/v3/reports/${reportId}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    let detail = `Download failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_e) {
      /* ignore */
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : fallbackName;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return filename;
};

// Org-scoped export URLs reusing the existing V3 exports surface (CSV/JSON).
export const exportEmissionsUrl = (organizationId, format = 'csv', params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  return `${API_URL}/api/v3/exports/emissions.${format}?${query.toString()}`;
};

export const exportDocumentsUrl = (organizationId) =>
  `${API_URL}/api/v3/exports/documents.csv?organization_id=${organizationId}`;

// Trigger a browser download of an org-scoped export endpoint.
export const downloadExport = async (url) => {
  const token = await getV3Token();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`Export failed (${response.status})`);
  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : 'export.csv';
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(objectUrl);
  return filename;
};

// ---------------------------------------------------------------------------
// Customer Administration API (V3 org-scoped surface)
// ---------------------------------------------------------------------------

export const getOrganizationProfile = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/profile`);

export const updateOrganizationProfile = (organizationId, fields) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/profile`, {
    method: 'PUT',
    body: JSON.stringify(fields),
  });

export const getOrganizationMetadata = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/metadata`);
export const updateOrganizationMetadata = (organizationId, fields) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/metadata`, {
    method: 'PUT',
    body: JSON.stringify(fields),
  });

export const listMembers = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/members`);

export const getMember = (memberId) =>
  v3Fetch(`/api/v3/organizations/members/${memberId}`);

export const addMember = (organizationId, payload) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/members`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateMember = (memberId, payload) =>
  v3Fetch(`/api/v3/organizations/members/${memberId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const removeMember = (memberId) =>
  v3Fetch(`/api/v3/organizations/members/${memberId}`, { method: 'DELETE' });

export const listOrgRoles = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/roles`);

export const listInvitations = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/invitations`);

export const createInvitation = (organizationId, payload) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/invitations`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const revokeInvitation = (invitationId) =>
  v3Fetch(`/api/v3/organizations/invitations/${invitationId}`, { method: 'DELETE' });

export const listFacilities = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/facilities`);

export const getFacility = (facilityId) =>
  v3Fetch(`/api/v3/organizations/facilities/${facilityId}`);

export const createFacility = (organizationId, payload) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/facilities`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateFacility = (facilityId, payload) =>
  v3Fetch(`/api/v3/organizations/facilities/${facilityId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const removeFacility = (facilityId) =>
  v3Fetch(`/api/v3/organizations/facilities/${facilityId}`, { method: 'DELETE' });

export const listAssets = (organizationId) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/assets`);

export const getAsset = (assetId) =>
  v3Fetch(`/api/v3/organizations/assets/${assetId}`);

export const createAsset = (organizationId, payload) =>
  v3Fetch(`/api/v3/organizations/${organizationId}/assets`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateAsset = (assetId, payload) =>
  v3Fetch(`/api/v3/organizations/assets/${assetId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const removeAsset = (assetId) =>
  v3Fetch(`/api/v3/organizations/assets/${assetId}`, { method: 'DELETE' });

export const listSuppliers = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  return v3Fetch(`/api/v3/suppliers?${query.toString()}`);
};

export const getSupplier = (supplierId) =>
  v3Fetch(`/api/v3/suppliers/${supplierId}`);

export const createSupplier = (payload) =>
  v3Fetch('/api/v3/suppliers', { method: 'POST', body: JSON.stringify(payload) });

export const updateSupplier = (supplierId, payload) =>
  v3Fetch(`/api/v3/suppliers/${supplierId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const removeSupplier = (supplierId) =>
  v3Fetch(`/api/v3/suppliers/${supplierId}`, { method: 'DELETE' });

// ---------------------------------------------------------------------------
// Consultant / multi-client API (V3 org-authorized surface)
// ---------------------------------------------------------------------------

export const getConsultantProfile = (options = {}) => v3Fetch('/api/v3/consultants/me', options);

export const getConsultantBranding = () =>
  v3Fetch('/api/v3/consultants/me/branding');

export const getConsultantBrandingContext = () =>
  v3Fetch('/api/v3/consultants/me/branding/context');

export const updateConsultantBranding = (payload) =>
  v3Fetch('/api/v3/consultants/me/branding', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const listConsultantClients = () => v3Fetch('/api/v3/consultants/me/clients');

export const getConsultantDashboard = () => v3Fetch('/api/v3/consultants/me/dashboard');

// CL-61 — consultant team + internal tasks.
export const getConsultantTeam = () => v3Fetch('/api/v3/consultants/me/team');

export const addConsultantTeamMember = (userId, role = 'consultant') =>
  v3Fetch('/api/v3/consultants/me/team', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, role }),
  });

// CL-61 close-out — revoke (deactivate) / reactivate a team member.
export const deactivateConsultantTeamMember = (memberId) =>
  v3Fetch(`/api/v3/consultants/me/team/${memberId}/deactivate`, { method: 'POST' });

export const reactivateConsultantTeamMember = (memberId) =>
  v3Fetch(`/api/v3/consultants/me/team/${memberId}/reactivate`, { method: 'POST' });

export const getConsultantTasks = (status) => {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return v3Fetch(`/api/v3/consultants/me/tasks${query}`);
};

export const createConsultantTask = (payload) =>
  v3Fetch('/api/v3/consultants/me/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateConsultantTaskStatus = (taskId, status) =>
  v3Fetch(`/api/v3/consultants/tasks/${taskId}/status`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  });

export const getConsultantClient = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}`);

// CON-1 / PO Decision 3 — a consultant creates a new customer organisation
// (owner identity provisioned server-side, firm linked as active client).
export const createConsultantCustomer = (payload) =>
  v3Fetch('/api/v3/consultants/me/customers', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateConsultantClientStatus = (clientId, status) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  });

export const deactivateConsultantClient = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}`, { method: 'DELETE' });

export const getClientWorkspaceContext = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/context`);

export const getClientReports = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/reports`);

export const getClientDashboard = (clientId, startDate, endDate) => {
  const query = new URLSearchParams({ start_date: startDate, end_date: endDate });
  return v3Fetch(`/api/v3/consultants/clients/${clientId}/dashboard?${query.toString()}`);
};

export const getClientDocuments = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/documents`);

// CON-2 — consultant uploads a document INTO an authorized client's org
// (durable server-side pipeline: storage → item → auto-processing job → OCR).
export const uploadConsultantDocument = (clientId, file, dataType = 'utility') => {
  const form = new FormData();
  form.append('file', file);
  form.append('data_type', dataType);
  return v3Fetch(`/api/v3/consultants/clients/${clientId}/documents`, {
    method: 'POST',
    body: form,
  });
};

// CON-3 — the client's processing items (with org context) for the consultant
// processing workspace. Optional `stage` narrows to a workflow stage.
export const getClientProcessingItems = (clientId, stage) => {
  const query = stage ? `?stage=${encodeURIComponent(stage)}` : '';
  return v3Fetch(`/api/v3/consultants/clients/${clientId}/processing/items${query}`);
};

// E7 — the consultant's evidence view for an authorized client (persisted
// calculation history with provenance from the same evidence contract the
// customer sees; grant-scoped server-side).
export const getClientEvidence = (clientId, limit = 50, offset = 0) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/evidence?limit=${limit}&offset=${offset}`);

export const getClientProcessingStatus = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/processing/status`);

export const getClientIssues = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/issues`);

// ---------------------------------------------------------------------------
// Internal Operations API (V3 authoritative surface — /api/v3/ops/*)
// ---------------------------------------------------------------------------

export const getOpsMe = (options = {}) => v3Fetch('/api/v3/ops/me', options);

export const getOpsDashboard = () => v3Fetch('/api/v3/ops/dashboard');

// --- Phase 8-X X5 — operational health console (read-only) -------------------
// Thin wrappers over the already-authorised, internal-only X1/X4 endpoints. X5
// adds no metric, no filter and no action: it displays these payloads verbatim.
export const getOperationalHealthQueue = () =>
  v3Fetch('/api/v3/ops/operational-health/queue');

export const getOperationalHealthWorker = () =>
  v3Fetch('/api/v3/ops/operational-health/worker');

export const getOperationalIntelligence = () =>
  v3Fetch('/api/v3/ops/operational-intelligence');


// CL-63 — dedicated authorised organisation search/list contract for staff
// messaging (paginated + searchable). The ops dashboard summary is never used
// as a row collection by any UI component.
export const getOpsOrganizations = ({ q = '', limit = 50, offset = 0 } = {}) => {
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  const qs = params.toString();
  return v3Fetch(`/api/v3/ops/organizations${qs ? `?${qs}` : ''}`);
};

export const listOpsStaff = (limit = 25, offset = 0) =>
  v3Fetch(`/api/v3/ops/staff?limit=${limit}&offset=${offset}`);

export const createOpsStaff = (payload) =>
  v3Fetch('/api/v3/ops/staff', { method: 'POST', body: JSON.stringify(payload) });

export const listStaffRoles = () => v3Fetch('/api/v3/ops/staff-roles');

export const updateOpsStaff = (profileId, payload) =>
  v3Fetch(`/api/v3/ops/staff/${profileId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const listProcessingEntities = (limit = 25, offset = 0, status) => {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (status) query.set('status', status);
  return v3Fetch(`/api/v3/ops/entities?${query.toString()}`);
};

// Creating a Processing Entity is a CarbonTally-internal admin action
// (backend: /api/v3/processing-entities, require_admin).
export const createProcessingEntity = (payload) =>
  v3Fetch('/api/v3/processing-entities', {
    method: 'POST',
    body: JSON.stringify(payload),
  });


export const getEntityDashboard = (entityId) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/dashboard`);

// Entity extraction workspace (D22) — Processing Entity staff process ONLY the
// work assigned to their entity.
export const getEntityExtractionBatches = (entityId, status = '') => {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/batches${query}`);
};

export const getEntityExtractionBatch = (entityId, batchId) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/batches/${batchId}`);

export const getEntityExtractionBatchItems = (entityId, batchId) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/batches/${batchId}/items`);

export const getEntityMappingOptions = (entityId, itemId, params = {}) => {
  const query = new URLSearchParams();
  if (params.activity) query.set('activity', params.activity);
  if (params.unit) query.set('unit', params.unit);
  const qs = query.toString();
  return v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/mapping-options${qs ? `?${qs}` : ''}`);
};

export const getEntityExtractionItem = (entityId, itemId) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}`);

export const getEntityNextItem = (entityId, stage, excludeItemId = '') => {
  const query = new URLSearchParams({ stage });
  if (excludeItemId) query.set('exclude_item_id', excludeItemId);
  return v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/next-item?${query}`);
};

export const entityValidateItem = (entityId, itemId) =>
  v3Fetch(`/api/v3/pe/items/${itemId}/validate`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
export const entityStartItem = (entityId, itemId, stage) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/start`, {
    method: 'POST',
    body: JSON.stringify({ stage }),
  });

export const entityExtractItem = (entityId, itemId, extractedData) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/extract`, {
    method: 'POST',
    body: JSON.stringify({ extracted_data: extractedData }),
  });

export const entityMapItem = (entityId, itemId, payload) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/map`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const entityCalculateItem = (entityId, itemId, payload = {}) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/calculate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const entitySetItemStatus = (entityId, itemId, status) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  });

export const entityClarifyItem = (entityId, itemId, payload) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/extraction/items/${itemId}/clarify`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const getOperatorQueue = (status = '', limit = 25, offset = 0) => {
  const query = new URLSearchParams();
  if (status) query.set('status', status);
  query.set('limit', String(limit));
  query.set('offset', String(offset));
  return v3Fetch(`/api/v3/ops/queues/operator?${query.toString()}`);
};

export const getReviewQueue = (params = {}) => {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.assigned_to) query.set('assigned_to', params.assigned_to);
  query.set('limit', String(params.limit ?? 25));
  query.set('offset', String(params.offset ?? 0));
  return v3Fetch(`/api/v3/ops/queues/review?${query.toString()}`);
};

export const getQcQueue = (limit = 25, offset = 0) =>
  v3Fetch(`/api/v3/ops/queues/qc?limit=${limit}&offset=${offset}`);

export const getNextItem = (stage) =>
  v3Fetch(`/api/v3/ops/next-item?stage=${encodeURIComponent(stage)}`);

export const getItemWorkspace = (itemId) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/workspace`);

// P6-2F (consultant surface, IV-N6) — the consultant item workspace must use
// the scope-aware processing route. The internal-staff /api/v3/ops workspace
// is guarded by require_staff(), which correctly denies consultants, so the
// consultant page must not call it.
export const getConsultantItemWorkspace = (itemId) =>
  v3Fetch(`/api/v3/processing/items/${itemId}/workspace`);

// P6-2F — consultant review + submit actions on the consultant surface
// (P6-2B boundaries: review needs active grant + stage eligibility; submit
// needs the `can_submit` capability). The backend re-authorizes every call.
export const consultantReviewItem = (itemId, payload) =>
  v3Fetch(`/api/v3/processing/items/${itemId}/consultant-review`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const consultantSubmitItem = (itemId) =>
  v3Fetch(`/api/v3/processing/items/${itemId}/consultant-submit`, {
    method: 'POST',
  });

export const getMappingOptions = (itemId, params = {}) => {
  const query = new URLSearchParams();
  if (params.activity) query.set('activity', params.activity);
  if (params.unit) query.set('unit', params.unit);
  const qs = query.toString();
  return v3Fetch(`/api/v3/ops/items/${itemId}/mapping-options${qs ? `?${qs}` : ''}`);
};

export const getOpsBatchItems = (batchId) =>
  v3Fetch(`/api/v3/ops/batches/${batchId}/items`);

export const startItem = (itemId, stage) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/start`, {
    method: 'POST',
    body: JSON.stringify({ stage }),
  });

export const extractItem = (itemId, extractedData) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/extract`, {
    method: 'POST',
    body: JSON.stringify({ extracted_data: extractedData }),
  });

export const mapItem = (itemId, payload) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/map`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const validateItem = (itemId) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/validate`, { method: 'POST' });

export const calculateItem = (itemId, payload = {}) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/calculate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const qcReviewItem = (itemId, payload) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/qc`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const assignBatch = (batchId, assignedTo, opts = {}) => {
  // D22: exactly one of assigned_to (internal operator) / entity_id (Processing
  // Entity); reason recorded on reassignment.
  const payload = { assigned_to: assignedTo || null, ...opts };
  return v3Fetch(`/api/v3/ops/batches/${batchId}/assign`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const assignReview = (reviewId, assignedTo) =>
  v3Fetch(`/api/v3/ops/review/${reviewId}/assign`, {
    method: 'POST',
    body: JSON.stringify({ assigned_to: assignedTo }),
  });

export const completeReview = (reviewId, payload) =>
  v3Fetch(`/api/v3/ops/review/${reviewId}/complete`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const getSlaSettings = () => v3Fetch('/api/v3/ops/sla/settings');

// ---------------------------------------------------------------------------
// QC surface (admin) — /api/v3/qc/*
// ---------------------------------------------------------------------------

export const getQcQueueAdmin = () => v3Fetch('/api/v3/qc/queue');

export const getQcStats = () => v3Fetch('/api/v3/qc/stats');

export const qcReviewItemAdmin = (itemId, payload) =>
  v3Fetch(`/api/v3/qc/items/${itemId}/review`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// ---------------------------------------------------------------------------
// V1.2 — Processing Entity contract (/api/v3/pe/*) — dedicated PE application
// ---------------------------------------------------------------------------

export const getPeMe = () => v3Fetch('/api/v3/pe/me');

export const getPeWork = (status) =>
  v3Fetch(`/api/v3/pe/work${status ? `?status=${encodeURIComponent(status)}` : ''}`);

export const getPeBatchItems = (batchId) => v3Fetch(`/api/v3/pe/batches/${batchId}/items`);

// WS4 — D38 work-item controls surfaced on the PE application.
export const peWorkInfo = (itemId) => v3Fetch(`/api/v3/pe/items/${itemId}/work`);
export const peWorkClaim = (itemId, reason) =>
  v3Fetch(`/api/v3/pe/items/${itemId}/work/claim`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason || null }),
  });
export const peWorkRelease = (itemId, reason) =>
  v3Fetch(`/api/v3/pe/items/${itemId}/work/release`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason || null }),
  });
export const peWorkComplete = (itemId, reason) =>
  v3Fetch(`/api/v3/pe/items/${itemId}/work/complete`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason || null }),
  });

// WS4 — D39 PE operational messaging (entity-scoped conversations).
export const listEntityConversations = (entityId) => {
  const qs = entityId ? `?entity_id=${encodeURIComponent(entityId)}` : '';
  return v3Fetch(`/api/v3/messaging/entity-conversations${qs}`);
};
export const createEntityConversation = (payload) =>
  v3Fetch('/api/v3/messaging/entity-conversations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
export const listEntityMessages = (conversationId) =>
  v3Fetch(`/api/v3/messaging/entity-conversations/${conversationId}/messages`);
export const sendEntityMessage = (conversationId, content) =>
  v3Fetch(`/api/v3/messaging/entity-conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
export const markEntityConversationRead = (conversationId) =>
  v3Fetch(`/api/v3/messaging/entity-conversations/${conversationId}/read`, {
    method: 'POST',
  });

// WS4 continuation — Operations D38 work-item assignment controls.
export const listStaff = () => v3Fetch('/api/v3/ops/staff');
export const opsWorkInfo = (itemId) => v3Fetch(`/api/v3/ops/items/${itemId}/work`);
export const opsWorkClaim = (itemId, reason) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/work/claim`, { method: 'POST', body: JSON.stringify({ reason: reason || null }) });
export const opsWorkAssign = (itemId, targetUserId, reason) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/work/assign`, { method: 'POST', body: JSON.stringify({ assigned_to: targetUserId, reason: reason || null }) });
// WS4 Gate 3 / 4C — item-level assignment to a Processing Entity OR an internal
// staff member (exactly one of entity_id / assigned_to; the server validates the
// target and records actor + previous_*). Reassign records the transition.
export const opsWorkAssignTarget = (itemId, target, reason) => {
  const payload = { reason: reason || null };
  if (target.assigned_to) payload.assigned_to = target.assigned_to;
  if (target.entity_id) payload.entity_id = target.entity_id;
  return v3Fetch(`/api/v3/ops/items/${itemId}/work/assign`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};
export const opsWorkReassignTarget = (itemId, target, reason) => {
  const payload = { reason: reason || null };
  if (target.assigned_to) payload.assigned_to = target.assigned_to;
  if (target.entity_id) payload.entity_id = target.entity_id;
  return v3Fetch(`/api/v3/ops/items/${itemId}/work/reassign`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};
export const opsWorkRelease = (itemId, reason) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/work/release`, { method: 'POST', body: JSON.stringify({ reason: reason || null }) });
export const opsWorkComplete = (itemId, reason) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/work/complete`, { method: 'POST', body: JSON.stringify({ reason: reason || null }) });

export const peReviewDecision = (itemId, approved) =>
  v3Fetch(`/api/v3/pe/items/${itemId}/pe-review`, {
    method: 'POST',
    body: JSON.stringify({ approved: !!approved }),
  });

export const peQcDecision = (itemId, approved) =>
  v3Fetch(`/api/v3/pe/items/${itemId}/pe-qc`, {
    method: 'POST',
    body: JSON.stringify({ approved: !!approved }),
  });

// ---------------------------------------------------------------------------
// V1.2 — Internal Review submit + late CarbonTally QC gate (/api/v3/ops/qc/*)
// ---------------------------------------------------------------------------

export const submitInternalReview = (itemId) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/submit-review`, { method: 'POST' });

export const getCtQcQueue = () => v3Fetch('/api/v3/ops/qc/ct-queue');

export const ctQcDecision = (itemId, payload) =>
  v3Fetch(`/api/v3/ops/qc/items/${itemId}/decision`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// ---------------------------------------------------------------------------
// Emissions intelligence — /api/v3/emissions/* (authoritative calculation)
// ---------------------------------------------------------------------------

export const v3CalculateEmissions = (payload) =>
  v3Fetch('/api/v3/emissions/calculate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// History reads the persisted rows through the verified exports surface.
export const v3ListEmissions = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  return v3Fetch(`/api/v3/exports/emissions.json?${query.toString()}`);
};

// ---------------------------------------------------------------------------
// Documents + uploads — /api/v3/uploads, /api/v3/documents, /api/v3/batches
// ---------------------------------------------------------------------------

export const v3ListDocuments = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  return v3Fetch(`/api/v3/documents?${query.toString()}`);
};

// Multipart upload — the browser sets the boundary; do not force JSON headers.
export const v3UploadDocument = async ({ organization_id, data_type, file }) => {
  const token = await getV3Token();
  const form = new FormData();
  form.append('organization_id', organization_id);
  form.append('data_type', data_type || 'utility');
  form.append('file', file);
  const response = await fetch(`${API_URL}/api/v3/uploads`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!response.ok) {
    let detail = `Upload failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_e) {
      /* non-JSON error body */
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  return response.json();
};

export const v3ListUploadBatches = (organizationId) =>
  v3Fetch(`/api/v3/batches?organization_id=${encodeURIComponent(organizationId)}`);

// ---------------------------------------------------------------------------
// Manual extraction (customer processing) — /api/v3/manual-extraction/*
// ---------------------------------------------------------------------------

export const v3ListExtractionBatches = (organizationId) =>
  v3Fetch(`/api/v3/manual-extraction/batches?organization_id=${encodeURIComponent(organizationId)}`);

export const v3CreateExtractionBatch = (organizationId, payload) =>
  v3Fetch(`/api/v3/manual-extraction/batches?organization_id=${encodeURIComponent(organizationId)}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const v3ListExtractionItems = (batchId) =>
  v3Fetch(`/api/v3/manual-extraction/batches/${encodeURIComponent(batchId)}/items`);

export const v3CreateExtractionItem = (batchId, payload) =>
  v3Fetch(`/api/v3/manual-extraction/batches/${encodeURIComponent(batchId)}/items`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// ---------------------------------------------------------------------------
// Customer Issues (D25) — /api/v3/issues (org-scoped; entity-scoped rows are
// never returned by the backend, so no internal/entity context can leak here).
// ---------------------------------------------------------------------------

export const listCustomerIssues = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
  });
  return v3Fetch(`/api/v3/issues?${query.toString()}`);
};

export const getCustomerIssue = (issueId) => v3Fetch(`/api/v3/issues/${issueId}`);

export const createCustomerIssue = (payload) =>
  v3Fetch('/api/v3/issues', { method: 'POST', body: JSON.stringify(payload) });


export const updateIssue = (issueId, payload) =>
  v3Fetch(`/api/v3/issues/${encodeURIComponent(issueId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

// CarbonTally-internal triage (staff admin, can_manage_staff) —
// /api/v3/issues/admin/*
export const listOpsOpenIssues = (organizationId) => {
  const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : '';
  return v3Fetch(`/api/v3/issues/admin/open${query}`);
};

export const listEntityIssues = (entityId) =>
  v3Fetch(`/api/v3/issues/admin/entity/${encodeURIComponent(entityId)}`);

// ---------------------------------------------------------------------------
// Notifications (D25) — /api/v3/notifications (per-recipient, user-isolated)
// ---------------------------------------------------------------------------

// Accepts either the D25 boolean signature ``listNotifications(unreadOnly)``
// or an options object ``listNotifications({ unreadOnly, limit, offset })``.
// The backend clamps limit to 1..500 (D26 scale hardening).
export const listNotifications = (options = false) => {
  const opts =
    typeof options === 'object' && options !== null
      ? options
      : { unreadOnly: options };
  const params = new URLSearchParams();
  if (opts.unreadOnly) params.set('unread_only', 'true');
  if (opts.limit !== undefined) params.set('limit', String(opts.limit));
  if (opts.offset !== undefined) params.set('offset', String(opts.offset));
  const qs = params.toString();
  return v3Fetch(`/api/v3/notifications${qs ? `?${qs}` : ''}`);
};

export const markNotificationRead = (notificationId) =>
  v3Fetch(`/api/v3/notifications/${notificationId}/read`, { method: 'POST' });

export const markAllNotificationsRead = () =>
  v3Fetch('/api/v3/notifications/read-all', { method: 'POST' });

// ---------------------------------------------------------------------------
// SLA settings (D25) — /api/v3/ops/sla/settings (staff admin writes)
// ---------------------------------------------------------------------------

export const updateSlaSettings = (payload) =>
  v3Fetch('/api/v3/ops/sla/settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });


// ---------------------------------------------------------------------------
// D19 — Existing-data discovery (D27) — /api/v3/discovery/*
// ---------------------------------------------------------------------------

export const discoveryLookup = (organizationId, signals) =>
  v3Fetch('/api/v3/discovery/lookup', {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, ...signals }),
  });

export const createDiscoveryRequest = (organizationId, candidateOrganizationId, verificationMethod = 'email', note = null) =>
  v3Fetch('/api/v3/discovery/requests', {
    method: 'POST',
    body: JSON.stringify({
      organization_id: organizationId,
      candidate_organization_id: candidateOrganizationId,
      verification_method: verificationMethod,
      note,
    }),
  });

export const listDiscoveryRequests = (organizationId) =>
  v3Fetch(`/api/v3/discovery/requests?organization_id=${encodeURIComponent(organizationId)}`);

export const getDiscoveryRequest = (requestId, organizationId) =>
  v3Fetch(`/api/v3/discovery/requests/${requestId}?organization_id=${encodeURIComponent(organizationId)}`);

export const verifyDiscoveryRequest = (requestId, organizationId, code) =>
  v3Fetch(`/api/v3/discovery/requests/${requestId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, code }),
  });

export const chooseDiscoveryAdoption = (requestId, organizationId, choice, scope = {}, note = null) =>
  v3Fetch(`/api/v3/discovery/requests/${requestId}/choice`, {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, choice, scope, note }),
  });

// ---------------------------------------------------------------------------
// D35 — Self-service customer onboarding (pre-org-creation discovery variants)
// ---------------------------------------------------------------------------
// A brand-new customer who has NOT yet created/adopted an organization runs the
// existing-data discovery flow WITHOUT organization_id. The backend binds these
// requests to the authenticated actor (created_by) and only that actor may
// verify and choose an outcome.

// Create the caller's organization (creator becomes OWNER). On a 409
// duplicate-prevention block the frontend routes to the existing-data review.
export const createOrganization = (payload) =>
  v3Fetch('/api/v3/organizations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const onboardingDiscoveryLookup = (signals) =>
  v3Fetch('/api/v3/discovery/lookup', {
    method: 'POST',
    body: JSON.stringify(signals),
  });

export const createOnboardingDiscoveryRequest = (candidateOrganizationId, verificationMethod = 'email', note = null) =>
  v3Fetch('/api/v3/discovery/requests', {
    method: 'POST',
    body: JSON.stringify({
      candidate_organization_id: candidateOrganizationId,
      verification_method: verificationMethod,
      note,
    }),
  });

export const getOnboardingDiscoveryRequest = (requestId) =>
  v3Fetch(`/api/v3/discovery/requests/${requestId}`);

export const verifyOnboardingDiscoveryRequest = (requestId, code) =>
  v3Fetch(`/api/v3/discovery/requests/${requestId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ code }),
  });

export const chooseOnboardingAdoption = (requestId, choice, scope = {}, note = null) =>
  v3Fetch(`/api/v3/discovery/requests/${requestId}/choice`, {
    method: 'POST',
    body: JSON.stringify({ choice, scope, note }),
  });

// ---------------------------------------------------------------------------
// D19 — Consultant-client lifecycle (D27) — /api/v3/consultants/clients/*
// ---------------------------------------------------------------------------

export const suspendConsultantClient = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/suspend`, { method: 'POST' });

export const endConsultantClient = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/end`, { method: 'POST' });

export const reactivateConsultantClient = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/reactivate`, { method: 'POST' });


// ---------------------------------------------------------------------------
// D19 — White-label (D27) — /api/v3/consultants/me/custom-domains + /senders
// ---------------------------------------------------------------------------

export const listCustomDomains = () => v3Fetch('/api/v3/consultants/me/custom-domains');

export const createCustomDomain = (domain) =>
  v3Fetch('/api/v3/consultants/me/custom-domains', {
    method: 'POST',
    body: JSON.stringify({ domain }),
  });

export const verifyCustomDomain = (domainId, token) =>
  v3Fetch(`/api/v3/consultants/me/custom-domains/${domainId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ token }),
  });

export const activateCustomDomain = (domainId) =>
  v3Fetch(`/api/v3/consultants/me/custom-domains/${domainId}/activate`, { method: 'POST' });

export const removeCustomDomain = (domainId) =>
  v3Fetch(`/api/v3/consultants/me/custom-domains/${domainId}/remove`, { method: 'POST' });

export const listCustomSenders = () => v3Fetch('/api/v3/consultants/me/senders');

export const createCustomSender = (email) =>
  v3Fetch('/api/v3/consultants/me/senders', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });

export const verifyCustomSender = (senderId) =>
  v3Fetch(`/api/v3/consultants/me/senders/${senderId}/verify`, { method: 'POST' });

export const removeCustomSender = (senderId) =>
  v3Fetch(`/api/v3/consultants/me/senders/${senderId}/remove`, { method: 'POST' });


// ---------------------------------------------------------------------------
// D19 — Consultant-client messaging (D27) — /api/v3/messaging/*
// ---------------------------------------------------------------------------

export const createMessagingConversation = (organizationId, subject, counterparty = null) =>
  v3Fetch('/api/v3/messaging/conversations', {
    method: 'POST',
    body: JSON.stringify({
      organization_id: organizationId,
      subject,
      ...(counterparty ? { counterparty } : {}),
    }),
  });

export const listMessagingConversations = (organizationId) =>
  v3Fetch(`/api/v3/messaging/conversations?organization_id=${encodeURIComponent(organizationId)}`);

export const listMessagingMessages = (conversationId) =>
  v3Fetch(`/api/v3/messaging/conversations/${conversationId}/messages`);

export const sendMessagingMessage = (conversationId, content) =>
  v3Fetch(`/api/v3/messaging/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });

export const markMessagingConversationRead = (conversationId) =>
  v3Fetch(`/api/v3/messaging/conversations/${conversationId}/read`, { method: 'POST' });

// ---------------------------------------------------------------------------
// D19 — White-label PDF (D27) — /api/v3/reports/{id}/pdf
// ---------------------------------------------------------------------------

export const downloadReportPdf = async (reportId, fallbackName = 'report.pdf') => {
  const token = await getV3Token();
  const response = await fetch(`${API_URL}/api/v3/reports/${reportId}/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    let detail = `PDF download failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_e) {
      /* ignore */
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : fallbackName;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return filename;
};


// ---------------------------------------------------------------------------
// D30 — Reporting surface
// ---------------------------------------------------------------------------

export const getCustomerDashboardReport = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  if (params.start_date) query.set('start_date', params.start_date);
  if (params.end_date) query.set('end_date', params.end_date);
  if (params.scope) query.set('scope', params.scope);
  return v3Fetch(`/api/v3/reporting/customer-dashboard?${query.toString()}`);
};

export const getEmissionEvidence = (logId) =>
  v3Fetch(`/api/v3/emissions/${logId}/evidence`);

export const getDocumentEmissions = (fileId) =>
  v3Fetch(`/api/v3/documents/${fileId}/emissions`);

export const getEmissionsTrend = (organizationId, months = 12) =>
  v3Fetch(`/api/v3/reporting/emissions-trend?organization_id=${organizationId}&months=${months}`);

export const getMemberActivity = (organizationId) =>
  v3Fetch(`/api/v3/reporting/member-activity?organization_id=${organizationId}`);

export const getConsultantPortfolio = () =>
  v3Fetch('/api/v3/reporting/consultant-portfolio');

export const getConsultantClientDetail = (clientId) =>
  v3Fetch(`/api/v3/reporting/consultant-client/${clientId}`);

export const getOpsPlatformReporting = () =>
  v3Fetch('/api/v3/ops/reporting/platform');

export const getOpsQueueAging = () =>
  v3Fetch('/api/v3/ops/reporting/aging');

export const getOpsReviewReporting = () =>
  v3Fetch('/api/v3/ops/reporting/review');

export const getOpsQcReporting = () =>
  v3Fetch('/api/v3/ops/reporting/qc');

export const getOpsAudit = (params = {}) => {
  const query = new URLSearchParams();
  // BL-4 — forward every supported audit filter/search/sort parameter.
  // Phase 7 adds the taxonomy investigation filters.
  ['limit', 'offset', 'action', 'entity_type', 'entity_id', 'actor',
    'category', 'origin', 'outcome', 'organization_id', 'since', 'until',
    'q', 'sort', 'order'].forEach((key) => {
    const value = params[key];
    if (value !== undefined && value !== null && value !== '') query.set(key, value);
  });
  return v3Fetch(`/api/v3/ops/reporting/audit${query.toString() ? `?${query.toString()}` : ''}`);
};

// ---------------------------------------------------------------------------
// Phase 7 — Auditor / Assurance (scoped auditability + evidence package)
// ---------------------------------------------------------------------------

export const getAuditReadiness = (organizationId) =>
  v3Fetch(`/api/v3/reporting/audit-readiness?organization_id=${encodeURIComponent(organizationId)}`);

export const getAuditActivity = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  ['category', 'origin', 'outcome', 'start_date', 'end_date', 'limit', 'offset'].forEach((key) => {
    const value = params[key];
    if (value !== undefined && value !== null && value !== '') query.set(key, value);
  });
  return v3Fetch(`/api/v3/reporting/audit-activity?${query.toString()}`);
};

export const getConsultantClientAuditActivity = (clientId, params = {}) => {
  const query = new URLSearchParams();
  ['category', 'origin', 'outcome', 'limit', 'offset'].forEach((key) => {
    const value = params[key];
    if (value !== undefined && value !== null && value !== '') query.set(key, value);
  });
  return v3Fetch(
    `/api/v3/reporting/consultant-client/${encodeURIComponent(clientId)}/audit-activity`
    + (query.toString() ? `?${query.toString()}` : '')
  );
};

export const auditPackageUrl = (organizationId, reportingYear) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  if (reportingYear) query.set('reporting_year', reportingYear);
  return `${API_URL}/api/v3/exports/audit-package.json?${query.toString()}`;
};

export const getEntityPerformance = (entityId) =>
  v3Fetch(`/api/v3/ops/entities/${entityId}/performance`);

// ---------------------------------------------------------------------------
// D37-0 — Commercial (billing) configuration surface (staff, can_manage_billing)
// ---------------------------------------------------------------------------

export const getCommercialOverview = () =>
  v3Fetch('/api/v3/commercial/overview');

export const getCommercialConfig = (configKey) =>
  v3Fetch(`/api/v3/commercial/config/${encodeURIComponent(configKey)}`);

export const updateCommercialConfig = (configKey, configValue, reason) =>
  v3Fetch(`/api/v3/commercial/config/${encodeURIComponent(configKey)}`, {
    method: 'PUT',
    body: JSON.stringify({ config_value: configValue, reason: reason || null }),
  });

export const listCommercialPlans = () =>
  v3Fetch('/api/v3/commercial/plans');

export const getCommercialPlan = (planCode) =>
  v3Fetch(`/api/v3/commercial/plans/${encodeURIComponent(planCode)}`);

export const createCommercialPlan = (plan) =>
  v3Fetch('/api/v3/commercial/plans', {
    method: 'POST',
    body: JSON.stringify(plan),
  });

export const updateCommercialPlan = (planCode, fields) =>
  v3Fetch(`/api/v3/commercial/plans/${encodeURIComponent(planCode)}`, {
    method: 'PUT',
    body: JSON.stringify(fields),
  });

export const getCreditLedger = (organizationId) =>
  v3Fetch(`/api/v3/commercial/ledger?organization_id=${encodeURIComponent(organizationId)}`);

export const listCommercialOrganizations = (billingMode) =>
  v3Fetch(
    `/api/v3/commercial/organizations${
      billingMode ? `?billing_mode=${encodeURIComponent(billingMode)}` : ''
    }`
  );

// ---------------------------------------------------------------------------
// D37 — customer billing surface (org-scoped)
// ---------------------------------------------------------------------------

export const getMyBilling = () => v3Fetch('/api/v3/billing/me');

export const getMyCreditHistory = () => v3Fetch('/api/v3/billing/me/credits');

export const listMyOrders = () => v3Fetch('/api/v3/billing/me/orders');

export const getMyOrder = (orderId) =>
  v3Fetch(`/api/v3/billing/me/orders/${encodeURIComponent(orderId)}`);

export const listMyPayments = () => v3Fetch('/api/v3/billing/me/payments');

export const refreshMyStorage = () =>
  v3Fetch('/api/v3/billing/me/storage/refresh', { method: 'POST' });

export const createAssistedEstimate = (payload) =>
  v3Fetch('/api/v3/billing/orders/assisted', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const approveBillingOrder = (orderId, idempotencyKey) =>
  v3Fetch(`/api/v3/billing/orders/${encodeURIComponent(orderId)}/approve`, {
    method: 'POST',
    body: JSON.stringify({ idempotency_key: idempotencyKey }),
  });

export const cancelBillingOrder = (orderId) =>
  v3Fetch(`/api/v3/billing/orders/${encodeURIComponent(orderId)}/cancel`, {
    method: 'POST',
    body: JSON.stringify({}),
  });

export const createManagedOrder = (payload) =>
  v3Fetch('/api/v3/billing/managed/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// ---------------------------------------------------------------------------
// D37 — admin billing operations (staff + can_manage_billing)
// ---------------------------------------------------------------------------

export const listSubscriptions = () => v3Fetch('/api/v3/commercial/subscriptions');

export const activateSubscription = (payload) =>
  v3Fetch('/api/v3/commercial/subscriptions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const changeSubscriptionStatus = (subscriptionId, lifecycleStatus) =>
  v3Fetch(`/api/v3/commercial/subscriptions/${encodeURIComponent(subscriptionId)}/status`, {
    method: 'POST',
    body: JSON.stringify({ lifecycle_status: lifecycleStatus }),
  });

export const listAdminOrders = (status) =>
  v3Fetch(`/api/v3/commercial/orders${status ? `?status=${encodeURIComponent(status)}` : ''}`);

export const completeAdminOrder = (orderId) =>
  v3Fetch(`/api/v3/commercial/orders/${encodeURIComponent(orderId)}/complete`, {
    method: 'POST',
    body: JSON.stringify({}),
  });

export const listAdminStorage = () => v3Fetch('/api/v3/commercial/storage');

export const listAdminPayments = () => v3Fetch('/api/v3/commercial/payments');

export const getAdminEntitlement = (organizationId) =>
  v3Fetch(`/api/v3/commercial/entitlement/${encodeURIComponent(organizationId)}`);

export const adminGrantCredits = (payload) =>
  v3Fetch('/api/v3/commercial/credits/grant', { method: 'POST', body: JSON.stringify(payload) });

export const adminAdjustCredits = (payload) =>
  v3Fetch('/api/v3/commercial/credits/adjust', { method: 'POST', body: JSON.stringify(payload) });

export const adminReverseCredits = (payload) =>
  v3Fetch('/api/v3/commercial/credits/reverse', { method: 'POST', body: JSON.stringify(payload) });

export const adminRefundCredits = (payload) =>
  v3Fetch('/api/v3/commercial/credits/refund', { method: 'POST', body: JSON.stringify(payload) });

export const adminRolloverCredits = (payload) =>
  v3Fetch('/api/v3/commercial/credits/rollover', { method: 'POST', body: JSON.stringify(payload) });


// ---------------------------------------------------------------------------
// Customer Review & Approve (D2/D5/G-P0-2) — /api/v3/processing/*
// ---------------------------------------------------------------------------

/** Items awaiting customer review (evidence-first review queue). */
export const getCustomerReviewQueue = (organizationId) =>
  v3Fetch(`/api/v3/processing/customer-review?organization_id=${encodeURIComponent(organizationId)}`);

/** Approve/reject a processed item. Rejection requires a reason (D5). */
export const submitCustomerReview = (itemId, { approved, rejection_reason, customer_notes }) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/customer-review`, {
    method: 'POST',
    body: JSON.stringify({ approved, rejection_reason, customer_notes }),
  });

// ---------------------------------------------------------------------------
// Customer processing workspace (CL-54) — /api/v3/processing/* (org-scoped)
//
// The customer workspace uses ONLY the org-scoped processing surface. The
// staff/PE surfaces (/api/v3/ops/*, /api/v3/ops/entities/*) are require_staff
// and are never called from the customer application.
// ---------------------------------------------------------------------------

/** Split-screen workspace payload for one item (source + data + status + issues). */
export const getProcessingItemWorkspace = (itemId) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/workspace`);

/** Claim a pipeline stage for an item (server-enforced state machine). */
export const startProcessingItem = (itemId, stage) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/start`, {
    method: 'POST',
    body: JSON.stringify({ stage }),
  });

/** Persist the customer's confirmed extraction values (advances to extracted). */
export const saveProcessingExtraction = (itemId, extractedData) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/extract`, {
    method: 'POST',
    body: JSON.stringify({ extracted_data: extractedData }),
  });

/** Persist mapping decisions (factor + facility/asset/supplier) → mapped. */
export const saveProcessingMapping = (itemId, payload) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/map`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/** Run the server-side data-quality validation for an item. */
export const validateProcessingItem = (itemId) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/validate`, { method: 'POST' });

/** Run the authoritative server-side calculation (client never supplies the result). */
export const calculateProcessingItem = (itemId, payload = {}) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/calculate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/** Emission-factor + tenant candidates for the mapping picker. */
export const getProcessingMappingOptions = (itemId) =>
  v3Fetch(`/api/v3/processing/items/${encodeURIComponent(itemId)}/mapping-options`);

/** Pipeline status (per-stage counts + progress) for the organisation. */
export const getProcessingStatus = (organizationId) =>
  v3Fetch(`/api/v3/processing/status?organization_id=${encodeURIComponent(organizationId)}`);

/** Per-stage queue listing for the organisation. */
export const getProcessingQueue = (organizationId, stage, limit = 100) =>
  v3Fetch(
    `/api/v3/processing/queue?organization_id=${encodeURIComponent(organizationId)}&stage=${encodeURIComponent(stage)}&limit=${limit}`
  );

/** Next item awaiting `stage` work (operator-style high-volume flow, org-scoped). */
export const getProcessingNextItem = (organizationId, stage) =>
  v3Fetch(`/api/v3/processing/next-item?organization_id=${encodeURIComponent(organizationId)}&stage=${encodeURIComponent(stage)}`);

/** Processing issues for the organisation. */
export const getProcessingIssues = (organizationId, status) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  if (status) query.set('status', status);
  return v3Fetch(`/api/v3/processing/issues?${query.toString()}`);
};

// ---------------------------------------------------------------------------
// Durable automatic-processing jobs (Phase A / CL-56) — /api/v3/processing/jobs
// ---------------------------------------------------------------------------

/** List durable automatic-processing jobs (filters optional). */
export const getProcessingJobs = (organizationId, params = {}) => {
  const query = new URLSearchParams({ organization_id: organizationId });
  if (params.status) query.set('status', params.status);
  if (params.stage) query.set('stage', params.stage);
  if (params.limit) query.set('limit', String(params.limit));
  return v3Fetch(`/api/v3/processing/jobs?${query.toString()}`);
};

/** One durable job with its persisted pipeline outputs. */
export const getProcessingJob = (jobId) =>
  v3Fetch(`/api/v3/processing/jobs/${encodeURIComponent(jobId)}`);

/** Enqueue an uploaded document for automatic processing (Phase A). */
export const enqueueDocumentForProcessing = (fileId, payload = {}) =>
  v3Fetch(`/api/v3/processing/documents/${encodeURIComponent(fileId)}/enqueue`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/** Human gate: resume a blocked job after corrections (Phase A). */
export const confirmProcessingJob = (jobId, payload = {}) =>
  v3Fetch(`/api/v3/processing/jobs/${encodeURIComponent(jobId)}/confirm`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/** Retry a failed/blocked job (dead-letter recovery). */
export const retryProcessingJob = (jobId) =>
  v3Fetch(`/api/v3/processing/jobs/${encodeURIComponent(jobId)}/retry`, {
    method: 'POST',
    body: JSON.stringify({}),
  });

/** Distinct customer/owner review of a durable job (D5 — owner/admin only). */
export const reviewProcessingJob = (jobId, payload) =>
  v3Fetch(`/api/v3/processing/jobs/${encodeURIComponent(jobId)}/review`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/**
 * Resolve the caller's primary organisation + membership role (owner/admin/
 * member/viewer). Used to gate approver actions in the customer review surface
 * (D5) — the backend remains the authoritative boundary.
 */
export const resolveV3Membership = async () => {
  const token = await getV3Token();
  if (!token) return null;
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;
  const response = await fetch(
    `${API_URL}/api/organizations/members/user/${user.id}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) return null;
  const data = await response.json();
  return {
    org: data?.primary_organization || data?.organization || null,
    role: data?.primary_role || null,
  };
};

// ---------------------------------------------------------------------------
// Custom Factors (D9/G-P0-3) — /api/v3/customer-factors
// ---------------------------------------------------------------------------

export const listCustomerFactors = (organizationId) =>
  v3Fetch(`/api/v3/customer-factors?organization_id=${encodeURIComponent(organizationId)}`);

export const getCustomerFactor = (factorId) =>
  v3Fetch(`/api/v3/customer-factors/${encodeURIComponent(factorId)}`);

export const createCustomerFactor = (payload) =>
  v3Fetch('/api/v3/customer-factors', { method: 'POST', body: JSON.stringify(payload) });

export const updateCustomerFactor = (factorId, payload) =>
  v3Fetch(`/api/v3/customer-factors/${encodeURIComponent(factorId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const approveCustomerFactor = (factorId) =>
  v3Fetch(`/api/v3/customer-factors/${encodeURIComponent(factorId)}/approve`, { method: 'POST' });

export const deactivateCustomerFactor = (factorId) =>
  v3Fetch(`/api/v3/customer-factors/${encodeURIComponent(factorId)}/deactivate`, { method: 'POST' });

// ---------------------------------------------------------------------------
// Master data — Vehicles (D17/G-P1-2) — /api/v3/vehicles (org-scoped)
// ---------------------------------------------------------------------------

export const listVehicles = (organizationId) =>
  v3Fetch(`/api/v3/vehicles?organization_id=${encodeURIComponent(organizationId)}`);

export const createVehicle = (payload) =>
  v3Fetch('/api/v3/vehicles', { method: 'POST', body: JSON.stringify(payload) });

export const updateVehicle = (vehicleId, payload) =>
  v3Fetch(`/api/v3/vehicles/${encodeURIComponent(vehicleId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const removeVehicle = (vehicleId) =>
  v3Fetch(`/api/v3/vehicles/${encodeURIComponent(vehicleId)}`, { method: 'DELETE' });

// ---------------------------------------------------------------------------
// Retention configuration (N3) — /api/v3/settings/retention (org admin)
// ---------------------------------------------------------------------------

export const getRetentionSettings = () => v3Fetch('/api/v3/settings/retention');

export const updateRetentionSettings = (payload) =>
  v3Fetch('/api/v3/settings/retention', { method: 'PUT', body: JSON.stringify(payload) });

// ---------------------------------------------------------------------------
// Analytics & Integrations (GA4) — /api/v3/settings/analytics
// ---------------------------------------------------------------------------
// Only Google Analytics 4 is implemented. The read is public (the public
// marketing surface must know whether to load GA4 before a visitor signs in);
// every write requires CarbonTally internal admin authority.

export const getAnalyticsSettings = () => v3Fetch('/api/v3/settings/analytics');

export const updateAnalyticsSettings = (payload) =>
  v3Fetch('/api/v3/settings/analytics', { method: 'PUT', body: JSON.stringify(payload) });

// ---------------------------------------------------------------------------
// Org-scoped search (G-P1-1) — /api/v3/search
// ---------------------------------------------------------------------------

export const searchOrg = (organizationId, q, limit = 20) =>
  v3Fetch(`/api/v3/search?organization_id=${encodeURIComponent(organizationId)}&q=${encodeURIComponent(q)}&limit=${limit}`);

// ---------------------------------------------------------------------------
// CarbonTally Insight (I6 UI — authorized I6 stage)
//
// The Insight workspace consumes the **closed** I1–I4 backend contracts only:
// creator-private conversations and messages (I1), creator-private interactions
// (I4), and the ratified I3 read-only tool surface (reference resolution).
//
// There is deliberately no client-side authorization here. Every call is
// re-authorized server-side through the closed I2 boundary; a stored id or a
// reference is only ever a locator handed back to the backend, never a grant.
// A foreign/unauthorized resource answers 404 or a non-success status and the
// UI renders a non-disclosing state.
// ---------------------------------------------------------------------------

const insightQuery = (params) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) search.set(key, String(value));
  });
  return search.toString();
};

/** The caller's own (creator-private) Insight conversations for one org. */
export const listInsightConversations = (organizationId, { limit = 50, offset = 0 } = {}) =>
  v3Fetch(`/api/v3/insight/conversations?${insightQuery({ organization_id: organizationId, limit, offset })}`);

/** Start a new creator-private conversation. */
export const createInsightConversation = (organizationId, title) =>
  v3Fetch('/api/v3/insight/conversations', {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, title: title ? title : null }),
  });

/** The persisted message history (question + narration) of a conversation. */
export const listInsightMessages = (organizationId, conversationId, { limit = 200, offset = 0 } = {}) =>
  v3Fetch(
    `/api/v3/insight/conversations/${encodeURIComponent(conversationId)}/messages?`
    + insightQuery({ organization_id: organizationId, limit, offset }),
  );

/**
 * Run one authorized interaction (the I4 deterministic-first path).
 *
 * `idempotencyKey` is a plain client-generated request key so a retried submit
 * cannot create a duplicate interaction; the backend owns the replay decision
 * and reports it truthfully through `replayed`.
 */
export const runInsightInteraction = ({
  organizationId,
  conversationId,
  question,
  idempotencyKey,
  narration,
}) =>
  v3Fetch('/api/v3/insight/interactions', {
    method: 'POST',
    body: JSON.stringify({
      organization_id: organizationId,
      conversation_id: conversationId,
      question,
      ...(idempotencyKey ? { idempotency_key: idempotencyKey } : {}),
      ...(narration ? { narration } : {}),
    }),
  });

/** The caller's own interactions (optionally for one conversation). */
export const listInsightInteractions = (organizationId, { conversationId, limit = 50, offset = 0 } = {}) =>
  v3Fetch(`/api/v3/insight/interactions?${insightQuery({
    organization_id: organizationId,
    conversation_id: conversationId,
    limit,
    offset,
  })}`);

/** One interaction with its tool-call evidence and reference locators. */
export const getInsightInteraction = (organizationId, interactionId) =>
  v3Fetch(
    `/api/v3/insight/interactions/${encodeURIComponent(interactionId)}?`
    + insightQuery({ organization_id: organizationId }),
  );

/**
 * Reference resolution through the ratified I3 read-only tool surface.
 *
 * This is the only authorized path for resolving a reference identifier: the
 * backend re-checks the caller's scope against the resolved object and answers
 * `not_authorized`/`no_data` without the UI having made any access decision.
 */
export const invokeInsightTool = (organizationId, tool, input = {}) =>
  v3Fetch('/api/v3/insight/tools/invoke', {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, tool, input }),
  });

