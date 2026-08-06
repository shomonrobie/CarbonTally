// Organization Metadata Module - SPA Compatible
(function(){
    console.log('📋 Organization Metadata JS loaded');

    // ============================================
    // MOCK DATA - Custom Metrics
    // ============================================

    var customMetrics = [
        { name: 'Customer Satisfaction', value: '92%' },
        { name: 'Employee Engagement', value: '88%' },
        { name: 'Carbon Intensity', value: '0.45 tCO₂e/employee' },
        { name: 'Water Usage', value: '2,500 m³/year' },
        { name: 'Waste Diversion Rate', value: '68%' }
    ];

    // ============================================
    // STATE
    // ============================================

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
    // METADATA FUNCTIONS
    // ============================================

    function getInputValue(id) {
        var el = getEl(id);
        return el ? el.value : 0;
    }

    function getSelectValue(id) {
        var el = getEl(id);
        return el ? el.value : '';
    }

    function renderSummaryMetrics() {
        var container = getEl('summaryMetrics');
        if (!container) return;
        
        var employees = parseFloat(getInputValue('totalEmployees')) || 0;
        var revenue = parseFloat(getInputValue('annualRevenue')) || 0;
        var facilities = parseFloat(getInputValue('totalFacilities')) || 0;
        var renewable = parseFloat(getInputValue('renewableEnergy')) || 0;

        container.innerHTML =
            '<div class="metric-card"><div class="value">' + Number(employees).toLocaleString() + '</div><div class="label">👥 Total Employees</div><div class="trend up">↑ 8.5% YoY</div></div>' +
            '<div class="metric-card"><div class="value">£' + Number(revenue).toLocaleString() + '</div><div class="label">💰 Annual Revenue</div><div class="trend up">↑ 12.3% YoY</div></div>' +
            '<div class="metric-card"><div class="value">' + Number(facilities).toLocaleString() + '</div><div class="label">🏢 Total Facilities</div><div class="trend neutral">— No change</div></div>' +
            '<div class="metric-card"><div class="value">' + Number(renewable).toFixed(1) + '%</div><div class="label">🌱 Renewable Energy</div><div class="trend up">↑ 5.2% YoY</div></div>' +
            '<div class="metric-card"><div class="value">34%</div><div class="label">🎯 Net Zero Progress</div><div class="trend up">↑ 6% YoY</div></div>' +
            '<div class="metric-card"><div class="value">' + customMetrics.length + '</div><div class="label">📌 Custom Metrics</div><div class="trend neutral">— ' + customMetrics.filter(function(m) { return m.value; }).length + ' active</div></div>';
    }

    function renderCustomMetrics() {
        var container = getEl('customMetricsList');
        if (!container) return;
        
        if (customMetrics.length === 0) {
            container.innerHTML = '<div class="text-muted" style="text-align:center;padding:16px;font-size:13px;">No custom metrics added yet</div>';
            return;
        }

        var html = '';
        for (var i = 0; i < customMetrics.length; i++) {
            var metric = customMetrics[i];
            html +=
                '<div class="custom-metric-item">' +
                '<span class="label">' + metric.name + '</span>' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                '<span class="value">' + metric.value + '</span>' +
                '<button class="btn btn-ghost btn-sm" onclick="removeCustomMetric(' + i + ')" style="color:hsl(var(--destructive));padding:2px 6px;font-size:12px;">✕</button>' +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    function addCustomMetric() {
        var nameInput = getEl('customMetricName');
        var valueInput = getEl('customMetricValue');

        var name = nameInput ? nameInput.value.trim() : '';
        var value = valueInput ? valueInput.value.trim() : '';

        if (!name) {
            showToast('⚠️ Please enter a metric name', 'warning');
            if (nameInput) nameInput.focus();
            return;
        }

        if (!value) {
            showToast('⚠️ Please enter a metric value', 'warning');
            if (valueInput) valueInput.focus();
            return;
        }

        customMetrics.push({ name: name, value: value });
        if (nameInput) nameInput.value = '';
        if (valueInput) valueInput.value = '';
        renderCustomMetrics();
        renderSummaryMetrics();
        showToast('✅ Added custom metric: ' + name);
    }

    function removeCustomMetric(index) {
        var removed = customMetrics.splice(index, 1)[0];
        renderCustomMetrics();
        renderSummaryMetrics();
        showToast('🗑️ Removed custom metric: ' + removed.name);
    }

    function saveMetadata() {
        var metadata = {
            total_employees: getInputValue('totalEmployees'),
            full_time_employees: getInputValue('fullTimeEmployees'),
            part_time_employees: getInputValue('partTimeEmployees'),
            contract_employees: getInputValue('contractEmployees'),
            average_employees: getInputValue('averageEmployees'),
            annual_revenue: getInputValue('annualRevenue'),
            ebitda: getInputValue('ebitda'),
            total_assets: getInputValue('totalAssets'),
            total_facilities: getInputValue('totalFacilities'),
            total_floor_area_sqft: getInputValue('totalFloorArea'),
            occupied_floor_area_sqft: getInputValue('occupiedFloorArea'),
            renewable_energy_percentage: getInputValue('renewableEnergy'),
            carbon_offset_percentage: getInputValue('carbonOffsets'),
            energy_intensity: getInputValue('energyIntensity'),
            reporting_standard: getSelectValue('reportingStandard'),
            fiscal_year_start: getInputValue('fiscalYearStart'),
            fiscal_year_end: getInputValue('fiscalYearEnd'),
            primary_contact_name: getInputValue('primaryContactName'),
            primary_contact_email: getInputValue('primaryContactEmail'),
            primary_contact_phone: getInputValue('primaryContactPhone'),
            sustainability_officer_name: getInputValue('sustainabilityOfficer'),
            sustainability_officer_email: getInputValue('sustainabilityEmail'),
            industry_sector: getSelectValue('industrySector'),
            naics_code: getInputValue('naicsCode'),
            sic_code: getInputValue('sicCode'),
            custom_metrics: customMetrics
        };

        console.log('📋 Saving metadata:', metadata);
        showToast('💾 Organization metadata saved successfully!');
        renderSummaryMetrics();
    }

    function resetMetadata() {
        if (confirm('Reset all metadata to default values?')) {
            var inputs = document.querySelectorAll('.input, .select');
            for (var i = 0; i < inputs.length; i++) {
                var el = inputs[i];
                if (el.type === 'checkbox') {
                    el.checked = el.defaultChecked;
                } else {
                    el.value = el.defaultValue || '';
                }
            }

            customMetrics = [
                { name: 'Customer Satisfaction', value: '92%' },
                { name: 'Employee Engagement', value: '88%' },
                { name: 'Carbon Intensity', value: '0.45 tCO₂e/employee' },
                { name: 'Water Usage', value: '2,500 m³/year' },
                { name: 'Waste Diversion Rate', value: '68%' }
            ];

            renderCustomMetrics();
            renderSummaryMetrics();
            showToast('↺ Metadata reset to defaults');
        }
    }

    // ============================================
    // SEARCH FUNCTION
    // ============================================

    function setupSearch() {
        var searchEl = getEl('searchInput');
        if (!searchEl) return;
        
        searchEl.addEventListener('input', function() {
            var query = this.value.toLowerCase().trim();
            if (!query) {
                var sections = document.querySelectorAll('.metadata-section');
                for (var i = 0; i < sections.length; i++) {
                    sections[i].style.display = '';
                }
                return;
            }

            var sections = document.querySelectorAll('.metadata-section');
            for (var i = 0; i < sections.length; i++) {
                var text = sections[i].textContent.toLowerCase();
                sections[i].style.display = text.indexOf(query) !== -1 ? '' : 'none';
            }
        });
    }

    // ============================================
    // AUTO-UPDATE SUMMARY
    // ============================================

    function setupAutoUpdate() {
        var inputs = document.querySelectorAll('.input, .select');
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].addEventListener('change', renderSummaryMetrics);
            inputs[i].addEventListener('input', renderSummaryMetrics);
        }
    }

    // ============================================
    // KEYBOARD SHORTCUTS
    // ============================================

    function setupKeyboardShortcuts() {
        // Ctrl+S to save
        document.addEventListener('keydown', function(e) {
            if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                saveMetadata();
            }
        });

        // Enter key to add custom metric
        var valueInput = getEl('customMetricValue');
        var nameInput = getEl('customMetricName');
        
        if (valueInput) {
            valueInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    addCustomMetric();
                }
            });
        }
        
        if (nameInput) {
            nameInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var valueEl = getEl('customMetricValue');
                    if (valueEl) valueEl.focus();
                }
            });
        }
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Organization Metadata Module...');
        
        var container = getEl('summaryMetrics');
        if (!container) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Render initial data
        renderCustomMetrics();
        renderSummaryMetrics();
        
        // Set up event listeners
        setupSearch();
        setupAutoUpdate();
        setupKeyboardShortcuts();
        
        console.log('✅ Organization Metadata module loaded successfully!');
        console.log('📊 25 metadata fields loaded');
        console.log('📌 ' + customMetrics.length + ' custom metrics loaded');
        console.log('⌨️  Ctrl+S to save metadata');
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

    window.renderSummaryMetrics = renderSummaryMetrics;
    window.renderCustomMetrics = renderCustomMetrics;
    window.addCustomMetric = addCustomMetric;
    window.removeCustomMetric = removeCustomMetric;
    window.saveMetadata = saveMetadata;
    window.resetMetadata = resetMetadata;
    window.showToast = showToast;
})(); 