// Export History Module - SPA Compatible

(function() {

    console.log('📊 Export History JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var users = [
        { id: 'u1', name: 'John Doe', avatar: 'JD', role: 'Admin' },
        { id: 'u2', name: 'Sarah Johnson', avatar: 'SJ', role: 'Sustainability Officer' },
        { id: 'u3', name: 'Mike Chen', avatar: 'MC', role: 'Data Analyst' },
        { id: 'u4', name: 'Emma Wilson', avatar: 'EW', role: 'Compliance Manager' },
        { id: 'u5', name: 'Alex Rivera', avatar: 'AR', role: 'Analyst' },
    ];

    var formatLabels = { 'pdf': 'PDF', 'xlsx': 'Excel', 'csv': 'CSV', 'docx': 'Word', 'zip': 'ZIP' };
    var typeLabels = {
        'emissions': 'Emissions Data',
        'compliance': 'Compliance Report',
        'secr': 'SECR Report',
        'csrd': 'CSRD Report',
        'issb': 'ISSB Disclosure',
        'audit': 'Audit Log',
        'custom': 'Custom Query'
    };

    var exportItems = [
        { id: 'e1', userId: 'u1', fileName: 'SECR_Report_2026_Q4', format: 'pdf', recordCount: 245, size: '2.4 MB', status: 'completed', createdAt: '2026-01-15 14:30', expiresAt: '2026-02-14 14:30', downloads: 12, exportType: 'secr', filters: { year: '2026', quarter: 'Q4' } },
        { id: 'e2', userId: 'u2', fileName: 'Emissions_Data_2026_Annual', format: 'xlsx', recordCount: 1256, size: '5.8 MB', status: 'completed', createdAt: '2026-01-14 09:15', expiresAt: '2026-02-13 09:15', downloads: 8, exportType: 'emissions', filters: { year: '2026', scope: 'all' } },
        { id: 'e3', userId: 'u3', fileName: 'CSRD_Disclosure_Report', format: 'pdf', recordCount: 534, size: '3.2 MB', status: 'processing', createdAt: '2026-01-13 11:20', expiresAt: '2026-02-12 11:20', downloads: 0, exportType: 'csrd', filters: { year: '2026', standard: 'esrs_e1' } },
        { id: 'e4', userId: 'u4', fileName: 'Audit_Log_Export_Jan2026', format: 'csv', recordCount: 3456, size: '12.1 MB', status: 'completed', createdAt: '2026-01-12 08:00', expiresAt: '2026-02-11 08:00', downloads: 5, exportType: 'audit', filters: { startDate: '2026-01-01', endDate: '2026-01-31' } },
        { id: 'e5', userId: 'u1', fileName: 'ISSB_S1_S2_Disclosure', format: 'docx', recordCount: 89, size: '1.2 MB', status: 'completed', createdAt: '2026-01-11 16:45', expiresAt: '2026-02-10 16:45', downloads: 3, exportType: 'issb', filters: { standard: 's1_s2', year: '2026' } },
        { id: 'e6', userId: 'u5', fileName: 'Custom_Query_Emissions_Scope3', format: 'xlsx', recordCount: 789, size: '4.6 MB', status: 'failed', createdAt: '2026-01-10 13:50', expiresAt: '2026-02-09 13:50', downloads: 0, exportType: 'custom', filters: { scope: '3', category: 'all' } },
        { id: 'e7', userId: 'u2', fileName: 'Compliance_Summary_2026', format: 'pdf', recordCount: 167, size: '1.8 MB', status: 'expired', createdAt: '2025-12-15 10:10', expiresAt: '2026-01-14 10:10', downloads: 15, exportType: 'compliance', filters: { year: '2026', status: 'all' } },
        { id: 'e8', userId: 'u3', fileName: 'GHG_Inventory_Data_2026', format: 'zip', recordCount: 2345, size: '18.3 MB', status: 'completed', createdAt: '2026-01-09 09:30', expiresAt: '2026-02-08 09:30', downloads: 4, exportType: 'emissions', filters: { year: '2026', scope: 'all', format: 'zip' } },
        { id: 'e9', userId: 'u4', fileName: 'SECR_Financial_Data', format: 'xlsx', recordCount: 456, size: '2.9 MB', status: 'completed', createdAt: '2026-01-08 15:20', expiresAt: '2026-02-07 15:20', downloads: 7, exportType: 'secr', filters: { year: '2026', type: 'financial' } },
        { id: 'e10', userId: 'u1', fileName: 'CSRD_Data_Export_Jan', format: 'csv', recordCount: 1234, size: '6.7 MB', status: 'processing', createdAt: '2026-01-07 11:00', expiresAt: '2026-02-06 11:00', downloads: 0, exportType: 'csrd', filters: { month: 'January', year: '2026' } },
        { id: 'e11', userId: 'u5', fileName: 'Audit_Trail_Complete_2025', format: 'pdf', recordCount: 5678, size: '15.4 MB', status: 'expired', createdAt: '2025-12-20 14:00', expiresAt: '2026-01-19 14:00', downloads: 22, exportType: 'audit', filters: { year: '2025' } },
        { id: 'e12', userId: 'u2', fileName: 'Emissions_Trend_Analysis', format: 'docx', recordCount: 234, size: '1.5 MB', status: 'completed', createdAt: '2026-01-06 09:45', expiresAt: '2026-02-05 09:45', downloads: 2, exportType: 'custom', filters: { period: '5y', granularity: 'monthly' } },
        { id: 'e13', userId: 'u3', fileName: 'ISSB_Climate_Disclosure', format: 'pdf', recordCount: 145, size: '2.1 MB', status: 'failed', createdAt: '2026-01-05 13:30', expiresAt: '2026-02-04 13:30', downloads: 0, exportType: 'issb', filters: { standard: 's1', year: '2026' } },
        { id: 'e14', userId: 'u4', fileName: 'Carbon_Footprint_Report', format: 'xlsx', recordCount: 678, size: '3.4 MB', status: 'completed', createdAt: '2026-01-04 10:20', expiresAt: '2026-02-03 10:20', downloads: 6, exportType: 'emissions', filters: { scope: '1,2,3', year: '2026' } },
        { id: 'e15', userId: 'u1', fileName: 'Compliance_Checklist_2026', format: 'pdf', recordCount: 98, size: '0.8 MB', status: 'completed', createdAt: '2026-01-03 16:00', expiresAt: '2026-02-02 16:00', downloads: 10, exportType: 'compliance', filters: { framework: 'secr,csrd,issb' } }
    ];

    // ============================================
    // STATE
    // ============================================

    var filteredExports = [];
    var currentPage = 1;
    var perPage = 10;
    var currentSort = { field: 'createdAt', direction: 'desc' };
    var toastTimeout = null;
    var viewingId = null;

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
        return { name: 'Unknown', avatar: '??', role: 'Unknown' };
    }

    function getStatusBadge(status) {
        var map = {
            'completed': '<span class="badge badge-success">✅ Completed</span>',
            'processing': '<span class="badge badge-warning">⏳ Processing</span>',
            'failed': '<span class="badge badge-destructive">❌ Failed</span>',
            'expired': '<span class="badge badge-muted">⏰ Expired</span>'
        };
        return map[status] || status;
    }

    function getExpiryStatus(expiresAt) {
        var now = new Date();
        var expiry = new Date(expiresAt);
        var daysLeft = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));
        
        if (daysLeft < 0) return '<span style="color:hsl(var(--destructive));font-weight:500;">Expired</span>';
        if (daysLeft < 7) return '<span style="color:hsl(var(--warning));font-weight:500;">' + daysLeft + ' days</span>';
        return daysLeft + ' days';
    }

    function sortData(data, field, direction) {
        var sorted = data.slice();
        sorted.sort(function(a, b) {
            var aVal = a[field] || '';
            var bVal = b[field] || '';
            
            if (field === 'size') {
                aVal = parseFloat(aVal.replace(' MB', ''));
                bVal = parseFloat(bVal.replace(' MB', ''));
            }
            
            if (typeof aVal === 'string') {
                return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }
            return direction === 'asc' ? aVal - bVal : bVal - aVal;
        });
        return sorted;
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderStats(data) {
        var total = data.length;
        var completed = 0, processing = 0, failed = 0, downloads = 0;
        var totalMB = 0;
        
        for (var i = 0; i < data.length; i++) {
            var e = data[i];
            if (e.status === 'completed') completed++;
            if (e.status === 'processing') processing++;
            if (e.status === 'failed') failed++;
            downloads += (e.downloads || 0);
            var sizeStr = e.size.replace(' MB', '');
            var sizeVal = parseFloat(sizeStr);
            if (!isNaN(sizeVal)) totalMB += sizeVal;
        }
        
        var totalGB = totalMB > 1024 ? (totalMB / 1024).toFixed(1) + ' GB' : totalMB.toFixed(1) + ' MB';
        
        var el = getEl('totalExports');
        if (el) el.textContent = total;
        el = getEl('completedExports');
        if (el) el.textContent = completed;
        el = getEl('processingExports');
        if (el) el.textContent = processing;
        el = getEl('failedExports');
        if (el) el.textContent = failed;
        el = getEl('totalDownloads');
        if (el) el.textContent = downloads;
        el = getEl('totalSize');
        if (el) el.textContent = totalGB;
    }

    function renderTable(data) {
        var tbody = getEl('exportTableBody');
        var countEl = getEl('exportCount');
        var filterEl = getEl('filterCount');
        
        if (!tbody) return;
        
        var start = (currentPage - 1) * perPage;
        var pageItems = data.slice(start, start + perPage);
        
        if (!pageItems || pageItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:hsl(var(--muted-foreground));">📭 No exports found</td></tr>';
            if (countEl) countEl.textContent = '0';
            if (filterEl) filterEl.textContent = '0 exports';
            renderPagination(data.length);
            return;
        }
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var e = pageItems[i];
            var user = getUser(e.userId);
            var canDownload = e.status === 'completed' && e.status !== 'expired';
            var formatLabel = formatLabels[e.format] || e.format.toUpperCase();
            var typeLabel = typeLabels[e.exportType] || e.exportType;
            
            html += '<tr>' +
                '<td><div style="display:flex;align-items:center;gap:10px;">' +
                '<span style="font-size:20px;width:32px;text-align:center;">' + (e.format === 'pdf' ? '📄' : e.format === 'xlsx' ? '📊' : e.format === 'csv' ? '📈' : e.format === 'docx' ? '📝' : '📦') + '</span>' +
                '<div><div style="font-weight:500;">' + e.fileName + '</div>' +
                '<div style="font-size:11px;color:hsl(var(--muted-foreground));">' + typeLabel + ' · ' + user.name + '</div></div></div></td>' +
                '<td><span class="badge badge-secondary">' + formatLabel + '</span></td>' +
                '<td style="text-align:center;">' + e.recordCount.toLocaleString() + '</td>' +
                '<td>' + e.size + '</td>' +
                '<td>' + getStatusBadge(e.status) + '</td>' +
                '<td style="font-size:12px;color:hsl(var(--muted-foreground));">' + e.createdAt + '</td>' +
                '<td style="font-size:12px;">' + getExpiryStatus(e.expiresAt) + '</td>' +
                '<td><div style="display:flex;gap:4px;flex-wrap:wrap;">' +
                (canDownload ? '<button class="btn btn-sm btn-success" onclick="downloadExport(\'' + e.id + '\')" title="Download">⬇️</button>' : '') +
                '<button class="btn btn-sm btn-ghost" onclick="viewExportDetails(\'' + e.id + '\')" title="Details">👁️</button>' +
                (e.status === 'failed' ? '<button class="btn btn-sm btn-outline" onclick="retryExport(\'' + e.id + '\')" title="Retry">🔄</button>' : '') +
                '</div></td></tr>';
        }
        tbody.innerHTML = html;
        if (countEl) countEl.textContent = data.length;
        if (filterEl) filterEl.textContent = data.length + ' exports';
        renderPagination(data.length);
    }

    function renderPagination(total) {
        var container = getEl('pagination');
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' exports</div><div class="page-buttons"></div>';
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
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' exports</div><div class="page-buttons">' + btns + '</div>';
    }

    // ============================================
    // FILTER FUNCTIONS
    // ============================================

    function applyFilters() {
        var formatEl = getEl('formatFilter');
        var statusEl = getEl('statusFilter');
        var searchEl = getEl('globalSearch');
        var fromEl = getEl('dateFrom');
        var toEl = getEl('dateTo');
        
        var format = formatEl ? formatEl.value : 'all';
        var status = statusEl ? statusEl.value : 'all';
        var search = searchEl ? searchEl.value.toLowerCase().trim() : '';
        var from = fromEl ? fromEl.value : '';
        var to = toEl ? toEl.value : '';
        
        var filtered = [];
        for (var i = 0; i < exportItems.length; i++) {
            var e = exportItems[i];
            if (format !== 'all' && e.format !== format) continue;
            if (status !== 'all' && e.status !== status) continue;
            if (search) {
                var typeLabel = typeLabels[e.exportType] || e.exportType;
                var user = getUser(e.userId);
                var match = e.fileName.toLowerCase().indexOf(search) !== -1 ||
                        typeLabel.toLowerCase().indexOf(search) !== -1 ||
                        user.name.toLowerCase().indexOf(search) !== -1;
                if (!match) continue;
            }
            if (from && e.createdAt.split(' ')[0] < from) continue;
            if (to && e.createdAt.split(' ')[0] > to) continue;
            filtered.push(e);
        }
        
        filtered = sortData(filtered, currentSort.field, currentSort.direction);
        filteredExports = filtered;
        currentPage = 1;
        
        renderStats(exportItems);
        renderTable(filtered);
    }

    function clearFilters() {
        var formatEl = getEl('formatFilter');
        var statusEl = getEl('statusFilter');
        var searchEl = getEl('globalSearch');
        var fromEl = getEl('dateFrom');
        var toEl = getEl('dateTo');
        
        if (formatEl) formatEl.value = 'all';
        if (statusEl) statusEl.value = 'all';
        if (searchEl) searchEl.value = '';
        if (fromEl) fromEl.value = '';
        if (toEl) toEl.value = '';
        currentPage = 1;
        applyFilters();
        showToast('🔄 Filters cleared');
    }

    function sortBy(field) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = field === 'createdAt' ? 'desc' : 'asc';
        }
        currentPage = 1;
        
        var icons = document.querySelectorAll('.sort-icon');
        for (var i = 0; i < icons.length; i++) {
            icons[i].textContent = '↕';
        }
        var icon = getEl('sort-' + field);
        if (icon) {
            icon.textContent = currentSort.direction === 'asc' ? '↑' : '↓';
        }
        applyFilters();
    }

    function goToPage(page) {
        var totalPages = Math.ceil(filteredExports.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderTable(filteredExports);
    }

    // ============================================
    // DETAIL MODAL
    // ============================================

    function viewExportDetails(id) {
        var e = null;
        for (var i = 0; i < exportItems.length; i++) {
            if (exportItems[i].id === id) { e = exportItems[i]; break; }
        }
        if (!e) return;
        
        viewingId = id;
        var user = getUser(e.userId);
        var titleEl = getEl('detailTitle');
        var subtitleEl = getEl('detailSubtitle');
        var bodyEl = getEl('detailBody');
        var footerEl = getEl('detailFooter');
        var modal = getEl('detailModal');
        
        if (titleEl) titleEl.textContent = '📄 ' + e.fileName + '.' + e.format;
        if (subtitleEl) subtitleEl.textContent = (typeLabels[e.exportType] || e.exportType) + ' · ' + user.name;
        
        if (bodyEl) {
            var filtersHtml = '';
            if (e.filters) {
                var keys = Object.keys(e.filters);
                for (var k = 0; k < keys.length; k++) {
                    var key = keys[k];
                    filtersHtml += '<div><span style="color:hsl(var(--muted-foreground));">' + key + ':</span> ' + e.filters[key] + '</div>';
                }
            }
            
            bodyEl.innerHTML =
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
                '<div class="detail-row"><span class="label">File Name</span><span class="value">' + e.fileName + '</span></div>' +
                '<div class="detail-row"><span class="label">Format</span><span class="value">' + (formatLabels[e.format] || e.format.toUpperCase()) + '</span></div>' +
                '<div class="detail-row"><span class="label">Type</span><span class="value">' + (typeLabels[e.exportType] || e.exportType) + '</span></div>' +
                '<div class="detail-row"><span class="label">Records</span><span class="value">' + e.recordCount.toLocaleString() + '</span></div>' +
                '<div class="detail-row"><span class="label">Size</span><span class="value">' + e.size + '</span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + e.status + '</span></div>' +
                '<div class="detail-row"><span class="label">Created By</span><span class="value">' + user.name + '</span></div>' +
                '<div class="detail-row"><span class="label">Created</span><span class="value">' + e.createdAt + '</span></div>' +
                '<div class="detail-row"><span class="label">Expires</span><span class="value">' + e.expiresAt + '</span></div>' +
                '<div class="detail-row"><span class="label">Downloads</span><span class="value">' + (e.downloads || 0) + '</span></div>' +
                (filtersHtml ? '<div class="detail-row" style="grid-column:1/-1;"><span class="label">Filters</span><span class="value">' + filtersHtml + '</span></div>' : '') +
                '</div>';
        }
        
        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeDetailModal()">Close</button>' +
                (e.status === 'completed' ? '<button class="btn btn-success btn-sm" onclick="downloadExport(\'' + e.id + '\');closeDetailModal();">⬇️ Download</button>' : '') +
                (e.status === 'failed' ? '<button class="btn btn-outline btn-sm" onclick="retryExport(\'' + e.id + '\');closeDetailModal();">🔄 Retry</button>' : '');
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

    // ============================================
    // EXPORT ACTIONS
    // ============================================

    function downloadExport(id) {
        var e = null;
        for (var i = 0; i < exportItems.length; i++) {
            if (exportItems[i].id === id) { e = exportItems[i]; break; }
        }
        if (!e) return;
        
        e.downloads = (e.downloads || 0) + 1;
        showToast('⬇️ Downloading ' + e.fileName + '.' + e.format + '...');
        setTimeout(function() {
            applyFilters();
            showToast('✅ ' + e.fileName + ' downloaded successfully!');
        }, 1500);
    }

    function retryExport(id) {
        var e = null;
        for (var i = 0; i < exportItems.length; i++) {
            if (exportItems[i].id === id) { e = exportItems[i]; break; }
        }
        if (!e) return;
        
        if (confirm('Retry export "' + e.fileName + '"?')) {
            e.status = 'processing';
            showToast('🔄 Retrying ' + e.fileName + '...');
            setTimeout(function() {
                e.status = 'completed';
                e.downloads = (e.downloads || 0) + 1;
                applyFilters();
                showToast('✅ ' + e.fileName + ' regenerated successfully!');
            }, 2000);
        }
    }

    // ============================================
    // NEW EXPORT
    // ============================================

    function openExportModal() {
        var modal = getEl('exportModal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            // Reset form
            var typeEl = getEl('exportType');
            var formatEl = getEl('exportFormat');
            var fromEl = getEl('exportDateFrom');
            var toEl = getEl('exportDateTo');
            if (typeEl) typeEl.value = 'emissions';
            if (formatEl) formatEl.value = 'xlsx';
            if (fromEl) fromEl.value = '';
            if (toEl) toEl.value = '';
        }
    }

    function closeExportModal() {
        var modal = getEl('exportModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function generateExport() {
        var typeEl = getEl('exportType');
        var formatEl = getEl('exportFormat');
        var fromEl = getEl('exportDateFrom');
        var toEl = getEl('exportDateTo');
        
        var type = typeEl ? typeEl.value : 'emissions';
        var format = formatEl ? formatEl.value : 'xlsx';
        var dateFrom = fromEl ? fromEl.value : '';
        var dateTo = toEl ? toEl.value : '';
        
        var recordCount = Math.floor(Math.random() * 5000) + 100;
        var sizeMB = (recordCount / 1000 * 1.5).toFixed(1);
        var now = new Date();
        var dateStr = now.toISOString().slice(0, 10);
        var timeStr = now.toLocaleTimeString();
        var typeLabel = typeLabels[type] || type;
        
        var newExport = {
            id: 'e' + (exportItems.length + 1),
            userId: 'u1',
            fileName: typeLabel.replace(/\s/g, '_') + '_' + dateStr,
            format: format,
            recordCount: recordCount,
            size: sizeMB + ' MB',
            status: 'processing',
            createdAt: dateStr + ' ' + timeStr,
            expiresAt: new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10) + ' ' + timeStr,
            downloads: 0,
            exportType: type,
            filters: { dateFrom: dateFrom || 'N/A', dateTo: dateTo || 'N/A' }
        };
        
        exportItems.unshift(newExport);
        closeExportModal();
        applyFilters();
        showToast('🔄 Generating ' + typeLabel + ' export...');
        
        setTimeout(function() {
            newExport.status = 'completed';
            applyFilters();
            showToast('✅ ' + typeLabel + ' export ready for download!');
        }, 2500);
    }

    function refreshData() {
        showToast('🔄 Refreshing export data...');
        setTimeout(function() {
            applyFilters();
            showToast('✅ Data refreshed successfully!');
        }, 500);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Export History Module...');
        
        var tbody = getEl('exportTableBody');
        if (!tbody) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Set up event listeners
        var applyBtn = getEl('applyFiltersBtn');
        if (applyBtn) applyBtn.addEventListener('click', applyFilters);
        
        var clearBtn = getEl('clearFiltersBtn');
        if (clearBtn) clearBtn.addEventListener('click', clearFilters);
        
        var searchEl = getEl('globalSearch');
        if (searchEl) {
            searchEl.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') applyFilters();
            });
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
                var exportModal = getEl('exportModal');
                var detailModal = getEl('detailModal');
                if (exportModal && exportModal.classList.contains('show')) {
                    closeExportModal();
                }
                if (detailModal && detailModal.classList.contains('show')) {
                    closeDetailModal();
                }
            }
        });
        
        // Initial render
        applyFilters();
        
        console.log('✅ Export History module loaded successfully!');
        console.log('📊 ' + exportItems.length + ' exports tracked');
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
    window.sortBy = sortBy;
    window.goToPage = goToPage;
    window.downloadExport = downloadExport;
    window.retryExport = retryExport;
    window.viewExportDetails = viewExportDetails;
    window.closeDetailModal = closeDetailModal;
    window.openExportModal = openExportModal;
    window.closeExportModal = closeExportModal;
    window.generateExport = generateExport;
    window.refreshData = refreshData;
    window.showToast = showToast;
})(); // <-- End of the IIFE wrapper
