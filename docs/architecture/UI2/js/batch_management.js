// Batch Management Module - SPA Compatible

(function(){
    console.log('📦 Batch Management JS loaded');

    // ============================================
    // MOCK DATA - 15+ batches for pagination
    // ============================================

    var users = [
        { id: 'u1', name: 'John Doe', avatar: 'JD', role: 'Admin' },
        { id: 'u2', name: 'Sarah Johnson', avatar: 'SJ', role: 'Sustainability Officer' },
        { id: 'u3', name: 'Mike Chen', avatar: 'MC', role: 'Data Analyst' },
        { id: 'u4', name: 'Emma Wilson', avatar: 'EW', role: 'Compliance Manager' },
        { id: 'u5', name: 'Alex Rivera', avatar: 'AR', role: 'Analyst' },
        { id: 'u6', name: 'Lisa Park', avatar: 'LP', role: 'Data Scientist' },
    ];

    var batches = [
        {
            id: 'b1',
            name: 'Q4 2026 Fuel Data',
            type: 'fuel',
            status: 'completed',
            totalFiles: 12,
            processedFiles: 12,
            createdBy: 'u2',
            date: '2026-01-15',
            files: [
                { name: 'fuel_consumption_oct.xlsx', size: '2.4 MB', status: 'success' },
                { name: 'fuel_consumption_nov.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'fuel_consumption_dec.xlsx', size: '2.8 MB', status: 'success' },
                { name: 'fleet_logs_oct.csv', size: '1.2 MB', status: 'success' },
                { name: 'fleet_logs_nov.csv', size: '1.1 MB', status: 'success' },
                { name: 'fleet_logs_dec.csv', size: '1.3 MB', status: 'success' },
                { name: 'fuel_invoices_oct.pdf', size: '0.8 MB', status: 'success' },
                { name: 'fuel_invoices_nov.pdf', size: '0.9 MB', status: 'success' },
                { name: 'fuel_invoices_dec.pdf', size: '0.7 MB', status: 'success' },
                { name: 'mileage_report_oct.xlsx', size: '1.5 MB', status: 'success' },
                { name: 'mileage_report_nov.xlsx', size: '1.6 MB', status: 'success' },
                { name: 'mileage_report_dec.xlsx', size: '1.4 MB', status: 'success' },
            ]
        },
        {
            id: 'b2',
            name: 'Utility Bills - London Office',
            type: 'utility',
            status: 'processing',
            totalFiles: 8,
            processedFiles: 5,
            createdBy: 'u3',
            date: '2026-01-14',
            files: [
                { name: 'electricity_oct.pdf', size: '1.2 MB', status: 'success' },
                { name: 'electricity_nov.pdf', size: '1.1 MB', status: 'success' },
                { name: 'electricity_dec.pdf', size: '1.3 MB', status: 'success' },
                { name: 'gas_oct.pdf', size: '0.9 MB', status: 'success' },
                { name: 'gas_nov.pdf', size: '0.8 MB', status: 'success' },
                { name: 'gas_dec.pdf', size: '1.0 MB', status: 'processing' },
                { name: 'water_oct.pdf', size: '0.5 MB', status: 'pending' },
                { name: 'water_nov.pdf', size: '0.6 MB', status: 'pending' },
            ]
        },
        {
            id: 'b3',
            name: 'Scope 3 Supplier Data',
            type: 'scope3',
            status: 'processing',
            totalFiles: 15,
            processedFiles: 9,
            createdBy: 'u4',
            date: '2026-01-13',
            files: [
                { name: 'supplier_a_emissions.xlsx', size: '3.2 MB', status: 'success' },
                { name: 'supplier_b_emissions.xlsx', size: '2.8 MB', status: 'success' },
                { name: 'supplier_c_emissions.xlsx', size: '4.1 MB', status: 'success' },
                { name: 'supplier_d_emissions.xlsx', size: '2.5 MB', status: 'success' },
                { name: 'supplier_e_emissions.xlsx', size: '3.6 MB', status: 'success' },
                { name: 'supplier_f_emissions.xlsx', size: '2.2 MB', status: 'success' },
                { name: 'supplier_g_emissions.xlsx', size: '3.9 MB', status: 'success' },
                { name: 'supplier_h_emissions.xlsx', size: '2.7 MB', status: 'success' },
                { name: 'supplier_i_emissions.xlsx', size: '3.1 MB', status: 'success' },
                { name: 'supplier_j_emissions.xlsx', size: '2.9 MB', status: 'processing' },
                { name: 'supplier_k_emissions.xlsx', size: '3.4 MB', status: 'pending' },
                { name: 'supplier_l_emissions.xlsx', size: '2.3 MB', status: 'pending' },
                { name: 'supplier_m_emissions.xlsx', size: '2.6 MB', status: 'pending' },
                { name: 'supplier_n_emissions.xlsx', size: '3.7 MB', status: 'pending' },
                { name: 'supplier_o_emissions.xlsx', size: '2.4 MB', status: 'pending' },
            ]
        },
        {
            id: 'b4',
            name: 'SECR Documentation 2026',
            type: 'document',
            status: 'completed',
            totalFiles: 6,
            processedFiles: 6,
            createdBy: 'u2',
            date: '2026-01-12',
            files: [
                { name: 'secr_report_draft.docx', size: '0.8 MB', status: 'success' },
                { name: 'secr_financial_data.xlsx', size: '1.5 MB', status: 'success' },
                { name: 'secr_emissions_calc.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'secr_appendices.pdf', size: '3.2 MB', status: 'success' },
                { name: 'secr_signoff.pdf', size: '0.3 MB', status: 'success' },
                { name: 'secr_cover_letter.docx', size: '0.2 MB', status: 'success' },
            ]
        },
        {
            id: 'b5',
            name: 'CSRD Data Collection',
            type: 'scope3',
            status: 'failed',
            totalFiles: 10,
            processedFiles: 4,
            createdBy: 'u4',
            date: '2026-01-11',
            files: [
                { name: 'csrd_esrs_e1.xlsx', size: '2.3 MB', status: 'success' },
                { name: 'csrd_esrs_e2.xlsx', size: '1.8 MB', status: 'success' },
                { name: 'csrd_esrs_e3.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'csrd_esrs_e4.xlsx', size: '1.9 MB', status: 'success' },
                { name: 'csrd_esrs_e5.xlsx', size: '2.4 MB', status: 'failed' },
                { name: 'csrd_esrs_s1.xlsx', size: '1.6 MB', status: 'failed' },
                { name: 'csrd_esrs_s2.xlsx', size: '1.7 MB', status: 'pending' },
                { name: 'csrd_esrs_s3.xlsx', size: '1.5 MB', status: 'pending' },
                { name: 'csrd_esrs_s4.xlsx', size: '2.0 MB', status: 'pending' },
                { name: 'csrd_esrs_g1.xlsx', size: '1.4 MB', status: 'pending' },
            ]
        },
        {
            id: 'b6',
            name: 'GHG Protocol Inventory',
            type: 'fuel',
            status: 'pending',
            totalFiles: 5,
            processedFiles: 0,
            createdBy: 'u3',
            date: '2026-01-10',
            files: [
                { name: 'ghg_scope1_calc.xlsx', size: '1.2 MB', status: 'pending' },
                { name: 'ghg_scope2_calc.xlsx', size: '1.1 MB', status: 'pending' },
                { name: 'ghg_scope3_calc.xlsx', size: '1.4 MB', status: 'pending' },
                { name: 'ghg_emission_factors.xlsx', size: '0.8 MB', status: 'pending' },
                { name: 'ghg_inventory_report.docx', size: '0.5 MB', status: 'pending' },
            ]
        },
        {
            id: 'b7',
            name: 'ISSB Disclosure Data',
            type: 'document',
            status: 'processing',
            totalFiles: 4,
            processedFiles: 2,
            createdBy: 'u2',
            date: '2026-01-09',
            files: [
                { name: 'issb_s1_disclosure.xlsx', size: '1.8 MB', status: 'success' },
                { name: 'issb_s2_disclosure.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'issb_s3_disclosure.xlsx', size: '1.6 MB', status: 'processing' },
                { name: 'issb_metrics.xlsx', size: '1.2 MB', status: 'pending' },
            ]
        },
        {
            id: 'b8',
            name: 'Fleet Management Data',
            type: 'fuel',
            status: 'completed',
            totalFiles: 9,
            processedFiles: 9,
            createdBy: 'u1',
            date: '2026-01-08',
            files: [
                { name: 'fleet_vehicle_registry.xlsx', size: '2.3 MB', status: 'success' },
                { name: 'fleet_emissions_calc.xlsx', size: '1.9 MB', status: 'success' },
                { name: 'fleet_fuel_consumption.csv', size: '3.1 MB', status: 'success' },
                { name: 'fleet_mileage_logs.csv', size: '2.8 MB', status: 'success' },
                { name: 'fleet_maintenance_records.xlsx', size: '1.5 MB', status: 'success' },
                { name: 'fleet_insurance_data.pdf', size: '0.8 MB', status: 'success' },
                { name: 'fleet_driver_info.xlsx', size: '0.6 MB', status: 'success' },
                { name: 'fleet_route_optimization.xlsx', size: '1.2 MB', status: 'success' },
                { name: 'fleet_annual_report.pdf', size: '4.2 MB', status: 'success' },
            ]
        },
        {
            id: 'b9',
            name: 'Q1 2026 Fuel Data',
            type: 'fuel',
            status: 'completed',
            totalFiles: 10,
            processedFiles: 10,
            createdBy: 'u2',
            date: '2026-01-07',
            files: [
                { name: 'fuel_consumption_jan.xlsx', size: '2.2 MB', status: 'success' },
                { name: 'fuel_consumption_feb.xlsx', size: '2.0 MB', status: 'success' },
                { name: 'fuel_consumption_mar.xlsx', size: '2.6 MB', status: 'success' },
                { name: 'fleet_logs_jan.csv', size: '1.1 MB', status: 'success' },
                { name: 'fleet_logs_feb.csv', size: '1.0 MB', status: 'success' },
                { name: 'fleet_logs_mar.csv', size: '1.2 MB', status: 'success' },
                { name: 'fuel_invoices_jan.pdf', size: '0.7 MB', status: 'success' },
                { name: 'fuel_invoices_feb.pdf', size: '0.8 MB', status: 'success' },
                { name: 'fuel_invoices_mar.pdf', size: '0.6 MB', status: 'success' },
                { name: 'mileage_report_q1.xlsx', size: '1.8 MB', status: 'success' },
            ]
        },
        {
            id: 'b10',
            name: 'Utility Bills - Manchester',
            type: 'utility',
            status: 'pending',
            totalFiles: 6,
            processedFiles: 0,
            createdBy: 'u5',
            date: '2026-01-06',
            files: [
                { name: 'electricity_jan.pdf', size: '1.0 MB', status: 'pending' },
                { name: 'electricity_feb.pdf', size: '0.9 MB', status: 'pending' },
                { name: 'gas_jan.pdf', size: '0.7 MB', status: 'pending' },
                { name: 'gas_feb.pdf', size: '0.6 MB', status: 'pending' },
                { name: 'water_jan.pdf', size: '0.4 MB', status: 'pending' },
                { name: 'water_feb.pdf', size: '0.5 MB', status: 'pending' },
            ]
        },
        {
            id: 'b11',
            name: 'Scope 3 - Logistics Providers',
            type: 'scope3',
            status: 'processing',
            totalFiles: 8,
            processedFiles: 3,
            createdBy: 'u6',
            date: '2026-01-05',
            files: [
                { name: 'logistics_a_data.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'logistics_b_data.xlsx', size: '1.8 MB', status: 'success' },
                { name: 'logistics_c_data.xlsx', size: '2.3 MB', status: 'success' },
                { name: 'logistics_d_data.xlsx', size: '1.9 MB', status: 'processing' },
                { name: 'logistics_e_data.xlsx', size: '2.2 MB', status: 'pending' },
                { name: 'logistics_f_data.xlsx', size: '1.6 MB', status: 'pending' },
                { name: 'logistics_g_data.xlsx', size: '2.0 MB', status: 'pending' },
                { name: 'logistics_h_data.xlsx', size: '1.7 MB', status: 'pending' },
            ]
        },
        {
            id: 'b12',
            name: 'SECR Report 2025',
            type: 'document',
            status: 'completed',
            totalFiles: 5,
            processedFiles: 5,
            createdBy: 'u1',
            date: '2026-01-04',
            files: [
                { name: 'secr_2025_final.docx', size: '1.2 MB', status: 'success' },
                { name: 'secr_2025_data.xlsx', size: '2.8 MB', status: 'success' },
                { name: 'secr_2025_calculations.xlsx', size: '3.1 MB', status: 'success' },
                { name: 'secr_2025_appendices.pdf', size: '4.2 MB', status: 'success' },
                { name: 'secr_2025_cover.pdf', size: '0.3 MB', status: 'success' },
            ]
        },
        {
            id: 'b13',
            name: 'CBAM Data Collection',
            type: 'scope3',
            status: 'failed',
            totalFiles: 7,
            processedFiles: 2,
            createdBy: 'u4',
            date: '2026-01-03',
            files: [
                { name: 'cbam_steel_data.xlsx', size: '2.5 MB', status: 'success' },
                { name: 'cbam_cement_data.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'cbam_fertilizer_data.xlsx', size: '2.8 MB', status: 'failed' },
                { name: 'cbam_aluminum_data.xlsx', size: '2.3 MB', status: 'failed' },
                { name: 'cbam_electricity_data.xlsx', size: '1.9 MB', status: 'pending' },
                { name: 'cbam_hydrogen_data.xlsx', size: '1.7 MB', status: 'pending' },
                { name: 'cbam_other_data.xlsx', size: '2.0 MB', status: 'pending' },
            ]
        },
        {
            id: 'b14',
            name: 'ESRS Data Collection',
            type: 'document',
            status: 'processing',
            totalFiles: 5,
            processedFiles: 2,
            createdBy: 'u2',
            date: '2026-01-02',
            files: [
                { name: 'esrs_e1_data.xlsx', size: '2.4 MB', status: 'success' },
                { name: 'esrs_e2_data.xlsx', size: '2.1 MB', status: 'success' },
                { name: 'esrs_s1_data.xlsx', size: '1.8 MB', status: 'processing' },
                { name: 'esrs_s2_data.xlsx', size: '1.6 MB', status: 'pending' },
                { name: 'esrs_g1_data.xlsx', size: '1.9 MB', status: 'pending' },
            ]
        },
        {
            id: 'b15',
            name: 'Q4 2025 Fuel Data',
            type: 'fuel',
            status: 'completed',
            totalFiles: 12,
            processedFiles: 12,
            createdBy: 'u3',
            date: '2025-12-15',
            files: [
                { name: 'fuel_consumption_oct_2025.xlsx', size: '2.3 MB', status: 'success' },
                { name: 'fuel_consumption_nov_2025.xlsx', size: '2.0 MB', status: 'success' },
                { name: 'fuel_consumption_dec_2025.xlsx', size: '2.7 MB', status: 'success' },
                { name: 'fleet_logs_oct_2025.csv', size: '1.1 MB', status: 'success' },
                { name: 'fleet_logs_nov_2025.csv', size: '1.0 MB', status: 'success' },
                { name: 'fleet_logs_dec_2025.csv', size: '1.2 MB', status: 'success' },
                { name: 'fuel_invoices_oct_2025.pdf', size: '0.7 MB', status: 'success' },
                { name: 'fuel_invoices_nov_2025.pdf', size: '0.8 MB', status: 'success' },
                { name: 'fuel_invoices_dec_2025.pdf', size: '0.6 MB', status: 'success' },
                { name: 'mileage_report_oct_2025.xlsx', size: '1.4 MB', status: 'success' },
                { name: 'mileage_report_nov_2025.xlsx', size: '1.5 MB', status: 'success' },
                { name: 'mileage_report_dec_2025.xlsx', size: '1.3 MB', status: 'success' },
            ]
        },
    ];

    console.log('📊 Loaded ' + batches.length + ' batches');

    // ============================================
    // STATE
    // ============================================

    var filteredBatches = [];
    var currentBatchId = null;
    var currentPage = 1;
    var perPage = 5;

    // ============================================
    // DOM REFS
    // ============================================

    var tbody, rowCount, filterCount, totalBatches, completedBatches, processingBatches;
    var totalFiles, failedBatches, successRate, statusFilter, typeFilter, dateFrom, dateTo;
    var globalSearch, modal, modalBody, modalBatchName, paginationEl;

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
            'pending': '<span class="badge badge-muted">⏳ Pending</span>',
            'processing': '<span class="badge badge-warning">⏳ Processing</span>',
            'completed': '<span class="badge badge-success">✅ Completed</span>',
            'failed': '<span class="badge badge-destructive">❌ Failed</span>'
        };
        return map[status] || status;
    }

    function getTypeBadge(type) {
        var map = {
            'fuel': '<span class="badge badge-secondary">⛽ Fuel</span>',
            'utility': '<span class="badge badge-secondary">⚡ Utility</span>',
            'scope3': '<span class="badge badge-secondary">🌍 Scope 3</span>',
            'document': '<span class="badge badge-secondary">📄 Document</span>'
        };
        return map[type] || type;
    }

    function getTypeIcon(type) {
        var map = {
            'fuel': '⛽',
            'utility': '⚡',
            'scope3': '🌍',
            'document': '📄'
        };
        return map[type] || '📦';
    }

    function getFileStatusIcon(status) {
        var map = {
            'success': '✅',
            'processing': '⏳',
            'failed': '❌',
            'pending': '⏸️'
        };
        return map[status] || '●';
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderStats(data) {
        console.log('📊 Rendering stats for ' + data.length + ' items');
        
        var total = data.length;
        var completed = 0, processing = 0, failed = 0, files = 0, processed = 0;

        for (var i = 0; i < data.length; i++) {
            var b = data[i];
            if (b.status === 'completed') completed++;
            if (b.status === 'processing') processing++;
            if (b.status === 'failed') failed++;
            files += b.totalFiles;
            processed += b.processedFiles;
        }

        var rate = files > 0 ? Math.round((processed / files) * 100) : 0;

        if (totalBatches) totalBatches.textContent = total;
        if (completedBatches) completedBatches.textContent = completed;
        if (processingBatches) processingBatches.textContent = processing;
        if (totalFiles) totalFiles.textContent = files;
        if (failedBatches) failedBatches.textContent = failed;
        if (successRate) successRate.textContent = rate + '%';
    }

    function renderPagination(total) {
        var totalPages = Math.ceil(total / perPage);
        if (!paginationEl) return;

        if (totalPages <= 1) {
            paginationEl.innerHTML = '<div class="page-info">Showing ' + total + ' batches</div><div class="page-buttons"></div>';
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

        paginationEl.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' batches</div><div class="page-buttons">' + btns + '</div>';
    }

    function renderTable(data) {
        console.log('📋 Rendering table with ' + data.length + ' items, page ' + currentPage);
        
        var start = (currentPage - 1) * perPage;
        var pageItems = data.slice(start, start + perPage);

        if (!tbody) {
            console.error('❌ tbody not found');
            return;
        }

        if (!pageItems || pageItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:hsl(var(--muted-foreground));">📭 No batches match filters</td></tr>';
            if (rowCount) rowCount.textContent = '0';
            if (filterCount) filterCount.textContent = '0 batches';
            renderPagination(data.length);
            return;
        }

        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var batch = pageItems[i];
            var user = getUser(batch.createdBy);
            var progress = batch.totalFiles > 0 ? Math.round((batch.processedFiles / batch.totalFiles) * 100) : 0;
            var typeIcon = getTypeIcon(batch.type);

            html += '<tr>' +
                '<td>' +
                '<div style="font-weight:500;">' + typeIcon + ' ' + batch.name + '</div>' +
                '<div style="font-size:11px;color:hsl(var(--muted-foreground));">' + batch.id + '</div>' +
                '</td>' +
                '<td>' + getTypeBadge(batch.type) + '</td>' +
                '<td>' + batch.processedFiles + '/' + batch.totalFiles + '</td>' +
                '<td>' +
                '<div class="batch-progress">' +
                '<span>' + progress + '%</span>' +
                '<div class="progress-bar"><div class="fill" style="width:' + progress + '%;' + (progress === 100 ? 'background:hsl(var(--success));' : '') + '"></div></div>' +
                '</div>' +
                '</td>' +
                '<td>' + getStatusBadge(batch.status) + '</td>' +
                '<td>' +
                '<div style="display:flex;align-items:center;gap:6px;">' +
                '<div class="avatar avatar-sm" style="width:24px;height:24px;font-size:10px;">' + user.avatar + '</div>' +
                user.name +
                '</div>' +
                '</td>' +
                '<td style="font-size:12px;color:hsl(var(--muted-foreground));">' + batch.date + '</td>' +
                '<td>' +
                '<button class="btn btn-sm btn-ghost view-batch" data-id="' + batch.id + '">👁️</button>' +
                '<button class="btn btn-sm btn-ghost" onclick="downloadBatch(\'' + batch.id + '\')">⬇️</button>' +
                '</td>' +
                '</tr>';
        }

        tbody.innerHTML = html;
        if (rowCount) rowCount.textContent = data.length;
        if (filterCount) filterCount.textContent = data.length + ' batches';
        renderPagination(data.length);

        // Attach detail handlers
        var viewBtns = document.querySelectorAll('.view-batch');
        for (var j = 0; j < viewBtns.length; j++) {
            viewBtns[j].addEventListener('click', function(e) {
                var id = this.getAttribute('data-id');
                console.log('👁️ View batch: ' + id);
                var batch = null;
                for (var k = 0; k < batches.length; k++) {
                    if (batches[k].id === id) { batch = batches[k]; break; }
                }
                if (batch) showBatchDetail(batch);
            });
        }
    }

    // ============================================
    // FILTER FUNCTIONS
    // ============================================

    function filterData() {
        console.log('🔍 Applying filters...');
        
        var status = statusFilter ? statusFilter.value : 'all';
        var type = typeFilter ? typeFilter.value : 'all';
        var search = globalSearch ? globalSearch.value.toLowerCase().trim() : '';
        var from = dateFrom ? dateFrom.value : '';
        var to = dateTo ? dateTo.value : '';

        console.log('  Status: ' + status + ', Type: ' + type + ', Search: "' + search + '"');

        var filtered = [];
        for (var i = 0; i < batches.length; i++) {
            var batch = batches[i];
            if (status !== 'all' && batch.status !== status) continue;
            if (type !== 'all' && batch.type !== type) continue;
            if (search) {
                var searchable = (batch.name + ' ' + batch.id + ' ' + batch.type).toLowerCase();
                if (searchable.indexOf(search) === -1) continue;
            }
            if (from && batch.date < from) continue;
            if (to && batch.date > to) continue;
            filtered.push(batch);
        }

        console.log('  Found ' + filtered.length + ' batches after filtering');
        filteredBatches = filtered;
        currentPage = 1;
        renderStats(batches);
        renderTable(filtered);
    }

    function clearFilters() {
        console.log('🧹 Clearing filters');
        if (statusFilter) statusFilter.value = 'all';
        if (typeFilter) typeFilter.value = 'all';
        if (globalSearch) globalSearch.value = '';
        if (dateFrom) dateFrom.value = '';
        if (dateTo) dateTo.value = '';
        currentPage = 1;
        filterData();
    }

    function goToPage(page) {
        var totalPages = Math.ceil(filteredBatches.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderTable(filteredBatches);
        // Scroll to top of table
        var table = document.querySelector('.table-wrap');
        if (table) {
            table.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    function openNewBatchModal() {
        console.log('📦 Opening new batch modal');
        var newModal = document.getElementById('newBatchModal');
        console.log('  newModal element:', newModal);
        
        if (newModal) {
            // Reset form
            var nameInput = document.getElementById('newBatchName');
            var typeSelect = document.getElementById('newBatchType');
            var descInput = document.getElementById('newBatchDesc');
            
            if (nameInput) nameInput.value = '';
            if (typeSelect) typeSelect.value = 'fuel';
            if (descInput) descInput.value = '';
            
            // Force display with inline style and class
            newModal.style.display = 'flex';
            newModal.classList.add('show');
            document.body.style.overflow = 'hidden';
            console.log('✅ New batch modal opened');
        } else {
            console.error('❌ New batch modal not found in DOM');
            showToast('⚠️ New batch modal not available');
        }
    }

    function closeNewBatchModal() {
        var newModal = document.getElementById('newBatchModal');
        if (newModal) {
            newModal.style.display = 'none';
            newModal.classList.remove('show');
            document.body.style.overflow = '';
            console.log('✅ New batch modal closed');
        }
    }

    function showBatchDetail(batch) {
        console.log('📦 Showing detail for: ' + batch.name);
        currentBatchId = batch.id;
        
        var nameEl = document.getElementById('modalBatchName');
        if (nameEl) nameEl.textContent = batch.name;

        var user = getUser(batch.createdBy);
        var progress = batch.totalFiles > 0 ? Math.round((batch.processedFiles / batch.totalFiles) * 100) : 0;

        var fileListHtml = '';
        for (var i = 0; i < batch.files.length; i++) {
            var f = batch.files[i];
            fileListHtml += '<div class="file-item" style="display:flex;align-items:center;gap:10px;padding:6px 8px;border-bottom:1px solid hsl(var(--border));font-size:13px;">' +
                '<span class="file-icon" style="width:20px;text-align:center;">' + getFileStatusIcon(f.status) + '</span>' +
                '<span style="flex:1;">' + f.name + '</span>' +
                '<span style="font-size:12px;color:hsl(var(--muted-foreground));">' + f.size + '</span>' +
                '<span style="font-size:11px;">' + f.status + '</span>' +
                '</div>';
        }

        var body = document.getElementById('modalBody');
        if (body) {
            body.innerHTML =
                '<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">' +
                '<div><strong>Batch ID:</strong> ' + batch.id + '</div>' +
                '<div><strong>Type:</strong> ' + getTypeBadge(batch.type) + '</div>' +
                '<div><strong>Status:</strong> ' + getStatusBadge(batch.status) + '</div>' +
                '<div><strong>Created By:</strong> ' + user.name + '</div>' +
                '<div><strong>Date:</strong> ' + batch.date + '</div>' +
                '<div><strong>Files:</strong> ' + batch.processedFiles + '/' + batch.totalFiles + '</div>' +
                '<div style="grid-column: span 2;">' +
                '<strong>Progress:</strong>' +
                '<div class="batch-progress" style="display:flex;align-items:center;gap:8px;min-width:120px;">' +
                '<span style="min-width:36px;font-size:12px;font-weight:500;">' + progress + '%</span>' +
                '<div class="progress-bar" style="flex:1;height:6px;background:hsl(var(--muted));border-radius:4px;overflow:hidden;"><div class="fill" style="height:100%;border-radius:4px;transition:width 0.6s cubic-bezier(0.4,0,0.2,1);background:hsl(var(--primary));width:' + progress + '%;' + (progress === 100 ? 'background:hsl(var(--success));' : '') + '"></div></div>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '<div style="margin-top:12px;">' +
                '<div style="font-weight:600;margin-bottom:8px;">📄 Files in this batch</div>' +
                '<div style="max-height:300px;overflow-y:auto;border:1px solid hsl(var(--border));border-radius:var(--radius);padding:8px;">' +
                fileListHtml +
                '</div>' +
                '</div>';
        }

        var modal = document.getElementById('batchDetailModal');
        console.log('  detail modal element:', modal);
        
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            console.log('✅ Detail modal opened');
        } else {
            console.error('❌ Detail modal not found');
            showToast('⚠️ Detail modal not available');
        }
    }

    function closeBatchDetailModal() {
        var modal = document.getElementById('batchDetailModal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('show');
            document.body.style.overflow = '';
            console.log('✅ Detail modal closed');
        }
    }

    // ============================================
    // NEW BATCH MODAL
    // ============================================

    function createNewBatch() {
        var name = document.getElementById('newBatchName').value.trim();
        var type = document.getElementById('newBatchType').value;
        var desc = document.getElementById('newBatchDesc').value.trim();

        if (!name) {
            showToast('⚠️ Please enter a batch name');
            return;
        }

        var newBatch = {
            id: 'b' + (batches.length + 1),
            name: name,
            type: type,
            status: 'pending',
            totalFiles: 0,
            processedFiles: 0,
            createdBy: 'u1',
            date: new Date().toISOString().slice(0, 10),
            files: []
        };

        batches.unshift(newBatch);
        closeNewBatchModal();
        filterData();
        showToast('✅ Batch "' + name + '" created successfully!');
    }

    // ============================================
    // BATCH ACTIONS
    // ============================================

    function downloadBatch(id) {
        var batch = null;
        for (var i = 0; i < batches.length; i++) {
            if (batches[i].id === id) { batch = batches[i]; break; }
        }
        if (batch) {
            showToast('⬇️ Downloading: ' + batch.name);
        }
    }

    function processBatch() {
        console.log('▶️ Processing batch: ' + currentBatchId);
        if (currentBatchId) {
            var batch = null;
            for (var i = 0; i < batches.length; i++) {
                if (batches[i].id === currentBatchId) { batch = batches[i]; break; }
            }
            if (!batch) {
                console.error('❌ Batch not found: ' + currentBatchId);
                return;
            }

            console.log('  Current status: ' + batch.status);

            if (batch.status === 'pending') {
                batch.status = 'processing';
                batch.processedFiles = Math.min(batch.processedFiles + 2, batch.totalFiles);
                showToast('🔄 Batch processing started!');
                filterData();
                showBatchDetail(batch);
            } else if (batch.status === 'processing') {
                batch.processedFiles = Math.min(batch.processedFiles + 3, batch.totalFiles);
                if (batch.processedFiles === batch.totalFiles) {
                    batch.status = 'completed';
                    showToast('✅ Batch processing completed!');
                } else {
                    showToast('⏳ Batch processing in progress... (' + batch.processedFiles + '/' + batch.totalFiles + ')');
                }
                filterData();
                showBatchDetail(batch);
            } else if (batch.status === 'failed') {
                batch.status = 'processing';
                batch.processedFiles = Math.min(batch.processedFiles + 2, batch.totalFiles);
                showToast('🔄 Restarting failed batch...');
                filterData();
                showBatchDetail(batch);
            } else {
                showToast('✅ Batch is already completed!');
            }
        }
    }

    function refreshData() {
        showToast('🔄 Refreshing...');
        setTimeout(function() {
            filterData();
            showToast('✅ Refreshed');
        }, 400);
    }

    // ============================================
    // TOAST
    // ============================================

    function showToast(message) {
        var old = document.querySelector('.custom-toast');
        if (old) old.remove();
        var el = document.createElement('div');
        el.className = 'custom-toast';
        el.style.cssText = 'position:fixed;bottom:24px;right:24px;background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius);padding:12px 20px;box-shadow:var(--shadow-lg);z-index:99999;font-size:14px;animation:slideUp 0.3s ease;max-width:400px;color:hsl(var(--foreground));';
        el.textContent = message;
        document.body.appendChild(el);
        setTimeout(function() {
            el.style.opacity = '0';
            el.style.transition = 'opacity 0.3s';
            setTimeout(function() { el.remove(); }, 300);
        }, 3000);
    }

    // ============================================
    // INIT MODULE
    // ============================================
    function initModule() {
        console.log('🚀 Initializing Batch Management Module...');
        
        // Get DOM refs
        tbody = document.getElementById('batchTableBody');
        rowCount = document.getElementById('rowCount');
        filterCount = document.getElementById('filterCount');
        paginationEl = document.getElementById('pagination');
        
        totalBatches = document.getElementById('totalBatches');
        completedBatches = document.getElementById('completedBatches');
        processingBatches = document.getElementById('processingBatches');
        totalFiles = document.getElementById('totalFiles');
        failedBatches = document.getElementById('failedBatches');
        successRate = document.getElementById('successRate');
        
        statusFilter = document.getElementById('statusFilter');
        typeFilter = document.getElementById('typeFilter');
        dateFrom = document.getElementById('dateFrom');
        dateTo = document.getElementById('dateTo');
        globalSearch = document.getElementById('globalSearch');
        
        // Modal refs - using direct references
        var detailModal = document.getElementById('batchDetailModal');
        var newModal = document.getElementById('newBatchModal');
        modal = detailModal;
        modalBody = document.getElementById('modalBody');
        modalBatchName = document.getElementById('modalBatchName');

        console.log('  tbody found:', !!tbody);
        console.log('  pagination found:', !!paginationEl);
        console.log('  detail modal found:', !!detailModal);
        console.log('  new batch modal found:', !!newModal);
        console.log('  modalBody found:', !!modalBody);
        console.log('  modalBatchName found:', !!modalBatchName);

        if (!tbody) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }

        console.log('✅ All DOM elements found, rendering ' + batches.length + ' batches');

        // Set up event listeners
        var applyBtn = document.getElementById('applyFilters');
        if (applyBtn) {
            applyBtn.addEventListener('click', filterData);
            console.log('  Apply button listener attached');
        }

        var clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', clearFilters);
            console.log('  Clear button listener attached');
        }

        if (globalSearch) {
            globalSearch.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') filterData();
            });
            console.log('  Search listener attached');
        }

        // Detail modal overlay click
        if (detailModal) {
            detailModal.addEventListener('click', function(e) {
                if (e.target === this) closeBatchDetailModal();
            });
            console.log('  Detail modal overlay listener attached');
        }

        // New batch modal overlay click
        if (newModal) {
            newModal.addEventListener('click', function(e) {
                if (e.target === this) closeNewBatchModal();
            });
            console.log('  New modal overlay listener attached');
        }

        // Process batch button
        var processBtn = document.getElementById('modalProcessBtn');
        if (processBtn) {
            processBtn.addEventListener('click', processBatch);
            console.log('  Process button listener attached');
        }

        // Escape key to close modals
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                if (detailModal && detailModal.classList.contains('show')) {
                    closeBatchDetailModal();
                }
                if (newModal && newModal.classList.contains('show')) {
                    closeNewBatchModal();
                }
            }
        });

        // Initial render
        filteredBatches = batches.slice();
        renderStats(batches);
        renderTable(batches);

        console.log('✅ Batch Management module loaded successfully!');
        console.log('📊 ' + batches.length + ' batches loaded');
    }

    // ============================================
    // MAKE FUNCTIONS GLOBAL
    // ============================================

    window.filterData = filterData;
    window.clearFilters = clearFilters;
    window.goToPage = goToPage;
    window.downloadBatch = downloadBatch;
    window.processBatch = processBatch;
    window.openNewBatchModal = openNewBatchModal;
    window.closeNewBatchModal = closeNewBatchModal;
    window.createNewBatch = createNewBatch;
    window.closeBatchDetailModal = closeBatchDetailModal;
    window.showBatchDetail = showBatchDetail;
    window.refreshData = refreshData;
    window.showToast = showToast;
    window.initModule = initModule;

    // ============================================
    // INIT - Try immediately and with retry
    // ============================================

    // Try immediately
    initModule();

    // Fallback: retry after DOM ready
    if (document.readyState !== 'complete') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOMContentLoaded fired');
            initModule();
        });
        window.addEventListener('load', function() {
            console.log('📄 Window load fired');
            if (tbody && tbody.children.length === 0) {
                console.log('⚠️ Table empty after load, re-initializing...');
                initModule();
            }
        });
    }
})();
