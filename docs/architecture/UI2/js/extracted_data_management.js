    // Extracted Data Management Module - SPA Compatible
(function() {

    console.log('📂 Extracted Data Management JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var now = new Date();

    function makeDate(daysAgo) {
        var d = new Date(now);
        d.setDate(d.getDate() - daysAgo);
        return d.toISOString().slice(0, 10);
    }

    var mockEntries = [
        { id: 'e1', type: 'fuel', data: { fuel_type: 'Diesel', quantity: 12450, unit: 'litres', co2e: 32.4 }, progress: 100, status: 'validated', batch: 'BATCH-2026-01', lastUpdated: makeDate(1) },
        { id: 'e2', type: 'utility', data: { utility: 'Electricity', consumption: 4500, unit: 'kWh', co2e: 1.8 }, progress: 100, status: 'completed', batch: 'BATCH-2026-01', lastUpdated: makeDate(2) },
        { id: 'e3', type: 'scope3', data: { category: 'Business Travel', distance: 1200, unit: 'km', co2e: 0.6 }, progress: 45, status: 'in-progress', batch: 'BATCH-2026-02', lastUpdated: makeDate(3) },
        { id: 'e4', type: 'document', data: { document: 'Invoice #234', amount: 1200, currency: 'GBP' }, progress: 20, status: 'draft', batch: null, lastUpdated: makeDate(5) },
        { id: 'e5', type: 'fuel', data: { fuel_type: 'Petrol', quantity: 8700, unit: 'litres', co2e: 19.2 }, progress: 100, status: 'validated', batch: 'BATCH-2026-01', lastUpdated: makeDate(1) },
        { id: 'e6', type: 'utility', data: { utility: 'Natural Gas', consumption: 3200, unit: 'therms', co2e: 16.8 }, progress: 70, status: 'in-progress', batch: 'BATCH-2026-02', lastUpdated: makeDate(2) },
        { id: 'e7', type: 'scope3', data: { category: 'Purchased Goods', value: 45000, currency: 'GBP', co2e: 8.2 }, progress: 100, status: 'validated', batch: 'BATCH-2026-03', lastUpdated: makeDate(4) },
        { id: 'e8', type: 'document', data: { document: 'Utility Statement', period: 'Q4 2026' }, progress: 10, status: 'draft', batch: null, lastUpdated: makeDate(6) },
        { id: 'e9', type: 'fuel', data: { fuel_type: 'Jet Fuel', quantity: 5600, unit: 'litres', co2e: 14.6 }, progress: 100, status: 'completed', batch: 'BATCH-2026-02', lastUpdated: makeDate(3) },
        { id: 'e10', type: 'utility', data: { utility: 'Water', consumption: 2200, unit: 'm³', co2e: 1.2 }, progress: 60, status: 'in-progress', batch: 'BATCH-2026-03', lastUpdated: makeDate(5) },
        { id: 'e11', type: 'scope3', data: { category: 'Waste Disposal', tonnes: 12, co2e: 4.5 }, progress: 100, status: 'validated', batch: 'BATCH-2026-01', lastUpdated: makeDate(2) },
        { id: 'e12', type: 'document', data: { document: 'Fleet Report', vehicle_count: 25 }, progress: 50, status: 'in-progress', batch: 'BATCH-2026-03', lastUpdated: makeDate(4) },
        { id: 'e13', type: 'fuel', data: { fuel_type: 'CNG', quantity: 3200, unit: 'kg', co2e: 8.9 }, progress: 100, status: 'validated', batch: 'BATCH-2026-02', lastUpdated: makeDate(2) },
        { id: 'e14', type: 'utility', data: { utility: 'Electricity', consumption: 7800, unit: 'kWh', co2e: 3.1 }, progress: 30, status: 'draft', batch: null, lastUpdated: makeDate(7) },
        { id: 'e15', type: 'scope3', data: { category: 'Employee Commuting', trips: 340, co2e: 2.2 }, progress: 100, status: 'completed', batch: 'BATCH-2026-01', lastUpdated: makeDate(3) },
        { id: 'e16', type: 'document', data: { document: 'Supplier Invoice', amount: 6800, currency: 'GBP' }, progress: 80, status: 'in-progress', batch: 'BATCH-2026-03', lastUpdated: makeDate(1) },
        { id: 'e17', type: 'fuel', data: { fuel_type: 'Biofuel', quantity: 2100, unit: 'litres', co2e: 1.1 }, progress: 100, status: 'validated', batch: 'BATCH-2026-02', lastUpdated: makeDate(2) },
        { id: 'e18', type: 'utility', data: { utility: 'District Heating', consumption: 1500, unit: 'MWh', co2e: 5.6 }, progress: 40, status: 'in-progress', batch: null, lastUpdated: makeDate(6) },
        { id: 'e19', type: 'scope3', data: { category: 'Downstream Transport', distance: 800, unit: 'km', co2e: 2.8 }, progress: 100, status: 'validated', batch: 'BATCH-2026-03', lastUpdated: makeDate(3) },
        { id: 'e20', type: 'document', data: { document: 'Asset Register', asset_count: 42 }, progress: 15, status: 'draft', batch: null, lastUpdated: makeDate(8) },
        { id: 'e21', type: 'fuel', data: { fuel_type: 'LPG', quantity: 4500, unit: 'litres', co2e: 11.2 }, progress: 85, status: 'in-progress', batch: 'BATCH-2026-04', lastUpdated: makeDate(1) },
        { id: 'e22', type: 'utility', data: { utility: 'Solar', consumption: 1200, unit: 'kWh', co2e: 0.0 }, progress: 100, status: 'validated', batch: 'BATCH-2026-04', lastUpdated: makeDate(2) },
        { id: 'e23', type: 'scope3', data: { category: 'Investments', value: 120000, currency: 'GBP', co2e: 12.5 }, progress: 30, status: 'draft', batch: null, lastUpdated: makeDate(4) },
        { id: 'e24', type: 'document', data: { document: 'Environmental Policy', version: '3.0' }, progress: 100, status: 'validated', batch: 'BATCH-2026-04', lastUpdated: makeDate(3) },
    ];

    var entries = [];
    var filteredEntries = [];
    var currentEditId = null;
    var toastTimeout = null;

    // ============================================
    // PAGINATION STATE
    // ============================================

    var currentPage = 1;
    var perPage = 10;
    var currentSort = { field: 'lastUpdated', direction: 'desc' };

    // ============================================
    // DOM REFS
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
        
        if (!document.body) {
            console.warn('⚠️ Toast: document.body not available');
            return;
        }
        
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
    // SORTING
    // ============================================

    function sortData(data, field, direction) {
        var sorted = data.slice();
        sorted.sort(function(a, b) {
            var aVal = a[field] || '';
            var bVal = b[field] || '';
            
            if (field === 'data') {
                aVal = a.data.document || a.data.fuel_type || a.data.utility || a.data.category || '';
                bVal = b.data.document || b.data.fuel_type || b.data.utility || b.data.category || '';
            }
            
            if (typeof aVal === 'string') {
                return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }
            return direction === 'asc' ? aVal - bVal : bVal - aVal;
        });
        return sorted;
    }

    function sortBy(field) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = field === 'lastUpdated' ? 'desc' : 'asc';
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
        
        filterData();
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderStats() {
        var total = entries.length;
        var completed = 0, inProgress = 0, validated = 0, pending = 0;
        var batchMap = {};
        
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];
            if (e.progress === 100) completed++;
            if (e.progress > 0 && e.progress < 100) inProgress++;
            if (e.status === 'validated') validated++;
            if (e.status !== 'validated' && e.status !== 'completed') pending++;
            if (e.batch) { batchMap[e.batch] = (batchMap[e.batch] || 0) + 1; }
        }
        var batches = Object.keys(batchMap).length;
        
        var el = getEl('totalRecords');
        if (el) el.textContent = total;
        el = getEl('completedCount');
        if (el) el.textContent = completed;
        el = getEl('inProgressCount');
        if (el) el.textContent = inProgress;
        el = getEl('batchCount');
        if (el) el.textContent = batches;
        el = getEl('validationPending');
        if (el) el.textContent = pending;
        el = getEl('validatedCount');
        if (el) el.textContent = validated;
    }

    function renderPagination(total) {
        var totalPages = Math.ceil(total / perPage);
        var container = getEl('pagination');
        if (!container) return;
        
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' entries</div><div class="page-buttons"></div>';
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
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' entries</div><div class="page-buttons">' + btns + '</div>';
    }

    function renderTable(data) {
        var tbody = getEl('dataTableBody');
        var rowCount = getEl('rowCount');
        var filterCount = getEl('filterCount');
        
        if (!tbody) return;
        
        // Sort the data
        var sortedData = sortData(data, currentSort.field, currentSort.direction);
        
        // Paginate
        var start = (currentPage - 1) * perPage;
        var pageItems = sortedData.slice(start, start + perPage);
        
        if (!pageItems || pageItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:hsl(var(--muted-foreground));">📭 No entries match filters</td></tr>';
            if (rowCount) rowCount.textContent = '0';
            if (filterCount) filterCount.textContent = '0 entries';
            renderPagination(data.length);
            return;
        }
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var e = pageItems[i];
            var statusBadge = {
                'draft': '<span class="badge badge-muted">⏳ Draft</span>',
                'in-progress': '<span class="badge badge-warning">⏳ In Progress</span>',
                'completed': '<span class="badge badge-success">✅ Completed</span>',
                'validated': '<span class="badge badge-primary">✅ Validated</span>'
            }[e.status] || e.status;
            
            var progressColor = e.progress === 100 ? 'hsl(var(--success))' : e.progress > 50 ? 'hsl(var(--warning))' : 'hsl(var(--destructive))';
            var typeIcon = { fuel: '⛽', utility: '⚡', scope3: '🌍', document: '📄' }[e.type] || '📄';
            
            var dataPreview = '';
            if (e.type === 'fuel') dataPreview = (e.data.fuel_type || '') + ' ' + (e.data.quantity || '') + ' ' + (e.data.unit || '');
            else if (e.type === 'utility') dataPreview = (e.data.utility || '') + ' ' + (e.data.consumption || '') + ' ' + (e.data.unit || '');
            else if (e.type === 'scope3') dataPreview = (e.data.category || '') + ' ' + (e.data.co2e || '') + ' tCO2e';
            else dataPreview = e.data.document || 'Document';
            dataPreview = dataPreview.trim() || '—';
            
            html += '<tr>' +
                '<td><span style="font-size:16px;">' + typeIcon + '</span> ' + e.type + '</td>' +
                '<td><strong>' + dataPreview + '</strong><br><span style="font-size:11px;color:hsl(var(--muted-foreground));">' + (e.data.co2e ? e.data.co2e + ' tCO₂e' : '') + '</span></td>' +
                '<td><div style="display:flex;align-items:center;gap:8px;"><span style="font-size:12px;font-weight:500;">' + e.progress + '%</span><div class="progress-bar" style="flex:1;max-width:80px;"><div class="fill" style="width:' + e.progress + '%;background:' + progressColor + ';"></div></div></div></td>' +
                '<td>' + statusBadge + '</td>' +
                '<td>' + (e.batch || '—') + '</td>' +
                '<td style="font-size:12px;color:hsl(var(--muted-foreground));">' + e.lastUpdated + '</td>' +
                '<td>' +
                '<button class="btn btn-sm btn-ghost edit-btn" data-id="' + e.id + '" title="Edit">✏️</button>' +
                '<button class="btn btn-sm btn-ghost" onclick="previewDocument(\'' + e.id + '\')" title="Preview">👁️</button>' +
                '<button class="btn btn-sm btn-ghost" onclick="validateEntry(\'' + e.id + '\')" title="Validate">✅</button>' +
                '</td>' +
                '</tr>';
        }
        tbody.innerHTML = html;
        if (rowCount) rowCount.textContent = data.length;
        if (filterCount) filterCount.textContent = data.length + ' entries';
        renderPagination(data.length);
        
        // Attach edit handlers
        var editBtns = document.querySelectorAll('.edit-btn');
        for (var j = 0; j < editBtns.length; j++) {
            editBtns[j].addEventListener('click', function() {
                var id = this.getAttribute('data-id');
                var entry = null;
                for (var k = 0; k < entries.length; k++) {
                    if (entries[k].id === id) { entry = entries[k]; break; }
                }
                if (entry) openEditModal(entry);
            });
        }
    }

    function renderBatches() {
        var container = getEl('batchList');
        if (!container) return;
        
        var batchMap = {};
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];
            if (e.batch) {
                batchMap[e.batch] = (batchMap[e.batch] || 0) + 1;
            }
        }
        var batchList = Object.keys(batchMap).map(function(name) {
            return { name: name, count: batchMap[name] };
        });
        
        if (batchList.length === 0) {
            container.innerHTML = '<div style="color:hsl(var(--muted-foreground));font-size:13px;">No batches</div>';
            return;
        }
        
        var html = '';
        for (var j = 0; j < batchList.length; j++) {
            var b = batchList[j];
            html += '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid hsl(var(--border));">' +
                '<span>📦 ' + b.name + '</span>' +
                '<span class="badge badge-muted">' + b.count + ' files</span>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    function renderValidationSummary() {
        var container = getEl('validationSummary');
        if (!container) return;
        
        var groups = { draft: 0, 'in-progress': 0, completed: 0, validated: 0 };
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];
            if (groups[e.status] !== undefined) groups[e.status]++;
        }
        var total = entries.length;
        
        container.innerHTML =
            '<div style="display:flex;justify-content:space-between;font-size:13px;"><span>⏳ Draft</span><span class="badge badge-muted">' + groups.draft + '</span></div>' +
            '<div style="display:flex;justify-content:space-between;font-size:13px;"><span>⏳ In Progress</span><span class="badge badge-warning">' + groups['in-progress'] + '</span></div>' +
            '<div style="display:flex;justify-content:space-between;font-size:13px;"><span>✅ Completed</span><span class="badge badge-success">' + groups.completed + '</span></div>' +
            '<div style="display:flex;justify-content:space-between;font-size:13px;"><span>✅ Validated</span><span class="badge badge-primary">' + groups.validated + '</span></div>' +
            '<div style="margin-top:6px;font-size:12px;color:hsl(var(--muted-foreground));">Total: ' + total + '</div>';
    }

    // ============================================
    // FILTER FUNCTIONS
    // ============================================

    function filterData() {
        var statusEl = getEl('statusFilter');
        var typeEl = getEl('typeFilter');
        var searchEl = getEl('globalSearch');
        var fromEl = getEl('dateFrom');
        var toEl = getEl('dateTo');
        
        var status = statusEl ? statusEl.value : 'all';
        var type = typeEl ? typeEl.value : 'all';
        var search = searchEl ? searchEl.value.toLowerCase().trim() : '';
        var from = fromEl ? fromEl.value : '';
        var to = toEl ? toEl.value : '';
        
        filteredEntries = [];
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];
            if (status !== 'all' && e.status !== status) continue;
            if (type !== 'all' && e.type !== type) continue;
            if (search) {
                var searchable = (e.type + ' ' + e.id + ' ' + (e.batch || '') + ' ' + JSON.stringify(e.data) + ' ' + e.status).toLowerCase();
                if (searchable.indexOf(search) === -1) continue;
            }
            if (from && e.lastUpdated < from) continue;
            if (to && e.lastUpdated > to) continue;
            filteredEntries.push(e);
        }
        
        currentPage = 1;
        renderStats();
        renderTable(filteredEntries);
        renderBatches();
        renderValidationSummary();
    }

    function goToPage(page) {
        var totalPages = Math.ceil(filteredEntries.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderTable(filteredEntries);
        
        var table = document.querySelector('.table-wrap');
        if (table) {
            table.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // ============================================
    // MODAL FUNCTIONS
    // ============================================

    function openEditModal(entry) {
        currentEditId = entry.id;
        var idEl = getEl('modalEntryId');
        if (idEl) idEl.textContent = '#' + entry.id;
        
        var body = getEl('modalBody');
        if (!body) return;
        
        var fields = '';
        var d = entry.data;
        
        fields +=
            '<div class="settings-group"><label>Status</label>' +
            '<select id="editStatus">' +
            '<option value="draft"' + (entry.status === 'draft' ? ' selected' : '') + '>Draft</option>' +
            '<option value="in-progress"' + (entry.status === 'in-progress' ? ' selected' : '') + '>In Progress</option>' +
            '<option value="completed"' + (entry.status === 'completed' ? ' selected' : '') + '>Completed</option>' +
            '<option value="validated"' + (entry.status === 'validated' ? ' selected' : '') + '>Validated</option>' +
            '</select></div>' +
            '<div class="settings-group"><label>Progress (%)</label><input type="number" id="editProgress" value="' + entry.progress + '" min="0" max="100" /></div>' +
            '<div class="settings-group"><label>Batch</label><input type="text" id="editBatch" value="' + (entry.batch || '') + '" placeholder="e.g. BATCH-2026-01" /></div>';
        
        if (entry.type === 'fuel') {
            fields +=
                '<div class="settings-group"><label>Fuel Type</label><input type="text" id="editFuelType" value="' + (d.fuel_type || '') + '" /></div>' +
                '<div class="settings-group"><label>Quantity</label><input type="number" id="editQuantity" value="' + (d.quantity || '') + '" /></div>' +
                '<div class="settings-group"><label>Unit</label><input type="text" id="editUnit" value="' + (d.unit || '') + '" /></div>' +
                '<div class="settings-group"><label>CO₂e (t)</label><input type="number" step="0.01" id="editCo2e" value="' + (d.co2e || '') + '" /></div>';
        } else if (entry.type === 'utility') {
            fields +=
                '<div class="settings-group"><label>Utility Type</label><input type="text" id="editUtility" value="' + (d.utility || '') + '" /></div>' +
                '<div class="settings-group"><label>Consumption</label><input type="number" id="editConsumption" value="' + (d.consumption || '') + '" /></div>' +
                '<div class="settings-group"><label>Unit</label><input type="text" id="editUnit" value="' + (d.unit || '') + '" /></div>' +
                '<div class="settings-group"><label>CO₂e (t)</label><input type="number" step="0.01" id="editCo2e" value="' + (d.co2e || '') + '" /></div>';
        } else if (entry.type === 'scope3') {
            fields +=
                '<div class="settings-group"><label>Category</label><input type="text" id="editCategory" value="' + (d.category || '') + '" /></div>' +
                '<div class="settings-group"><label>Value</label><input type="text" id="editScopeValue" value="' + (d.value || d.distance || d.tonnes || '') + '" /></div>' +
                '<div class="settings-group"><label>Unit</label><input type="text" id="editUnit" value="' + (d.unit || '') + '" /></div>' +
                '<div class="settings-group"><label>CO₂e (t)</label><input type="number" step="0.01" id="editCo2e" value="' + (d.co2e || '') + '" /></div>';
        } else {
            fields +=
                '<div class="settings-group"><label>Document Name</label><input type="text" id="editDocument" value="' + (d.document || '') + '" /></div>' +
                '<div class="settings-group"><label>Amount</label><input type="number" id="editAmount" value="' + (d.amount || '') + '" /></div>' +
                '<div class="settings-group"><label>Currency</label><input type="text" id="editCurrency" value="' + (d.currency || 'GBP') + '" /></div>';
        }
        
        body.innerHTML = fields;
        var modal = getEl('editModal');
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        var modal = getEl('editModal');
        if (modal) modal.classList.remove('show');
        document.body.style.overflow = '';
        currentEditId = null;
    }

    function saveModal() {
        if (!currentEditId) return;
        
        var entry = null;
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].id === currentEditId) { entry = entries[i]; break; }
        }
        if (!entry) return;
        
        var statusEl = getEl('editStatus');
        var progressEl = getEl('editProgress');
        var batchEl = getEl('editBatch');
        
        if (statusEl) entry.status = statusEl.value;
        if (progressEl) entry.progress = parseInt(progressEl.value) || 0;
        if (batchEl) entry.batch = batchEl.value || null;
        
        var d = entry.data;
        if (entry.type === 'fuel') {
            var fuelEl = getEl('editFuelType');
            var qtyEl = getEl('editQuantity');
            var unitEl = getEl('editUnit');
            var co2eEl = getEl('editCo2e');
            if (fuelEl) d.fuel_type = fuelEl.value;
            if (qtyEl) d.quantity = parseFloat(qtyEl.value) || 0;
            if (unitEl) d.unit = unitEl.value;
            if (co2eEl) d.co2e = parseFloat(co2eEl.value) || 0;
        } else if (entry.type === 'utility') {
            var utilityEl = getEl('editUtility');
            var consEl = getEl('editConsumption');
            var unitEl = getEl('editUnit');
            var co2eEl = getEl('editCo2e');
            if (utilityEl) d.utility = utilityEl.value;
            if (consEl) d.consumption = parseFloat(consEl.value) || 0;
            if (unitEl) d.unit = unitEl.value;
            if (co2eEl) d.co2e = parseFloat(co2eEl.value) || 0;
        } else if (entry.type === 'scope3') {
            var catEl = getEl('editCategory');
            var valEl = getEl('editScopeValue');
            var unitEl = getEl('editUnit');
            var co2eEl = getEl('editCo2e');
            if (catEl) d.category = catEl.value;
            if (valEl) d.value = valEl.value;
            if (unitEl) d.unit = unitEl.value;
            if (co2eEl) d.co2e = parseFloat(co2eEl.value) || 0;
        } else {
            var docEl = getEl('editDocument');
            var amtEl = getEl('editAmount');
            var curEl = getEl('editCurrency');
            if (docEl) d.document = docEl.value;
            if (amtEl) d.amount = parseFloat(amtEl.value) || 0;
            if (curEl) d.currency = curEl.value || 'GBP';
        }
        
        entry.lastUpdated = new Date().toISOString().slice(0, 10);
        
        closeModal();
        filterData();
        showToast('✅ Entry updated successfully!');
    }

    // ============================================
    // ACTION FUNCTIONS
    // ============================================

    function previewDocument(id) {
        var entry = null;
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].id === id) { entry = entries[i]; break; }
        }
        if (entry) {
            showToast('👁️ Previewing: ' + (entry.data.document || entry.type + ' data'));
        }
    }

    function validateEntry(id) {
        var entry = null;
        for (var i = 0; i < entries.length; i++) {
            if (entries[i].id === id) { entry = entries[i]; break; }
        }
        if (entry) {
            if (entry.status === 'validated') {
                showToast('✅ Already validated');
                return;
            }
            entry.status = 'validated';
            entry.progress = 100;
            entry.lastUpdated = new Date().toISOString().slice(0, 10);
            filterData();
            showToast('✅ Entry validated successfully!');
        }
    }

    function exportData() {
        var count = filteredEntries.length || entries.length;
        showToast('📊 Exporting ' + count + ' entries to CSV...');
        setTimeout(function() {
            showToast('✅ Export completed!');
        }, 1000);
    }

    function refreshData() {
        showToast('🔄 Refreshing data...');
        entries = mockEntries.slice();
        filterData();
        setTimeout(function() {
            showToast('✅ Data refreshed!');
        }, 500);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        console.log('🚀 Initializing Extracted Data Management Module...');
        
        var tbody = getEl('dataTableBody');
        if (!tbody) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        entries = mockEntries.slice();
        filteredEntries = entries.slice();
        
        var applyBtn = getEl('applyFilters');
        if (applyBtn) applyBtn.addEventListener('click', filterData);
        
        var clearBtn = getEl('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                var statusEl = getEl('statusFilter');
                var typeEl = getEl('typeFilter');
                var searchEl = getEl('globalSearch');
                var fromEl = getEl('dateFrom');
                var toEl = getEl('dateTo');
                if (statusEl) statusEl.value = 'all';
                if (typeEl) typeEl.value = 'all';
                if (searchEl) searchEl.value = '';
                if (fromEl) fromEl.value = '';
                if (toEl) toEl.value = '';
                filterData();
            });
        }
        
        var searchEl = getEl('globalSearch');
        if (searchEl) {
            searchEl.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') filterData();
            });
        }
        
        var saveBtn = getEl('modalSaveBtn');
        if (saveBtn) saveBtn.addEventListener('click', saveModal);
        
        var modal = getEl('editModal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) closeModal();
            });
        }
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var modalEl = getEl('editModal');
                if (modalEl && modalEl.classList.contains('show')) {
                    closeModal();
                }
            }
        });
        
        filterData();
        
        console.log('✅ Extracted Data Management module loaded successfully!');
        console.log('📊 ' + entries.length + ' entries loaded');
        console.log('📄 ' + perPage + ' entries per page');
        console.log('↕ Sort by clicking column headers');
    }

    initModule();

    if (document.readyState !== 'complete') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOMContentLoaded fired');
            initModule();
        });
    }

    // ============================================
    // MAKE FUNCTIONS GLOBAL
    // ============================================

    window.filterData = filterData;
    window.sortBy = sortBy;
    window.goToPage = goToPage;
    window.openEditModal = openEditModal;
    window.closeModal = closeModal;
    window.saveModal = saveModal;
    window.previewDocument = previewDocument;
    window.validateEntry = validateEntry;
    window.exportData = exportData;
    window.refreshData = refreshData;
    window.showToast = showToast;
})(); // <-- End of the IIFE wrapper