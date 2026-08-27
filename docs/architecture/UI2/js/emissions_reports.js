    // Emissions Reports Module - SPA Compatible
(function() {

    console.log('📈 Emissions Reports JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var monthlyData = {
        '2025': {
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            scope1: [28, 32, 25, 38, 30, 35, 28, 22, 32, 18, 21, 26],
            scope2: [42, 38, 46, 33, 40, 30, 36, 38, 32, 34, 38, 30],
            scope3: [16, 19, 18, 22, 20, 18, 19, 16, 14, 13, 12, 10]
        },
        '2024': {
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            scope1: [32, 36, 29, 42, 34, 39, 32, 26, 36, 22, 25, 30],
            scope2: [46, 42, 50, 37, 44, 34, 40, 42, 36, 38, 42, 34],
            scope3: [18, 22, 20, 25, 23, 20, 22, 18, 16, 15, 14, 12]
        },
        '2023': {
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            scope1: [35, 40, 32, 46, 38, 42, 35, 30, 40, 25, 28, 33],
            scope2: [50, 46, 54, 41, 48, 38, 44, 46, 40, 42, 46, 38],
            scope3: [20, 24, 22, 28, 25, 22, 24, 20, 18, 17, 16, 14]
        }
    };

    var facilityData = [
        { name: 'London Office', scope1: 45.2, scope2: 89.6, scope3: 34.8, total: 169.6 },
        { name: 'Manchester Office', scope1: 28.4, scope2: 56.2, scope3: 22.4, total: 107.0 },
        { name: 'Birmingham Office', scope1: 22.6, scope2: 44.8, scope3: 18.2, total: 85.6 },
        { name: 'Data Center', scope1: 12.8, scope2: 134.2, scope3: 8.4, total: 155.4 },
        { name: 'Distribution Center', scope1: 36.2, scope2: 42.6, scope3: 15.6, total: 94.4 }
    ];

    var assetData = [
        { name: 'Fleet #001', type: 'Vehicle', scope1: 56.4, scope2: 0, scope3: 0, total: 56.4 },
        { name: 'Fleet #002', type: 'Vehicle', scope1: 48.2, scope2: 0, scope3: 0, total: 48.2 },
        { name: 'Fleet #003', type: 'Vehicle', scope1: 42.8, scope2: 0, scope3: 0, total: 42.8 },
        { name: 'Building A', type: 'Facility', scope1: 22.6, scope2: 89.6, scope3: 12.4, total: 124.6 },
        { name: 'Building B', type: 'Facility', scope1: 18.4, scope2: 56.2, scope3: 8.2, total: 82.8 },
        { name: 'Building C', type: 'Facility', scope1: 14.2, scope2: 44.8, scope3: 6.8, total: 65.8 },
        { name: 'Data Center', type: 'Facility', scope1: 8.6, scope2: 134.2, scope3: 4.2, total: 147.0 }
    ];

    var complianceData = [
        { standard: 'SECR', status: 'compliant', dueDate: '2026-06-30', lastReported: '2025-12-31', progress: 100 },
        { standard: 'CSRD (ESRS E1)', status: 'in-progress', dueDate: '2026-12-31', lastReported: '2025-09-30', progress: 65 },
        { standard: 'ISSB S1', status: 'compliant', dueDate: '2026-03-31', lastReported: '2025-12-31', progress: 100 },
        { standard: 'ISSB S2', status: 'in-progress', dueDate: '2026-06-30', lastReported: '2025-09-30', progress: 70 },
        { standard: 'GHG Protocol', status: 'compliant', dueDate: '2026-12-31', lastReported: '2025-12-31', progress: 100 },
        { standard: 'TCFD', status: 'in-progress', dueDate: '2026-09-30', lastReported: '2025-06-30', progress: 55 }
    ];

    var topSources = [
        { name: 'Electricity Usage', scope: 'Scope 2', emissions: 245.6, pct: 28 },
        { name: 'Fleet Fuel', scope: 'Scope 1', emissions: 189.2, pct: 22 },
        { name: 'Natural Gas', scope: 'Scope 1', emissions: 132.4, pct: 15 },
        { name: 'Supply Chain', scope: 'Scope 3', emissions: 98.7, pct: 11 },
        { name: 'Business Travel', scope: 'Scope 3', emissions: 67.8, pct: 8 },
        { name: 'Data Center Cooling', scope: 'Scope 2', emissions: 45.6, pct: 5 }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentReport = 'overview';
    var currentYear = '2025';
    var chartView = 'year';
    var toastTimeout = null;

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
    // REPORT NAVIGATION
    // ============================================

    function switchReport(report) {
        currentReport = report;
        var tabs = document.querySelectorAll('.report-tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.toggle('active', tabs[i].getAttribute('data-report') === report);
        }
        var sections = document.querySelectorAll('.report-section');
        for (var j = 0; j < sections.length; j++) {
            sections[j].classList.toggle('active', sections[j].id === 'report-' + report);
        }
        renderReport(report);
    }

    function setChartView(view, btn) {
        chartView = view;
        var btns = document.querySelectorAll('.btn-ghost');
        for (var i = 0; i < btns.length; i++) {
            btns[i].classList.remove('active');
        }
        if (btn) btn.classList.add('active');
        renderOverviewChart();
    }

    function applyFilters() {
        var yearEl = document.getElementById('filterYear');
        var scopeEl = document.getElementById('filterScope');
        var facilityEl = document.getElementById('filterFacility');
        var typeEl = document.getElementById('filterType');
        
        currentYear = yearEl ? yearEl.value : '2025';
        var scope = scopeEl ? scopeEl.value : 'all';
        var facility = facilityEl ? facilityEl.value : 'all';
        var type = typeEl ? typeEl.value : 'all';
        
        renderReport(currentReport);
    }

    function resetFilters() {
        var yearEl = document.getElementById('filterYear');
        var scopeEl = document.getElementById('filterScope');
        var facilityEl = document.getElementById('filterFacility');
        var typeEl = document.getElementById('filterType');
        
        if (yearEl) yearEl.value = '2025';
        if (scopeEl) scopeEl.value = 'all';
        if (facilityEl) facilityEl.value = 'all';
        if (typeEl) typeEl.value = 'all';
        
        applyFilters();
        showToast('🔄 Filters reset');
    }

    function generateReport() {
        showToast('📊 Report generation started...');
        setTimeout(function() {
            showToast('✅ Report generated successfully!');
        }, 1500);
    }

    function exportReport(format) {
        var name = format.toUpperCase();
        showToast('📊 Exporting ' + name + ' report...');
        setTimeout(function() {
            showToast('✅ ' + name + ' report generated successfully!');
        }, 1500);
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderReport(report) {
        switch (report) {
            case 'overview': renderOverview(); break;
            case 'scope': renderScope(); break;
            case 'trend': renderTrend(); break;
            case 'facility': renderFacility(); break;
            case 'asset': renderAsset(); break;
            case 'compliance': renderCompliance(); break;
        }
    }

    // ============================================
    // OVERVIEW REPORT
    // ============================================

    function renderOverview() {
        var data = monthlyData[currentYear] || monthlyData['2025'];
        var totalS1 = 0, totalS2 = 0, totalS3 = 0;
        for (var i = 0; i < data.scope1.length; i++) {
            totalS1 += data.scope1[i];
            totalS2 += data.scope2[i];
            totalS3 += data.scope3[i];
        }
        var total = totalS1 + totalS2 + totalS3;

        var el = document.getElementById('totalEmissions');
        if (el) el.textContent = total.toFixed(1);
        el = document.getElementById('scope1Emissions');
        if (el) el.textContent = totalS1.toFixed(1);
        el = document.getElementById('scope2Emissions');
        if (el) el.textContent = totalS2.toFixed(1);
        el = document.getElementById('scope3Emissions');
        if (el) el.textContent = totalS3.toFixed(1);

        renderOverviewChart();
        renderTopSources();
        renderEmissionsByType();
    }

    function renderOverviewChart() {
        var container = document.getElementById('overviewChart');
        if (!container) return;
        
        var data = monthlyData[currentYear] || monthlyData['2025'];
        var months = data.months;
        var maxVal = 0;
        for (var i = 0; i < data.scope1.length; i++) {
            var m = Math.max(data.scope1[i], data.scope2[i], data.scope3[i]);
            if (m > maxVal) maxVal = m;
        }
        maxVal *= 1.2;

        var html = '<div class="chart-bars">';
        for (var i = 0; i < months.length; i++) {
            var h1 = (data.scope1[i] / maxVal) * 100;
            var h2 = (data.scope2[i] / maxVal) * 100;
            var h3 = (data.scope3[i] / maxVal) * 100;
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar scope1" style="height:' + h1 + '%;"></div>' +
                '<div class="chart-bar scope2" style="height:' + h2 + '%;"></div>' +
                '<div class="chart-bar scope3" style="height:' + h3 + '%;"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + months[i] + '</div>' +
                '</div>';
        }
        html += '</div>';
        container.innerHTML = html;
    }

    function renderTopSources() {
        var container = document.getElementById('topSources');
        if (!container) return;
        
        var html = '';
        for (var i = 0; i < topSources.length; i++) {
            var s = topSources[i];
            var color = s.scope === 'Scope 1' ? '#10b981' : s.scope === 'Scope 2' ? '#3b82f6' : '#8b5cf6';
            html += '<div style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid hsl(var(--border));">' +
                '<div style="width:4px;height:24px;border-radius:4px;background:' + color + ';"></div>' +
                '<div style="flex:1;">' +
                '<div style="font-size:13px;font-weight:500;color:hsl(var(--foreground));">' + s.name + '</div>' +
                '<div style="font-size:11px;color:hsl(var(--muted-foreground));">' + s.scope + '</div>' +
                '</div>' +
                '<div style="text-align:right;">' +
                '<div style="font-size:13px;font-weight:600;color:hsl(var(--foreground));">' + s.emissions.toFixed(1) + ' t</div>' +
                '<div style="font-size:11px;color:hsl(var(--muted-foreground));">' + s.pct + '%</div>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    function renderEmissionsByType() {
        var container = document.getElementById('emissionsByType');
        if (!container) return;
        
        var types = [
            { name: 'Fuel', value: 45, color: '#10b981' },
            { name: 'Electricity', value: 30, color: '#3b82f6' },
            { name: 'Natural Gas', value: 15, color: '#f59e0b' },
            { name: 'Business Travel', value: 7, color: '#8b5cf6' },
            { name: 'Waste', value: 3, color: '#ec4899' }
        ];

        var html = '';
        for (var i = 0; i < types.length; i++) {
            var t = types[i];
            html += '<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">' +
                '<div style="width:12px;height:12px;border-radius:3px;background:' + t.color + ';"></div>' +
                '<div style="flex:1;font-size:13px;color:hsl(var(--foreground));">' + t.name + '</div>' +
                '<div style="font-size:13px;font-weight:600;color:hsl(var(--foreground));">' + t.value + '%</div>' +
                '<div style="width:60px;height:4px;background:hsl(var(--muted));border-radius:4px;overflow:hidden;">' +
                '<div style="width:' + t.value + '%;height:100%;background:' + t.color + ';border-radius:4px;"></div>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    // ============================================
    // SCOPE ANALYSIS
    // ============================================

    function renderScope() {
        var data = monthlyData[currentYear] || monthlyData['2025'];
        var totalS1 = 0, totalS2 = 0, totalS3 = 0;
        for (var i = 0; i < data.scope1.length; i++) {
            totalS1 += data.scope1[i];
            totalS2 += data.scope2[i];
            totalS3 += data.scope3[i];
        }
        var total = totalS1 + totalS2 + totalS3;

        var container = document.getElementById('scopeBreakdown');
        if (!container) return;
        
        var breakdown = [
            { name: 'Scope 1', value: totalS1, pct: (totalS1 / total) * 100, color: '#10b981' },
            { name: 'Scope 2', value: totalS2, pct: (totalS2 / total) * 100, color: '#3b82f6' },
            { name: 'Scope 3', value: totalS3, pct: (totalS3 / total) * 100, color: '#8b5cf6' }
        ];

        var html = '';
        for (var i = 0; i < breakdown.length; i++) {
            var s = breakdown[i];
            html += '<div style="padding:8px 0;border-bottom:1px solid hsl(var(--border));">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;">' +
                '<div>' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                '<div style="width:12px;height:12px;border-radius:3px;background:' + s.color + ';"></div>' +
                '<span style="font-weight:600;color:hsl(var(--foreground));">' + s.name + '</span>' +
                '</div>' +
                '<div style="font-size:12px;color:hsl(var(--muted-foreground));margin-top:2px;">' + s.value.toFixed(1) + ' tCO₂e</div>' +
                '</div>' +
                '<div style="text-align:right;">' +
                '<div style="font-size:16px;font-weight:700;color:hsl(var(--foreground));">' + s.pct.toFixed(1) + '%</div>' +
                '<div style="width:100px;height:4px;background:hsl(var(--muted));border-radius:4px;overflow:hidden;margin-top:4px;">' +
                '<div style="width:' + s.pct + '%;height:100%;background:' + s.color + ';border-radius:4px;"></div>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderScopeTable();
    }

    function renderScopeTable() {
        var container = document.getElementById('scopeTable');
        if (!container) return;
        
        var data = monthlyData[currentYear] || monthlyData['2025'];
        var months = data.months;

        var html = '<table><thead><tr><th>Month</th><th>Scope 1 (tCO₂e)</th><th>Scope 2 (tCO₂e)</th><th>Scope 3 (tCO₂e)</th><th>Total (tCO₂e)</th><th>% Change</th></tr></thead><tbody>';
        var prevTotal = 0;
        for (var i = 0; i < months.length; i++) {
            var s1 = data.scope1[i];
            var s2 = data.scope2[i];
            var s3 = data.scope3[i];
            var total = s1 + s2 + s3;
            var change = prevTotal > 0 ? ((total - prevTotal) / prevTotal * 100) : 0;
            var changeClass = change > 0 ? 'negative' : 'positive';
            var changeArrow = change > 0 ? '↑' : '↓';
            prevTotal = total;

            html += '<tr><td><strong>' + months[i] + '</strong></td><td>' + s1.toFixed(1) + '</td><td>' + s2.toFixed(1) + '</td><td>' + s3.toFixed(1) + '</td><td><strong>' + total.toFixed(1) + '</strong></td><td class="' + changeClass + '">' + changeArrow + ' ' + Math.abs(change).toFixed(1) + '%</td></tr>';
        }

        var totalS1 = 0, totalS2 = 0, totalS3 = 0;
        for (var i = 0; i < data.scope1.length; i++) {
            totalS1 += data.scope1[i];
            totalS2 += data.scope2[i];
            totalS3 += data.scope3[i];
        }
        var totalAll = totalS1 + totalS2 + totalS3;

        html += '<tr class="total-row"><td><strong>Total</strong></td><td><strong>' + totalS1.toFixed(1) + '</strong></td><td><strong>' + totalS2.toFixed(1) + '</strong></td><td><strong>' + totalS3.toFixed(1) + '</strong></td><td><strong>' + totalAll.toFixed(1) + '</strong></td><td>—</td></tr>';
        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // ============================================
    // TRENDS
    // ============================================

    function renderTrend() {
        var container = document.getElementById('trendChart');
        if (!container) return;
        
        var years = ['2023', '2024', '2025'];
        var yearData = [];
        for (var y = 0; y < years.length; y++) {
            var d = monthlyData[years[y]];
            var total = 0;
            for (var i = 0; i < d.scope1.length; i++) {
                total += d.scope1[i] + d.scope2[i] + d.scope3[i];
            }
            yearData.push({ year: years[y], total: total });
        }

        var maxVal = 0;
        for (var i = 0; i < yearData.length; i++) {
            if (yearData[i].total > maxVal) maxVal = yearData[i].total;
        }
        maxVal *= 1.2;

        var html = '<div class="chart-bars">';
        for (var i = 0; i < yearData.length; i++) {
            var d = yearData[i];
            var h = (d.total / maxVal) * 100;
            var isProjected = i === 2;
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar total" style="height:' + h + '%;background:' + (isProjected ? '#f59e0b' : '#10b981') + ';border:' + (isProjected ? '2px dashed #f59e0b' : 'none') + ';"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + d.year + '</div>' +
                '<div class="chart-bar-value">' + d.total.toFixed(1) + 't</div>' +
                '</div>';
        }

        var target = yearData[2].total * 0.7;
        var targetH = (target / maxVal) * 100;
        html += '<div class="chart-bar-wrap">' +
            '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
            '<div class="chart-bar" style="height:' + targetH + '%;background:hsl(var(--destructive));opacity:0.7;border:2px dashed hsl(var(--destructive));"></div>' +
            '</div>' +
            '<div class="chart-bar-label">Target</div>' +
            '<div class="chart-bar-value">' + target.toFixed(1) + 't</div>' +
            '</div>';
        html += '</div>';
        container.innerHTML = html;
        renderYoyTable();
    }

    function renderYoyTable() {
        var container = document.getElementById('yoyTable');
        if (!container) return;
        
        var years = ['2023', '2024', '2025'];
        var data = [];
        for (var y = 0; y < years.length; y++) {
            var d = monthlyData[years[y]];
            var s1 = 0, s2 = 0, s3 = 0;
            for (var i = 0; i < d.scope1.length; i++) {
                s1 += d.scope1[i];
                s2 += d.scope2[i];
                s3 += d.scope3[i];
            }
            data.push({ year: years[y], s1: s1, s2: s2, s3: s3, total: s1 + s2 + s3 });
        }

        var html = '<table><thead><tr><th>Year</th><th>Scope 1 (tCO₂e)</th><th>Scope 2 (tCO₂e)</th><th>Scope 3 (tCO₂e)</th><th>Total (tCO₂e)</th><th>YoY Change</th></tr></thead><tbody>';
        var prevTotal = 0;
        for (var i = 0; i < data.length; i++) {
            var d = data[i];
            var change = prevTotal > 0 ? ((d.total - prevTotal) / prevTotal * 100) : 0;
            var changeClass = change > 0 ? 'negative' : 'positive';
            var changeArrow = change > 0 ? '↑' : '↓';
            prevTotal = d.total;

            html += '<tr><td><strong>' + d.year + '</strong></td><td>' + d.s1.toFixed(1) + '</td><td>' + d.s2.toFixed(1) + '</td><td>' + d.s3.toFixed(1) + '</td><td><strong>' + d.total.toFixed(1) + '</strong></td><td class="' + changeClass + '">' + (i > 0 ? changeArrow + ' ' + Math.abs(change).toFixed(1) + '%' : '—') + '</td></tr>';
        }
        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // ============================================
    // FACILITY REPORT
    // ============================================

    function renderFacility() {
        var container = document.getElementById('facilityChart');
        if (!container) return;
        
        var maxVal = 0;
        for (var i = 0; i < facilityData.length; i++) {
            if (facilityData[i].total > maxVal) maxVal = facilityData[i].total;
        }
        maxVal *= 1.2;

        var html = '<div class="chart-bars">';
        for (var i = 0; i < facilityData.length; i++) {
            var f = facilityData[i];
            var h = (f.total / maxVal) * 100;
            var label = f.name.split(' ')[0];
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar" style="height:' + h + '%;background:hsl(var(--primary));"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + label + '</div>' +
                '<div class="chart-bar-value">' + f.total.toFixed(1) + 't</div>' +
                '</div>';
        }
        html += '</div>';
        container.innerHTML = html;
        renderFacilityTable();
    }

    function renderFacilityTable() {
        var container = document.getElementById('facilityTable');
        if (!container) return;
        
        var totalAll = 0;
        for (var i = 0; i < facilityData.length; i++) {
            totalAll += facilityData[i].total;
        }

        var html = '<table><thead><tr><th>Facility</th><th>Scope 1 (tCO₂e)</th><th>Scope 2 (tCO₂e)</th><th>Scope 3 (tCO₂e)</th><th>Total (tCO₂e)</th><th>% of Total</th></tr></thead><tbody>';
        var totalS1 = 0, totalS2 = 0, totalS3 = 0;
        for (var i = 0; i < facilityData.length; i++) {
            var f = facilityData[i];
            var pct = (f.total / totalAll) * 100;
            totalS1 += f.scope1;
            totalS2 += f.scope2;
            totalS3 += f.scope3;
            html += '<tr><td><strong>' + f.name + '</strong></td><td>' + f.scope1.toFixed(1) + '</td><td>' + f.scope2.toFixed(1) + '</td><td>' + f.scope3.toFixed(1) + '</td><td><strong>' + f.total.toFixed(1) + '</strong></td><td>' + pct.toFixed(1) + '%</td></tr>';
        }
        html += '<tr class="total-row"><td><strong>Total</strong></td><td><strong>' + totalS1.toFixed(1) + '</strong></td><td><strong>' + totalS2.toFixed(1) + '</strong></td><td><strong>' + totalS3.toFixed(1) + '</strong></td><td><strong>' + totalAll.toFixed(1) + '</strong></td><td>100%</td></tr>';
        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // ============================================
    // ASSET REPORT
    // ============================================

    function renderAsset() {
        var container = document.getElementById('assetChart');
        if (!container) return;
        
        var maxVal = 0;
        for (var i = 0; i < assetData.length; i++) {
            if (assetData[i].total > maxVal) maxVal = assetData[i].total;
        }
        maxVal *= 1.2;
        var sorted = assetData.slice().sort(function(a, b) { return b.total - a.total; }).slice(0, 8);

        var html = '<div class="chart-bars">';
        for (var i = 0; i < sorted.length; i++) {
            var a = sorted[i];
            var h = (a.total / maxVal) * 100;
            var color = a.type === 'Vehicle' ? '#10b981' : '#3b82f6';
            var label = a.name.split('#')[1] || a.name.split(' ')[0];
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar" style="height:' + h + '%;background:' + color + ';"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + label + '</div>' +
                '<div class="chart-bar-value">' + a.total.toFixed(1) + 't</div>' +
                '</div>';
        }
        html += '</div>';
        container.innerHTML = html;
        renderAssetTable();
    }

    function renderAssetTable() {
        var container = document.getElementById('assetTable');
        if (!container) return;
        
        var html = '<table><thead><tr><th>Asset</th><th>Type</th><th>Scope 1 (tCO₂e)</th><th>Scope 2 (tCO₂e)</th><th>Scope 3 (tCO₂e)</th><th>Total (tCO₂e)</th></tr></thead><tbody>';
        var totalS1 = 0, totalS2 = 0, totalS3 = 0, totalAll = 0;
        for (var i = 0; i < assetData.length; i++) {
            var a = assetData[i];
            totalS1 += a.scope1;
            totalS2 += a.scope2;
            totalS3 += a.scope3;
            totalAll += a.total;
            html += '<tr><td><strong>' + a.name + '</strong></td><td><span class="badge badge-muted">' + a.type + '</span></td><td>' + a.scope1.toFixed(1) + '</td><td>' + a.scope2.toFixed(1) + '</td><td>' + a.scope3.toFixed(1) + '</td><td><strong>' + a.total.toFixed(1) + '</strong></td></tr>';
        }
        html += '<tr class="total-row"><td><strong>Total</strong></td><td>—</td><td><strong>' + totalS1.toFixed(1) + '</strong></td><td><strong>' + totalS2.toFixed(1) + '</strong></td><td><strong>' + totalS3.toFixed(1) + '</strong></td><td><strong>' + totalAll.toFixed(1) + '</strong></td></tr>';
        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // ============================================
    // COMPLIANCE REPORT
    // ============================================

    function renderCompliance() {
        var container = document.getElementById('complianceTable');
        if (!container) return;
        
        var statusMap = {
            'compliant': '<span class="badge badge-success">✅ Compliant</span>',
            'in-progress': '<span class="badge badge-warning">⏳ In Progress</span>',
            'not-started': '<span class="badge badge-muted">📝 Not Started</span>',
            'overdue': '<span class="badge badge-destructive">❌ Overdue</span>'
        };

        var html = '<table><thead><tr><th>Standard</th><th>Status</th><th>Due Date</th><th>Last Reported</th><th>Progress</th><th>Actions</th></tr></thead><tbody>';
        for (var i = 0; i < complianceData.length; i++) {
            var c = complianceData[i];
            var statusBadge = statusMap[c.status] || statusMap['not-started'];
            var progressColor = c.progress >= 80 ? 'hsl(var(--success))' : c.progress >= 50 ? 'hsl(var(--warning))' : 'hsl(var(--destructive))';
            html += '<tr><td><strong>' + c.standard + '</strong></td><td>' + statusBadge + '</td><td>' + c.dueDate + '</td><td>' + c.lastReported + '</td><td>' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                '<span style="font-size:12px;font-weight:600;">' + c.progress + '%</span>' +
                '<div style="width:80px;height:4px;background:hsl(var(--muted));border-radius:4px;overflow:hidden;">' +
                '<div style="width:' + c.progress + '%;height:100%;background:' + progressColor + ';border-radius:4px;"></div>' +
                '</div></div></td>' +
                '<td><button class="btn btn-ghost btn-sm" onclick="showToast(\'📄 Viewing ' + c.standard + ' report\')">👁️</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="showToast(\'📊 Exporting ' + c.standard + ' data\')">📊</button></td></tr>';
        }
        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Emissions Reports Module...');
        
        var chartEl = document.getElementById('overviewChart');
        if (!chartEl) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        renderOverview();
        console.log('✅ Emissions Reports module loaded successfully!');
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

    window.switchReport = switchReport;
    window.setChartView = setChartView;
    window.applyFilters = applyFilters;
    window.resetFilters = resetFilters;
    window.generateReport = generateReport;
    window.exportReport = exportReport;
    window.showToast = showToast;

})(); // <-- End of the IIFE wrapper
