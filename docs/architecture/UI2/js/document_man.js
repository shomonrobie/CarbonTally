// Document Management Module - SPA Compatible
(function() {

    console.log('📁 Document Management JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var documents = [
        { id: 'doc_001', name: 'Utility_Bill_London_Dec2026.pdf', type: 'utility', status: 'approved', size: 2.4, date: '2026-12-15', records: 12, uploadedBy: 'John Doe' },
        { id: 'doc_002', name: 'Fleet_Fuel_Q4_2026.csv', type: 'fuel', status: 'processing', size: 1.8, date: '2026-12-14', records: 245, uploadedBy: 'Sarah Johnson' },
        { id: 'doc_003', name: 'Supplier_Invoice_IT_Equipment.pdf', type: 'scope3', status: 'review', size: 3.1, date: '2026-12-13', records: 8, uploadedBy: 'Mike Roberts' },
        { id: 'doc_004', name: 'Electricity_Bill_Manchester.xlsx', type: 'utility', status: 'uploaded', size: 1.2, date: '2026-12-12', records: 18, uploadedBy: 'Anna Liu' },
        { id: 'doc_005', name: 'Gas_Bill_Birmingham_Q4.pdf', type: 'utility', status: 'processing', size: 0.89, date: '2026-12-11', records: 6, uploadedBy: 'Tom Chen' },
        { id: 'doc_006', name: 'Scope3_Supplier_Report.csv', type: 'scope3', status: 'review', size: 3.2, date: '2026-12-10', records: 156, uploadedBy: 'Emma Martinez' },
        { id: 'doc_007', name: 'Water_Bill_Manchester_Nov2026.pdf', type: 'utility', status: 'approved', size: 1.1, date: '2026-12-09', records: 4, uploadedBy: 'Anna Liu' },
        { id: 'doc_008', name: 'Fleet_Maintenance_Logs_Q4.csv', type: 'fuel', status: 'uploaded', size: 2.2, date: '2026-12-08', records: 89, uploadedBy: 'John Doe' },
        { id: 'doc_009', name: 'GHG_Inventory_Data_2026.xlsx', type: 'document', status: 'approved', size: 4.5, date: '2026-12-07', records: 456, uploadedBy: 'Sarah Johnson' },
        { id: 'doc_010', name: 'CSRD_Data_Collection_2026.pdf', type: 'scope3', status: 'review', size: 2.8, date: '2026-12-06', records: 34, uploadedBy: 'Mike Roberts' },
        { id: 'doc_011', name: 'Emissions_Factors_2026.xlsx', type: 'document', status: 'approved', size: 1.6, date: '2026-12-05', records: 78, uploadedBy: 'Tom Chen' },
        { id: 'doc_012', name: 'Utility_Bill_Manchester_Dec2026.pdf', type: 'utility', status: 'processing', size: 0.95, date: '2026-12-04', records: 5, uploadedBy: 'Emma Martinez' },
        { id: 'doc_013', name: 'Fleet_Fuel_Q3_2026.csv', type: 'fuel', status: 'approved', size: 1.9, date: '2026-12-03', records: 234, uploadedBy: 'John Doe' },
        { id: 'doc_014', name: 'Supplier_Emissions_Data_2026.xlsx', type: 'scope3', status: 'uploaded', size: 3.6, date: '2026-12-02', records: 45, uploadedBy: 'Sarah Johnson' },
        { id: 'doc_015', name: 'Energy_Audit_Report_2026.pdf', type: 'document', status: 'review', size: 5.2, date: '2026-12-01', records: 23, uploadedBy: 'Mike Roberts' }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentView = 'grid';
    var currentStatusFilter = 'all';
    var currentTypeFilter = 'all';
    var currentSearchTerm = '';
    var currentPage = 1;
    var perPage = 6;
    var toastTimeout = null;
    var viewingDocId = null;

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
            'uploaded': '<span class="badge badge-muted">📤 Uploaded</span>',
            'processing': '<span class="badge badge-warning">⏳ Processing</span>',
            'review': '<span class="badge badge-primary">📝 Review</span>',
            'approved': '<span class="badge badge-success">✅ Approved</span>',
            'rejected': '<span class="badge badge-destructive">❌ Rejected</span>'
        };
        return badges[status] || badges.uploaded;
    }

    function getFileIcon(type) {
        var icons = { 'fuel': '⛽', 'utility': '💡', 'scope3': '🌍', 'document': '📄' };
        return icons[type] || '📄';
    }

    function getStatusProgress(status) {
        var progress = { 'uploaded': 0, 'processing': 45, 'review': 70, 'approved': 100, 'rejected': 100 };
        return progress[status] || 0;
    }

    function updateStats() {
        var total = documents.length;
        var uploaded = 0, processing = 0, review = 0, approved = 0, rejected = 0;
        
        for (var i = 0; i < documents.length; i++) {
            var d = documents[i];
            if (d.status === 'uploaded') uploaded++;
            else if (d.status === 'processing') processing++;
            else if (d.status === 'review') review++;
            else if (d.status === 'approved') approved++;
            else if (d.status === 'rejected') rejected++;
        }

        var el = getEl('statTotal');
        if (el) el.textContent = total;
        el = getEl('statUploaded');
        if (el) el.textContent = uploaded;
        el = getEl('statProcessing');
        if (el) el.textContent = processing;
        el = getEl('statReview');
        if (el) el.textContent = review;
        el = getEl('statApproved');
        if (el) el.textContent = approved;
        el = getEl('statRejected');
        if (el) el.textContent = rejected;
    }

    function getFilteredDocuments() {
        var filtered = documents.slice();
        
        if (currentStatusFilter !== 'all') {
            filtered = filtered.filter(function(d) { return d.status === currentStatusFilter; });
        }
        
        if (currentTypeFilter !== 'all') {
            filtered = filtered.filter(function(d) { return d.type === currentTypeFilter; });
        }
        
        if (currentSearchTerm) {
            var term = currentSearchTerm.toLowerCase();
            filtered = filtered.filter(function(d) {
                return d.name.toLowerCase().indexOf(term) !== -1 ||
                    d.type.toLowerCase().indexOf(term) !== -1 ||
                    d.uploadedBy.toLowerCase().indexOf(term) !== -1;
            });
        }
        
        return filtered;
    }

    function renderPagination(total) {
        var container = getEl('pagination');
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' documents</div><div class="page-buttons"></div>';
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
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' documents</div><div class="page-buttons">' + btns + '</div>';
    }

    function renderDocuments() {
        var filtered = getFilteredDocuments();
        var container = getEl('docGrid');
        var countEl = getEl('docCount');
        
        if (!container) return;
        
        if (countEl) countEl.textContent = filtered.length + ' documents';
        
        var start = (currentPage - 1) * perPage;
        var pageItems = filtered.slice(start, start + perPage);
        
        if (pageItems.length === 0) {
            container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px 20px;color:hsl(var(--muted-foreground));"><div style="font-size:48px;margin-bottom:16px;">📭</div><div style="font-size:16px;font-weight:600;">No documents found</div><div style="font-size:13px;margin-top:4px;">Try adjusting your filters or upload a new document</div></div>';
            renderPagination(filtered.length);
            return;
        }

        if (currentView === 'grid') {
            container.className = 'doc-grid';
            var html = '';
            for (var i = 0; i < pageItems.length; i++) {
                var doc = pageItems[i];
                html += '<div class="doc-card">' +
                    '<div class="doc-icon">' + getFileIcon(doc.type) + '</div>' +
                    '<div class="doc-name">' + doc.name + '</div>' +
                    '<div class="doc-meta"><span>' + doc.type.toUpperCase() + '</span><span>' + doc.size + ' MB</span><span>' + (doc.records || 0) + ' records</span></div>' +
                    '<div style="margin:8px 0;">' + getStatusBadge(doc.status) + '</div>' +
                    '<div class="progress-bar"><div class="fill" style="width:' + getStatusProgress(doc.status) + '%;"></div></div>' +
                    '<div class="doc-actions">' +
                    '<button class="btn btn-ghost btn-sm" onclick="viewDocument(\'' + doc.id + '\')">👁️ View</button>' +
                    '<button class="btn btn-ghost btn-sm" onclick="downloadDocument(\'' + doc.id + '\')">⬇️ Download</button>' +
                    '<button class="btn btn-ghost btn-sm" onclick="deleteDocument(\'' + doc.id + '\')" style="color:hsl(var(--destructive));">🗑️</button>' +
                    '</div></div>';
            }
            container.innerHTML = html;
        } else {
            container.className = '';
            var html = '';
            for (var j = 0; j < pageItems.length; j++) {
                var doc = pageItems[j];
                html += '<div class="doc-list-item">' +
                    '<div class="doc-icon">' + getFileIcon(doc.type) + '</div>' +
                    '<div class="doc-info"><div class="name">' + doc.name + '</div><div class="meta">' + doc.type.toUpperCase() + ' • ' + doc.size + ' MB • ' + (doc.records || 0) + ' records • ' + doc.date + '</div></div>' +
                    '<div class="doc-status">' + getStatusBadge(doc.status) + '</div>' +
                    '<div class="doc-actions">' +
                    '<button class="btn btn-ghost btn-sm" onclick="viewDocument(\'' + doc.id + '\')">👁️</button>' +
                    '<button class="btn btn-ghost btn-sm" onclick="downloadDocument(\'' + doc.id + '\')">⬇️</button>' +
                    '<button class="btn btn-ghost btn-sm" onclick="deleteDocument(\'' + doc.id + '\')" style="color:hsl(var(--destructive));">🗑️</button>' +
                    '</div></div>';
            }
            container.innerHTML = html;
        }
        
        renderPagination(filtered.length);
        updateStats();
    }

    // ============================================
    // FILTER FUNCTIONS
    // ============================================

    function applyFilters() {
        var searchEl = getEl('moduleSearch');
        currentSearchTerm = searchEl ? searchEl.value : '';
        currentPage = 1;
        renderDocuments();
    }

    function filterByStatus(status) {
        currentStatusFilter = status;
        var tabs = document.querySelectorAll('#statusFilter .tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.toggle('active', tabs[i].getAttribute('data-status') === status);
        }
        currentPage = 1;
        renderDocuments();
        showToast('📊 Filtered by: ' + status);
    }

    function filterByType(type) {
        var typeEl = getEl('typeFilter');
        if (typeEl) typeEl.value = type;
        currentPage = 1;
        applyFilters();
        showToast('📊 Filtered by type: ' + type);
    }

    function clearFilters() {
        currentStatusFilter = 'all';
        currentTypeFilter = 'all';
        currentSearchTerm = '';
        currentPage = 1;
        
        var tabs = document.querySelectorAll('#statusFilter .tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.toggle('active', tabs[i].getAttribute('data-status') === 'all');
        }
        var typeEl = getEl('typeFilter');
        if (typeEl) typeEl.value = 'all';
        var searchEl = getEl('moduleSearch');
        if (searchEl) searchEl.value = '';
        
        renderDocuments();
        showToast('🔄 Filters cleared');
    }

    function toggleView() {
        currentView = currentView === 'grid' ? 'list' : 'grid';
        renderDocuments();
        showToast('📋 ' + (currentView === 'grid' ? 'Grid' : 'List') + ' view');
    }

    function goToPage(page) {
        var totalPages = Math.ceil(getFilteredDocuments().length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderDocuments();
    }

    // ============================================
    // DOCUMENT ACTIONS
    // ============================================

    function viewDocument(id) {
        var doc = null;
        for (var i = 0; i < documents.length; i++) {
            if (documents[i].id === id) { doc = documents[i]; break; }
        }
        if (!doc) return;
        
        viewingDocId = id;
        var titleEl = getEl('detailTitle');
        var subtitleEl = getEl('detailSubtitle');
        var bodyEl = getEl('detailBody');
        var footerEl = getEl('detailFooter');
        var modal = getEl('detailModal');
        
        if (titleEl) titleEl.textContent = '📄 ' + doc.name;
        if (subtitleEl) subtitleEl.textContent = doc.type.toUpperCase() + ' • ' + doc.status.toUpperCase() + ' • ' + doc.date;
        
        if (bodyEl) {
            bodyEl.innerHTML =
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
                '<div class="detail-row"><span class="label">Document Name</span><span class="value">' + doc.name + '</span></div>' +
                '<div class="detail-row"><span class="label">Type</span><span class="value"><span class="badge badge-secondary">' + doc.type.toUpperCase() + '</span></span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + getStatusBadge(doc.status) + '</span></div>' +
                '<div class="detail-row"><span class="label">File Size</span><span class="value">' + doc.size + ' MB</span></div>' +
                '<div class="detail-row"><span class="label">Records</span><span class="value">' + (doc.records || 0) + '</span></div>' +
                '<div class="detail-row"><span class="label">Upload Date</span><span class="value">' + doc.date + '</span></div>' +
                '<div class="detail-row"><span class="label">Uploaded By</span><span class="value">' + doc.uploadedBy + '</span></div>' +
                '<div class="detail-row" style="grid-column:1/-1;"><span class="label">Progress</span><span class="value"><div class="progress-bar" style="max-width:200px;"><div class="fill" style="width:' + getStatusProgress(doc.status) + '%;"></div></div></span></div>' +
                '</div>';
        }
        
        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeDetailModal()">Close</button>' +
                '<button class="btn btn-outline btn-sm" onclick="downloadDocument(\'' + doc.id + '\');closeDetailModal();">⬇️ Download</button>' +
                '<button class="btn btn-danger btn-sm" onclick="deleteDocument(\'' + doc.id + '\');closeDetailModal();">🗑️ Delete</button>';
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
        viewingDocId = null;
    }

    function downloadDocument(id) {
        var doc = null;
        for (var i = 0; i < documents.length; i++) {
            if (documents[i].id === id) { doc = documents[i]; break; }
        }
        if (doc) {
            showToast('⬇️ Downloading: ' + doc.name);
        }
    }

    function deleteDocument(id) {
        if (confirm('Are you sure you want to delete this document?')) {
            var doc = null;
            var index = -1;
            for (var i = 0; i < documents.length; i++) {
                if (documents[i].id === id) { doc = documents[i]; index = i; break; }
            }
            if (doc) {
                documents.splice(index, 1);
                renderDocuments();
                showToast('🗑️ Deleted: ' + doc.name);
            }
        }
    }

    // ============================================
    // UPLOAD MODAL
    // ============================================

    function showUploadModal() {
        var modal = getEl('uploadModal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            var nameEl = getEl('docName');
            var typeEl = getEl('docType');
            var statusEl = getEl('docStatus');
            var sizeEl = getEl('docSize');
            var recordsEl = getEl('docRecords');
            if (nameEl) nameEl.value = '';
            if (typeEl) typeEl.value = 'fuel';
            if (statusEl) statusEl.value = 'uploaded';
            if (sizeEl) sizeEl.value = '1.0';
            if (recordsEl) recordsEl.value = '0';
        }
    }

    function closeUploadModal() {
        var modal = getEl('uploadModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function uploadDocument() {
        var nameEl = getEl('docName');
        var typeEl = getEl('docType');
        var statusEl = getEl('docStatus');
        var sizeEl = getEl('docSize');
        var recordsEl = getEl('docRecords');
        
        var name = nameEl ? nameEl.value.trim() : '';
        var type = typeEl ? typeEl.value : 'fuel';
        var status = statusEl ? statusEl.value : 'uploaded';
        var size = parseFloat(sizeEl ? sizeEl.value : 1.0) || 1.0;
        var records = parseInt(recordsEl ? recordsEl.value : 0) || 0;

        if (!name) {
            showToast('⚠️ Please enter a document name', 'warning');
            if (nameEl) nameEl.focus();
            return;
        }

        var newDoc = {
            id: 'doc_' + String(documents.length + 1).padStart(3, '0'),
            name: name,
            type: type,
            status: status,
            size: size,
            date: new Date().toISOString().split('T')[0],
            records: records,
            uploadedBy: 'Current User'
        };

        documents.unshift(newDoc);
        closeUploadModal();
        renderDocuments();
        showToast('📤 Uploaded: ' + name);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Document Management Module...');
        
        var container = getEl('docGrid');
        if (!container) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
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
                var uploadModal = getEl('uploadModal');
                var detailModal = getEl('detailModal');
                if (uploadModal && uploadModal.classList.contains('show')) {
                    closeUploadModal();
                }
                if (detailModal && detailModal.classList.contains('show')) {
                    closeDetailModal();
                }
            }
            // Enter key in doc name field to upload
            if (e.key === 'Enter') {
                var nameEl = getEl('docName');
                if (nameEl && document.activeElement === nameEl) {
                    uploadDocument();
                }
            }
        });
        
        // Type filter change
        var typeEl = getEl('typeFilter');
        if (typeEl) {
            typeEl.addEventListener('change', function() {
                currentTypeFilter = this.value;
                currentPage = 1;
                renderDocuments();
            });
        }
        
        // Search
        var searchEl = getEl('moduleSearch');
        if (searchEl) {
            searchEl.addEventListener('input', function() {
                currentSearchTerm = this.value;
                currentPage = 1;
                renderDocuments();
            });
        }
        
        renderDocuments();
        
        console.log('✅ Document Management module loaded successfully!');
        console.log('📄 ' + documents.length + ' documents loaded');
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
    window.filterByStatus = filterByStatus;
    window.filterByType = filterByType;
    window.clearFilters = clearFilters;
    window.toggleView = toggleView;
    window.goToPage = goToPage;
    window.viewDocument = viewDocument;
    window.closeDetailModal = closeDetailModal;
    window.downloadDocument = downloadDocument;
    window.deleteDocument = deleteDocument;
    window.showUploadModal = showUploadModal;
    window.closeUploadModal = closeUploadModal;
    window.uploadDocument = uploadDocument;
    window.renderDocuments = renderDocuments;
    window.showToast = showToast;
})(); 