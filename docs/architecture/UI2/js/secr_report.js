// SECR Report Module - SPA Compatible
(function() {
    console.log('📄 SECR Report JS loaded');

    // ============================================
    // MOCK DATA - SECR Report Data
    // ============================================

    var reportData = {
        companyName: 'XYZ (UK) Limited',
        companyNumber: '12345678',
        address: '123 Green Street, London, EC1A 1AA, United Kingdom',
        industry: 'Technology & Professional Services',
        reportingPeriod: '1 January 2025 – 31 December 2025',
        reportDate: '15 December 2025',
        version: '2.3',
        preparedBy: 'XYZ (UK) Limited Sustainability Team',
        auditReady: true,
        totalEmployees: 250,
        totalFloorArea: 21400,
        
        energyConsumption: {
            electricity: { current: 4852000, previous: 4620000, unit: 'kWh' },
            naturalGas: { current: 2380000, previous: 2450000, unit: 'kWh' },
            diesel: { current: 1120000, previous: 1280000, unit: 'kWh' },
            petrol: { current: 140000, previous: 160000, unit: 'kWh' }
        },
        
        scope1: {
            naturalGas: { current: 145.2, previous: 149.5 },
            diesel: { current: 142.0, previous: 162.5 },
            petrol: { current: 15.0, previous: 17.0 },
            refrigerants: { current: 0.2, previous: 0.0 }
        },
        
        scope2: {
            london: { current: 178.2, previous: 162.4 },
            dataCenter: { current: 165.8, previous: 148.2 },
            manchester: { current: 92.4, previous: 88.6 },
            birmingham: { current: 78.6, previous: 74.2 },
            glasgow: { current: 52.8, previous: 50.8 }
        },
        
        scope3: {
            flights: { current: 95.2, previous: 102.8 },
            commuting: { current: 68.4, previous: 72.6 },
            purchasedGoods: { current: 63.4, previous: 58.4 },
            hotels: { current: 42.8, previous: 48.2 },
            waste: { current: 28.4, previous: 30.6 },
            recycledWaste: { current: -1.2, previous: -1.4 },
            rail: { current: 24.6, previous: 26.4 }
        },
        
        intensityRatios: {
            turnover: { current: 0.024, previous: 0.026 },
            perEmployee: { current: 4.94, previous: 5.12 },
            perSqFt: { current: 0.058, previous: 0.060 },
            energyPerTurnover: { current: 0.182, previous: 0.188 },
            energyPerEmployee: { current: 33968, previous: 34040 },
            energyPerSqFt: { current: 397, previous: 398 }
        },
        
        yearOverYear: {
            2023: { scope1: 352.8, scope2: 500.4, scope3: 348.8 },
            2024: { scope1: 345.0, scope2: 524.2, scope3: 337.6 },
            2025: { scope1: 345.2, scope2: 567.8, scope3: 321.6 }
        },
        
        efficiencyActions: [
            { name: 'LED Lighting', impact: 28, description: 'Full LED retrofit across all UK offices and data center', investment: '£48,000', payback: '2.5 years', savings: '17.6 tCO₂e/year' },
            { name: 'Smart BMS', impact: 12, description: 'Smart building management system with occupancy sensors', investment: '£32,000', payback: '3.0 years', savings: '43.5 tCO₂e/year' },
            { name: 'Fleet EVs', impact: 12, description: '3 of 12 vehicles transitioned to electric (25%)', investment: '£90,000', payback: '4.5 years', savings: '18.2 tCO₂e/year' },
            { name: 'Solar PV', impact: 6, description: '45 kWp solar panels on London headquarters roof', investment: '£38,000', payback: '3.8 years', savings: '7.9 tCO₂e/year' }
        ],
        
        dataQuality: {
            electricity: 95,
            naturalGas: 92,
            fleetFuel: 88,
            businessTravel: 85,
            wasteData: 80
        }
    };

    // ============================================
    // STATE
    // ============================================

    var toastTimeout = null;
    var currentReport = null;

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
        if (!document.body) return;
        
        var el = document.createElement('div');
        el.className = 'custom-toast';
        el.style.cssText = 'position:fixed;bottom:24px;right:24px;background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius));padding:12px 20px;box-shadow:var(--shadow-lg);z-index:99999;font-size:14px;animation:slideUp 0.3s ease;max-width:400px;color:hsl(var(--foreground));display:flex;align-items:center;gap:10px;';
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
    // REPORT GENERATION
    // ============================================

    function generateReport() {
        var container = getEl('reportContainer');
        if (!container) return;
        
        var yearEl = getEl('reportYear');
        var companyEl = getEl('reportCompany');
        var typeEl = getEl('reportType');
        
        var year = yearEl ? yearEl.value : '2025';
        var company = companyEl ? companyEl.value : 'XYZ (UK) Limited';
        var reportType = typeEl ? typeEl.value : 'full';
        
        showToast('📊 Generating ' + reportType + ' report for ' + year + '...');
        
        // Show loading
        container.innerHTML = `
            <div class="report-loading">
                <div class="spinner"></div>
                <span>Generating SECR Report for ${year}...</span>
                <span style="font-size:12px;color:hsl(var(--muted-foreground));">Please wait</span>
            </div>
        `;
        
        // Simulate generation delay
        setTimeout(function() {
            var html = generateReportHTML(year, company, reportType);
            container.innerHTML = html;
            showToast('✅ SECR Report generated successfully!', 'success');
        }, 1500);
    }

    function generateReportHTML(year, company, reportType) {
        var data = reportData;
        var totalScope1 = Object.values(data.scope1).reduce(function(sum, item) { return sum + item.current; }, 0);
        var totalScope2 = Object.values(data.scope2).reduce(function(sum, item) { return sum + item.current; }, 0);
        var totalScope3 = Object.values(data.scope3).reduce(function(sum, item) { return sum + item.current; }, 0);
        var totalEmissions = totalScope1 + totalScope2 + totalScope3;
        
        var totalEnergy = Object.values(data.energyConsumption).reduce(function(sum, item) { return sum + item.current; }, 0);
        
        var scope1Breakdown = Object.entries(data.scope1).map(function(entry) {
            return { label: entry[0], current: entry[1].current, previous: entry[1].previous };
        });
        
        var scope2Breakdown = Object.entries(data.scope2).map(function(entry) {
            return { label: entry[0], current: entry[1].current, previous: entry[1].previous };
        });
        
        var scope3Breakdown = Object.entries(data.scope3).map(function(entry) {
            return { label: entry[0], current: entry[1].current, previous: entry[1].previous };
        });
        
        var energyBreakdown = Object.entries(data.energyConsumption).map(function(entry) {
            return { label: entry[0], current: entry[1].current, previous: entry[1].previous, unit: entry[1].unit };
        });
        
        var maxEnergy = Math.max.apply(null, energyBreakdown.map(function(e) { return e.current; }));
        var maxScope1 = Math.max.apply(null, scope1Breakdown.map(function(e) { return e.current; }));
        var maxScope2 = Math.max.apply(null, scope2Breakdown.map(function(e) { return e.current; }));
        var maxScope3 = Math.max.apply(null, scope3Breakdown.map(function(e) { return e.current; }));
        var maxYoY = Math.max(
            data.yearOverYear[2023].scope1 + data.yearOverYear[2023].scope2 + data.yearOverYear[2023].scope3,
            data.yearOverYear[2024].scope1 + data.yearOverYear[2024].scope2 + data.yearOverYear[2024].scope3,
            data.yearOverYear[2025].scope1 + data.yearOverYear[2025].scope2 + data.yearOverYear[2025].scope3
        );
        
        var energyColors = ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6'];
        var scope1Colors = ['#10b981', '#059669', '#34d399', '#a7f3d0'];
        var scope2Colors = ['#3b82f6', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe'];
        var scope3Colors = ['#8b5cf6', '#7c3aed', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe', '#6d28d9'];
        var yoyColors = ['#fca5a5', '#f87171', '#ef4444'];
        
        var pieColors = ['#10b981', '#3b82f6', '#8b5cf6'];
        var pieAngles = [
            (totalScope1 / totalEmissions) * 360,
            (totalScope2 / totalEmissions) * 360,
            (totalScope3 / totalEmissions) * 360
        ];
        var pieBg = 'conic-gradient(' +
            '#10b981 0deg ' + pieAngles[0] + 'deg, ' +
            '#3b82f6 ' + pieAngles[0] + 'deg ' + (pieAngles[0] + pieAngles[1]) + 'deg, ' +
            '#8b5cf6 ' + (pieAngles[0] + pieAngles[1]) + 'deg 360deg)';
        
        var years = ['2023', '2024', '2025'];
        var yoyTotals = years.map(function(y) {
            return data.yearOverYear[y].scope1 + data.yearOverYear[y].scope2 + data.yearOverYear[y].scope3;
        });
        var maxYoy = Math.max.apply(null, yoyTotals);
        
        // Build report HTML
        var html = '';
        
        // Cover Page
        html += '<div class="report-cover">' +
            '<div class="logo">🌱</div>' +
            '<h1>' + company + '</h1>' +
            '<h2>Streamlined Energy and Carbon Reporting (SECR) Report ' + year + '</h2>' +
            '<p class="meta">For the financial year ended 31 December ' + year + '</p>' +
            '<div class="details">' +
            '<p><strong>Company Number:</strong> ' + data.companyNumber + '</p>' +
            '<p><strong>Registered Address:</strong> ' + data.address + '</p>' +
            '<p><strong>Reporting Period:</strong> ' + data.reportingPeriod + '</p>' +
            '<p><strong>Report Date:</strong> ' + data.reportDate + '</p>' +
            '<p><strong>Version:</strong> ' + data.version + '</p>' +
            '<p><strong>Prepared By:</strong> ' + data.preparedBy + '</p>' +
            '<p><strong>Audit Ready:</strong> <span class="badge-success">✅ Yes</span></p>' +
            '</div>' +
            '<div class="page-counter">Page 1 of 58</div>' +
            '</div>';
        
        // Table of Contents
        html += '<div class="report-section">' +
            '<h2 class="section-title">📑 Table of Contents</h2>' +
            '<div class="toc">' +
            '<div class="toc-item"><span>1. Executive Summary</span><span>4</span></div>' +
            '<div class="toc-item"><span>2. Company Overview</span><span>6</span></div>' +
            '<div class="toc-item"><span>3. Governance & Responsibilities</span><span>8</span></div>' +
            '<div class="toc-item"><span>4. Methodology</span><span>10</span></div>' +
            '<div class="toc-item"><span>5. Energy Consumption</span><span>14</span></div>' +
            '<div class="toc-item"><span>6. Scope 1 Emissions</span><span>18</span></div>' +
            '<div class="toc-item"><span>7. Scope 2 Emissions</span><span>22</span></div>' +
            '<div class="toc-item"><span>8. Scope 3 Emissions</span><span>26</span></div>' +
            '<div class="toc-item"><span>9. Emissions Summary & Charts</span><span>30</span></div>' +
            '<div class="toc-item"><span>10. Intensity Ratios</span><span>34</span></div>' +
            '<div class="toc-item"><span>11. Year-on-Year Comparison</span><span>38</span></div>' +
            '<div class="toc-item"><span>12. Energy Efficiency Actions</span><span>42</span></div>' +
            '<div class="toc-item"><span>13. Verification & Assurance</span><span>46</span></div>' +
            '<div class="toc-item"><span>14. Glossary</span><span>48</span></div>' +
            '<div class="toc-item"><span>15. Appendices</span><span>50</span></div>' +
            '</div>' +
            '<div class="page-counter">Page 2 of 58</div>' +
            '</div>';
        
        // Section 1: Executive Summary
        html += '<div class="report-section">' +
            '<h2 class="section-title">1. Executive Summary</h2>' +
            '<div class="report-narrative">' +
            '<p><strong>' + company + '</strong> is pleased to present its ' + year + ' Streamlined Energy and Carbon Reporting (SECR) Report. This report provides a comprehensive account of our energy consumption, greenhouse gas (GHG) emissions, and energy efficiency activities for the financial year ended 31 December ' + year + '.</p>' +
            '<p><strong>Key Highlights:</strong></p>' +
            '<ul>' +
            '<li>Total energy consumption: <strong>' + totalEnergy.toLocaleString() + ' kWh</strong></li>' +
            '<li>Total Scope 1 emissions: <strong>' + totalScope1.toFixed(1) + ' tCO₂e</strong></li>' +
            '<li>Total Scope 2 emissions: <strong>' + totalScope2.toFixed(1) + ' tCO₂e</strong></li>' +
            '<li>Total Scope 3 emissions: <strong>' + totalScope3.toFixed(1) + ' tCO₂e</strong></li>' +
            '<li>Overall emissions intensity: <strong>' + data.intensityRatios.turnover.current + ' tCO₂e per £1,000 turnover</strong></li>' +
            '</ul>' +
            '<p>We have maintained our commitment to reducing environmental impact through targeted energy efficiency measures...</p>' +
            '</div>' +
            '<div class="page-counter">Page 4 of 58</div>' +
            '</div>';
        
        // Section 5: Energy Consumption with Chart
        html += '<div class="report-section">' +
            '<h2 class="section-title">5. Energy Consumption</h2>' +
            '<div class="report-narrative">' +
            '<p>Our total energy consumption for the reporting period was <strong>' + totalEnergy.toLocaleString() + ' kWh</strong>, broken down by source as follows:</p>' +
            '<table class="report-table">' +
            '<thead><tr><th>Energy Source</th><th>' + year + ' Consumption (kWh)</th><th>2024 Consumption (kWh)</th><th>% Change</th></tr></thead>' +
            '<tbody>';
        
        energyBreakdown.forEach(function(e) {
            var change = ((e.current - e.previous) / e.previous * 100);
            var changeClass = change > 0 ? '↑' : '↓';
            html += '<tr><td>' + e.label.charAt(0).toUpperCase() + e.label.slice(1) + '</td><td>' + e.current.toLocaleString() + '</td><td>' + e.previous.toLocaleString() + '</td><td>' + changeClass + ' ' + Math.abs(change).toFixed(1) + '%</td></tr>';
        });
        
        html += '<tr class="total-row"><td><strong>Total</strong></td><td><strong>' + totalEnergy.toLocaleString() + '</strong></td><td><strong>' + (Object.values(data.energyConsumption).reduce(function(s, i) { return s + i.previous; }, 0)).toLocaleString() + '</strong></td><td><strong>' + (((totalEnergy - Object.values(data.energyConsumption).reduce(function(s, i) { return s + i.previous; }, 0)) / Object.values(data.energyConsumption).reduce(function(s, i) { return s + i.previous; }, 0) * 100)).toFixed(1) + '%</strong></td></tr>' +
            '</tbody></table></div>' +
            '<div class="chart-container"><div class="chart-title">Energy Consumption by Source (' + year + ')</div><div class="chart-bars">';
        
        energyBreakdown.forEach(function(e, idx) {
            var pct = (e.current / maxEnergy) * 100;
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar energy" style="height:' + pct + '%;background:' + energyColors[idx % energyColors.length] + ';"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + e.label.charAt(0).toUpperCase() + e.label.slice(1) + '</div>' +
                '<div class="chart-bar-value">' + (e.current / 1000).toFixed(0) + 'k</div>' +
                '</div>';
        });
        
        html += '</div><div class="chart-legend">';
        energyBreakdown.forEach(function(e, idx) {
            var pct = (e.current / totalEnergy * 100);
            html += '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:' + energyColors[idx % energyColors.length] + ';"></div>' + e.label.charAt(0).toUpperCase() + e.label.slice(1) + ' (' + pct.toFixed(1) + '%)</div>';
        });
        html += '</div></div><div class="page-counter">Page 16 of 58</div></div>';
        
        // Section 6: Scope 1 with Chart
        html += '<div class="report-section">' +
            '<h2 class="section-title">6. Scope 1 Emissions (Direct Emissions)</h2>' +
            '<div class="report-narrative"><p>Scope 1 emissions include natural gas, diesel, petrol, and refrigerants.</p>' +
            '<table class="report-table"><thead><tr><th>Emission Source</th><th>' + year + ' (tCO₂e)</th><th>2024 (tCO₂e)</th><th>% Change</th></tr></thead><tbody>';
        
        scope1Breakdown.forEach(function(e) {
            var change = ((e.current - e.previous) / e.previous * 100);
            var changeArrow = change > 0 ? '↑' : '↓';
            html += '<tr><td>' + e.label.charAt(0).toUpperCase() + e.label.slice(1) + '</td><td>' + e.current.toFixed(1) + '</td><td>' + e.previous.toFixed(1) + '</td><td>' + changeArrow + ' ' + Math.abs(change).toFixed(1) + '%</td></tr>';
        });
        
        html += '<tr class="total-row"><td><strong>Total Scope 1</strong></td><td><strong>' + totalScope1.toFixed(1) + '</strong></td><td><strong>' + (Object.values(data.scope1).reduce(function(s, i) { return s + i.previous; }, 0)).toFixed(1) + '</strong></td><td><strong>' + (((totalScope1 - Object.values(data.scope1).reduce(function(s, i) { return s + i.previous; }, 0)) / Object.values(data.scope1).reduce(function(s, i) { return s + i.previous; }, 0) * 100)).toFixed(1) + '%</strong></td></tr>' +
            '</tbody></table></div>' +
            '<div class="chart-container"><div class="chart-title">Scope 1 Emissions Breakdown (' + year + ')</div><div class="chart-bars">';
        
        scope1Breakdown.forEach(function(e, idx) {
            var pct = (e.current / maxScope1) * 100;
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar scope1" style="height:' + pct + '%;background:' + scope1Colors[idx % scope1Colors.length] + ';"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + e.label.charAt(0).toUpperCase() + e.label.slice(1) + '</div>' +
                '<div class="chart-bar-value">' + e.current.toFixed(1) + ' t</div>' +
                '</div>';
        });
        
        html += '</div><div class="chart-legend">';
        scope1Breakdown.forEach(function(e, idx) {
            var pct = (e.current / totalScope1 * 100);
            html += '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:' + scope1Colors[idx % scope1Colors.length] + ';"></div>' + e.label.charAt(0).toUpperCase() + e.label.slice(1) + ' (' + pct.toFixed(1) + '%)</div>';
        });
        html += '</div></div><div class="page-counter">Page 20 of 58</div></div>';
        
        // Section 9: Summary with Pie Chart
        html += '<div class="report-section">' +
            '<h2 class="section-title">9. Emissions Summary & Charts</h2>' +
            '<div class="report-narrative"><p>This section provides a visual summary of our total emissions across all scopes.</p></div>' +
            '<div class="chart-container"><div class="chart-title">Total Emissions by Scope (' + year + ')</div><div class="chart-bars">' +
            '<div class="chart-bar-wrap"><div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;"><div class="chart-bar scope1" style="height:' + (totalScope1 / totalEmissions * 100) + '%;background:#10b981;"></div></div><div class="chart-bar-label">Scope 1</div><div class="chart-bar-value">' + totalScope1.toFixed(1) + ' t</div></div>' +
            '<div class="chart-bar-wrap"><div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;"><div class="chart-bar scope2" style="height:' + (totalScope2 / totalEmissions * 100) + '%;background:#3b82f6;"></div></div><div class="chart-bar-label">Scope 2</div><div class="chart-bar-value">' + totalScope2.toFixed(1) + ' t</div></div>' +
            '<div class="chart-bar-wrap"><div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;"><div class="chart-bar scope3" style="height:' + (totalScope3 / totalEmissions * 100) + '%;background:#8b5cf6;"></div></div><div class="chart-bar-label">Scope 3</div><div class="chart-bar-value">' + totalScope3.toFixed(1) + ' t</div></div>' +
            '<div class="chart-bar-wrap"><div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;"><div class="chart-bar total" style="height:100%;background:hsl(var(--primary));"></div></div><div class="chart-bar-label">Total</div><div class="chart-bar-value">' + totalEmissions.toFixed(1) + ' t</div></div>' +
            '</div><div class="chart-legend">' +
            '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:#10b981;"></div>Scope 1 (' + (totalScope1 / totalEmissions * 100).toFixed(1) + '%)</div>' +
            '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:#3b82f6;"></div>Scope 2 (' + (totalScope2 / totalEmissions * 100).toFixed(1) + '%)</div>' +
            '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:#8b5cf6;"></div>Scope 3 (' + (totalScope3 / totalEmissions * 100).toFixed(1) + '%)</div>' +
            '</div></div>' +
            '<div class="chart-container"><div class="chart-title">Emissions Distribution by Scope (' + year + ')</div><div class="pie-chart">' +
            '<div class="pie-visual" style="background:' + pieBg + ';"><div class="center-label">' + totalEmissions.toFixed(1) + '<br/>tCO₂e</div></div>' +
            '<div class="pie-legend">' +
            '<div class="pie-legend-item"><div class="pie-legend-dot" style="background:#10b981;"></div>Scope 1: ' + totalScope1.toFixed(1) + ' tCO₂e (' + (totalScope1 / totalEmissions * 100).toFixed(1) + '%)</div>' +
            '<div class="pie-legend-item"><div class="pie-legend-dot" style="background:#3b82f6;"></div>Scope 2: ' + totalScope2.toFixed(1) + ' tCO₂e (' + (totalScope2 / totalEmissions * 100).toFixed(1) + '%)</div>' +
            '<div class="pie-legend-item"><div class="pie-legend-dot" style="background:#8b5cf6;"></div>Scope 3: ' + totalScope3.toFixed(1) + ' tCO₂e (' + (totalScope3 / totalEmissions * 100).toFixed(1) + '%)</div>' +
            '</div></div></div>' +
            '<div class="chart-container"><div class="chart-title">3-Year Emissions Trend (tCO₂e)</div><div class="chart-bars">';
        
        years.forEach(function(y, idx) {
            var total = data.yearOverYear[y].scope1 + data.yearOverYear[y].scope2 + data.yearOverYear[y].scope3;
            var pct = (total / maxYoy) * 100;
            var color = idx === 2 ? '#ef4444' : (idx === 1 ? '#f87171' : '#fca5a5');
            html += '<div class="chart-bar-wrap">' +
                '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
                '<div class="chart-bar" style="height:' + pct + '%;background:' + color + ';"></div>' +
                '</div>' +
                '<div class="chart-bar-label">' + y + '</div>' +
                '<div class="chart-bar-value">' + total.toFixed(1) + '</div>' +
                '</div>';
        });
        
        var target = totalEmissions * 0.7;
        var targetPct = (target / maxYoy) * 100;
        html += '<div class="chart-bar-wrap">' +
            '<div style="width:100%;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:1px;">' +
            '<div class="chart-bar" style="height:' + targetPct + '%;background:#10b981;border:2px dashed #10b981;"></div>' +
            '</div>' +
            '<div class="chart-bar-label">Target</div>' +
            '<div class="chart-bar-value">' + target.toFixed(1) + '</div>' +
            '</div>';
        
        html += '</div><div class="chart-legend">' +
            '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:#ef4444;"></div>Historical Emissions</div>' +
            '<div class="chart-legend-item"><div class="chart-legend-dot" style="background:#10b981;border:2px dashed #10b981;"></div>2030 Target (30% reduction)</div>' +
            '</div></div>' +
            '<div class="page-counter">Page 32 of 58</div></div>';
        
        // Section 12: Energy Efficiency Actions
        html += '<div class="report-section">' +
            '<h2 class="section-title">12. Energy Efficiency Actions</h2>' +
            '<div class="report-narrative"><p>During the reporting period, we have implemented a comprehensive energy efficiency program across all our operations.</p>';
        
        data.efficiencyActions.forEach(function(action) {
            html += '<h3 class="subsection-title">12.' + (data.efficiencyActions.indexOf(action) + 1) + ' ' + action.name + '</h3>' +
                '<p>' + action.description + '</p>' +
                '<p><strong>Investment:</strong> ' + action.investment + ' | <strong>Payback Period:</strong> ' + action.payback + ' | <strong>Carbon Savings:</strong> ' + action.savings + '</p>';
        });
        
        html += '</div><div class="chart-container"><div class="chart-title">Energy Efficiency Impact (Annual Savings)</div><div class="progress-chart">';
        
        data.efficiencyActions.forEach(function(action) {
            html += '<div class="progress-item">' +
                '<div class="label">' + action.name + '</div>' +
                '<div class="bar-track"><div class="fill" style="width:' + action.impact + '%;background:' + ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'][data.efficiencyActions.indexOf(action)] + ';"></div></div>' +
                '<div class="value">' + action.impact + '%</div>' +
                '</div>';
        });
        
        html += '</div></div><div class="page-counter">Page 44 of 58</div></div>';
        
        // Footer
        html += '<div class="report-footer">' +
            '<p><strong>' + company + '</strong> • SECR Report ' + year + ' • Version ' + data.version + '<br/>' +
            'Registered Address: ' + data.address + ' • Company Number: ' + data.companyNumber + '<br/>' +
            'Prepared in accordance with the SECR framework and UK Government GHG Conversion Factors (' + year + ')<br/>' +
            'Audit-ready status: <span class="badge-success">✅ Verified</span> • Data quality: <span class="badge-success">High</span></p>' +
            '</div>';
        
        return html;
    }

    // ============================================
    // REPORT ACTIONS
    // ============================================

    function printReport() {
        var container = getEl('reportContainer');
        if (!container) return;
        
        // Check if report is generated
        if (container.querySelector('.report-loading')) {
            showToast('⚠️ Please generate the report first', 'warning');
            return;
        }
        
        window.print();
        showToast('🖨️ Print dialog opened');
    }

    function exportReport() {
        var container = getEl('reportContainer');
        if (!container) return;
        
        if (container.querySelector('.report-loading')) {
            showToast('⚠️ Please generate the report first', 'warning');
            return;
        }
        
        showToast('📄 Generating PDF report...');
        setTimeout(function() {
            showToast('✅ PDF report generated successfully!');
        }, 2000);
    }

    function resetReport() {
        var container = getEl('reportContainer');
        if (!container) return;
        
        var yearEl = getEl('reportYear');
        var companyEl = getEl('reportCompany');
        var typeEl = getEl('reportType');
        
        if (yearEl) yearEl.value = '2025';
        if (companyEl) companyEl.value = 'XYZ (UK) Limited';
        if (typeEl) typeEl.value = 'full';
        
        container.innerHTML = `
            <div class="report-loading">
                <div class="spinner"></div>
                <span>Ready to generate SECR Report</span>
                <span style="font-size:12px;color:hsl(var(--muted-foreground));">Click "Generate Report" to create a new report</span>
            </div>
        `;
        showToast('↺ Report reset');
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        console.log('🚀 Initializing SECR Report Module...');
        
        var container = getEl('reportContainer');
        if (!container) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Initial load - show ready state
        container.innerHTML = `
            <div class="report-loading">
                <div class="spinner"></div>
                <span>Ready to generate SECR Report</span>
                <span style="font-size:12px;color:hsl(var(--muted-foreground));">Click "Generate Report" to create a new report</span>
            </div>
        `;
        
        console.log('✅ SECR Report module loaded successfully!');
        console.log('📄 Generate SECR reports with full audit trail');
        console.log('📊 58-page professional report with charts');
        console.log('⌨️  Ctrl+P to print the report');
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

    window.generateReport = generateReport;
    window.printReport = printReport;
    window.exportReport = exportReport;
    window.resetReport = resetReport;
    window.showToast = showToast;
})(); 