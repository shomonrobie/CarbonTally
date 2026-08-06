// Activity Feed Module - SPA Compatible

(function(){
    console.log('🔄 Activity Feed JS loaded');

    // ============================================
    // MOCK DATA (16 activities)
    // ============================================

    var activities = [
        {
            id: 'act_001',
            type: 'upload',
            user: 'John Doe',
            userRole: 'Admin',
            action: 'uploaded',
            title: 'Utility_Bill_London_Dec2026.pdf',
            description: 'Uploaded a new utility bill for London office',
            details: 'File size: 2.4 MB • 12 records extracted',
            time: '2026-12-15T14:30:00Z',
            read: false,
            metadata: { fileId: 'file_001', fileType: 'pdf', dataType: 'utility', records: 12, size: '2.4 MB' },
            scope: 'Scope 2',
            facility: 'London Office'
        },
        {
            id: 'act_002',
            type: 'approved',
            user: 'Sarah Johnson',
            userRole: 'Manager',
            action: 'approved',
            title: 'Fleet Fuel Q4 2026 Data',
            description: 'Approved fleet fuel consumption data for Q4 2026',
            details: '245 records • 14,500 L total consumption',
            time: '2026-12-15T13:15:00Z',
            read: false,
            metadata: { fileId: 'file_002', fileType: 'csv', dataType: 'fuel', records: 245, totalConsumption: 14500, unit: 'L' },
            scope: 'Scope 1',
            facility: 'London Office'
        },
        {
            id: 'act_003',
            type: 'emission',
            user: 'Mike Roberts',
            userRole: 'Analyst',
            action: 'added',
            title: 'Emissions Data - December 2026',
            description: 'Added new emissions data for December 2026',
            details: '324.5 kgCO₂e added • 8 new records',
            time: '2026-12-15T11:45:00Z',
            read: true,
            metadata: { emissions: 324.5, unit: 'kgCO₂e', records: 8, period: 'December 2026' },
            scope: 'Scope 2',
            facility: 'Data Center'
        },
        {
            id: 'act_004',
            type: 'report',
            user: 'Anna Liu',
            userRole: 'Analyst',
            action: 'generated',
            title: 'SECR Report 2026',
            description: 'Generated SECR compliance report for 2026',
            details: '45 pages • 12.4 MB • Ready for review',
            time: '2026-12-15T10:00:00Z',
            read: true,
            metadata: { reportId: 'rpt_001', type: 'SECR', year: 2026, pages: 45, size: '12.4 MB' },
            scope: 'All Scopes',
            facility: 'All Facilities'
        },
        {
            id: 'act_005',
            type: 'team',
            user: 'John Doe',
            userRole: 'Admin',
            action: 'added',
            title: 'New Team Member: Emma Martinez',
            description: 'Added Emma Martinez as Sustainability Analyst',
            details: 'Role: Analyst • Department: Sustainability',
            time: '2026-12-15T09:30:00Z',
            read: true,
            metadata: { userId: 'user_012', role: 'Analyst', department: 'Sustainability' },
            scope: null,
            facility: null
        },
        {
            id: 'act_006',
            type: 'review',
            user: 'Tom Chen',
            userRole: 'Staff',
            action: 'started',
            title: 'Supplier Invoice Review',
            description: 'Started review of supplier invoice for IT equipment',
            details: 'Priority: High • Scope 3',
            time: '2026-12-14T16:20:00Z',
            read: true,
            metadata: { fileId: 'file_003', priority: 'High', scope: 'Scope 3' },
            scope: 'Scope 3',
            facility: 'Data Center'
        },
        {
            id: 'act_007',
            type: 'rejected',
            user: 'Sarah Johnson',
            userRole: 'Manager',
            action: 'rejected',
            title: 'Water Bill Manchester Q4',
            description: 'Rejected water bill due to missing consumption data',
            details: 'Reason: Insufficient data • Requires resubmission',
            time: '2026-12-14T14:45:00Z',
            read: true,
            metadata: { fileId: 'file_004', reason: 'Insufficient data', needsResubmission: true },
            scope: 'Scope 2',
            facility: 'Manchester Office'
        },
        {
            id: 'act_008',
            type: 'upload',
            user: 'Mike Roberts',
            userRole: 'Analyst',
            action: 'uploaded',
            title: 'Business Travel Expenses Q4 2026',
            description: 'Uploaded business travel expenses for Q4 2026',
            details: '89 records • 12,500 kgCO₂e',
            time: '2026-12-14T12:00:00Z',
            read: false,
            metadata: { fileId: 'file_005', fileType: 'csv', dataType: 'scope3', records: 89, totalEmissions: 12500, unit: 'kgCO₂e' },
            scope: 'Scope 3',
            facility: 'All Facilities'
        },
        {
            id: 'act_009',
            type: 'system',
            user: 'System',
            userRole: 'System',
            action: 'updated',
            title: 'System Update v2.4.1 Deployed',
            description: 'New features: Enhanced reporting and API improvements',
            details: 'Release notes: SECR templates, improved validation',
            time: '2026-12-14T09:00:00Z',
            read: true,
            metadata: { version: '2.4.1', features: ['SECR templates', 'Improved validation', 'API rate limiting'] },
            scope: null,
            facility: null
        },
        {
            id: 'act_010',
            type: 'approved',
            user: 'Anna Liu',
            userRole: 'Analyst',
            action: 'approved',
            title: 'Renewable Energy Certificates 2026',
            description: 'Approved renewable energy certificates for 2026',
            details: '125 certificates • 2,500 MWh solar energy',
            time: '2026-12-13T15:30:00Z',
            read: true,
            metadata: { fileId: 'file_006', certificates: 125, energySource: 'Solar', totalMwh: 2500 },
            scope: 'Scope 2',
            facility: 'London Office'
        },
        {
            id: 'act_011',
            type: 'review',
            user: 'Emma Martinez',
            userRole: 'Analyst',
            action: 'completed',
            title: 'Fleet Fuel November 2026 Review',
            description: 'Completed review of fleet fuel data for November 2026',
            details: '210 records • 11,800 L • Ready for approval',
            time: '2026-12-13T13:00:00Z',
            read: false,
            metadata: { fileId: 'file_007', records: 210, totalConsumption: 11800, unit: 'L', readyForApproval: true },
            scope: 'Scope 1',
            facility: 'Birmingham Office'
        },
        {
            id: 'act_012',
            type: 'emission',
            user: 'Mike Roberts',
            userRole: 'Analyst',
            action: 'updated',
            title: 'Emissions Data Correction',
            description: 'Updated emissions data for November 2026 (Scope 1)',
            details: 'Corrected 3 records • -45.2 kgCO₂e adjustment',
            time: '2026-12-13T10:15:00Z',
            read: true,
            metadata: { correction: -45.2, unit: 'kgCO₂e', records: 3, scope: 'Scope 1' },
            scope: 'Scope 1',
            facility: 'London Office'
        },
        {
            id: 'act_013',
            type: 'upload',
            user: 'Tom Chen',
            userRole: 'Staff',
            action: 'uploaded',
            title: 'Gas Bill Birmingham Q4 2026',
            description: 'Uploaded gas consumption data for Birmingham office',
            details: '1.8 MB • 6 records • 18,200 kWh',
            time: '2026-12-12T16:00:00Z',
            read: true,
            metadata: { fileId: 'file_008', fileType: 'pdf', dataType: 'utility', records: 6, consumption: 18200, unit: 'kWh' },
            scope: 'Scope 2',
            facility: 'Birmingham Office'
        },
        {
            id: 'act_014',
            type: 'approved',
            user: 'John Doe',
            userRole: 'Admin',
            action: 'approved',
            title: 'CSRD Data Q4 2026',
            description: 'Approved CSRD compliance data for Q4 2026',
            details: '12 ESRS metrics validated • Ready for disclosure',
            time: '2026-12-12T14:30:00Z',
            read: false,
            metadata: { fileId: 'file_009', metrics: 12, standard: 'CSRD', period: 'Q4 2026' },
            scope: 'All Scopes',
            facility: 'All Facilities'
        },
        {
            id: 'act_015',
            type: 'rejected',
            user: 'Emma Martinez',
            userRole: 'Analyst',
            action: 'rejected',
            title: 'Supplier Data Incomplete',
            description: 'Rejected supplier emissions data due to missing Scope 3 information',
            details: 'Reason: Missing waste data for 3 suppliers',
            time: '2026-12-12T11:00:00Z',
            read: true,
            metadata: { fileId: 'file_010', reason: 'Missing waste data for 3 suppliers', suppliers: 8, missingData: 'Waste data' },
            scope: 'Scope 3',
            facility: 'Distribution Center'
        },
        {
            id: 'act_016',
            type: 'review',
            user: 'Sarah Johnson',
            userRole: 'Manager',
            action: 'started',
            title: 'ISEB Disclosure Review',
            description: 'Started review of ISSB S1 & S2 disclosures',
            details: '34 pages • Priority: High',
            time: '2026-12-11T15:45:00Z',
            read: true,
            metadata: { fileId: 'file_011', pages: 34, priority: 'High', standard: 'ISSB' },
            scope: 'All Scopes',
            facility: 'London Office'
        }
    ];

    // ============================================
    // STATE
    // ============================================

    var liveUpdates = true;
    var liveInterval = null;
    var currentFilters = { type: 'all', user: 'all', dateFrom: '', dateTo: '' };
    var currentPage = 1;
    var perPage = 5;
    var currentSort = { field: 'time', direction: 'desc' };
    var toastTimeout = null;

    // ============================================
    // DOM REFS
    // ============================================

    function getEl(id) { return document.getElementById(id); }
    function getFeedStats() { return getEl('feedStats'); }
    function getActivityList() { return getEl('activityList'); }
    function getActivityCount() { return getEl('activityCount'); }
    function getSearchInput() { return getEl('searchInput'); }
    function getPagination() { return getEl('pagination'); }

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
    // ACTIVITY FUNCTIONS
    // ============================================

    function getActivityIcon(type) {
        var icons = { 'upload': '📤', 'approved': '✅', 'rejected': '❌', 'emission': '📈', 'report': '📊', 'team': '👥', 'system': '⚙️', 'review': '📝' };
        return icons[type] || '📌';
    }

    function getActivityDotClass(type) {
        var classes = { 'upload': 'upload', 'approved': 'approved', 'rejected': 'rejected', 'emission': 'emission', 'report': 'report', 'team': 'team', 'system': 'system', 'review': 'review' };
        return classes[type] || 'system';
    }

    function getStatusBadge(type) {
        var badges = { 'upload': 'badge-primary', 'approved': 'badge-success', 'rejected': 'badge-destructive', 'emission': 'badge-primary', 'report': 'badge-warning', 'team': 'badge-primary', 'system': 'badge-muted', 'review': 'badge-primary' };
        return badges[type] || 'badge-muted';
    }

    function formatTime(dateStr) {
        var date = new Date(dateStr);
        var now = new Date();
        var diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
        if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
        if (diff < 172800000) return 'Yesterday';
        return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    }

    function renderStats() {
        var container = getFeedStats();
        if (!container) return;
        
        var total = activities.length;
        var unread = 0, uploads = 0, approvals = 0;
        for (var i = 0; i < activities.length; i++) {
            var a = activities[i];
            if (!a.read) unread++;
            if (a.type === 'upload') uploads++;
            if (a.type === 'approved') approvals++;
        }

        container.innerHTML =
            '<div class="feed-stat"><span class="icon">📊</span><div class="value">' + total + '</div><div class="label">Total Activities</div></div>' +
            '<div class="feed-stat"><span class="icon">🔴</span><div class="value">' + unread + '</div><div class="label">Unread</div></div>' +
            '<div class="feed-stat"><span class="icon">📤</span><div class="value">' + uploads + '</div><div class="label">Uploads</div></div>' +
            '<div class="feed-stat"><span class="icon">✅</span><div class="value">' + approvals + '</div><div class="label">Approvals</div></div>';
    }

    function renderPagination(total) {
        var container = getPagination();
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' activities</div><div class="page-buttons"></div>';
            return;
        }
        
        var startItem = (currentPage - 1) * perPage + 1;
        var endItem = Math.min(currentPage * perPage, total);
        
        var btns = '<button class="page-btn" onclick="goToPage(' + (currentPage - 1) + ')" ' + (currentPage <= 1 ? 'disabled' : '') + '>‹</button>';
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            btns += '<button class="page-btn" onclick="goToPage(1)">1</button>';
            if (startPage > 2) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
        }
        for (var i = startPage; i <= endPage; i++) {
            btns += '<button class="page-btn ' + (i === currentPage ? 'active' : '') + '" onclick="goToPage(' + i + ')">' + i + '</button>';
        }
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
            btns += '<button class="page-btn" onclick="goToPage(' + totalPages + ')">' + totalPages + '</button>';
        }
        btns += '<button class="page-btn" onclick="goToPage(' + (currentPage + 1) + ')" ' + (currentPage >= totalPages ? 'disabled' : '') + '>›</button>';
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' activities</div><div class="page-buttons">' + btns + '</div>';
    }

    function goToPage(page) {
        var totalPages = Math.ceil(filteredActivities.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderActivities();
        var timeline = document.querySelector('.activity-timeline');
        if (timeline) timeline.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    var filteredActivities = [];

    function applyFilters() {
        var typeEl = getEl('typeFilter');
        var userEl = getEl('userFilter');
        var fromEl = getEl('dateFrom');
        var toEl = getEl('dateTo');
        var searchEl = getSearchInput();
        
        currentFilters.type = typeEl ? typeEl.value : 'all';
        currentFilters.user = userEl ? userEl.value : 'all';
        currentFilters.dateFrom = fromEl ? fromEl.value : '';
        currentFilters.dateTo = toEl ? toEl.value : '';
        var searchTerm = searchEl ? searchEl.value.toLowerCase().trim() : '';
        
        filteredActivities = [];
        for (var i = 0; i < activities.length; i++) {
            var a = activities[i];
            if (currentFilters.type !== 'all' && a.type !== currentFilters.type) continue;
            if (currentFilters.user !== 'all' && a.user !== currentFilters.user) continue;
            if (currentFilters.dateFrom && a.time < currentFilters.dateFrom) continue;
            if (currentFilters.dateTo && a.time > currentFilters.dateTo + 'T23:59:59Z') continue;
            if (searchTerm) {
                var match = a.title.toLowerCase().indexOf(searchTerm) !== -1 ||
                        a.description.toLowerCase().indexOf(searchTerm) !== -1 ||
                        a.user.toLowerCase().indexOf(searchTerm) !== -1 ||
                        a.details.toLowerCase().indexOf(searchTerm) !== -1 ||
                        (a.scope && a.scope.toLowerCase().indexOf(searchTerm) !== -1) ||
                        (a.facility && a.facility.toLowerCase().indexOf(searchTerm) !== -1);
                if (!match) continue;
            }
            filteredActivities.push(a);
        }
        
        // Sort
        filteredActivities.sort(function(a, b) {
            var aVal = a[currentSort.field] || '';
            var bVal = b[currentSort.field] || '';
            if (typeof aVal === 'string') {
                return currentSort.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }
            return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        });
        
        currentPage = 1;
        renderActivities();
    }

    function clearFilters() {
        var typeEl = getEl('typeFilter');
        var userEl = getEl('userFilter');
        var fromEl = getEl('dateFrom');
        var toEl = getEl('dateTo');
        var searchEl = getSearchInput();
        
        if (typeEl) typeEl.value = 'all';
        if (userEl) userEl.value = 'all';
        if (fromEl) fromEl.value = '';
        if (toEl) toEl.value = '';
        if (searchEl) searchEl.value = '';
        
        currentFilters.type = 'all';
        currentFilters.user = 'all';
        currentFilters.dateFrom = '';
        currentFilters.dateTo = '';
        currentPage = 1;
        applyFilters();
        showToast('🔄 Filters cleared');
    }

    function sortBy(field) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = 'asc';
        }
        currentPage = 1;
        applyFilters();
    }

    function renderActivities() {
        var container = getActivityList();
        var countEl = getActivityCount();
        if (!container) return;
        
        var start = (currentPage - 1) * perPage;
        var pageItems = filteredActivities.slice(start, start + perPage);
        
        if (countEl) countEl.textContent = filteredActivities.length + ' activities';
        
        if (pageItems.length === 0) {
            container.innerHTML =
                '<div class="text-center text-muted" style="padding:60px 20px;">' +
                '<div style="font-size:48px;margin-bottom:16px;">🔍</div>' +
                '<div style="font-size:18px;font-weight:600;">No activities found</div>' +
                '<div style="font-size:14px;color:hsl(var(--muted-foreground));margin-top:8px;">Try adjusting your filters or check back later</div>' +
                '</div>';
            renderPagination(0);
            return;
        }

        var html = '';
        for (var j = 0; j < pageItems.length; j++) {
            var a = pageItems[j];
            var isUnread = !a.read;
            var avatar = a.user.split(' ').map(function(n) { return n[0]; }).join('');
            
            html +=
                '<div class="activity-item" onclick="openDetail(\'' + a.id + '\')" style="' + (isUnread ? 'border-left: 3px solid hsl(var(--primary));' : '') + '">' +
                '<div class="activity-dot ' + getActivityDotClass(a.type) + '"></div>' +
                '<div class="activity-header">' +
                '<div class="activity-user">' +
                '<div class="avatar avatar-sm">' + avatar + '</div>' +
                '<div><div class="name">' + a.user + '</div><div class="role">' + a.userRole + '</div></div>' +
                '</div>' +
                '<div class="activity-time">' + formatTime(a.time) + '</div>' +
                '</div>' +
                '<div class="activity-content">' +
                '<div class="title">' +
                '<span>' + getActivityIcon(a.type) + '</span> ' +
                a.action + ' ' + a.title +
                (isUnread ? '<span class="badge badge-primary" style="font-size:9px;">NEW</span>' : '') +
                '</div>' +
                '<div class="description">' + a.description + '</div>' +
                '<div class="meta">' +
                '<span>' + a.details + '</span>' +
                (a.scope ? '<span class="badge ' + getStatusBadge(a.type) + '">' + a.scope + '</span>' : '') +
                (a.facility ? '<span class="badge badge-muted">🏢 ' + a.facility + '</span>' : '') +
                '</div>' +
                '</div>' +
                '<div class="activity-actions">' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openDetail(\'' + a.id + '\')">👁️ View</button>' +
                (isUnread ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();markRead(\'' + a.id + '\')">✅ Mark Read</button>' : '') +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderPagination(filteredActivities.length);
    }

    // ============================================
    // DETAIL MODAL
    // ============================================

    function openDetail(id) {
        var a = null;
        for (var i = 0; i < activities.length; i++) {
            if (activities[i].id === id) { a = activities[i]; break; }
        }
        if (!a) return;

        if (!a.read) {
            a.read = true;
            renderActivities();
            renderStats();
        }

        var titleEl = getEl('detailTitle');
        var subtitleEl = getEl('detailSubtitle');
        var bodyEl = getEl('detailBody');
        var footerEl = getEl('detailFooter');
        var modal = getEl('detailModal');
        
        if (titleEl) titleEl.textContent = a.title;
        if (subtitleEl) subtitleEl.textContent = a.type.toUpperCase() + ' • ' + a.user + ' • ' + formatTime(a.time);

        if (bodyEl) {
            var metaHtml = '';
            var metaKeys = Object.keys(a.metadata);
            for (var k = 0; k < metaKeys.length; k++) {
                var key = metaKeys[k];
                var val = a.metadata[key];
                metaHtml += '<div><div style="font-size:10px;color:hsl(var(--muted-foreground));">' + key.replace(/([A-Z])/g, ' $1').toUpperCase().trim() + '</div><div style="font-size:13px;font-weight:500;color:hsl(var(--foreground));">' + (typeof val === 'object' ? JSON.stringify(val) : val) + '</div></div>';
            }

            bodyEl.innerHTML =
                '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">' +
                '<div style="font-size:32px;">' + getActivityIcon(a.type) + '</div>' +
                '<div><div style="font-size:16px;font-weight:600;color:hsl(var(--foreground));">' + a.action + ' ' + a.title + '</div><div style="font-size:14px;color:hsl(var(--muted-foreground));">' + a.description + '</div></div>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
                '<div class="detail-row"><span class="label">User</span><span class="value">' + a.user + '</span></div>' +
                '<div class="detail-row"><span class="label">Role</span><span class="value">' + a.userRole + '</span></div>' +
                '<div class="detail-row"><span class="label">Type</span><span class="value">' + a.type.toUpperCase() + '</span></div>' +
                '<div class="detail-row"><span class="label">Time</span><span class="value">' + new Date(a.time).toLocaleString() + '</span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + (a.read ? 'Read' : 'Unread') + '</span></div>' +
                (a.scope ? '<div class="detail-row"><span class="label">Scope</span><span class="value">' + a.scope + '</span></div>' : '') +
                (a.facility ? '<div class="detail-row"><span class="label">Facility</span><span class="value">' + a.facility + '</span></div>' : '') +
                '<div class="detail-row" style="grid-column:1/-1;"><span class="label">Details</span><span class="value">' + a.details + '</span></div>' +
                '</div>' +
                (metaKeys.length > 0 ? '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:hsl(var(--foreground));margin-bottom:4px;">📊 Metadata</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px;background:hsl(var(--muted));border-radius:var(--radius));">' + metaHtml + '</div></div>' : '');
        }

        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeDetail()">Close</button>' +
                '<button class="btn btn-outline btn-sm" onclick="closeDetail();showToast(\'📤 Sharing activity...\')">📤 Share</button>';
        }

        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeDetail() {
        var modal = getEl('detailModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    // ============================================
    // ACTIVITY ACTIONS
    // ============================================

    function markRead(id) {
        for (var i = 0; i < activities.length; i++) {
            if (activities[i].id === id) {
                activities[i].read = true;
                break;
            }
        }
        renderActivities();
        renderStats();
        showToast('✅ Marked as read');
    }

    function markAllRead() {
        for (var i = 0; i < activities.length; i++) {
            activities[i].read = true;
        }
        renderActivities();
        renderStats();
        showToast('✅ All activities marked as read');
    }

    function refreshFeed() {
        showToast('🔄 Refreshing feed...');
        setTimeout(function() {
            renderActivities();
            renderStats();
            showToast('✅ Feed refreshed');
        }, 800);
    }

    function toggleLiveUpdates() {
        liveUpdates = !liveUpdates;
        var btn = getEl('liveToggleBtn');
        if (liveUpdates) {
            if (btn) { btn.innerHTML = '🔴 Live'; btn.className = 'btn btn-ghost btn-sm'; }
            startLiveUpdates();
            showToast('🔴 Live updates enabled');
        } else {
            if (btn) { btn.innerHTML = '⏸️ Paused'; btn.className = 'btn btn-secondary btn-sm'; }
            stopLiveUpdates();
            showToast('⏸️ Live updates paused');
        }
    }

    function startLiveUpdates() {
        if (liveInterval) return;
        liveInterval = setInterval(function() {
            var types = ['upload', 'approved', 'emission', 'review'];
            var users = ['John Doe', 'Sarah Johnson', 'Mike Roberts', 'Anna Liu', 'Emma Martinez'];
            var actions = ['uploaded', 'approved', 'added', 'updated', 'started'];
            var items = ['document', 'data', 'report', 'record'];
            var verbs = ['uploaded', 'added', 'generated', 'created'];
            
            var newActivity = {
                id: 'act_' + String(activities.length + 1).padStart(3, '0'),
                type: types[Math.floor(Math.random() * types.length)],
                user: users[Math.floor(Math.random() * users.length)],
                userRole: ['Admin', 'Manager', 'Analyst', 'Analyst', 'Analyst'][Math.floor(Math.random() * 5)],
                action: actions[Math.floor(Math.random() * actions.length)],
                title: 'New ' + items[Math.floor(Math.random() * items.length)],
                description: 'A new ' + items[Math.floor(Math.random() * items.length)] + ' was ' + verbs[Math.floor(Math.random() * verbs.length)],
                details: 'Auto-generated activity from live feed',
                time: new Date().toISOString(),
                read: false,
                metadata: { source: 'live_feed' },
                scope: ['Scope 1', 'Scope 2', 'Scope 3', null][Math.floor(Math.random() * 4)],
                facility: ['London Office', 'Manchester Office', 'Data Center', null][Math.floor(Math.random() * 4)]
            };
            activities.unshift(newActivity);
            if (activities.length > 50) {
                activities.pop();
            }
            applyFilters();
            renderStats();
            showToast('🔴 New activity: ' + newActivity.title, 'info');
        }, 30000);
    }

    function stopLiveUpdates() {
        if (liveInterval) {
            clearInterval(liveInterval);
            liveInterval = null;
        }
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Activity Feed Module...');
        
        var container = getActivityList();
        if (!container) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }

        var searchEl = getSearchInput();
        if (searchEl) {
            searchEl.addEventListener('input', function() { applyFilters(); });
        }

        // Date inputs
        var fromEl = getEl('dateFrom');
        var toEl = getEl('dateTo');
        if (fromEl) fromEl.addEventListener('change', applyFilters);
        if (toEl) toEl.addEventListener('change', applyFilters);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var modal = getEl('detailModal');
                if (modal && modal.classList.contains('show')) {
                    closeDetail();
                }
            }
        });

        var modal = getEl('detailModal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) closeDetail();
            });
        }

        applyFilters();
        renderStats();
        startLiveUpdates();

        console.log('✅ Activity Feed module loaded successfully!');
        console.log('📊 ' + activities.length + ' activities loaded');
        console.log('🔴 Live updates enabled');
    }

    initModule();

    if (document.readyState !== 'complete') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOMContentLoaded fired');
            initModule();
        });
    }

    window.addEventListener('beforeunload', function() {
        stopLiveUpdates();
    });

    // ============================================
    // MAKE FUNCTIONS GLOBAL
    // ============================================

    window.applyFilters = applyFilters;
    window.clearFilters = clearFilters;
    window.sortBy = sortBy;
    window.goToPage = goToPage;
    window.markRead = markRead;
    window.markAllRead = markAllRead;
    window.refreshFeed = refreshFeed;
    window.toggleLiveUpdates = toggleLiveUpdates;
    window.openDetail = openDetail;
    window.closeDetail = closeDetail;
    window.showToast = showToast;
})();