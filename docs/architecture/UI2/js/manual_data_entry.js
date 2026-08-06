// Manual Data Entry Module - SPA Compatible

(function() {

    console.log('📝 Manual Data Entry JS loaded');

    // ============================================
    // MOCK DATA / CONFIG
    // ============================================

    var defraFactors = {
        'Diesel': 2.54,
        'Petrol': 2.16,
        'AdBlue': 0.00,
        'Electricity': 0.20712,
        'Natural Gas': 0.18316,
        'LPG': 1.49,
        'Jet Fuel': 2.50,
        'Marine Diesel': 3.10,
        'Short Haul Flight': 0.155,
        'Long Haul Flight': 0.195,
        'National Rail': 0.035,
        'Hotel Stay': 10.5,
        'Mixed Waste': 0.500,
        'Recycled Waste': 0.200,
        'Custom': 0.000
    };

    var unitMapping = {
        'Diesel': 'L',
        'Petrol': 'L',
        'AdBlue': 'L',
        'Electricity': 'kWh',
        'Natural Gas': 'kWh',
        'LPG': 'L',
        'Jet Fuel': 'L',
        'Marine Diesel': 'L',
        'Short Haul Flight': 'km',
        'Long Haul Flight': 'km',
        'National Rail': 'km',
        'Hotel Stay': 'night',
        'Mixed Waste': 'kg',
        'Recycled Waste': 'kg',
        'Custom': 'kg'
    };

    // ============================================
    // STATE
    // ============================================

    var currentEntryType = 'fuel';
    var entryQueue = [];
    var entryHistory = [];
    var entryIdCounter = 0;
    var toastTimeout = null;

    // ============================================
    // DOM REFS (lazy loaded)
    // ============================================

    function getEl(id) {
        return document.getElementById(id);
    }

    function getAssetSelect() { return getEl('assetSelect'); }
    function getFacilitySelect() { return getEl('facilitySelect'); }
    function getFuelTypeSelect() { return getEl('fuelTypeSelect'); }
    function getScopeSelect() { return getEl('scopeSelect'); }
    function getQuantityInput() { return getEl('quantityInput'); }
    function getDefraFactorSelect() { return getEl('defraFactorSelect'); }
    function getStartDate() { return getEl('startDate'); }
    function getEndDate() { return getEl('endDate'); }
    function getNotesInput() { return getEl('notesInput'); }
    function getDisplayQuantity() { return getEl('displayQuantity'); }
    function getDisplayFactor() { return getEl('displayFactor'); }
    function getDisplayEmissions() { return getEl('displayEmissions'); }
    function getDisplayUnit() { return getEl('displayUnit'); }
    function getUnitHint() { return getEl('unitHint'); }
    function getValidationResults() { return getEl('validationResults'); }
    function getQueueContainer() { return getEl('queueContainer'); }
    function getQueueCount() { return getEl('queueCount'); }
    function getHistoryTableBody() { return getEl('historyTableBody'); }
    function getFormStatus() { return getEl('formStatus'); }
    function getFormTitle() { return getEl('formTitle'); }
    function getFormDescription() { return getEl('formDescription'); }

    // ============================================
    // TOAST (fixed - checks for body)
    // ============================================

    function showToast(message, type) {
        type = type || 'success';
        var icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        // Remove old toast
        var old = document.querySelector('.custom-toast');
        if (old) old.remove();
        
        // Clear any existing timeout
        if (toastTimeout) {
            clearTimeout(toastTimeout);
            toastTimeout = null;
        }
        
        // Check if body exists
        if (!document.body) {
            console.warn('⚠️ Toast: document.body not available, message:', message);
            return;
        }
        
        var el = document.createElement('div');
        el.className = 'custom-toast';
        el.style.cssText = 'position:fixed;bottom:24px;right:24px;background:hsl(var(--card));border:1px solid hsl(var(--border));border-radius:var(--radius);padding:12px 20px;box-shadow:var(--shadow-lg);z-index:99999;font-size:14px;animation:slideUp 0.3s ease;max-width:400px;color:hsl(var(--foreground));display:flex;align-items:center;gap:10px;';
        el.innerHTML = '<span>' + (icons[type] || 'ℹ️') + '</span><span>' + message + '</span>';
        document.body.appendChild(el);
        
        toastTimeout = setTimeout(function() {
            if (el && el.parentNode) {
                el.style.opacity = '0';
                el.style.transition = 'opacity 0.3s';
                setTimeout(function() { 
                    if (el && el.parentNode) el.remove(); 
                }, 300);
            }
            toastTimeout = null;
        }, 3000);
    }

    // ============================================
    // ENTRY TYPE SWITCHER
    // ============================================

    function switchEntryType(type) {
        currentEntryType = type;
        var tabs = document.querySelectorAll('.tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.toggle('active', tabs[i].getAttribute('data-entry-type') === type);
        }

        var configs = {
            'fuel': {
                title: '⛽ Fuel Consumption Entry',
                desc: 'Enter fuel consumption data for vehicles and equipment',
                scope: 'Scope 1',
                unit: 'L',
                fuelOptions: ['Diesel', 'Petrol', 'AdBlue', 'LPG']
            },
            'utility': {
                title: '💡 Utility Consumption Entry',
                desc: 'Enter electricity, gas, and water consumption data',
                scope: 'Scope 2',
                unit: 'kWh',
                fuelOptions: ['Electricity', 'Natural Gas']
            },
            'scope3': {
                title: '🌍 Scope 3 Entry',
                desc: 'Enter supply chain and business travel emissions',
                scope: 'Scope 3',
                unit: 'kgCO₂e',
                fuelOptions: ['Short Haul Flight', 'Long Haul Flight', 'National Rail', 'Hotel Stay', 'Mixed Waste', 'Recycled Waste']
            },
            'manual': {
                title: '📝 Manual Entry',
                desc: 'Custom manual entry with custom values',
                scope: 'Scope 1',
                unit: 'kg',
                fuelOptions: ['Custom']
            }
        };

        var config = configs[type];
        var titleEl = getFormTitle();
        var descEl = getFormDescription();
        var scopeEl = getScopeSelect();
        var fuelEl = getFuelTypeSelect();
        var hintEl = getUnitHint();
        
        if (titleEl) titleEl.textContent = config.title;
        if (descEl) descEl.textContent = config.desc;
        if (scopeEl) scopeEl.value = config.scope;

        // Update fuel options
        if (fuelEl) {
            fuelEl.innerHTML = '<option value="">Select Type...</option>';
            for (var i = 0; i < config.fuelOptions.length; i++) {
                var opt = document.createElement('option');
                opt.value = config.fuelOptions[i];
                opt.textContent = config.fuelOptions[i];
                fuelEl.appendChild(opt);
            }
        }

        if (hintEl) hintEl.textContent = 'Unit: ' + config.unit;

        clearForm();
        // Don't show toast during initialization
        if (document.querySelector('.main-body')) {
            showToast('Switched to ' + config.title, 'info');
        }
    }

    // ============================================
    // CALCULATION ENGINE
    // ============================================

    function calculateEmissions() {
        var fuelType = getFuelTypeSelect();
        var quantityEl = getQuantityInput();
        var defraEl = getDefraFactorSelect();
        
        var fuel = fuelType ? fuelType.value : '';
        var quantity = parseFloat(quantityEl ? quantityEl.value : 0) || 0;

        var factor = parseFloat(defraEl ? defraEl.value : 0) || 0;
        if (!factor && fuel) {
            factor = defraFactors[fuel] || 0;
        }

        var unit = unitMapping[fuel] || 'kg';
        var emissions = quantity * factor;

        var qtyDisplay = getDisplayQuantity();
        var factorDisplay = getDisplayFactor();
        var emDisplay = getDisplayEmissions();
        var unitDisplay = getDisplayUnit();
        
        if (qtyDisplay) qtyDisplay.textContent = quantity.toFixed(2);
        if (factorDisplay) factorDisplay.textContent = factor.toFixed(4);
        if (emDisplay) emDisplay.textContent = emissions.toFixed(2);
        if (unitDisplay) unitDisplay.textContent = unit;

        // Color code emissions
        var emissionEl = getDisplayEmissions();
        if (emissionEl) {
            if (emissions > 1000) {
                emissionEl.className = 'value high';
            } else if (emissions > 100) {
                emissionEl.className = 'value medium';
            } else {
                emissionEl.className = 'value low';
            }
        }

        return { quantity: quantity, factor: factor, emissions: emissions, unit: unit };
    }

    // ============================================
    // VALIDATION
    // ============================================

    function validateEntry() {
        var errors = [];
        var warnings = [];

        var assetEl = getAssetSelect();
        var facilityEl = getFacilitySelect();
        var fuelEl = getFuelTypeSelect();
        var qtyEl = getQuantityInput();
        var startEl = getStartDate();
        var endEl = getEndDate();
        var defraEl = getDefraFactorSelect();

        if (!assetEl || !assetEl.value) errors.push('Asset/Vehicle is required');
        if (!facilityEl || !facilityEl.value) errors.push('Facility/Site is required');
        if (!fuelEl || !fuelEl.value) errors.push('Energy/Fuel Type is required');
        
        var qty = parseFloat(qtyEl ? qtyEl.value : 0) || 0;
        if (!qtyEl || !qtyEl.value || qty <= 0) {
            errors.push('Quantity must be greater than 0');
        }
        
        if (!startEl || !startEl.value) errors.push('Start Date is required');
        if (!endEl || !endEl.value) errors.push('End Date is required');
        if (startEl && endEl && startEl.value && endEl.value && startEl.value > endEl.value) {
            errors.push('Start Date must be before End Date');
        }

        if (qty > 10000) warnings.push('Very high quantity - please verify');
        if (qty > 0 && qty < 0.01) warnings.push('Very small quantity - please verify');

        var factor = parseFloat(defraEl ? defraEl.value : 0) || 0;
        if (factor === 0 && fuelEl && fuelEl.value) {
            warnings.push('DEFRA factor is 0 - emissions will be 0');
        }

        // Display validation results
        var html = '';
        var resultsEl = getValidationResults();
        var statusEl = getFormStatus();
        
        if (errors.length === 0 && warnings.length === 0) {
            html = '<div style="padding:12px;border-radius:var(--radius);background:#dcfce7;border:1px solid #86efac;">' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                '<span style="font-size:18px;">✅</span>' +
                '<div>' +
                '<div style="font-weight:600;color:#166534;">All validations passed!</div>' +
                '<div style="font-size:13px;color:#166534;">Entry is ready for submission.</div>' +
                '</div>' +
                '</div>' +
                '</div>';
            if (statusEl) {
                statusEl.textContent = 'Valid ✅';
                statusEl.className = 'badge badge-success';
            }
        } else {
            var errorHtml = '';
            for (var i = 0; i < errors.length; i++) {
                errorHtml += '<li style="color:hsl(var(--destructive));">❌ ' + errors[i] + '</li>';
            }
            var warningHtml = '';
            for (var j = 0; j < warnings.length; j++) {
                warningHtml += '<li style="color:hsl(var(--warning));">⚠️ ' + warnings[j] + '</li>';
            }

            var hasErrors = errors.length > 0;
            html = '<div style="padding:12px;border-radius:var(--radius);background:' + (hasErrors ? '#fee2e2' : '#fef3c7') + ';border:1px solid ' + (hasErrors ? '#fca5a5' : '#fcd34d') + ';">' +
                '<div style="display:flex;align-items:flex-start;gap:8px;">' +
                '<span style="font-size:18px;">' + (hasErrors ? '❌' : '⚠️') + '</span>' +
                '<div>' +
                '<div style="font-weight:600;color:' + (hasErrors ? '#991b1b' : '#92400e') + ';">' +
                (hasErrors ? 'Validation failed' : 'Validation warnings') +
                '</div>' +
                '<ul style="margin:4px 0 0 20px;font-size:13px;">' +
                errorHtml +
                warningHtml +
                '</ul>' +
                '</div>' +
                '</div>' +
                '</div>';
            
            if (statusEl) {
                statusEl.textContent = hasErrors ? 'Invalid ❌' : 'Warnings ⚠️';
                statusEl.className = hasErrors ? 'badge badge-destructive' : 'badge badge-warning';
            }
        }

        if (resultsEl) resultsEl.innerHTML = html;
        return errors.length === 0;
    }

    // ============================================
    // QUEUE MANAGEMENT
    // ============================================

    function addToQueue() {
        var result = calculateEmissions();
        var validation = validateEntry();

        if (!validation) {
            showToast('⚠️ Please fix validation errors before adding to queue', 'warning');
            return;
        }

        var assetEl = getAssetSelect();
        var facilityEl = getFacilitySelect();
        var fuelEl = getFuelTypeSelect();
        var scopeEl = getScopeSelect();
        var startEl = getStartDate();
        var endEl = getEndDate();
        var notesEl = getNotesInput();

        var entry = {
            id: 'entry_' + (++entryIdCounter),
            asset: assetEl ? assetEl.value : '',
            facility: facilityEl ? facilityEl.value : '',
            fuelType: fuelEl ? fuelEl.value : '',
            scope: scopeEl ? scopeEl.value : '',
            quantity: result.quantity,
            factor: result.factor,
            emissions: result.emissions,
            unit: result.unit,
            startDate: startEl ? startEl.value : '',
            endDate: endEl ? endEl.value : '',
            notes: notesEl ? notesEl.value : '',
            status: 'queued',
            createdAt: new Date().toISOString()
        };

        entryQueue.push(entry);
        renderQueue();
        showToast('📋 Added ' + entry.asset + ' to queue');
        clearForm();
    }

    function renderQueue() {
        var container = getQueueContainer();
        var countEl = getQueueCount();

        if (entryQueue.length === 0) {
            if (container) {
                container.innerHTML = '<div class="text-center text-muted" style="padding:32px;">' +
                    '<div style="font-size:32px;margin-bottom:8px;">📭</div>' +
                    '<div>No entries in queue</div>' +
                    '<div style="font-size:13px;">Add entries using the form above</div>' +
                    '</div>';
            }
            if (countEl) countEl.textContent = '0 entries';
            return;
        }

        var html = '';
        for (var i = 0; i < entryQueue.length; i++) {
            var entry = entryQueue[i];
            html += '<div class="entry-row" style="animation:slideIn 0.3s ease;">' +
                '<div class="entry-field">' +
                '<span class="label">Asset</span>' +
                '<span class="value">' + entry.asset + '</span>' +
                '</div>' +
                '<div class="entry-field">' +
                '<span class="label">Type</span>' +
                '<span class="value">' + entry.fuelType + '</span>' +
                '</div>' +
                '<div class="entry-field">' +
                '<span class="label">Quantity</span>' +
                '<span class="value">' + entry.quantity.toFixed(2) + ' ' + entry.unit + '</span>' +
                '</div>' +
                '<div class="entry-field">' +
                '<span class="label">Emissions</span>' +
                '<span class="value" style="color:hsl(var(--primary));font-weight:700;">' + entry.emissions.toFixed(2) + ' kgCO₂e</span>' +
                '</div>' +
                '<div style="display:flex;gap:4px;">' +
                '<button class="btn btn-ghost btn-sm" onclick="editQueueEntry(' + i + ')" title="Edit">✏️</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="removeQueueEntry(' + i + ')" title="Remove" style="color:hsl(var(--destructive));">✕</button>' +
                '</div>' +
                '</div>';
        }

        if (container) container.innerHTML = html;
        if (countEl) countEl.textContent = entryQueue.length + ' entries';
    }

    function removeQueueEntry(index) {
        var removed = entryQueue.splice(index, 1)[0];
        renderQueue();
        showToast('🗑️ Removed ' + removed.asset + ' from queue');
    }

    function editQueueEntry(index) {
        var entry = entryQueue[index];
        var assetEl = getAssetSelect();
        var facilityEl = getFacilitySelect();
        var fuelEl = getFuelTypeSelect();
        var scopeEl = getScopeSelect();
        var qtyEl = getQuantityInput();
        var startEl = getStartDate();
        var endEl = getEndDate();
        var notesEl = getNotesInput();
        
        if (assetEl) assetEl.value = entry.asset;
        if (facilityEl) facilityEl.value = entry.facility;
        if (fuelEl) fuelEl.value = entry.fuelType;
        if (scopeEl) scopeEl.value = entry.scope;
        if (qtyEl) qtyEl.value = entry.quantity;
        if (startEl) startEl.value = entry.startDate;
        if (endEl) endEl.value = entry.endDate;
        if (notesEl) notesEl.value = entry.notes || '';

        calculateEmissions();
        entryQueue.splice(index, 1);
        renderQueue();
        showToast('✏️ Editing ' + entry.asset, 'info');
        
        var card = document.querySelector('.card');
        if (card) card.scrollIntoView({ behavior: 'smooth' });
    }

    function clearQueue() {
        if (entryQueue.length === 0) return;
        if (confirm('Clear all entries from queue?')) {
            entryQueue = [];
            renderQueue();
            showToast('🗑️ Queue cleared');
        }
    }

    function submitQueue() {
        if (entryQueue.length === 0) {
            showToast('⚠️ No entries to submit', 'warning');
            return;
        }

        for (var i = 0; i < entryQueue.length; i++) {
            var entry = entryQueue[i];
            entry.status = 'submitted';
            entry.submittedAt = new Date().toISOString();
            entryHistory.push({ ...entry });
        }

        var count = entryQueue.length;
        entryQueue = [];
        renderQueue();
        renderHistory();
        showToast('✅ Submitted ' + count + ' entries successfully!');
    }

    // ============================================
    // SUBMIT ENTRY
    // ============================================

    function submitEntry() {
        var validation = validateEntry();
        if (!validation) {
            showToast('⚠️ Please fix validation errors before submitting', 'warning');
            return;
        }

        var result = calculateEmissions();
        
        var assetEl = getAssetSelect();
        var facilityEl = getFacilitySelect();
        var fuelEl = getFuelTypeSelect();
        var scopeEl = getScopeSelect();
        var startEl = getStartDate();
        var endEl = getEndDate();
        var notesEl = getNotesInput();

        var entry = {
            id: 'history_' + (++entryIdCounter),
            asset: assetEl ? assetEl.value : '',
            facility: facilityEl ? facilityEl.value : '',
            fuelType: fuelEl ? fuelEl.value : '',
            scope: scopeEl ? scopeEl.value : '',
            quantity: result.quantity,
            factor: result.factor,
            emissions: result.emissions,
            unit: result.unit,
            startDate: startEl ? startEl.value : '',
            endDate: endEl ? endEl.value : '',
            notes: notesEl ? notesEl.value : '',
            status: 'submitted',
            submittedAt: new Date().toISOString()
        };

        entryHistory.push(entry);
        renderHistory();
        showToast('✅ Entry saved successfully! ' + result.emissions.toFixed(2) + ' kgCO₂e');
        clearForm();
    }

    // ============================================
    // HISTORY
    // ============================================

    function renderHistory() {
        var tbody = getHistoryTableBody();
        if (!tbody) return;

        if (entryHistory.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted" style="padding:32px;">' +
                '<div style="font-size:32px;margin-bottom:8px;">📭</div>' +
                '<div>No entries yet</div>' +
                '<div style="font-size:13px;">Start adding manual entries</div>' +
                '</td></tr>';
            return;
        }

        var html = '';
        for (var i = entryHistory.length - 1; i >= 0; i--) {
            var entry = entryHistory[i];
            html += '<tr>' +
                '<td style="font-size:12px;">' + (entry.submittedAt ? new Date(entry.submittedAt).toLocaleDateString() : 'N/A') + '</td>' +
                '<td><strong>' + entry.asset + '</strong></td>' +
                '<td><span class="badge badge-muted">' + entry.fuelType + '</span></td>' +
                '<td>' + entry.quantity.toFixed(2) + ' ' + entry.unit + '</td>' +
                '<td style="font-weight:600;color:hsl(var(--primary));">' + entry.emissions.toFixed(2) + ' kgCO₂e</td>' +
                '<td><span class="badge badge-primary">' + entry.scope + '</span></td>' +
                '<td><span class="badge badge-success">✅ Submitted</span></td>' +
                '<td>' +
                '<button class="btn btn-ghost btn-sm" onclick="viewEntry(\'' + entry.id + '\')" title="View">👁️</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="deleteEntry(\'' + entry.id + '\')" title="Delete" style="color:hsl(var(--destructive));">✕</button>' +
                '</td>' +
                '</tr>';
        }
        tbody.innerHTML = html;
    }

    function viewEntry(id) {
        for (var i = 0; i < entryHistory.length; i++) {
            if (entryHistory[i].id === id) {
                var entry = entryHistory[i];
                showToast('📄 ' + entry.asset + ': ' + entry.emissions.toFixed(2) + ' kgCO₂e (' + entry.fuelType + ')');
                return;
            }
        }
    }

    function deleteEntry(id) {
        if (confirm('Delete this entry?')) {
            var newHistory = [];
            for (var i = 0; i < entryHistory.length; i++) {
                if (entryHistory[i].id !== id) {
                    newHistory.push(entryHistory[i]);
                }
            }
            entryHistory = newHistory;
            renderHistory();
            showToast('🗑️ Entry deleted');
        }
    }

    function refreshHistory() {
        renderHistory();
        showToast('🔄 History refreshed');
    }

    // ============================================
    // FORM HELPERS
    // ============================================

    function clearForm() {
        var fuelEl = getFuelTypeSelect();
        var qtyEl = getQuantityInput();
        var defraEl = getDefraFactorSelect();
        var notesEl = getNotesInput();
        var qtyDisplay = getDisplayQuantity();
        var factorDisplay = getDisplayFactor();
        var emDisplay = getDisplayEmissions();
        var resultsEl = getValidationResults();
        var statusEl = getFormStatus();
        
        if (fuelEl) fuelEl.value = '';
        if (qtyEl) qtyEl.value = '';
        if (defraEl) defraEl.value = '';
        if (notesEl) notesEl.value = '';
        if (qtyDisplay) qtyDisplay.textContent = '0.00';
        if (factorDisplay) factorDisplay.textContent = '0.00';
        if (emDisplay) emDisplay.textContent = '0.00';
        if (resultsEl) resultsEl.innerHTML = '';
        if (statusEl) {
            statusEl.textContent = 'Ready';
            statusEl.className = 'badge badge-success';
        }
        calculateEmissions();
    }

    function loadMockEntry() {
        var mockEntries = [{
            asset: 'Fleet_001',
            facility: 'London_Office',
            fuelType: 'Diesel',
            scope: 'Scope 1',
            quantity: 245.5,
            startDate: '2026-12-01',
            endDate: '2026-12-31',
            notes: 'Q4 fleet fuel consumption'
        }, {
            asset: 'Building_A',
            facility: 'London_Office',
            fuelType: 'Electricity',
            scope: 'Scope 2',
            quantity: 4520,
            startDate: '2026-12-01',
            endDate: '2026-12-31',
            notes: 'December electricity usage'
        }, {
            asset: 'Data_Center',
            facility: 'Data_Center',
            fuelType: 'Natural Gas',
            scope: 'Scope 2',
            quantity: 1800,
            startDate: '2026-12-01',
            endDate: '2026-12-31',
            notes: 'Data center heating'
        }];

        var mock = mockEntries[Math.floor(Math.random() * mockEntries.length)];
        var assetEl = getAssetSelect();
        var facilityEl = getFacilitySelect();
        var fuelEl = getFuelTypeSelect();
        var scopeEl = getScopeSelect();
        var qtyEl = getQuantityInput();
        var startEl = getStartDate();
        var endEl = getEndDate();
        var notesEl = getNotesInput();
        var defraEl = getDefraFactorSelect();
        
        if (assetEl) assetEl.value = mock.asset;
        if (facilityEl) facilityEl.value = mock.facility;
        if (fuelEl) fuelEl.value = mock.fuelType;
        if (scopeEl) scopeEl.value = mock.scope;
        if (qtyEl) qtyEl.value = mock.quantity;
        if (startEl) startEl.value = mock.startDate;
        if (endEl) endEl.value = mock.endDate;
        if (notesEl) notesEl.value = mock.notes;

        var factor = defraFactors[mock.fuelType] || 0;
        if (defraEl) {
            var options = defraEl.options;
            for (var i = 0; i < options.length; i++) {
                if (parseFloat(options[i].value) === factor) {
                    defraEl.selectedIndex = i;
                    break;
                }
            }
        }

        calculateEmissions();
        validateEntry();
        showToast('🧪 Loaded mock entry: ' + mock.asset + ' (' + mock.fuelType + ')');
    }

    // ============================================
    // MAKE FUNCTIONS GLOBAL
    // ============================================

    window.switchEntryType = switchEntryType;
    window.calculateEmissions = calculateEmissions;
    window.validateEntry = validateEntry;
    window.addToQueue = addToQueue;
    window.renderQueue = renderQueue;
    window.removeQueueEntry = removeQueueEntry;
    window.editQueueEntry = editQueueEntry;
    window.clearQueue = clearQueue;
    window.submitQueue = submitQueue;
    window.submitEntry = submitEntry;
    window.renderHistory = renderHistory;
    window.viewEntry = viewEntry;
    window.deleteEntry = deleteEntry;
    window.refreshHistory = refreshHistory;
    window.clearForm = clearForm;
    window.loadMockEntry = loadMockEntry;
    window.showToast = showToast;

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Manual Data Entry Module...');
        
        // Check if main elements exist
        var tbody = getHistoryTableBody();
        if (!tbody) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Set default dates
        var today = new Date();
        var firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        var lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        
        var startEl = getStartDate();
        var endEl = getEndDate();
        if (startEl) startEl.value = firstDay.toISOString().split('T')[0];
        if (endEl) endEl.value = lastDay.toISOString().split('T')[0];

        // Initialize with fuel type
        switchEntryType('fuel');

        // Load sample history
        var sampleHistory = [
            { id: 'h1', asset: 'Fleet_001', facility: 'London_Office', fuelType: 'Diesel', scope: 'Scope 1',
                quantity: 245.5, factor: 2.54, emissions: 623.57, unit: 'L', startDate: '2026-11-01',
                endDate: '2026-11-30', notes: 'November fleet data', status: 'submitted',
                submittedAt: '2026-12-01T10:30:00' },
            { id: 'h2', asset: 'Building_A', facility: 'London_Office', fuelType: 'Electricity', scope: 'Scope 2',
                quantity: 4520, factor: 0.207, emissions: 935.64, unit: 'kWh', startDate: '2026-11-01',
                endDate: '2026-11-30', notes: 'November electricity', status: 'submitted',
                submittedAt: '2026-12-02T14:20:00' },
            { id: 'h3', asset: 'Data_Center', facility: 'Data_Center', fuelType: 'Natural Gas', scope: 'Scope 2',
                quantity: 1800, factor: 0.183, emissions: 329.4, unit: 'kWh', startDate: '2026-11-01',
                endDate: '2026-11-30', notes: 'Data center heating', status: 'submitted',
                submittedAt: '2026-12-03T09:15:00' }
        ];
        entryHistory = sampleHistory;
        renderHistory();

        // Auto-calculate on input change
        var inputs = [getQuantityInput(), getFuelTypeSelect(), getDefraFactorSelect()];
        for (var i = 0; i < inputs.length; i++) {
            if (inputs[i]) {
                inputs[i].addEventListener('change', calculateEmissions);
                inputs[i].addEventListener('input', calculateEmissions);
            }
        }

        // Keyboard shortcut: Ctrl+Enter to submit
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                submitEntry();
            }
        });

        console.log('✅ Manual Data Entry module loaded successfully!');
        console.log('📝 4 entry types available');
        console.log('⌨️  Ctrl+Enter to submit');
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
})(); 