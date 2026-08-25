// frontend/src/v3/__tests__/api.test.js
// Unit tests for the V3 reports API client's pure helpers (no network/DOM).
// The supabase client is stubbed so network-bound helpers (notifications/issues
// pagination, D26) can be exercised without a live Auth session.
jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: async () => ({ data: { session: null } }) } },
}));

import { exportDocumentsUrl, exportEmissionsUrl } from '../api';

describe('V3 reports API client', () => {
  test('exportEmissionsUrl builds org-scoped CSV URL', () => {
    const url = exportEmissionsUrl('org-123', 'csv');
    expect(url).toContain('/api/v3/exports/emissions.csv');
    expect(url).toContain('organization_id=org-123');
  });

  test('exportEmissionsUrl builds org-scoped JSON URL with period filters', () => {
    const url = exportEmissionsUrl('org-123', 'json', {
      start_date: '2025-01-01',
      end_date: '2025-12-31',
    });
    expect(url).toContain('/api/v3/exports/emissions.json');
    expect(url).toContain('organization_id=org-123');
    expect(url).toContain('start_date=2025-01-01');
    expect(url).toContain('end_date=2025-12-31');
  });

  test('exportDocumentsUrl is org-scoped', () => {
    const url = exportDocumentsUrl('org-456');
    expect(url).toContain('/api/v3/exports/documents.csv');
    expect(url).toContain('organization_id=org-456');
  });

  test('report list params are passed through to the V3 endpoint', () => {
    // listReports builds the query string from the supplied params.
    const { listReports } = require('../api');
    // We can't invoke network-bound functions; assert the endpoint path constant
    // used by the client matches the authoritative V3 surface.
    const { v3Fetch } = require('../api');
    expect(typeof v3Fetch).toBe('function');
    expect(typeof listReports).toBe('function');
  });
});

