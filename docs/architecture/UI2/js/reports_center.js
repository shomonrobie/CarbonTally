// Reports Center Module - SPA Compatible

(function(){
    console.log('📊 Reports Center JS loaded');

    // ============================================
    // MOCK DATA - Based on Schema
    // ============================================

    var reports = [
        { id: 'rep_001', name: 'SECR Report 2025', type: 'regulatory', category: 'SECR', description: 'Streamlined Energy and Carbon Reporting for UK compliance', format: 'PDF', pages: 45, size: 2.4, date: '2025-12-15', year: 2025, status: 'ready', generatedBy: 'John Doe', scope: 'All Scopes', includes: ['Charts', 'Narratives', 'Comparative Data'], icon: '🇬🇧' },
        { id: 'rep_002', name: 'CSRD Compliance Report', type: 'compliance', category: 'CSRD', description: 'Corporate Sustainability Reporting Directive - ESRS E1', format: 'PDF', pages: 32, size: 1.8, date: '2025-11-20', year: 2025, status: 'ready', generatedBy: 'Sarah Johnson', scope: 'All Scopes', includes: ['Charts', 'Narratives'], icon: '🇪🇺' },
        { id: 'rep_003', name: 'ISSB Disclosure S1 & S2', type: 'regulatory', category: 'ISSB', description: 'International Sustainability Standards Board disclosure', format: 'PDF', pages: 28, size: 1.6, date: '2025-10-10', year: 2025, status: 'draft', generatedBy: 'Mike Roberts', scope: 'All Scopes', includes: ['Charts', 'Comparative Data'], icon: '🌍' },
        { id: 'rep_004', name: 'Emissions Trend Analysis', type: 'operational', category: 'Trend', description: 'Year-over-year emissions trend analysis with projections', format: 'Excel', pages: 0, size: 3.2, date: '2025-09-05', year: 2025, status: 'ready', generatedBy: 'Anna Liu', scope: 'All Scopes', includes: ['Charts', 'Raw Data'], icon: '📈' },
        { id: 'rep_005', name: 'Facility Emissions Report', type: 'operational', category: 'Facility', description: 'Detailed emissions breakdown by facility and location', format: 'PDF', pages: 18, size: 1.2, date: '2025-08-15', year: 2025, status: 'ready', generatedBy: 'Tom Chen', scope: 'All Scopes', includes: ['Charts', 'Narratives'], icon: '🏢' },
        { id: 'rep_006', name: 'Asset Emissions Analysis', type: 'operational', category: 'Asset', description: 'Emissions by asset, vehicle, and equipment', format: 'Excel', pages: 0, size: 2.8, date: '2025-07-20', year: 2025, status: 'ready', generatedBy: 'Emma Martinez', scope: 'Scope 1', includes: ['Charts', 'Raw Data'], icon: '🚗' },
        { id: 'rep_007', name: 'Scope Analysis Report', type: 'operational', category: 'Scope', description: 'Detailed breakdown by GHG Protocol scopes', format: 'PDF', pages: 22, size: 1.5, date: '2025-06-10', year: 2025, status: 'ready', generatedBy: 'John Doe', scope: 'All Scopes', includes: ['Charts', 'Narratives', 'Comparative Data'], icon: '🎯' },
        { id: 'rep_008', name: 'TCFD Report 2025', type: 'compliance', category: 'TCFD', description: 'Task Force on Climate-related Financial Disclosures', format: 'PDF', pages: 38, size: 2.1, date: '2025-05-15', year: 2025, status: 'ready', generatedBy: 'Sarah Johnson', scope: 'All Scopes', includes: ['Charts', 'Narratives'], icon: '📋' },
        { id: 'rep_009', name: 'SECR Report 2024', type: 'regulatory', category: 'SECR', description: 'Streamlined Energy and Carbon Reporting for UK compliance', format: 'PDF', pages: 42, size: 2.2, date: '2024-12-15', year: 2024, status: 'archived', generatedBy: 'John Doe', scope: 'All Scopes', includes: ['Charts', 'Narratives', 'Comparative Data'], icon: '🇬🇧' },
        { id: 'rep_010', name: 'Audit Data Export 2025', type: 'financial', category: 'Audit', description: 'Comprehensive data export for external audit', format: 'Excel', pages: 0, size: 8.5, date: '2025-11-01', year: 2025, status: 'processing', generatedBy: 'Mike Roberts', scope: 'All Scopes', includes: ['Raw Data', 'Comparative Data'], icon: '📊' },
        { id: 'rep_011', name: 'GHG Protocol Report', type: 'compliance', category: 'GHG', description: 'Complete GHG Protocol corporate standard report', format: 'PDF', pages: 55, size: 3.6, date: '2025-04-20', year: 2025, status: 'ready', generatedBy: 'Anna Liu', scope: 'All Scopes', includes: ['Charts', 'Narratives', 'Raw Data'], icon: '📐' },
        { id: 'rep_012', name: 'Net Zero Progress Report', type: 'operational', category: 'Net Zero', description: 'Progress towards net zero targets with pathway analysis', format: 'PDF', pages: 30, size: 1.9, date: '2025-09-30', year: 2025, status: 'draft', generatedBy: 'Emma Martinez', scope: 'All Scopes', includes: ['Charts', 'Narratives', 'Comparative Data'], icon: '🎯' },
        { id: 'rep_013', name: 'CSRD Report 2024', type: 'compliance', category: 'CSRD', description: 'Corporate Sustainability Reporting Directive 2024', format: 'PDF', pages: 30, size: 1.7, date: '2024-11-15', year: 2024, status: 'archived', generatedBy: 'Sarah Johnson', scope: 'All Scopes', includes: ['Charts', 'Narratives'], icon: '🇪🇺' },
        { id: 'rep_014', name: 'Scope 3 Analysis Report', type: 'operational', category: 'Scope', description: 'Detailed Scope 3 emissions analysis by category', format: 'Excel', pages: 0, size: 4.2, date: '2025-08-01', year: 2025, status: 'ready', generatedBy: 'Mike Roberts', scope: 'Scope 3', includes: ['Charts', 'Raw Data', 'Comparative Data'], icon: '🌍' },
        { id: 'rep_015', name: 'Facility Benchmarking Report', type: 'operational', category: 'Facility', description: 'Comparative facility emissions benchmarking', format: 'PDF', pages: 24, size: 1.4, date: '2025-07-10', year: 2025, status: 'draft', generatedBy: 'Anna Liu', scope: 'All Scopes', includes: ['Charts', 'Narratives', 'Comparative Data'], icon: '🏢' }
    ];

    var categories = [
        { id: 'regulatory', name: '📋 Regulatory', desc: 'SECR, CSRD, ISSB compliance reports', count: 0 },
        { id: 'compliance', name: '✅ Compliance', desc: 'GHG Protocol, TCFD, ESRS reports', count: 0 },
        { id: 'operational', name: '📊 Operational', desc: 'Trends, facilities, assets analysis', count: 0 },
        { id: 'financial', name: '💰 Financial', desc: 'Audit data, financial disclosures', count: 0 },
        { id: 'custom', name: '🎨 Custom', desc: 'Custom reports and exports', count: 0 }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentPage = 1;
    var perPage = 6;
    var currentSort = { field: 'date', direction: 'desc' };
    var toastTimeout = null;
    var selectedReportId = null;

    var filterYear = '2025';
    var filterType = 'all';
    var filterStatus = 'all';
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
    // HELPERS
    // ============================================

    function getStatusBadge(status) {
        var badges = {
            'ready': '<span class="badge badge-success">✅ Ready</span>',
            'draft': '<span class="badge badge-warning">📝 Draft</span>',
            'processing': '<span class="badge badge-muted">⏳ Processing</span>',
            'archived': '<span class="badge badge-muted">📦 Archived</span>',
            'error': '<span class="badge badge-destructive">❌ Error</span>'
        };
        return badges[status] || badges.ready;
    }

    function getStatusIcon(status) {
        var icons = {
            'ready': '✅',
            'draft': '📝',
            'processing': '⏳',
            'archived': '📦',
            'error': '❌'
        };
        return icons[status] || '✅';
    }

    function formatFileSize(mb) {
        if (mb < 1) return (mb * 1024).toFixed(0) + ' KB';
        return mb.toFixed(1) + ' MB';
    }

    function sortReportsBy(field) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = 'asc';
        }
        currentPage = 1;
        renderReports();
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderCategories() {
        var container = getEl('reportCategories');
        if (!container) return;
        
        var year = filterYear;
        for (var i = 0; i < categories.length; i++) {
            var cat = categories[i];
            cat.count = 0;
            for (var j = 0; j < reports.length; j++) {
                var r = reports[j];
                if (r.type === cat.id) {
                    if (year === 'all' || r.year === parseInt(year)) {
                        cat.count++;
                    }
                }
            }
        }

        var html = '';
        for (var k = 0; k < categories.length; k++) {
            var c = categories[k];
            html +=
                '<div class="report-category" onclick="filterByCategory(\'' + c.id + '\')">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;">' +
                '<span class="icon">' + c.name.split(' ')[0] + '</span>' +
                '<span class="badge badge-muted">' + c.count + '</span>' +
                '</div>' +
                '<div class="title">' + c.name + '</div>' +
                '<div class="desc">' + c.desc + '</div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    function renderReports() {
        var container = getEl('reportGrid');
        var countEl = getEl('reportCount');
        var paginationEl = getEl('pagination');
        if (!container) return;
        
        var filtered = reports.slice();
        
        // Year filter
        if (filterYear !== 'all') {
            filtered = filtered.filter(function(r) { return r.year === parseInt(filterYear); });
        }
        
        // Type filter
        if (filterType !== 'all') {
            filtered = filtered.filter(function(r) { return r.type === filterType; });
        }
        
        // Status filter
        if (filterStatus !== 'all') {
            filtered = filtered.filter(function(r) { return r.status === filterStatus; });
        }
        
        // Search filter
        if (filterSearch) {
            filtered = filtered.filter(function(r) {
                return r.name.toLowerCase().indexOf(filterSearch) !== -1 ||
                    r.description.toLowerCase().indexOf(filterSearch) !== -1 ||
                    r.category.toLowerCase().indexOf(filterSearch) !== -1 ||
                    r.generatedBy.toLowerCase().indexOf(filterSearch) !== -1;
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
        
        if (countEl) countEl.textContent = filtered.length + ' reports';
        
        var start = (currentPage - 1) * perPage;
        var pageItems = filtered.slice(start, start + perPage);
        
        if (pageItems.length === 0) {
            container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:60px 20px;color:hsl(var(--muted-foreground));">📭 No reports found</div>';
            renderPagination(filtered.length);
            return;
        }
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var report = pageItems[i];
            html +=
                '<div class="report-card" onclick="viewReportDetail(\'' + report.id + '\')">' +
                '<div class="report-header">' +
                '<div style="display:flex;align-items:center;gap:12px;">' +
                '<span class="report-icon">' + report.icon + '</span>' +
                '<div><div style="font-size:12px;color:hsl(var(--muted-foreground));">' + report.category + ' • ' + report.type.toUpperCase() + '</div></div>' +
                '</div>' +
                getStatusBadge(report.status) +
                '</div>' +
                '<div class="report-title">' + report.name + '</div>' +
                '<div class="report-desc">' + report.description + '</div>' +
                '<div class="report-meta">' +
                '<span>📅 ' + report.date + '</span>' +
                '<span>📄 ' + report.format + '</span>' +
                '<span>📄 ' + (report.pages > 0 ? report.pages + ' pages' : 'Data export') + '</span>' +
                '<span>💾 ' + formatFileSize(report.size) + '</span>' +
                '<span>👤 ' + report.generatedBy + '</span>' +
                '</div>' +
                '<div style="display:flex;gap:4px;margin-top:8px;flex-wrap:wrap;">' +
                report.includes.map(function(i) { return '<span class="badge badge-muted">' + i + '</span>'; }).join('') +
                '</div>' +
                '<div class="report-actions">' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();downloadReport(\'' + report.id + '\')">⬇️ Download</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();viewReportDetail(\'' + report.id + '\')">👁️ View</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();shareReport(\'' + report.id + '\')">📤 Share</button>' +
                (report.status !== 'archived' ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();archiveReport(\'' + report.id + '\')" style="color:hsl(var(--muted-foreground));">📦 Archive</button>' : '') +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();deleteReport(\'' + report.id + '\')" style="color:hsl(var(--destructive));margin-left:auto;">🗑️</button>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderPagination(filtered.length);
    }

    function renderPagination(total) {
        var container = getEl('pagination');
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' reports</div><div class="page-buttons"></div>';
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
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' reports</div><div class="page-buttons">' + btns + '</div>';
    }

    function goToPage(page) {
        var totalPages = Math.ceil(reports.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderReports();
    }

    function applyFilters() {
        var yearEl = getEl('reportYearFilter');
        var typeEl = getEl('reportTypeFilter');
        var statusEl = getEl('reportStatusFilter');
        var searchEl = getEl('searchInput');
        
        filterYear = yearEl ? yearEl.value : '2025';
        filterType = typeEl ? typeEl.value : 'all';
        filterStatus = statusEl ? statusEl.value : 'all';
        filterSearch = searchEl ? searchEl.value.toLowerCase().trim() : '';
        currentPage = 1;
        renderCategories();
        renderReports();
    }

    function clearFilters() {
        var yearEl = getEl('reportYearFilter');
        var typeEl = getEl('reportTypeFilter');
        var statusEl = getEl('reportStatusFilter');
        var searchEl = getEl('searchInput');
        
        if (yearEl) yearEl.value = '2025';
        if (typeEl) typeEl.value = 'all';
        if (statusEl) statusEl.value = 'all';
        if (searchEl) searchEl.value = '';
        filterYear = '2025';
        filterType = 'all';
        filterStatus = 'all';
        filterSearch = '';
        currentPage = 1;
        renderCategories();
        renderReports();
        showToast('🔄 Filters cleared');
    }

    function filterByCategory(category) {
        var typeEl = getEl('reportTypeFilter');
        if (typeEl) typeEl.value = category;
        applyFilters();
        showToast('📊 Filtered: ' + category.toUpperCase() + ' reports', 'info');
    }

    function sortReports(field) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = 'asc';
        }
        currentPage = 1;
        renderReports();
    }

    // ============================================
    // REPORT ACTIONS
    // ============================================

    function downloadReport(id) {
        var report = null;
        for (var i = 0; i < reports.length; i++) {
            if (reports[i].id === id) { report = reports[i]; break; }
        }
        if (report) {
            showToast('⬇️ Downloading: ' + report.name + ' (' + report.format + ')');
            setTimeout(function() {
                showToast('✅ ' + report.name + ' downloaded successfully!');
            }, 1500);
        }
    }

    function viewReportDetail(id) {
        var report = null;
        for (var i = 0; i < reports.length; i++) {
            if (reports[i].id === id) { report = reports[i]; break; }
        }
        if (!report) return;

        selectedReportId = id;
        var titleEl = getEl('detailReportTitle');
        var subtitleEl = getEl('detailReportSubtitle');
        var bodyEl = getEl('detailReportBody');
        var footerEl = getEl('detailReportFooter');
        var modal = getEl('reportDetailModal');
        
        if (titleEl) titleEl.textContent = report.name;
        if (subtitleEl) subtitleEl.textContent = report.category + ' • ' + report.type.toUpperCase() + ' • ' + report.format;

        if (bodyEl) {
            var includesHtml = '';
            for (var j = 0; j < report.includes.length; j++) {
                includesHtml += '<span class="badge badge-muted">' + report.includes[j] + '</span>';
            }
            
            bodyEl.innerHTML =
                '<div class="detail-row"><span class="label">Report ID</span><span class="value">' + report.id + '</span></div>' +
                '<div class="detail-row"><span class="label">Name</span><span class="value"><strong>' + report.name + '</strong></span></div>' +
                '<div class="detail-row"><span class="label">Description</span><span class="value">' + report.description + '</span></div>' +
                '<div class="detail-row"><span class="label">Category</span><span class="value"><span class="badge badge-primary">' + report.category + '</span></span></div>' +
                '<div class="detail-row"><span class="label">Type</span><span class="value"><span class="badge badge-muted">' + report.type.toUpperCase() + '</span></span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + getStatusBadge(report.status) + '</span></div>' +
                '<div class="detail-row"><span class="label">Format</span><span class="value">' + report.format + '</span></div>' +
                '<div class="detail-row"><span class="label">Pages</span><span class="value">' + (report.pages > 0 ? report.pages + ' pages' : 'Data export') + '</span></div>' +
                '<div class="detail-row"><span class="label">Size</span><span class="value">' + formatFileSize(report.size) + '</span></div>' +
                '<div class="detail-row"><span class="label">Date Generated</span><span class="value">' + report.date + '</span></div>' +
                '<div class="detail-row"><span class="label">Generated By</span><span class="value">' + report.generatedBy + '</span></div>' +
                '<div class="detail-row"><span class="label">Scope</span><span class="value">' + report.scope + '</span></div>' +
                '<div class="detail-row"><span class="label">Includes</span><span class="value" style="display:flex;gap:4px;flex-wrap:wrap;">' + includesHtml + '</span></div>';
        }

        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeReportDetail()">Close</button>' +
                '<button class="btn btn-primary btn-sm" onclick="downloadReport(\'' + report.id + '\');closeReportDetail();">⬇️ Download</button>' +
                '<button class="btn btn-outline btn-sm" onclick="shareReport(\'' + report.id + '\');closeReportDetail();">📤 Share</button>' +
                (report.status !== 'archived' ? '<button class="btn btn-secondary btn-sm" onclick="archiveReport(\'' + report.id + '\');closeReportDetail();">📦 Archive</button>' : '');
        }

        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeReportDetail() {
        var modal = getEl('reportDetailModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function shareReport(id) {
        var report = null;
        for (var i = 0; i < reports.length; i++) {
            if (reports[i].id === id) { report = reports[i]; break; }
        }
        if (report) {
            showToast('📤 Share link for: ' + report.name + ' copied to clipboard!');
        }
    }

    function archiveReport(id) {
        var report = null;
        for (var i = 0; i < reports.length; i++) {
            if (reports[i].id === id) { report = reports[i]; break; }
        }
        if (report) {
            report.status = 'archived';
            renderReports();
            showToast('📦 Archived: ' + report.name);
        }
    }

    function deleteReport(id) {
        var report = null;
        for (var i = 0; i < reports.length; i++) {
            if (reports[i].id === id) { report = reports[i]; break; }
        }
        if (!report) return;
        
        if (confirm('Are you sure you want to delete this report?')) {
            var index = -1;
            for (var i = 0; i < reports.length; i++) {
                if (reports[i].id === id) { index = i; break; }
            }
            if (index !== -1) {
                var name = reports[index].name;
                reports.splice(index, 1);
                renderCategories();
                renderReports();
                showToast('🗑️ Deleted: ' + name);
            }
        }
    }

    // ============================================
    // REPORT GENERATOR
    // ============================================

    function showReportGenerator() {
        var modal = getEl('reportGeneratorModal');
        if (!modal) return;
        
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        var nameEl = getEl('genReportName');
        if (nameEl) {
            var yearEl = getEl('genReportYear');
            var year = yearEl ? yearEl.value : '2025';
            nameEl.placeholder = 'CarbonTally_Report_' + year + '_' + new Date().toISOString().split('T')[0];
        }
        // Reset form
        var typeEl = getEl('genReportType');
        var formatEl = getEl('genReportFormat');
        var scopeEl = getEl('genReportScope');
        var facilityEl = getEl('genReportFacility');
        if (typeEl) typeEl.value = '';
        if (formatEl) formatEl.value = 'pdf';
        if (scopeEl) scopeEl.value = 'all';
        if (facilityEl) facilityEl.value = 'all';
        if (nameEl) nameEl.value = '';
        var chartsEl = getEl('genIncludeCharts');
        var narrativesEl = getEl('genIncludeNarratives');
        var rawDataEl = getEl('genIncludeRawData');
        var comparativeEl = getEl('genIncludeComparative');
        if (chartsEl) chartsEl.checked = true;
        if (narrativesEl) narrativesEl.checked = false;
        if (rawDataEl) rawDataEl.checked = false;
        if (comparativeEl) comparativeEl.checked = true;
    }

    function closeReportGenerator() {
        var modal = getEl('reportGeneratorModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function generateReport() {
        var typeEl = getEl('genReportType');
        var yearEl = getEl('genReportYear');
        var formatEl = getEl('genReportFormat');
        var nameEl = getEl('genReportName');
        var scopeEl = getEl('genReportScope');
        var chartsEl = getEl('genIncludeCharts');
        var narrativesEl = getEl('genIncludeNarratives');
        var rawDataEl = getEl('genIncludeRawData');
        var comparativeEl = getEl('genIncludeComparative');
        
        var type = typeEl ? typeEl.value : '';
        var year = yearEl ? yearEl.value : '2025';
        var format = formatEl ? formatEl.value : 'pdf';
        var name = nameEl ? nameEl.value.trim() : '';
        var scope = scopeEl ? scopeEl.value : 'all';
        
        if (!type) {
            showToast('⚠️ Please select a report type', 'warning');
            if (typeEl) typeEl.focus();
            return;
        }
        
        var typeMap = {
            'secr': { category: 'SECR', icon: '🇬🇧' },
            'csrd': { category: 'CSRD', icon: '🇪🇺' },
            'issb': { category: 'ISSB', icon: '🌍' },
            'ghg': { category: 'GHG', icon: '📐' },
            'tcfd': { category: 'TCFD', icon: '📋' },
            'audit': { category: 'Audit', icon: '📊' },
            'compliance': { category: 'Compliance', icon: '✅' },
            'trend': { category: 'Trend', icon: '📈' },
            'facility': { category: 'Facility', icon: '🏢' },
            'asset': { category: 'Asset', icon: '🚗' },
            'scope': { category: 'Scope', icon: '🎯' },
            'custom': { category: 'Custom', icon: '🎨' }
        };
        
        var info = typeMap[type] || { category: 'Custom', icon: '📄' };
        var includes = [];
        if (chartsEl && chartsEl.checked) includes.push('Charts');
        if (narrativesEl && narrativesEl.checked) includes.push('Narratives');
        if (rawDataEl && rawDataEl.checked) includes.push('Raw Data');
        if (comparativeEl && comparativeEl.checked) includes.push('Comparative Data');
        
        if (includes.length === 0) includes.push('Charts');
        
        var reportName = name || 'CarbonTally_Report_' + year + '_' + new Date().toISOString().split('T')[0];
        var scopeLabel = scope === 'all' ? 'All Scopes' : scope.toUpperCase();
        
        var newReport = {
            id: 'rep_' + String(reports.length + 1).padStart(3, '0'),
            name: reportName,
            type: type === 'custom' ? 'custom' :
                (['secr', 'issb'].indexOf(type) !== -1) ? 'regulatory' :
                (['csrd', 'ghg', 'tcfd'].indexOf(type) !== -1) ? 'compliance' :
                (['audit'].indexOf(type) !== -1) ? 'financial' : 'operational',
            category: info.category,
            description: info.category + ' report generated on ' + new Date().toLocaleDateString(),
            format: format.toUpperCase(),
            pages: format === 'pdf' ? Math.floor(Math.random() * 30) + 20 : 0,
            size: (Math.random() * 4 + 0.5).toFixed(1),
            date: new Date().toISOString().split('T')[0],
            year: parseInt(year),
            status: 'processing',
            generatedBy: 'Current User',
            scope: scopeLabel,
            includes: includes,
            icon: info.icon
        };
        
        reports.push(newReport);
        renderCategories();
        renderReports();
        closeReportGenerator();
        showToast('📊 Generating ' + newReport.name + '...');
        
        setTimeout(function() {
            newReport.status = 'ready';
            renderReports();
            showToast('✅ Report generated: ' + newReport.name);
        }, 3000);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Reports Center Module...');
        
        var container = getEl('reportGrid');
        if (!container) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Set up event listeners
        var searchEl = getEl('searchInput');
        if (searchEl) {
            searchEl.addEventListener('input', applyFilters);
        }
        
        // Modal overlay click to close
        var modals = document.querySelectorAll('.modal-overlay');
        for (var i = 0; i < modals.length; i++) {
            modals[i].addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.remove('show');
                    document.body.style.overflow = '';
                }
            });
        }
        
        // Escape key to close modals
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var genModal = getEl('reportGeneratorModal');
                var detailModal = getEl('reportDetailModal');
                if (genModal && genModal.classList.contains('show')) {
                    closeReportGenerator();
                }
                if (detailModal && detailModal.classList.contains('show')) {
                    closeReportDetail();
                }
            }
            // Ctrl+G to open generator
            if (e.key === 'g' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                showReportGenerator();
            }
        });
        
        // Initial render
        renderCategories();
        renderReports();
        
        console.log('✅ Reports Center module loaded successfully!');
        console.log('📊 ' + reports.length + ' reports loaded');
        console.log('⌨️  Ctrl+G to open report generator');
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
    // MAKE FUNCTIONS GLOBAL // reports_center.js
    // ============================================

    window.applyFilters = applyFilters;
    window.clearFilters = clearFilters;
    window.filterByCategory = filterByCategory;
    window.sortReports = sortReports;
    window.goToPage = goToPage;
    window.downloadReport = downloadReport;
    window.viewReportDetail = viewReportDetail;
    window.closeReportDetail = closeReportDetail;
    window.shareReport = shareReport;
    window.archiveReport = archiveReport;
    window.deleteReport = deleteReport;
    window.showReportGenerator = showReportGenerator;
    window.closeReportGenerator = closeReportGenerator;
    window.generateReport = generateReport;
    window.showToast = showToast;
})(); // <-- Keeps everything secure