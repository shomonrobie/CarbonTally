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
    // Keep the real backend message visible to developers.
    console.error(`[CarbonTally V3] ${options.method || 'GET'} ${path} → ${response.status}:`, raw);
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

// D29/F5 — resolve the authenticated actor's landing workspace from
// SERVER-AUTHORITATIVE role endpoints. This is the single post-login /
// session-restore routing decision; it never uses localStorage as an
// authorization source and never trusts client-supplied role claims.
//   org member (customer/owner)  -> /home
//   staff (incl. entity staff)   -> /ops  (OperationsPage renders the
//                                       entity workspace for entity staff)
//   consultant                   -> /consultant
//   authenticated but no role    -> /home (role guards redirect gracefully)
export const resolvePostLoginPath = async () => {
  if (!(await getV3Token())) return '/login';
  try {
    if (await resolveV3Organization()) return '/home';
  } catch (_e) { /* continue to staff/consultant resolution */ }
  try {
    if (await getOpsMe()) return '/ops';
  } catch (_e) { /* continue to consultant resolution */ }
  try {
    if (await getConsultantProfile()) return '/consultant';
  } catch (_e) { /* continue to onboarding */ }
  // D35 — an authenticated user with no org/staff/consultant relationship is a
  // brand-new customer: land on the self-service onboarding surface instead of
  // the legacy /dashboard or a dead-end /home empty state.
  return '/onboarding';
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

export const getConsultantProfile = () => v3Fetch('/api/v3/consultants/me');

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

export const getConsultantClient = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}`);

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

export const getClientProcessingStatus = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/processing/status`);

export const getClientIssues = (clientId) =>
  v3Fetch(`/api/v3/consultants/clients/${clientId}/issues`);

// ---------------------------------------------------------------------------
// Internal Operations API (V3 authoritative surface — /api/v3/ops/*)
// ---------------------------------------------------------------------------

export const getOpsMe = () => v3Fetch('/api/v3/ops/me');

export const getOpsDashboard = () => v3Fetch('/api/v3/ops/dashboard');

export const listOpsStaff = () => v3Fetch('/api/v3/ops/staff');

export const createOpsStaff = (payload) =>
  v3Fetch('/api/v3/ops/staff', { method: 'POST', body: JSON.stringify(payload) });

export const listStaffRoles = () => v3Fetch('/api/v3/ops/staff-roles');

export const updateOpsStaff = (profileId, payload) =>
  v3Fetch(`/api/v3/ops/staff/${profileId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const listProcessingEntities = () => v3Fetch('/api/v3/ops/entities');

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

export const getOperatorQueue = (status = '') => {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return v3Fetch(`/api/v3/ops/queues/operator${query}`);
};

export const getReviewQueue = (params = {}) => {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.assigned_to) query.set('assigned_to', params.assigned_to);
  const qs = query.toString();
  return v3Fetch(`/api/v3/ops/queues/review${qs ? `?${qs}` : ''}`);
};

export const getQcQueue = () => v3Fetch('/api/v3/ops/queues/qc');

export const getNextItem = (stage) =>
  v3Fetch(`/api/v3/ops/next-item?stage=${encodeURIComponent(stage)}`);

export const getItemWorkspace = (itemId) =>
  v3Fetch(`/api/v3/ops/items/${itemId}/workspace`);

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

export const createMessagingConversation = (organizationId, subject) =>
  v3Fetch('/api/v3/messaging/conversations', {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, subject }),
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
  if (params.limit) query.set('limit', params.limit);
  if (params.offset) query.set('offset', params.offset);
  return v3Fetch(`/api/v3/ops/reporting/audit${query.toString() ? `?${query.toString()}` : ''}`);
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
// Org-scoped search (G-P1-1) — /api/v3/search
// ---------------------------------------------------------------------------

export const searchOrg = (organizationId, q, limit = 20) =>
  v3Fetch(`/api/v3/search?organization_id=${encodeURIComponent(organizationId)}&q=${encodeURIComponent(q)}&limit=${limit}`);