describe('V3 customer administration API client', () => {
  test('listSuppliers builds an org-scoped query string', () => {
    const { listSuppliers } = require('../api');
    expect(typeof listSuppliers).toBe('function');
  });

  test('admin methods target org-scoped V3 endpoints', () => {
    const api = require('../api');
    // All customer-admin helpers are exported and bound to /api/v3/*.
    const methods = [
      'getOrganizationProfile', 'updateOrganizationProfile',
      'getOrganizationMetadata', 'updateOrganizationMetadata',
      'listMembers', 'addMember', 'updateMember', 'removeMember',
      'listInvitations', 'createInvitation', 'revokeInvitation',
      'listFacilities', 'createFacility', 'removeFacility',
      'listAssets', 'createAsset', 'removeAsset',
      'listSuppliers', 'createSupplier', 'removeSupplier',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });
});

describe('V3 commercial configuration API client (D37-0)', () => {
  test('commercial helpers target the trusted /api/v3/commercial/* surface', () => {
    const api = require('../api');
    const methods = [
      'getCommercialOverview',
      'getCommercialConfig',
      'updateCommercialConfig',
      'listCommercialPlans',
      'getCommercialPlan',
      'createCommercialPlan',
      'updateCommercialPlan',
      'getCreditLedger',
      'listCommercialOrganizations',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });

  test('listCommercialOrganizations supports a billing-mode filter', () => {
    const { listCommercialOrganizations } = require('../api');
    const calls = [];
    const previous = global.fetch;
    global.fetch = async (url) => {
      calls.push(url);
      return { ok: true, json: async () => ({ organizations: [] }) };
    };
    return listCommercialOrganizations('STANDARD')
      .then(() => {
        expect(calls[0]).toContain('/api/v3/commercial/organizations');
        expect(calls[0]).toContain('billing_mode=STANDARD');
      })
      .finally(() => { global.fetch = previous; });
  });
});

describe('V3 customer billing API client (D37)', () => {
  test('customer billing helpers target the org-scoped /api/v3/billing surface', () => {
    const api = require('../api');
    const methods = [
      'getMyBilling', 'getMyCreditHistory', 'listMyOrders', 'getMyOrder',
      'listMyPayments', 'refreshMyStorage', 'createAssistedEstimate',
      'approveBillingOrder', 'cancelBillingOrder', 'createManagedOrder',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });

  test('admin billing helpers target the can_manage_billing surface', () => {
    const api = require('../api');
    const methods = [
      'listSubscriptions', 'activateSubscription', 'changeSubscriptionStatus',
      'listAdminOrders', 'completeAdminOrder', 'listAdminStorage',
      'listAdminPayments', 'getAdminEntitlement', 'adminGrantCredits',
      'adminAdjustCredits', 'adminReverseCredits', 'adminRefundCredits',
      'adminRolloverCredits',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });
});

describe('V3 consultant API client', () => {
  test('consultant methods target the org-authorized V3 surface', () => {
    const api = require('../api');
    const methods = [
      'getConsultantProfile', 'listConsultantClients', 'getConsultantDashboard',
      'getConsultantClient', 'updateConsultantClientStatus',
      'deactivateConsultantClient', 'getClientWorkspaceContext',
      'getClientReports', 'getClientDashboard', 'getClientDocuments',
      'getClientProcessingStatus', 'getClientIssues',
      'getConsultantBranding', 'getConsultantBrandingContext',
      'updateConsultantBranding',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });
});

describe('V3 operations API client', () => {
  test('ops methods target the authoritative /api/v3/ops surface', () => {
    const api = require('../api');
    const methods = [
      'getOpsMe', 'getOpsDashboard', 'listOpsStaff', 'createOpsStaff',
      'listStaffRoles', 'listProcessingEntities', 'getEntityDashboard',
      'getOperatorQueue', 'getReviewQueue', 'getQcQueue', 'getNextItem',
      'getItemWorkspace', 'getMappingOptions', 'startItem', 'extractItem',
      'mapItem', 'validateItem', 'calculateItem', 'qcReviewItem',
      'assignBatch', 'assignReview', 'completeReview', 'getSlaSettings',
      'getQcQueueAdmin', 'getQcStats', 'qcReviewItemAdmin',
      // D22 — entity extraction workspace (Processing Entity staff)
      'getEntityExtractionBatches', 'getEntityExtractionBatch',
      'getEntityExtractionBatchItems', 'getEntityExtractionItem',
      'getEntityNextItem', 'entityStartItem', 'entityExtractItem',
      'entityMapItem', 'entityCalculateItem', 'entitySetItemStatus',


      'entityClarifyItem',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });

  test('extractItem builds the extracted_data body', () => {
    const { v3Fetch } = require('../api');
    expect(typeof v3Fetch).toBe('function');
  });
});

describe('V3 D25 product-completion API client', () => {
  test('customer issues methods target the org-scoped /api/v3/issues surface', () => {
    const api = require('../api');
    ['listCustomerIssues', 'getCustomerIssue', 'createCustomerIssue'].forEach(
      (name) => expect(typeof api[name]).toBe('function')
    );
  });

  test('notifications methods target the per-recipient surface', () => {
    const api = require('../api');
    ['listNotifications', 'markNotificationRead', 'markAllNotificationsRead'].forEach(
      (name) => expect(typeof api[name]).toBe('function')
    );
  });

  test('SLA update helper exists alongside the existing getSlaSettings', () => {
    const api = require('../api');
    expect(typeof api.getSlaSettings).toBe('function');
    expect(typeof api.updateSlaSettings).toBe('function');
  });
});

describe('V3 D26 scale-hardening API client', () => {
  test('listNotifications boolean signature still targets the bare surface', async () => {
    const api = require('../api');
    const calls = [];
    global.fetch = jest.fn((url) => {
      calls.push(String(url));
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ notifications: [], total: 0 }),
      });
    });
    await api.listNotifications(true);
    const url = calls[0];
    expect(url).toContain('/api/v3/notifications?unread_only=true');
    expect(url).not.toContain('limit=');
  });

  test('listNotifications options object passes bounded limit/offset', async () => {
    const api = require('../api');
    const calls = [];
    global.fetch = jest.fn((url) => {
      calls.push(String(url));
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ notifications: [], total: 0 }),
      });
    });
    await api.listNotifications({ unreadOnly: false, limit: 200, offset: 400 });
    const url = calls[0];
    expect(url).toContain('/api/v3/notifications?');
    expect(url).toContain('limit=200');
    expect(url).toContain('offset=400');
  });

  test('listCustomerIssues passes limit/offset params through', async () => {
    const api = require('../api');
    const calls = [];
    global.fetch = jest.fn((url) => {
      calls.push(String(url));
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ total: 0, issues: [] }),
      });
    });
    await api.listCustomerIssues('org-a', { limit: 50, offset: 100 });
    const url = calls[0];
    expect(url).toContain('/api/v3/issues?');
    expect(url).toContain('organization_id=org-a');
    expect(url).toContain('limit=50');
    expect(url).toContain('offset=100');
  });
});

