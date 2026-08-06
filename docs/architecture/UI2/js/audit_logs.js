// Audit & Compliance Module - SPA Compatible
(function(){
    console.log('📋 Audit & Compliance JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var users = [
        { id: 'u1', name: 'John Doe', avatar: 'JD', role: 'Admin' },
        { id: 'u2', name: 'Sarah Johnson', avatar: 'SJ', role: 'Sustainability Officer' },
        { id: 'u3', name: 'Mike Chen', avatar: 'MC', role: 'Data Analyst' },
        { id: 'u4', name: 'Emma Wilson', avatar: 'EW', role: 'Compliance Manager' },
        { id: 'u5', name: 'Alex Rivera', avatar: 'AR', role: 'Analyst' },
        { id: 'u6', name: 'System', avatar: '🤖', role: 'System' },
    ];

    var auditLogs = [
        { id: 'a1', userId: 'u2', action: 'APPROVE', resource: 'document', resourceId: 'doc-123', details: 'SECR Report Q4 2026 approved', severity: 'low', time: '2026-07-30 14:30:00', changes: { status: 'pending', newStatus: 'approved' }, related: ['a2'] },
        { id: 'a2', userId: 'u3', action: 'UPDATE', resource: 'emissions', resourceId: 'em-456', details: 'Updated Scope 2 emissions data', severity: 'medium', time: '2026-07-30 14:15:00', changes: { consumption: '4500', newConsumption: '4800' }, related: ['a1'] },
        { id: 'a3', userId: 'u1', action: 'LOGIN', resource: 'user', resourceId: 'u1', details: 'User login from IP 192.168.1.1', severity: 'low', time: '2026-07-30 13:00:00', changes: {}, related: [] },
        { id: 'a4', userId: 'u4', action: 'VERIFY', resource: 'compliance', resourceId: 'csrd-789', details: 'CSRD data validation completed', severity: 'high', time: '2026-07-30 12:00:00', changes: { status: 'pending', newStatus: 'validated' }, related: [] },
        { id: 'a5', userId: 'u5', action: 'CREATE', resource: 'document', resourceId: 'doc-124', details: 'Uploaded new utility bill', severity: 'low', time: '2026-07-30 11:00:00', changes: {}, related: [] },
        { id: 'a6', userId: 'u2', action: 'REJECT', resource: 'document', resourceId: 'doc-125', details: 'Rejected incomplete invoice', severity: 'medium', time: '2026-07-30 10:00:00', changes: { reason: 'Missing VAT number' }, related: [] },
        { id: 'a7', userId: 'u6', action: 'UPDATE', resource: 'system', resourceId: 'sys-001', details: 'DEFRA 2026 emission factors imported', severity: 'high', time: '2026-07-30 09:00:00', changes: { version: '2025', newVersion: '2026' }, related: [] },
        { id: 'a8', userId: 'u3', action: 'DELETE', resource: 'message', resourceId: 'msg-789', details: 'Deleted spam message', severity: 'low', time: '2026-07-29 18:00:00', changes: {}, related: [] },
        { id: 'a9', userId: 'u1', action: 'APPROVE', resource: 'user', resourceId: 'u7', details: 'Approved new team member invitation', severity: 'medium', time: '2026-07-29 16:00:00', changes: { status: 'pending', newStatus: 'approved' }, related: [] },
        { id: 'a10', userId: 'u4', action: 'UPDATE', resource: 'compliance', resourceId: 'issb-456', details: 'Updated ISSB disclosure metrics', severity: 'high', time: '2026-07-29 14:00:00', changes: { score: '68', newScore: '71' }, related: [] },
        { id: 'a11', userId: 'u5', action: 'CREATE', resource: 'emissions', resourceId: 'em-457', details: 'Added new Scope 3 category data', severity: 'medium', time: '2026-07-29 12:00:00', changes: {}, related: [] },
        { id: 'a12', userId: 'u2', action: 'LOGOUT', resource: 'user', resourceId: 'u2', details: 'User logged out', severity: 'low', time: '2026-07-29 11:00:00', changes: {}, related: [] },
        { id: 'a13', userId: 'u6', action: 'VERIFY', resource: 'document', resourceId: 'doc-126', details: 'Auto-verified document OCR extraction', severity: 'medium', time: '2026-07-29 10:00:00', changes: { confidence: '85', newConfidence: '92' }, related: [] },
        { id: 'a14', userId: 'u1', action: 'UPDATE', resource: 'system', resourceId: 'sys-002', details: 'Updated system retention policy', severity: 'critical', time: '2026-07-29 08:00:00', changes: { days: '30', newDays: '45' }, related: [] },
        { id: 'a15', userId: 'u3', action: 'CREATE', resource: 'message', resourceId: 'msg-790', details: 'Sent message in Compliance Team chat', severity: 'low', time: '2026-07-28 20:00:00', changes: {}, related: [] },
        { id: 'a16', userId: 'u4', action: 'UPDATE', resource: 'compliance', resourceId: 'csrd-790', details: 'Updated CSRD compliance checklist', severity: 'medium', time: '2026-07-28 17:00:00', changes: { items: '12', newItems: '15' }, related: [] },
        { id: 'a17', userId: 'u1', action: 'LOGIN', resource: 'user', resourceId: 'u1', details: 'User login from IP 10.0.0.5', severity: 'low', time: '2026-07-28 09:00:00', changes: {}, related: [] },
        { id: 'a18', userId: 'u5', action: 'CREATE', resource: 'document', resourceId: 'doc-127', details: 'Uploaded fuel consumption data', severity: 'low', time: '2026-07-27 15:00:00', changes: {}, related: [] },
        { id: 'a19', userId: 'u2', action: 'APPROVE', resource: 'emissions', resourceId: 'em-458', details: 'Approved Scope 1 emissions report', severity: 'high', time: '2026-07-27 13:00:00', changes: { status: 'draft', newStatus: 'approved' }, related: [] },
        { id: 'a20', userId: 'u6', action: 'UPDATE', resource: 'system', resourceId: 'sys-003', details: 'Security patch applied', severity: 'critical', time: '2026-07-27 02:00:00', changes: { version: '1.0', newVersion: '1.1' }, related: [] }
    ];

    // ============================================
    // STATE
    // ============================================

    var filteredLogs = [];
    var currentPage = 1;
    var perPage = 5;
    var showingAdvanced = false;
    var toastTimeout = null;

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
    // HELPERS
    // ============================================

    function getUser(id) {
        for (var i = 0; i < users.length; i++) {
            if (users[i].id === id) return users[i];
        }
        return { name: 'Unknown', avatar: '?', role: 'Unknown' };
    }

    function getSeverityClass(severity) {
        var map = { critical: 'critical', high: 'high', medium: 'medium', low: 'low' };
        return map[severity] || 'low';
    }

    function getActionIcon(action) {
        var map = {
            'CREATE': '➕', 'UPDATE': '✏️', 'DELETE': '🗑️',
            'APPROVE': '✅', 'REJECT': '❌', 'LOGIN': '🔑',
            'LOGOUT': '🚪', 'VERIFY': '✔️'
        };
        return map[action] || '●';
    }

    function formatTime(dateStr) {
        var d = new Date(dateStr);
        var day = String(d.getDate()).padStart(2, '0');
        var month = d.toLocaleString('en', { month: 'short' });
        var hours = String(d.getHours()).padStart(2, '0');
        var minutes = String(d.getMinutes()).padStart(2, '0');
        return day + ' ' + month + ' ' + hours + ':' + minutes;
    }

    function getTimeAgo(dateStr) {
        var now = new Date();
        var then = new Date(dateStr);
        var diff = Math.floor((now - then) / 60000);
        if (diff < 1) return 'Just now';
        if (diff < 60) return diff + 'm ago';
        if (diff < 1440) return Math.floor(diff / 60) + 'h ago';
        return Math.floor(diff / 1440) + 'd ago';
    }

    function getSeverityBadge(severity) {
        var map = {
            'critical': '<span class="badge badge-destructive">Critical</span>',
            'high': '<span class="badge badge-warning">High</span>',
            'medium': '<span class="badge badge-secondary">Medium</span>',
            'low': '<span class="badge badge-muted">Low</span>'
        };
        return map[severity] || '';
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderStats(data) {
        var totalEl = getEl('statTotal');
        if (totalEl) totalEl.innerHTML = data.length + ' <span class="stat-trend">↑ 12%</span>';
        
        var uniqueUsers = {};
        for (var i = 0; i < data.length; i++) {
            uniqueUsers[data[i].userId] = true;
        }
        var usersEl = getEl('statUsers');
        if (usersEl) usersEl.textContent = Object.keys(uniqueUsers).length;
        
        var critical = 0;
        for (var j = 0; j < data.length; j++) {
            if (data[j].severity === 'critical') critical++;
        }
        var criticalEl = getEl('statCritical');
        if (criticalEl) criticalEl.innerHTML = critical + ' <span class="stat-trend down">↑ 2</span>';
        
        var complianceEl = getEl('statCompliance');
        if (complianceEl) complianceEl.textContent = '98%';
        
        if (data.length > 0) {
            var sorted = data.slice().sort(function(a, b) {
                return new Date(b.time) - new Date(a.time);
            });
            var recentEl = getEl('statRecent');
            if (recentEl) recentEl.textContent = getTimeAgo(sorted[0].time);
        }
    }

    function renderEvents(data) {
        var start = (currentPage - 1) * perPage;
        var pageItems = data.slice(start, start + perPage);
        var container = getEl('eventList');
        var rowCount = getEl('rowCount');
        var filterCount = getEl('filterCount');

        if (!container) return;

        if (pageItems.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:40px;color:hsl(var(--muted-foreground));">📭 No events match your filters</div>';
            if (rowCount) rowCount.textContent = '0';
            if (filterCount) filterCount.textContent = '0 events';
            renderPagination(data.length);
            return;
        }

        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var log = pageItems[i];
            var user = getUser(log.userId);
            var severityClass = getSeverityClass(log.severity);
            
            var changesHtml = '';
            var keys = Object.keys(log.changes);
            if (keys.length > 0) {
                changesHtml = '<div class="event-changes">→ ' + keys.join(' → ') + '</div>';
            }

            html += '<div class="event-card" onclick="openDetail(\'' + log.id + '\')">' +
                '<div class="event-icon ' + severityClass + '">' + getActionIcon(log.action) + '</div>' +
                '<div class="event-main">' +
                    '<div class="event-title">' + log.details + '</div>' +
                    '<div class="event-meta">' +
                        '<span>👤 ' + user.name + '</span>' +
                        '<span>🏷️ ' + log.action + '</span>' +
                        '<span>📁 ' + log.resource + '</span>' +
                        '<span>🕐 ' + formatTime(log.time) + ' (' + getTimeAgo(log.time) + ')</span>' +
                    '</div>' +
                    changesHtml +
                '</div>' +
                '<div class="event-actions">' +
                    getSeverityBadge(log.severity) +
                    '<button class="btn btn-sm btn-ghost" onclick="event.stopPropagation();openDetail(\'' + log.id + '\')">→</button>' +
                '</div>' +
            '</div>';
        }

        container.innerHTML = html;
        if (rowCount) rowCount.textContent = data.length;
        if (filterCount) filterCount.textContent = data.length + ' events';
        renderPagination(data.length);
    }

    function renderPagination(total) {
        var totalPages = Math.ceil(total / perPage);
        var container = getEl('pagination');
        if (!container) return;
        
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' events</div><div class="page-buttons"></div>';
            return;
        }

        var btns = '<button class="page-btn" onclick="goToPage(' + (currentPage - 1) + ')" ' + (currentPage <= 1 ? 'disabled' : '') + '>‹</button>';
        
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            btns += '<button class="page-btn" onclick="goToPage(1)">1</button>';
            if (startPage > 2) btns += '<span style="padding:0 4px;">…</span>';
        }
        
        for (var i = startPage; i <= endPage; i++) {
            btns += '<button class="page-btn ' + (i === currentPage ? 'active' : '') + '" onclick="goToPage(' + i + ')">' + i + '</button>';
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) btns += '<span style="padding:0 4px;">…</span>';
            btns += '<button class="page-btn" onclick="goToPage(' + totalPages + ')">' + totalPages + '</button>';
        }
        
        btns += '<button class="page-btn" onclick="goToPage(' + (currentPage + 1) + ')" ' + (currentPage >= totalPages ? 'disabled' : '') + '>›</button>';
        
        var startItem = (currentPage - 1) * perPage + 1;
        var endItem = Math.min(currentPage * perPage, total);
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + '</div><div class="page-buttons">' + btns + '</div>';
    }

    // ============================================
    // FILTER FUNCTIONS
    // ============================================

    function applyFilters() {
        var actionEl = getEl('filterAction');
        var resourceEl = getEl('filterResource');
        var severityEl = getEl('filterSeverity');
        var userEl = getEl('filterUser');
        var dateFromEl = getEl('filterDateFrom');
        var dateToEl = getEl('filterDateTo');
        
        var action = actionEl ? actionEl.value : 'all';
        var resource = resourceEl ? resourceEl.value : 'all';
        var severity = severityEl ? severityEl.value : 'all';
        var userFilter = userEl ? userEl.value : 'all';
        var dateFrom = dateFromEl ? dateFromEl.value : '';
        var dateTo = dateToEl ? dateToEl.value : '';

        filteredLogs = [];
        for (var i = 0; i < auditLogs.length; i++) {
            var log = auditLogs[i];
            if (action !== 'all' && log.action !== action) continue;
            if (resource !== 'all' && log.resource !== resource) continue;
            if (severity !== 'all' && log.severity !== severity) continue;
            if (userFilter !== 'all' && log.userId !== userFilter) continue;
            if (dateFrom && log.time < dateFrom) continue;
            if (dateTo && log.time > dateTo) continue;
            filteredLogs.push(log);
        }

        currentPage = 1;
        renderStats(filteredLogs);
        renderEvents(filteredLogs);
    }

    function clearFilters() {
        var actionEl = getEl('filterAction');
        var resourceEl = getEl('filterResource');
        var severityEl = getEl('filterSeverity');
        var userEl = getEl('filterUser');
        var dateFromEl = getEl('filterDateFrom');
        var dateToEl = getEl('filterDateTo');
        
        if (actionEl) actionEl.value = 'all';
        if (resourceEl) resourceEl.value = 'all';
        if (severityEl) severityEl.value = 'all';
        if (userEl) userEl.value = 'all';
        if (dateFromEl) dateFromEl.value = '';
        if (dateToEl) dateToEl.value = '';
        applyFilters();
        showToast('🔄 Filters cleared');
    }

    function setQuickView(range) {
        var views = document.querySelectorAll('.quick-view');
        for (var i = 0; i < views.length; i++) {
            views[i].classList.remove('active');
            if (views[i].getAttribute('data-range') === range) {
                views[i].classList.add('active');
            }
        }
        applyFilters();
        showToast('📅 View: ' + range);
    }

    function toggleAdvanced() {
        showingAdvanced = !showingAdvanced;
        var el = getEl('advancedFilters');
        if (el) {
            el.style.display = showingAdvanced ? 'flex' : 'none';
        }
    }

    function goToPage(page) {
        var total = Math.ceil(filteredLogs.length / perPage);
        if (page < 1 || page > total) return;
        currentPage = page;
        renderEvents(filteredLogs);
    }

    // ============================================
    // DRAWER FUNCTIONS
    // ============================================

    function openDetail(id) {
        var log = null;
        for (var i = 0; i < auditLogs.length; i++) {
            if (auditLogs[i].id === id) { log = auditLogs[i]; break; }
        }
        if (!log) return;

        var user = getUser(log.userId);
        var drawerTitle = getEl('drawerTitle');
        var drawerSubtitle = getEl('drawerSubtitle');
        var drawerBody = getEl('drawerBody');
        var overlay = getEl('drawerOverlay');
        
        if (drawerTitle) drawerTitle.textContent = log.details;
        if (drawerSubtitle) drawerSubtitle.textContent = log.action + ' · ' + log.resource + ' · ' + formatTime(log.time);

        var changesHtml = '';
        var keys = Object.keys(log.changes);
        if (keys.length > 0) {
            for (var j = 0; j < keys.length; j++) {
                var key = keys[j];
                var val = log.changes[key];
                changesHtml += '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid hsl(var(--border));font-size:13px;">' +
                    '<span style="color:hsl(var(--muted-foreground));">' + key + '</span>' +
                    '<span><span class="diff-remove">' + (typeof val === 'string' ? val : JSON.stringify(val)) + '</span> → <span class="diff-add">' + (typeof val === 'string' ? val : JSON.stringify(val)) + '</span></span>' +
                '</div>';
            }
        } else {
            changesHtml = '<div style="color:hsl(var(--muted-foreground));font-size:13px;">No changes recorded</div>';
        }

        var relatedHtml = '';
        if (log.related && log.related.length > 0) {
            relatedHtml = '<div class="drawer-section"><div class="section-label">Related Events (' + log.related.length + ')</div>';
            for (var k = 0; k < log.related.length; k++) {
                var relId = log.related[k];
                var rel = null;
                for (var m = 0; m < auditLogs.length; m++) {
                    if (auditLogs[m].id === relId) { rel = auditLogs[m]; break; }
                }
                if (rel) {
                    relatedHtml += '<div style="padding:6px 0;border-bottom:1px solid hsl(var(--border));font-size:13px;cursor:pointer;" onclick="openDetail(\'' + rel.id + '\');event.stopPropagation();">' + rel.details + ' <span style="color:hsl(var(--muted-foreground));font-size:12px;">' + getTimeAgo(rel.time) + '</span></div>';
                }
            }
            relatedHtml += '</div>';
        }

        if (drawerBody) {
            drawerBody.innerHTML = 
                '<div class="drawer-section">' +
                    '<div class="section-label">Event Details</div>' +
                    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;">' +
                        '<div><span style="color:hsl(var(--muted-foreground));">Event ID</span> <code>' + log.id + '</code></div>' +
                        '<div><span style="color:hsl(var(--muted-foreground));">Severity</span> ' + getSeverityBadge(log.severity) + '</div>' +
                        '<div><span style="color:hsl(var(--muted-foreground));">User</span> ' + user.name + ' (' + user.role + ')</div>' +
                        '<div><span style="color:hsl(var(--muted-foreground));">Resource</span> ' + log.resource + ' <span class="badge badge-outline">' + log.resourceId + '</span></div>' +
                        '<div style="grid-column:1/-1;"><span style="color:hsl(var(--muted-foreground));">Time</span> ' + new Date(log.time).toLocaleString() + '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="drawer-section">' +
                    '<div class="section-label">Changes</div>' +
                    '<div class="diff-view">' + changesHtml + '</div>' +
                '</div>' +
                relatedHtml +
                '<div class="drawer-section">' +
                    '<div class="section-label">Actions</div>' +
                    '<div style="display:flex;gap:8px;flex-wrap:wrap;">' +
                        '<button class="btn btn-sm btn-outline" onclick="shareEvent(\'' + log.id + '\')">📤 Share</button>' +
                        '<button class="btn btn-sm btn-ghost" onclick="flagEvent(\'' + log.id + '\')">🚩 Flag</button>' +
                        '<button class="btn btn-sm btn-ghost" onclick="addNote(\'' + log.id + '\')">💬 Add Note</button>' +
                    '</div>' +
                '</div>';
        }

        if (overlay) overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
        var overlay = getEl('drawerOverlay');
        if (overlay) overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    // ============================================
    // ACTION FUNCTIONS
    // ============================================

    function shareEvent(id) { showToast('📤 Share link copied to clipboard'); }
    function flagEvent(id) { showToast('🚩 Event flagged for review'); }
    function addNote(id) { showToast('💬 Note added successfully'); }
    function exportData() { showToast('📤 Exporting audit data...'); }
    function openComplianceReport() { showToast('📄 Generating compliance report...'); }

    function refreshData() {
        showToast('🔄 Refreshing audit log...');
        setTimeout(function() {
            applyFilters();
            showToast('✅ Updated');
        }, 400);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        console.log('🚀 Initializing Audit & Compliance Module...');
        
        var eventList = getEl('eventList');
        var pagination = getEl('pagination');
        
        if (!eventList || !pagination) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Set up event listeners
        var applyBtn = getEl('applyFiltersBtn');
        if (applyBtn) applyBtn.addEventListener('click', applyFilters);
        
        var clearBtn = getEl('clearFiltersBtn');
        if (clearBtn) clearBtn.addEventListener('click', clearFilters);
        
        // Drawer overlay click to close
        var overlay = getEl('drawerOverlay');
        if (overlay) {
            overlay.addEventListener('click', function(e) {
                if (e.target === this) closeDrawer();
            });
        }
        
        // Escape key to close drawer
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var drawerOverlay = getEl('drawerOverlay');
                if (drawerOverlay && drawerOverlay.classList.contains('show')) {
                    closeDrawer();
                }
            }
        });
        
        filteredLogs = auditLogs.slice();
        renderStats(filteredLogs);
        renderEvents(filteredLogs);
        
        console.log('✅ Audit & Compliance module loaded successfully!');
        console.log('📋 ' + auditLogs.length + ' events loaded');
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

    window.applyFilters = applyFilters;
    window.clearFilters = clearFilters;
    window.setQuickView = setQuickView;
    window.toggleAdvanced = toggleAdvanced;
    window.goToPage = goToPage;
    window.openDetail = openDetail;
    window.closeDrawer = closeDrawer;
    window.shareEvent = shareEvent;
    window.flagEvent = flagEvent;
    window.addNote = addNote;
    window.exportData = exportData;
    window.openComplianceReport = openComplianceReport;
    window.refreshData = refreshData;
    window.showToast = showToast;
})(); 