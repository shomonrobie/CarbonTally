// Manual Review Queue Module - SPA Compatible
(function(){
console.log('✅ Manual Review Queue JS loaded');

// ============================================
// MOCK DATA - 12 items with various statuses
// ============================================

var queueItems = [
    { id: 'q_001', file_name: 'Utility_Bill_London_Dec2026.pdf', file_type: 'pdf', data_type: 'utility', status: 'pending', priority: 'high', assigned_to: null, created_at: '2026-12-15T10:00:00Z', sla_deadline: '2026-12-16T10:00:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Please verify the electricity consumption values for December', staff_notes: null, auto_extraction_result: { confidence: 92, extracted_data: { period: 'Dec 2026', consumption: 4500, unit: 'kWh', facility: 'London Office', scope: 'Scope 2' } } },
    { id: 'q_002', file_name: 'Fleet_Fuel_Q4_2026.csv', file_type: 'csv', data_type: 'fuel', status: 'in-progress', priority: 'high', assigned_to: 'staff_001', created_at: '2026-12-14T14:30:00Z', sla_deadline: '2026-12-17T14:30:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Fleet fuel data for Q4 2026', staff_notes: 'Reviewing fuel consumption patterns', auto_extraction_result: { confidence: 88, extracted_data: { period: 'Q4 2026', records: 245, total_consumption: 14500, unit: 'L', fleet_size: 12, scope: 'Scope 1' } } },
    { id: 'q_003', file_name: 'Supplier_Invoice_IT_Equipment.pdf', file_type: 'pdf', data_type: 'scope3', status: 'review', priority: 'medium', assigned_to: 'staff_003', created_at: '2026-12-13T09:15:00Z', sla_deadline: '2026-12-18T09:15:00Z', sla_breached: false, escalation_level: 1, customer_notes: 'IT equipment supplier invoice for Scope 3 reporting', staff_notes: 'Need to verify equipment category', auto_extraction_result: { confidence: 76, extracted_data: { period: 'Dec 2026', amount: 45000, currency: 'GBP', supplier: 'TechCorp Ltd', category: 'IT Equipment', scope: 'Scope 3' } } },
    { id: 'q_004', file_name: 'Electricity_Bill_Manchester.xlsx', file_type: 'xlsx', data_type: 'utility', status: 'pending', priority: 'medium', assigned_to: null, created_at: '2026-12-12T16:45:00Z', sla_deadline: '2026-12-19T16:45:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'December electricity bill for Manchester office', staff_notes: null, auto_extraction_result: { confidence: 94, extracted_data: { period: 'Dec 2026', consumption: 3200, unit: 'kWh', facility: 'Manchester Office', scope: 'Scope 2' } } },
    { id: 'q_005', file_name: 'Gas_Bill_Birmingham_Q4.pdf', file_type: 'pdf', data_type: 'utility', status: 'in-progress', priority: 'low', assigned_to: 'staff_004', created_at: '2026-12-11T11:20:00Z', sla_deadline: '2026-12-20T11:20:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Q4 gas bill for Birmingham office', staff_notes: 'Checking consumption against previous quarters', auto_extraction_result: { confidence: 82, extracted_data: { period: 'Q4 2026', consumption: 1800, unit: 'kWh', facility: 'Birmingham Office', scope: 'Scope 2' } } },
    { id: 'q_006', file_name: 'Scope3_Supplier_Report.csv', file_type: 'csv', data_type: 'scope3', status: 'review', priority: 'high', assigned_to: 'staff_005', created_at: '2026-12-10T08:00:00Z', sla_deadline: '2026-12-15T08:00:00Z', sla_breached: true, escalation_level: 2, customer_notes: 'Supplier sustainability report for Scope 3', staff_notes: 'URGENT: SLA breached - needs immediate attention', auto_extraction_result: { confidence: 68, extracted_data: { period: 'Q4 2026', records: 156, suppliers: 23, total_emissions: 45000, unit: 'kgCO₂e', scope: 'Scope 3' } } },
    { id: 'q_007', file_name: 'Fleet_Maintenance_Records.xlsx', file_type: 'xlsx', data_type: 'fuel', status: 'approved', priority: 'low', assigned_to: 'staff_002', created_at: '2026-12-09T13:30:00Z', sla_deadline: '2026-12-16T13:30:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Fleet maintenance and fuel records', staff_notes: 'All verified - approved', auto_extraction_result: { confidence: 95, extracted_data: { period: '2026', records: 34, vehicles: 12, total_fuel: 5600, unit: 'L', scope: 'Scope 1' } } },
    { id: 'q_008', file_name: 'Renewable_Energy_Certificates.pdf', file_type: 'pdf', data_type: 'document', status: 'approved', priority: 'low', assigned_to: 'staff_001', created_at: '2026-12-08T09:00:00Z', sla_deadline: '2026-12-22T09:00:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Renewable energy certificates for 2026', staff_notes: 'Verified and approved', auto_extraction_result: { confidence: 98, extracted_data: { period: '2026', certificates: 125, energy_source: 'Solar', total_mwh: 2500, scope: 'Scope 2' } } },
    { id: 'q_009', file_name: 'Water_Bill_Manchester_Q4.pdf', file_type: 'pdf', data_type: 'utility', status: 'pending', priority: 'medium', assigned_to: null, created_at: '2026-12-07T10:15:00Z', sla_deadline: '2026-12-21T10:15:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Water bill - missing consumption data', staff_notes: null, auto_extraction_result: { confidence: 45, extracted_data: null, error: 'Missing consumption values' } },
    { id: 'q_010', file_name: 'Business_Travel_Expenses_Q4.csv', file_type: 'csv', data_type: 'scope3', status: 'pending', priority: 'high', assigned_to: null, created_at: '2026-12-06T15:00:00Z', sla_deadline: '2026-12-18T15:00:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Q4 business travel expenses for Scope 3', staff_notes: null, auto_extraction_result: { confidence: 85, extracted_data: { period: 'Q4 2026', records: 89, total_emissions: 12500, unit: 'kgCO₂e', flights: 45, rail: 32, hotels: 12, scope: 'Scope 3' } } },
    { id: 'q_011', file_name: 'Data_Center_Energy_Report.pdf', file_type: 'pdf', data_type: 'document', status: 'in-progress', priority: 'medium', assigned_to: 'staff_004', created_at: '2026-12-05T12:00:00Z', sla_deadline: '2026-12-19T12:00:00Z', sla_breached: false, escalation_level: 0, customer_notes: 'Data center energy efficiency report', staff_notes: 'Reviewing PUE and energy consumption', auto_extraction_result: { confidence: 79, extracted_data: { period: '2026', pue: 1.35, total_energy: 1200000, unit: 'kWh', facility: 'Data Center', scope: 'Scope 2' } } },
    { id: 'q_012', file_name: 'Fleet_Fuel_Nov2026.csv', file_type: 'csv', data_type: 'fuel', status: 'review', priority: 'high', assigned_to: 'staff_005', created_at: '2026-12-04T08:45:00Z', sla_deadline: '2026-12-14T08:45:00Z', sla_breached: true, escalation_level: 1, customer_notes: 'November fleet fuel consumption data', staff_notes: 'SLA breached - escalation level 1', auto_extraction_result: { confidence: 87, extracted_data: { period: 'Nov 2026', records: 210, total_consumption: 11800, unit: 'L', fleet_size: 10, scope: 'Scope 1' } } }
];

// Staff mapping
var staffNames = {
    'staff_001': 'John Doe',
    'staff_002': 'Sarah Johnson',
    'staff_003': 'Mike Roberts',
    'staff_004': 'Anna Liu',
    'staff_005': 'Tom Chen'
};

// ============================================
// STATE
// ============================================

var currentFilters = { status: 'all', priority: 'all' };
var currentPage = 1;
var perPage = 5;
var selectedItemId = null;
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

function getStatusBadge(status) {
    var badges = {
        'pending': '<span class="badge badge-muted">📤 Pending</span>',
        'in-progress': '<span class="badge badge-warning">⏳ In Progress</span>',
        'review': '<span class="badge badge-primary">📝 Review</span>',
        'approved': '<span class="badge badge-success">✅ Approved</span>',
        'escalated': '<span class="badge badge-destructive">🚨 Escalated</span>'
    };
    return badges[status] || badges.pending;
}

function getPriorityBadge(priority) {
    var badges = {
        'high': '<span class="badge badge-destructive">🔴 High</span>',
        'medium': '<span class="badge badge-warning">🟡 Medium</span>',
        'low': '<span class="badge badge-success">🟢 Low</span>'
    };
    return badges[priority] || badges.medium;
}

function getStatusProgress(status) {
    var progress = { 'pending': 0, 'in-progress': 30, 'review': 60, 'approved': 100, 'escalated': 80 };
    return progress[status] || 0;
}

function formatDate(dateStr) {
    var date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getTimeRemaining(deadline) {
    var now = new Date();
    var end = new Date(deadline);
    var diff = end - now;

    if (diff < 0) return '⏰ Overdue';
    var hours = Math.floor(diff / (1000 * 60 * 60));
    var days = Math.floor(hours / 24);

    if (days > 0) return days + 'd ' + (hours % 24) + 'h remaining';
    if (hours > 0) return hours + 'h remaining';
    return 'Less than 1 hour';
}

function getStaffName(id) {
    return staffNames[id] || 'Unassigned';
}

// ============================================
// RENDER FUNCTIONS
// ============================================

function renderStats() {
    var total = queueItems.length;
    var pending = 0, inProgress = 0, review = 0, approved = 0, escalated = 0;
    
    for (var i = 0; i < queueItems.length; i++) {
        var q = queueItems[i];
        if (q.status === 'pending') pending++;
        else if (q.status === 'in-progress') inProgress++;
        else if (q.status === 'review') review++;
        else if (q.status === 'approved') approved++;
        if (q.escalation_level > 0) escalated++;
    }

    var el = getEl('statTotal');
    if (el) el.textContent = total;
    el = getEl('statPending');
    if (el) el.textContent = pending;
    el = getEl('statInProgress');
    if (el) el.textContent = inProgress;
    el = getEl('statReview');
    if (el) el.textContent = review;
    el = getEl('statApproved');
    if (el) el.textContent = approved;
    el = getEl('statEscalated');
    if (el) el.textContent = escalated;
}

function renderQueue() {
    var container = getEl('queueList');
    var countEl = getEl('queueCount');
    var paginationEl = getEl('pagination');
    if (!container) return;
    
    var filtered = queueItems.slice();
    
    if (currentFilters.status !== 'all') {
        filtered = filtered.filter(function(q) { return q.status === currentFilters.status; });
    }
    
    if (currentFilters.priority !== 'all') {
        filtered = filtered.filter(function(q) { return q.priority === currentFilters.priority; });
    }
    
    // Sort by priority (high first) and SLA deadline
    filtered.sort(function(a, b) {
        var priorityOrder = { high: 0, medium: 1, low: 2 };
        if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        }
        return new Date(a.sla_deadline) - new Date(b.sla_deadline);
    });
    
    if (countEl) countEl.textContent = filtered.length + ' items';
    
    var start = (currentPage - 1) * perPage;
    var pageItems = filtered.slice(start, start + perPage);
    
    if (pageItems.length === 0) {
        container.innerHTML = '<div class="text-center text-muted" style="padding:60px 20px;"><div style="font-size:48px;margin-bottom:16px;">✅</div><div style="font-size:18px;font-weight:600;">No items in queue</div><div style="font-size:14px;color:hsl(var(--muted-foreground));margin-top:8px;">All caught up! Check back later for new items.</div></div>';
        renderPagination(filtered.length);
        return;
    }
    
    var html = '';
    for (var i = 0; i < pageItems.length; i++) {
        var q = pageItems[i];
        var progress = getStatusProgress(q.status);
        var progressClass = q.status === 'approved' ? 'success' : q.status === 'in-progress' ? 'warning' : '';
        
        html +=
            '<div class="queue-item" onclick="openDetail(\'' + q.id + '\')">' +
            '<div class="priority-indicator ' + q.priority + '"></div>' +
            '<div class="queue-info">' +
            '<div class="title">' + q.file_name +
            (q.sla_breached ? ' <span class="badge badge-destructive">⏰ SLA Breached</span>' : '') +
            (q.escalation_level > 0 ? ' <span class="badge badge-destructive">🚨 Escalation Lvl ' + q.escalation_level + '</span>' : '') +
            '</div>' +
            '<div class="meta">' +
            '<span>📄 ' + q.data_type.toUpperCase() + '</span>' +
            '<span>📅 ' + formatDate(q.created_at) + '</span>' +
            '<span>👤 ' + getStaffName(q.assigned_to) + '</span>' +
            '<span>⏳ ' + getTimeRemaining(q.sla_deadline) + '</span>' +
            '<span>📊 ' + (q.auto_extraction_result ? q.auto_extraction_result.confidence || 0 : 0) + '%</span>' +
            '</div>' +
            '</div>' +
            '<div class="queue-status">' +
            getStatusBadge(q.status) +
            getPriorityBadge(q.priority) +
            '<div class="progress-info"><span style="font-size:11px;">' + progress + '% complete</span></div>' +
            '<div class="progress-bar"><div class="fill ' + progressClass + '" style="width:' + progress + '%;"></div></div>' +
            '</div>' +
            '<div class="queue-actions">' +
            '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openDetail(\'' + q.id + '\')" title="View Details">👁️</button>' +
            (q.status === 'pending' || q.status === 'in-progress' ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();showToast(\'👤 Assigning reviewer...\')" title="Assign">👤</button>' : '') +
            (q.status === 'review' ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();approveItem(\'' + q.id + '\')" title="Approve" style="color:hsl(var(--success));">✅</button><button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();rejectItem(\'' + q.id + '\')" title="Reject" style="color:hsl(var(--destructive));">❌</button>' : '') +
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
        container.innerHTML = '<div class="page-info">Showing ' + total + ' items</div><div class="page-buttons"></div>';
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
    
    container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' items</div><div class="page-buttons">' + btns + '</div>';
}

function goToPage(page) {
    var totalPages = Math.ceil(queueItems.length / perPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderQueue();
}

// ============================================
// FILTER FUNCTIONS
// ============================================

function applyFilters() {
    var statusEl = getEl('statusFilter');
    var priorityEl = getEl('priorityFilter');
    currentFilters.status = statusEl ? statusEl.value : 'all';
    currentFilters.priority = priorityEl ? priorityEl.value : 'all';
    currentPage = 1;
    renderQueue();
}

function clearFilters() {
    var statusEl = getEl('statusFilter');
    var priorityEl = getEl('priorityFilter');
    if (statusEl) statusEl.value = 'all';
    if (priorityEl) priorityEl.value = 'all';
    currentFilters.status = 'all';
    currentFilters.priority = 'all';
    currentPage = 1;
    renderQueue();
    showToast('🔄 Filters cleared');
}

// ============================================
// DETAIL MODAL
// ============================================

function openDetail(id) {
    var q = null;
    for (var i = 0; i < queueItems.length; i++) {
        if (queueItems[i].id === id) { q = queueItems[i]; break; }
    }
    if (!q) return;

    selectedItemId = id;
    var titleEl = getEl('detailTitle');
    var subtitleEl = getEl('detailSubtitle');
    var bodyEl = getEl('detailBody');
    var footerEl = getEl('detailFooter');
    var modal = getEl('detailModal');
    
    if (titleEl) titleEl.textContent = q.file_name;
    if (subtitleEl) subtitleEl.textContent = q.data_type.toUpperCase() + ' • ' + q.priority.toUpperCase() + ' Priority';

    if (bodyEl) {
        var extractedHtml = '';
        if (q.auto_extraction_result && q.auto_extraction_result.extracted_data) {
            var keys = Object.keys(q.auto_extraction_result.extracted_data);
            for (var k = 0; k < keys.length; k++) {
                var key = keys[k];
                var val = q.auto_extraction_result.extracted_data[key];
                extractedHtml += '<div><div style="font-size:10px;color:hsl(var(--muted-foreground));">' + key.replace(/_/g, ' ').toUpperCase() + '</div><div style="font-size:13px;font-weight:500;">' + val + '</div></div>';
            }
        }
        
        var errorHtml = '';
        if (q.auto_extraction_result && q.auto_extraction_result.error) {
            errorHtml = '<div style="margin-top:12px;padding:12px;background:#fee2e2;border-radius:var(--radius);border:1px solid #fca5a5;"><div style="font-size:12px;font-weight:600;color:#991b1b;margin-bottom:4px;">⚠️ Extraction Error</div><div style="font-size:13px;color:#991b1b;">' + q.auto_extraction_result.error + '</div></div>';
        }
        
        bodyEl.innerHTML =
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
            '<div class="detail-row"><span class="label">Status</span><span class="value">' + getStatusBadge(q.status) + '</span></div>' +
            '<div class="detail-row"><span class="label">Priority</span><span class="value">' + getPriorityBadge(q.priority) + '</span></div>' +
            '<div class="detail-row"><span class="label">File Type</span><span class="value">' + q.file_type.toUpperCase() + '</span></div>' +
            '<div class="detail-row"><span class="label">Data Type</span><span class="value">' + q.data_type.toUpperCase() + '</span></div>' +
            '<div class="detail-row"><span class="label">Created</span><span class="value">' + formatDate(q.created_at) + '</span></div>' +
            '<div class="detail-row"><span class="label">SLA Deadline</span><span class="value">' + formatDate(q.sla_deadline) + (q.sla_breached ? ' ⚠️' : '') + '</span></div>' +
            '<div class="detail-row"><span class="label">Assigned To</span><span class="value">' + getStaffName(q.assigned_to) + '</span></div>' +
            '<div class="detail-row"><span class="label">Confidence</span><span class="value">' + (q.auto_extraction_result ? q.auto_extraction_result.confidence || 0 : 0) + '%</span></div>' +
            (q.escalation_level > 0 ? '<div class="detail-row"><span class="label">Escalation Level</span><span class="value">' + q.escalation_level + '</span></div>' : '') +
            '</div>' +
            (q.customer_notes ? '<div style="margin-top:12px;padding:12px;background:hsl(var(--accent));border-radius:var(--radius));"><div style="font-size:12px;font-weight:600;margin-bottom:4px;">📝 Customer Notes</div><div style="font-size:13px;">' + q.customer_notes + '</div></div>' : '') +
            (q.staff_notes ? '<div style="margin-top:8px;padding:12px;background:hsl(var(--muted));border-radius:var(--radius));"><div style="font-size:12px;font-weight:600;margin-bottom:4px;">👤 Staff Notes</div><div style="font-size:13px;">' + q.staff_notes + '</div></div>' : '') +
            (extractedHtml ? '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;margin-bottom:4px;">📊 Extracted Data</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px;background:hsl(var(--muted));border-radius:var(--radius));">' + extractedHtml + '</div></div>' : '') +
            errorHtml;
    }

    if (footerEl) {
        footerEl.innerHTML =
            '<button class="btn btn-ghost btn-sm" onclick="closeDetail()">Close</button>' +
            (q.status === 'review' ? '<button class="btn btn-success btn-sm" onclick="approveItem(\'' + q.id + '\');closeDetail();">✅ Approve</button><button class="btn btn-danger btn-sm" onclick="rejectItem(\'' + q.id + '\');closeDetail();">❌ Reject</button>' : '') +
            (q.status === 'pending' || q.status === 'in-progress' ? '<button class="btn btn-outline btn-sm" onclick="startReview(\'' + q.id + '\');closeDetail();">▶️ Start Review</button>' : '') +
            (q.escalation_level === 0 && q.status !== 'approved' ? '<button class="btn btn-outline btn-sm" onclick="escalateItem(\'' + q.id + '\');closeDetail();" style="color:hsl(var(--destructive));">🚨 Escalate</button>' : '');
    }

    if (modal) modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeDetail() {
    var modal = getEl('detailModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// ============================================
// QUEUE ACTIONS
// ============================================

function approveItem(id) {
    var q = null;
    for (var i = 0; i < queueItems.length; i++) {
        if (queueItems[i].id === id) { q = queueItems[i]; break; }
    }
    if (q) {
        q.status = 'approved';
        renderQueue();
        renderStats();
        showToast('✅ Approved: ' + q.file_name);
    }
}

function rejectItem(id) {
    var q = null;
    for (var i = 0; i < queueItems.length; i++) {
        if (queueItems[i].id === id) { q = queueItems[i]; break; }
    }
    if (q) {
        showToast('❌ Rejected: ' + q.file_name);
    }
}

function startReview(id) {
    var q = null;
    for (var i = 0; i < queueItems.length; i++) {
        if (queueItems[i].id === id) { q = queueItems[i]; break; }
    }
    if (q) {
        q.status = 'in-progress';
        q.assigned_to = 'staff_001';
        renderQueue();
        renderStats();
        showToast('▶️ Started review: ' + q.file_name);
    }
}

function escalateItem(id) {
    var q = null;
    for (var i = 0; i < queueItems.length; i++) {
        if (queueItems[i].id === id) { q = queueItems[i]; break; }
    }
    if (q) {
        q.escalation_level = (q.escalation_level || 0) + 1;
        q.status = 'escalated';
        renderQueue();
        renderStats();
        showToast('🚨 Escalated: ' + q.file_name + ' (Level ' + q.escalation_level + ')');
    }
}

function refreshQueue() {
    showToast('🔄 Refreshing queue...');
    setTimeout(function() {
        renderQueue();
        renderStats();
        showToast('✅ Queue refreshed');
    }, 1000);
}

function exportQueue() {
    showToast('📊 Exporting queue data...');
    setTimeout(function() {
        showToast('✅ Queue exported successfully!');
    }, 1000);
}

// ============================================
// INIT
// ============================================

function initModule() {
    console.log('🚀 Initializing Manual Review Queue Module...');
    
    var container = getEl('queueList');
    if (!container) {
        console.log('⏳ Waiting for DOM elements...');
        setTimeout(initModule, 100);
        return;
    }
    
    // Modal overlay click to close
    var modal = getEl('detailModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) closeDetail();
        });
    }
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            var detailModal = getEl('detailModal');
            if (detailModal && detailModal.classList.contains('show')) {
                closeDetail();
            }
        }
    });
    
    // Initial render
    renderStats();
    renderQueue();
    
    console.log('✅ Manual Review Queue module loaded successfully!');
    console.log('📊 ' + queueItems.length + ' items in queue');
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
window.goToPage = goToPage;
window.openDetail = openDetail;
window.closeDetail = closeDetail;
window.approveItem = approveItem;
window.rejectItem = rejectItem;
window.startReview = startReview;
window.escalateItem = escalateItem;
window.refreshQueue = refreshQueue;
window.exportQueue = exportQueue;
window.renderQueue = renderQueue;
window.showToast = showToast;
})();