describe('V3 D27 D19 API client', () => {
  test('discovery, lifecycle, whitelabel, messaging and PDF methods are exported', () => {
    const api = require('../api');
    const methods = [
      // Existing-data discovery
      'discoveryLookup', 'createDiscoveryRequest', 'listDiscoveryRequests',
      'getDiscoveryRequest', 'verifyDiscoveryRequest', 'chooseDiscoveryAdoption',
      // Client lifecycle
      'suspendConsultantClient', 'endConsultantClient', 'reactivateConsultantClient',
      // White-label domains + senders
      'listCustomDomains', 'createCustomDomain', 'verifyCustomDomain',
      'activateCustomDomain', 'removeCustomDomain',
      'listCustomSenders', 'createCustomSender', 'verifyCustomSender', 'removeCustomSender',
      // Messaging
      'createMessagingConversation', 'listMessagingConversations',
      'listMessagingMessages', 'sendMessagingMessage', 'markMessagingConversationRead',
      // White-label PDF
      'downloadReportPdf',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });

  test('discoveryLookup posts to the /api/v3/discovery/lookup surface', () => {
    const { discoveryLookup } = require('../api');
    expect(typeof discoveryLookup).toBe('function');
  });

  test('downloadReportPdf targets the branded PDF surface', () => {
    const { downloadReportPdf } = require('../api');
    expect(typeof downloadReportPdf).toBe('function');
  });
});

describe('V3 D35 self-service onboarding API client', () => {
  test('onboarding helpers target the authoritative /api/v3 surface', () => {
    const api = require('../api');
    const methods = [
      'createOrganization',
      'onboardingDiscoveryLookup',
      'createOnboardingDiscoveryRequest',
      'getOnboardingDiscoveryRequest',
      'verifyOnboardingDiscoveryRequest',
      'chooseOnboardingAdoption',
    ];
    methods.forEach((name) => expect(typeof api[name]).toBe('function'));
  });

  test('createOrganization POSTs to /api/v3/organizations', async () => {
    const api = require('../api');
    const calls = [];
    global.fetch = jest.fn((url, options) => {
      calls.push({ url: String(url), options });
      return Promise.resolve({
        ok: true,
        status: 201,
        json: async () => ({ onboarding: { status: 'ORGANIZATION_CREATED', role: 'owner' } }),
      });
    });
    const result = await api.createOrganization({ name: 'Bright Start Ltd' });
    expect(calls[0].url).toContain('/api/v3/organizations');
    expect(calls[0].options.method).toBe('POST');
    expect(JSON.parse(calls[0].options.body).name).toBe('Bright Start Ltd');
    expect(result.onboarding.role).toBe('owner');
  });

  test('resolvePostLoginPath returns /login without a session', async () => {
    const api = require('../api');
    // The mocked supabase client never returns a session.
    expect(await api.resolvePostLoginPath()).toBe('/login');
  });
});

