// Integration Management Module - SPA Compatible

(function() {
    console.log('🔌 Integration Management JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var apiKeys = [
        { id: 'ak_001', name: 'Production API Key', key: 'ct_pk_live_xxxxxxxxxxxxxxxxxxxxxx', created: '2026-12-01', expires: '2027-03-01', scope: 'write', lastUsed: '2026-12-15', isActive: true },
        { id: 'ak_002', name: 'Development Key', key: 'ct_pk_dev_yyyyyyyyyyyyyyyyyyyyyy', created: '2026-11-15', expires: 'never', scope: 'admin', lastUsed: '2026-12-10', isActive: true },
        { id: 'ak_003', name: 'Staging API Key', key: 'ct_pk_stg_zzzzzzzzzzzzzzzzzzzzzz', created: '2026-10-20', expires: '2027-01-20', scope: 'read', lastUsed: '2026-12-01', isActive: true },
        { id: 'ak_004', name: 'Old Production Key', key: 'ct_pk_old_aaaaaaaaaaaaaaaaaaaaaa', created: '2026-08-15', expires: '2026-11-15', scope: 'write', lastUsed: '2026-11-10', isActive: false }
    ];

    var integrations = [
        { id: 'int_001', name: 'Persefoni', description: 'Enterprise carbon accounting platform integration', icon: '🌍', status: 'connected', lastSync: '2026-12-15 14:30', type: 'Carbon Accounting' },
        { id: 'int_002', name: 'SAP S/4HANA', description: 'ERP integration for financial and operational data', icon: '🏢', status: 'connected', lastSync: '2026-12-15 12:00', type: 'ERP' },
        { id: 'int_003', name: 'Salesforce', description: 'CRM and customer sustainability data integration', icon: '☁️', status: 'disconnected', lastSync: '2026-12-10 09:00', type: 'CRM' },
        { id: 'int_004', name: 'Watershed', description: 'Climate data and emissions tracking platform', icon: '💧', status: 'error', lastSync: '2026-12-14 16:45', type: 'Carbon Accounting' },
        { id: 'int_005', name: 'Microsoft Sustainability Manager', description: 'Microsoft Cloud for Sustainability integration', icon: '🖥️', status: 'connected', lastSync: '2026-12-15 10:00', type: 'Carbon Accounting' },
        { id: 'int_006', name: 'Oracle ERP Cloud', description: 'Enterprise resource planning integration', icon: '☕', status: 'disconnected', lastSync: '2026-12-08 14:00', type: 'ERP' }
    ];

    var webhooks = [
        { id: 'wh_001', url: 'https://api.example.com/webhook/v1/emissions', secret: 'whsec_xxxxxxxxxxxxxx', format: 'json', events: ['document.uploaded', 'document.approved', 'emission.added'], status: 'active', lastTriggered: '2026-12-15 14:30', successCount: 245, failureCount: 3 },
        { id: 'wh_002', url: 'https://dashboard.partner.com/webhook', secret: 'whsec_yyyyyyyyyyyyyy', format: 'json', events: ['report.generated', 'sla.breached'], status: 'active', lastTriggered: '2026-12-14 22:15', successCount: 89, failureCount: 1 },
        { id: 'wh_003', url: 'https://internal.company.com/carbon-webhook', secret: 'whsec_zzzzzzzzzzzzzz', format: 'xml', events: ['document.uploaded', 'document.approved', 'emission.added', 'report.generated'], status: 'inactive', lastTriggered: '2026-12-10 08:00', successCount: 156, failureCount: 12 },
        { id: 'wh_004', url: 'https://audit.logic.com/incoming', secret: 'whsec_aaaaaaaaaaaaaa', format: 'json', events: ['document.approved', 'sla.breached'], status: 'active', lastTriggered: '2026-12-15 13:45', successCount: 67, failureCount: 0 },
        { id: 'wh_005', url: 'https://analytics.partner.io/webhook', secret: 'whsec_bbbbbbbbbbbbbb', format: 'json', events: ['emission.added', 'report.generated'], status: 'active', lastTriggered: '2026-12-13 09:30', successCount: 34, failureCount: 2 },
        { id: 'wh_006', url: 'https://internal.logging.internal/webhook', secret: 'whsec_cccccccccccccc', format: 'form', events: ['document.uploaded'], status: 'inactive', lastTriggered: '2026-12-01 11:00', successCount: 12, failureCount: 0 }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentTab = 'integrations';
    var currentPage = {
        integrations: 1,
        'api-keys': 1,
        webhooks: 1
    };
    var perPage = 6;
    var currentSort = { field: 'name', direction: 'asc' };
    var toastTimeout = null;
    var viewingId = null;

    var filterStatus = 'all';
    var filterType = 'all';
    var filterSearch = '';

    // ============================================
    // DOM REFS (lazy loaded)
    // ============================================

    function getEl(id) { return document.getElementById(id); }

    // ============================================
    // TOAST
    // ============================================

    function showToast(message, type) {
        type = type || 'success';
        var icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
        
        var old = document.querySelector('.custom-toast');
        if (old) old.remove();
        if (!document.body) return;
        
        var el = document.createElement('div');
        el.className = 'custom-toast';
        el.style.cssText = 'position:fixed;bottom:24px;right:24px;background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius);padding:12px 20px;box-shadow:var(--shadow-lg);z-index:99999;font-size:14px;animation:slideUp 0.3s ease;max-width:400px;color:hsl(var(--foreground));display:flex;align-items:center;gap:10px;';
        el.innerHTML = '<span>' + (icons[type] || 'ℹ️') + '</span><span>' + message + '</span>';
        document.body.appendChild(el);
        
        if (toastTimeout) clearTimeout(toastTimeout);
        toastTimeout = setTimeout(function() {
            if (el && el.parentNode) {
                el.style.opacity = '0';
                el.style.transition = 'opacity 0.3s';
                setTimeout(function() { if (el && el.parentNode) el.remove(); }, 300);
            }
            toastTimeout = null;
        }, 3000);
    }

    // ============================================
    // TAB FUNCTIONS
    // ============================================

    function switchTab(tab) {
        currentTab = tab;
        var tabs = document.querySelectorAll('.tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.toggle('active', tabs[i].getAttribute('data-tab') === tab);
        }
        var sections = document.querySelectorAll('[id^="tab-"]');
        for (var j = 0; j < sections.length; j++) {
            sections[j].style.display = sections[j].id === 'tab-' + tab ? 'block' : 'none';
        }
        
        // Show/hide filter bar
        var filterBar = getEl('filterBar');
        if (filterBar) {
            filterBar.style.display = tab === 'integrations' ? 'flex' : 'none';
        }
        
        renderCurrentTab();
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderStats() {
        var activeIntegrations = integrations.filter(function(i) { return i.status === 'connected'; }).length;
        var activeApiKeys = apiKeys.filter(function(k) { return k.isActive; }).length;
        var activeWebhooks = webhooks.filter(function(w) { return w.status === 'active'; }).length;
        var failedSyncs = integrations.filter(function(i) { return i.status === 'error'; }).length;
        
        var el = getEl('statIntegrations');
        if (el) el.textContent = activeIntegrations;
        el = getEl('statApiKeys');
        if (el) el.textContent = activeApiKeys;
        el = getEl('statWebhooks');
        if (el) el.textContent = activeWebhooks;
        el = getEl('statFailed');
        if (el) el.textContent = failedSyncs;
    }

    function renderCurrentTab() {
        if (currentTab === 'integrations') renderIntegrations();
        else if (currentTab === 'api-keys') renderApiKeys();
        else if (currentTab === 'webhooks') renderWebhooks();
    }

    function applyFilters() {
        var statusEl = getEl('statusFilter');
        var typeEl = getEl('typeFilter');
        var searchEl = getEl('searchFilter');
        
        filterStatus = statusEl ? statusEl.value : 'all';
        filterType = typeEl ? typeEl.value : 'all';
        filterSearch = searchEl ? searchEl.value.toLowerCase().trim() : '';
        currentPage.integrations = 1;
        renderIntegrations();
    }

    function clearFilters() {
        var statusEl = getEl('statusFilter');
        var typeEl = getEl('typeFilter');
        var searchEl = getEl('searchFilter');
        
        if (statusEl) statusEl.value = 'all';
        if (typeEl) typeEl.value = 'all';
        if (searchEl) searchEl.value = '';
        filterStatus = 'all';
        filterType = 'all';
        filterSearch = '';
        currentPage.integrations = 1;
        renderIntegrations();
        showToast('🔄 Filters cleared');
    }

    // ============================================
    // INTEGRATIONS
    // ============================================

    function renderIntegrations() {
        var container = getEl('integrationsList');
        var countEl = getEl('integrationCount');
        var paginationEl = getEl('integrationPagination');
        if (!container) return;
        
        var filtered = integrations.slice();
        
        if (filterStatus !== 'all') {
            filtered = filtered.filter(function(i) { return i.status === filterStatus; });
        }
        if (filterType !== 'all') {
            filtered = filtered.filter(function(i) { return i.type === filterType; });
        }
        if (filterSearch) {
            filtered = filtered.filter(function(i) {
                return i.name.toLowerCase().indexOf(filterSearch) !== -1 ||
                    i.description.toLowerCase().indexOf(filterSearch) !== -1 ||
                    i.type.toLowerCase().indexOf(filterSearch) !== -1;
            });
        }
        
        // Sort
        filtered.sort(function(a, b) {
            var aVal = a[currentSort.field] || '';
            var bVal = b[currentSort.field] || '';
            if (typeof aVal === 'string') {
                return currentSort.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }
            return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        });
        
        if (countEl) countEl.textContent = filtered.length;
        
        var start = (currentPage.integrations - 1) * perPage;
        var pageItems = filtered.slice(start, start + perPage);
        
        if (pageItems.length === 0) {
            container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px 20px;color:hsl(var(--muted-foreground));">🔌 No integrations found</div>';
            renderPagination(paginationEl, filtered.length, 'integrations');
            return;
        }
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var int = pageItems[i];
            var statusBadge = int.status === 'connected' ? 'badge-success' : int.status === 'disconnected' ? 'badge-muted' : 'badge-destructive';
            var statusText = int.status === 'connected' ? '✅ Connected' : int.status === 'disconnected' ? '⚪ Disconnected' : '❌ Error';
            
            html +=
                '<div class="integration-card" onclick="viewIntegration(\'' + int.id + '\')">' +
                '<div class="integration-header">' +
                '<div class="integration-icon">' + int.icon + '<span class="name">' + int.name + '</span></div>' +
                '<span class="badge ' + statusBadge + '">' + statusText + '</span>' +
                '</div>' +
                '<div class="integration-desc">' + int.description + '</div>' +
                '<div class="integration-meta">' +
                '<span>📂 ' + int.type + '</span>' +
                '<span>🔄 Last sync: ' + int.lastSync + '</span>' +
                '</div>' +
                '<div class="integration-actions">' +
                '<button class="btn btn-outline btn-sm" onclick="event.stopPropagation();syncIntegration(\'' + int.id + '\')">🔄 Sync</button>' +
                (int.status === 'disconnected' ? '<button class="btn btn-primary btn-sm" onclick="event.stopPropagation();connectIntegration(\'' + int.id + '\')">🔗 Connect</button>' : '<button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();disconnectIntegration(\'' + int.id + '\')">🔌 Disconnect</button>') +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();viewIntegration(\'' + int.id + '\')">👁️</button>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderPagination(paginationEl, filtered.length, 'integrations');
    }

    function viewIntegration(id) {
        var int = null;
        for (var i = 0; i < integrations.length; i++) {
            if (integrations[i].id === id) { int = integrations[i]; break; }
        }
        if (!int) return;
        
        viewingId = id;
        var titleEl = getEl('detailTitle');
        var subtitleEl = getEl('detailSubtitle');
        var bodyEl = getEl('detailBody');
        var footerEl = getEl('detailFooter');
        var modal = getEl('detailModal');
        
        if (titleEl) titleEl.textContent = int.icon + ' ' + int.name;
        if (subtitleEl) subtitleEl.textContent = int.type + ' • ' + int.status.toUpperCase();
        
        if (bodyEl) {
            bodyEl.innerHTML =
                '<div class="detail-row"><span class="label">Name</span><span class="value">' + int.name + '</span></div>' +
                '<div class="detail-row"><span class="label">Type</span><span class="value">' + int.type + '</span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + int.status + '</span></div>' +
                '<div class="detail-row"><span class="label">Last Sync</span><span class="value">' + int.lastSync + '</span></div>' +
                '<div class="detail-row"><span class="label">Description</span><span class="value">' + int.description + '</span></div>';
        }
        
        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeDetailModal()">Close</button>' +
                (int.status === 'disconnected' ? '<button class="btn btn-primary btn-sm" onclick="connectIntegration(\'' + int.id + '\');closeDetailModal();">🔗 Connect</button>' : '') +
                '<button class="btn btn-outline btn-sm" onclick="syncIntegration(\'' + int.id + '\');closeDetailModal();">🔄 Sync</button>';
        }
        
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeDetailModal() {
        var modal = getEl('detailModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
        viewingId = null;
    }

    function syncIntegration(id) {
        var int = null;
        for (var i = 0; i < integrations.length; i++) {
            if (integrations[i].id === id) { int = integrations[i]; break; }
        }
        if (!int) return;
        
        showToast('🔄 Syncing ' + int.name + '...');
        setTimeout(function() {
            int.lastSync = new Date().toLocaleString();
            renderIntegrations();
            renderStats();
            showToast('✅ ' + int.name + ' synced successfully');
        }, 2000);
    }

    function connectIntegration(id) {
        var int = null;
        for (var i = 0; i < integrations.length; i++) {
            if (integrations[i].id === id) { int = integrations[i]; break; }
        }
        if (!int) return;
        
        int.status = 'connected';
        renderIntegrations();
        renderStats();
        showToast('🔗 Connected to ' + int.name);
    }

    function disconnectIntegration(id) {
        var int = null;
        for (var i = 0; i < integrations.length; i++) {
            if (integrations[i].id === id) { int = integrations[i]; break; }
        }
        if (!int) return;
        
        if (confirm('Disconnect ' + int.name + '?')) {
            int.status = 'disconnected';
            renderIntegrations();
            renderStats();
            showToast('🔌 Disconnected from ' + int.name);
        }
    }

    // ============================================
    // API KEYS
    // ============================================

    function renderApiKeys() {
        var container = getEl('apiKeysList');
        var paginationEl = getEl('apiKeyPagination');
        if (!container) return;
        
        if (apiKeys.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:40px 20px;"><div style="font-size:32px;margin-bottom:8px;">🔑</div><div>No API keys generated</div><div style="font-size:13px;">Create your first API key for programmatic access</div></div>';
            renderPagination(paginationEl, 0, 'api-keys');
            return;
        }
        
        var start = (currentPage['api-keys'] - 1) * perPage;
        var pageItems = apiKeys.slice(start, start + perPage);
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var key = pageItems[i];
            html +=
                '<div class="webhook-item">' +
                '<div style="display:flex;align-items:center;gap:12px;flex:1;flex-wrap:wrap;">' +
                '<div style="font-size:24px;">🔑</div>' +
                '<div class="webhook-info">' +
                '<div class="url">' + key.name + '</div>' +
                '<div class="meta">' +
                '<span>📅 Created ' + key.created + '</span>' +
                '<span>⏰ ' + (key.expires === 'never' ? 'Never expires' : 'Expires ' + key.expires) + '</span>' +
                '<span>🔒 Scope: ' + key.scope.toUpperCase() + '</span>' +
                '<span>📊 Last used: ' + key.lastUsed + '</span>' +
                '</div>' +
                '<div class="api-key-display"><span class="key">' + key.key + '</span><span class="badge ' + (key.isActive ? 'badge-success' : 'badge-destructive') + '">' + (key.isActive ? 'Active' : 'Revoked') + '</span></div>' +
                '</div>' +
                '</div>' +
                '<div style="display:flex;gap:4px;flex-shrink:0;">' +
                '<button class="btn btn-ghost btn-sm" onclick="copyApiKey(\'' + key.id + '\')" title="Copy">📋</button>' +
                (key.isActive ? '<button class="btn btn-ghost btn-sm" onclick="revokeApiKey(\'' + key.id + '\')" style="color:hsl(var(--destructive));" title="Revoke">🔒</button>' : '') +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderPagination(paginationEl, apiKeys.length, 'api-keys');
    }

    function showApiKeyModal() {
        var modal = getEl('apiKeyModal');
        if (!modal) return;
        
        var nameEl = getEl('apiKeyName');
        var expiryEl = getEl('apiKeyExpiry');
        var scopeEl = getEl('apiKeyScope');
        var ipsEl = getEl('apiKeyRestrictIps');
        var ipsGroupEl = getEl('apiKeyIpsGroup');
        
        if (nameEl) nameEl.value = '';
        if (expiryEl) expiryEl.value = '90';
        if (scopeEl) scopeEl.value = 'write';
        if (ipsEl) ipsEl.checked = false;
        if (ipsGroupEl) ipsGroupEl.style.display = 'none';
        
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeApiKeyModal() {
        var modal = getEl('apiKeyModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function toggleIpRestriction() {
        var ipsEl = getEl('apiKeyRestrictIps');
        var ipsGroupEl = getEl('apiKeyIpsGroup');
        if (ipsGroupEl) {
            ipsGroupEl.style.display = ipsEl && ipsEl.checked ? 'block' : 'none';
        }
    }

    function generateApiKey() {
        var nameEl = getEl('apiKeyName');
        var expiryEl = getEl('apiKeyExpiry');
        var scopeEl = getEl('apiKeyScope');
        
        var name = nameEl ? nameEl.value.trim() : '';
        var expiry = expiryEl ? expiryEl.value : '90';
        var scope = scopeEl ? scopeEl.value : 'write';
        
        if (!name) {
            showToast('⚠️ Please enter a key name', 'warning');
            return;
        }
        
        var chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        var randomStr = '';
        for (var i = 0; i < 24; i++) {
            randomStr += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        
        var newKey = {
            id: 'ak_' + String(apiKeys.length + 1).padStart(3, '0'),
            name: name,
            key: 'ct_pk_' + scope + '_' + randomStr,
            created: new Date().toISOString().split('T')[0],
            expires: expiry === 'never' ? 'never' : expiry + ' days',
            scope: scope,
            lastUsed: 'Never',
            isActive: true
        };
        
        apiKeys.push(newKey);
        closeApiKeyModal();
        renderApiKeys();
        renderStats();
        showToast('🔑 API Key generated: ' + name);
    }

    function copyApiKey(id) {
        var key = null;
        for (var i = 0; i < apiKeys.length; i++) {
            if (apiKeys[i].id === id) { key = apiKeys[i]; break; }
        }
        if (key) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(key.key).then(function() {
                    showToast('📋 Copied API key to clipboard');
                });
            } else {
                showToast('📋 Copy: ' + key.key);
            }
        }
    }

    function revokeApiKey(id) {
        var key = null;
        for (var i = 0; i < apiKeys.length; i++) {
            if (apiKeys[i].id === id) { key = apiKeys[i]; break; }
        }
        if (key && confirm('Revoke API key "' + key.name + '"?')) {
            key.isActive = false;
            renderApiKeys();
            renderStats();
            showToast('🔒 API key revoked: ' + key.name);
        }
    }

    // ============================================
    // WEBHOOKS
    // ============================================

    function renderWebhooks() {
        var container = getEl('webhooksList');
        var paginationEl = getEl('webhookPagination');
        if (!container) return;
        
        if (webhooks.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:40px 20px;"><div style="font-size:32px;margin-bottom:8px;">🔗</div><div>No webhooks configured</div><div style="font-size:13px;">Add a webhook to receive real-time event notifications</div></div>';
            renderPagination(paginationEl, 0, 'webhooks');
            return;
        }
        
        var start = (currentPage.webhooks - 1) * perPage;
        var pageItems = webhooks.slice(start, start + perPage);
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var wh = pageItems[i];
            var eventsHtml = '';
            for (var j = 0; j < wh.events.length; j++) {
                eventsHtml += '<span class="badge badge-muted">' + wh.events[j].replace('.', ' → ') + '</span>';
            }
            
            html +=
                '<div class="webhook-item">' +
                '<div style="display:flex;align-items:center;gap:12px;flex:1;flex-wrap:wrap;">' +
                '<div style="font-size:20px;">🔗</div>' +
                '<div class="webhook-info">' +
                '<div class="url">' + wh.url + '</div>' +
                '<div class="meta">' +
                '<span>📦 ' + wh.format.toUpperCase() + '</span>' +
                '<span>📅 ' + wh.events.length + ' events</span>' +
                '<span>✅ ' + wh.successCount + ' successes</span>' +
                '<span>❌ ' + wh.failureCount + ' failures</span>' +
                '<span>🔄 Last triggered: ' + wh.lastTriggered + '</span>' +
                '</div>' +
                '<div style="display:flex;gap:4px;margin-top:4px;flex-wrap:wrap;">' + eventsHtml + '</div>' +
                '</div>' +
                '</div>' +
                '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0;">' +
                '<span class="badge ' + (wh.status === 'active' ? 'badge-success' : 'badge-muted') + '">' + (wh.status === 'active' ? '🟢 Active' : '⚪ Inactive') + '</span>' +
                '<div style="display:flex;gap:4px;">' +
                '<button class="btn btn-ghost btn-sm" onclick="toggleWebhook(\'' + wh.id + '\')" title="Toggle">' + (wh.status === 'active' ? '⏸️' : '▶️') + '</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="editWebhook(\'' + wh.id + '\')" title="Edit">✏️</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="deleteWebhook(\'' + wh.id + '\')" style="color:hsl(var(--destructive));" title="Delete">🗑️</button>' +
                '</div>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderPagination(paginationEl, webhooks.length, 'webhooks');
    }

    function showWebhookModal() {
        var modal = getEl('webhookModal');
        if (!modal) return;
        
        var urlEl = getEl('webhookUrl');
        var secretEl = getEl('webhookSecret');
        var formatEl = getEl('webhookFormat');
        var activeEl = getEl('webhookActive');
        
        if (urlEl) urlEl.value = '';
        if (secretEl) secretEl.value = '';
        if (formatEl) formatEl.value = 'json';
        if (activeEl) activeEl.checked = true;
        
        var eventCheckboxes = document.querySelectorAll('[id^="webhookEvent"]');
        for (var i = 0; i < eventCheckboxes.length; i++) {
            eventCheckboxes[i].checked = true;
        }
        
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeWebhookModal() {
        var modal = getEl('webhookModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function addWebhook() {
        var urlEl = getEl('webhookUrl');
        var secretEl = getEl('webhookSecret');
        var formatEl = getEl('webhookFormat');
        var activeEl = getEl('webhookActive');
        
        var url = urlEl ? urlEl.value.trim() : '';
        var secret = secretEl ? secretEl.value.trim() : '';
        var format = formatEl ? formatEl.value : 'json';
        var active = activeEl ? activeEl.checked : true;
        
        if (!url) {
            showToast('⚠️ Please enter a webhook URL', 'warning');
            return;
        }
        
        var events = [];
        var eventCheckboxes = document.querySelectorAll('[id^="webhookEvent"]');
        for (var i = 0; i < eventCheckboxes.length; i++) {
            if (eventCheckboxes[i].checked) {
                var eventName = eventCheckboxes[i].id.replace('webhookEvent', '');
                eventName = eventName.replace(/([A-Z])/g, ' $1').trim().toLowerCase().replace(' ', '.');
                events.push(eventName);
            }
        }
        
        var chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        var randomSecret = '';
        for (var i = 0; i < 14; i++) {
            randomSecret += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        
        var newWebhook = {
            id: 'wh_' + String(webhooks.length + 1).padStart(3, '0'),
            url: url,
            secret: secret || 'whsec_' + randomSecret,
            format: format,
            events: events,
            status: active ? 'active' : 'inactive',
            lastTriggered: 'Never',
            successCount: 0,
            failureCount: 0
        };
        
        webhooks.push(newWebhook);
        closeWebhookModal();
        renderWebhooks();
        renderStats();
        showToast('🔗 Webhook added: ' + url);
    }

    function toggleWebhook(id) {
        var wh = null;
        for (var i = 0; i < webhooks.length; i++) {
            if (webhooks[i].id === id) { wh = webhooks[i]; break; }
        }
        if (wh) {
            wh.status = wh.status === 'active' ? 'inactive' : 'active';
            renderWebhooks();
            renderStats();
            showToast((wh.status === 'active' ? '▶️ Activated' : '⏸️ Deactivated') + ' webhook');
        }
    }

    function editWebhook(id) {
        var wh = null;
        for (var i = 0; i < webhooks.length; i++) {
            if (webhooks[i].id === id) { wh = webhooks[i]; break; }
        }
        if (wh) {
            showToast('✏️ Editing webhook: ' + wh.url, 'info');
            // In a real app, this would open the edit modal with pre-filled values
        }
    }

    function deleteWebhook(id) {
        var wh = null;
        for (var i = 0; i < webhooks.length; i++) {
            if (webhooks[i].id === id) { wh = webhooks[i]; break; }
        }
        if (wh && confirm('Delete webhook "' + wh.url + '"?')) {
            var newWebhooks = [];
            for (var i = 0; i < webhooks.length; i++) {
                if (webhooks[i].id !== id) {
                    newWebhooks.push(webhooks[i]);
                }
            }
            webhooks = newWebhooks;
            renderWebhooks();
            renderStats();
            showToast('🗑️ Webhook deleted');
        }
    }

    // ============================================
    // PAGINATION HELPER
    // ============================================

    function renderPagination(container, total, tabKey) {
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' items</div><div class="page-buttons"></div>';
            return;
        }
        
        var current = currentPage[tabKey] || 1;
        var startItem = (current - 1) * perPage + 1;
        var endItem = Math.min(current * perPage, total);
        
        var btns = '<button class="page-btn" onclick="goToPage(\'' + tabKey + '\', ' + (current - 1) + ')" ' + (current <= 1 ? 'disabled' : '') + '>‹</button>';
        
        var startPage = Math.max(1, current - 2);
        var endPage = Math.min(totalPages, current + 2);
        
        if (startPage > 1) {
            btns += '<button class="page-btn" onclick="goToPage(\'' + tabKey + '\', 1)">1</button>';
            if (startPage > 2) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
        }
        for (var i = startPage; i <= endPage; i++) {
            btns += '<button class="page-btn ' + (i === current ? 'active' : '') + '" onclick="goToPage(\'' + tabKey + '\', ' + i + ')">' + i + '</button>';
        }
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
            btns += '<button class="page-btn" onclick="goToPage(\'' + tabKey + '\', ' + totalPages + ')">' + totalPages + '</button>';
        }
        btns += '<button class="page-btn" onclick="goToPage(\'' + tabKey + '\', ' + (current + 1) + ')" ' + (current >= totalPages ? 'disabled' : '') + '>›</button>';
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' items</div><div class="page-buttons">' + btns + '</div>';
    }

    function goToPage(tabKey, page) {
        var total = 0;
        if (tabKey === 'integrations') total = integrations.length;
        else if (tabKey === 'api-keys') total = apiKeys.length;
        else if (tabKey === 'webhooks') total = webhooks.length;
        
        var totalPages = Math.ceil(total / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage[tabKey] = page;
        renderCurrentTab();
    }

    // ============================================
    // INIT
    // ============================================

    var originalInit = initModule;
    initModule = function() {
        console.log('🚀 Integration Management - Forced init');
        
        // Check if container exists
        var container = document.getElementById('integrationsList');
        if (!container) {
            console.log('⏳ Container not ready, retrying...');
            setTimeout(initModule, 200);
            return;
        }
        
        // Set up event listeners
        var modals = document.querySelectorAll('.modal-overlay');
        for (var i = 0; i < modals.length; i++) {
            modals[i].addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.remove('show');
                    document.body.style.overflow = '';
                }
            });
        }
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var modals = document.querySelectorAll('.modal-overlay.show');
                for (var i = 0; i < modals.length; i++) {
                    modals[i].classList.remove('show');
                    document.body.style.overflow = '';
                }
            }
        });
        
        // FORCE RENDER - call all render functions
        console.log('📊 Rendering integrations...');
        renderStats();
        renderIntegrations();
        renderApiKeys();
        renderWebhooks();
        
        console.log('✅ Integration Management rendered successfully!');
        console.log('🔌 ' + integrations.length + ' integrations loaded');
        console.log('🔑 ' + apiKeys.length + ' API keys loaded');
        console.log('🔗 ' + webhooks.length + ' webhooks loaded');
    };

    // Also expose the data globally
    window.integrations = integrations;
    window.apiKeys = apiKeys;
    window.webhooks = webhooks;

    // Force immediate render if DOM is ready
    if (document.getElementById('integrationsList')) {
        console.log('📄 DOM ready, rendering immediately...');
        initModule();
    } else {
        console.log('⏳ Waiting for DOM...');
        // Use MutationObserver to detect when container appears
        var observer = new MutationObserver(function() {
            if (document.getElementById('integrationsList')) {
                console.log('📄 Container detected, rendering...');
                initModule();
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Fallback - retry every 200ms
        var attempts = 0;
        var interval = setInterval(function() {
            attempts++;
            if (document.getElementById('integrationsList')) {
                console.log('📄 Container detected via interval, rendering...');
                initModule();
                clearInterval(interval);
                observer.disconnect();
            } else if (attempts > 20) {
                console.log('⚠️ Max attempts reached for integrations module');
                clearInterval(interval);
                observer.disconnect();
            }
        }, 200);
    }

    // Try to init immediately
    initModule();

    // Fallback: retry after DOM ready
    if (document.readyState !== 'complete') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOMContentLoaded fired');
            initModule();
        });
    }

    // ============================================
    // MAKE FUNCTIONS GLOBAL
    // ============================================
    window.initModule = initModule;
    window.renderIntegrations = renderIntegrations;
    window.renderApiKeys = renderApiKeys;
    window.renderWebhooks = renderWebhooks;
    window.renderStats = renderStats;
    window.applyFilters = applyFilters;
    window.switchTab = switchTab;

    window.clearFilters = clearFilters;
    window.goToPage = goToPage;
    window.syncIntegration = syncIntegration;
    window.connectIntegration = connectIntegration;
    window.disconnectIntegration = disconnectIntegration;
    window.viewIntegration = viewIntegration;
    window.closeDetailModal = closeDetailModal;
    window.showApiKeyModal = showApiKeyModal;
    window.closeApiKeyModal = closeApiKeyModal;
    window.toggleIpRestriction = toggleIpRestriction;
    window.generateApiKey = generateApiKey;
    window.copyApiKey = copyApiKey;
    window.revokeApiKey = revokeApiKey;
    window.showWebhookModal = showWebhookModal;
    window.closeWebhookModal = closeWebhookModal;
    window.addWebhook = addWebhook;
    window.toggleWebhook = toggleWebhook;
    window.editWebhook = editWebhook;
    window.deleteWebhook = deleteWebhook;
    window.showToast = showToast;

    function forceRenderIntegrations() {
        if (document.getElementById('integrationsList')) {
            console.log('✅ Rendering integrations...');
            renderStats();
            renderIntegrations();
            renderApiKeys();
            renderWebhooks();
            return true;
        }
        return false;
    }

    // Try immediately
    if (!forceRenderIntegrations()) {
        // If DOM not ready, wait for it
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    forceRenderIntegrations();
                }, 100);
            });
        } else {
            // DOM already loaded but container not found, retry
            var retryCount = 0;
            var retryInterval = setInterval(function() {
                retryCount++;
                if (forceRenderIntegrations() || retryCount > 10) {
                    clearInterval(retryInterval);
                }
            }, 300);
        }
    }
})(); // <-- The closing parenthesis safely locks the scope