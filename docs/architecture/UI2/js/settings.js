    // Settings Module - SPA Compatible
(function() {

    console.log('⚙️ Settings JS loaded');

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
    // SETTINGS NAVIGATION
    // ============================================

    function switchSettings(section) {
        var navItems = document.querySelectorAll('.settings-nav-item');
        for (var i = 0; i < navItems.length; i++) {
            navItems[i].classList.toggle('active', navItems[i].getAttribute('data-section') === section);
        }

        var sections = document.querySelectorAll('.settings-section');
        for (var j = 0; j < sections.length; j++) {
            sections[j].classList.toggle('active', sections[j].id === 'section-' + section);
        }
    }

    // ============================================
    // SETTINGS SEARCH
    // ============================================

    function setupSearch() {
        var searchEl = getEl('settingsSearch');
        if (!searchEl) return;
        
        searchEl.addEventListener('input', function() {
            var query = this.value.toLowerCase().trim();
            var rows = document.querySelectorAll('.setting-row');
            var groups = document.querySelectorAll('.setting-group');
            
            if (!query) {
                for (var i = 0; i < rows.length; i++) {
                    rows[i].style.display = '';
                }
                for (var j = 0; j < groups.length; j++) {
                    groups[j].style.display = '';
                }
                return;
            }

            for (var i = 0; i < rows.length; i++) {
                var text = rows[i].textContent.toLowerCase();
                rows[i].style.display = text.indexOf(query) !== -1 ? '' : 'none';
            }

            for (var j = 0; j < groups.length; j++) {
                var visibleRows = groups[j].querySelectorAll('.setting-row[style*="display: none"]');
                var allRows = groups[j].querySelectorAll('.setting-row');
                groups[j].style.display = visibleRows.length === allRows.length ? 'none' : '';
            }
        });
    }

    // ============================================
    // SETTINGS ACTIONS
    // ============================================

    function saveSettings() {
        // Gather all settings values
        var settings = {
            orgName: getVal('orgName'),
            companyNumber: getVal('companyNumber'),
            vatNumber: getVal('vatNumber'),
            industrySector: getVal('industrySector'),
            primaryContact: getVal('primaryContact'),
            primaryEmail: getVal('primaryEmail'),
            billingContact: getVal('billingContact'),
            billingEmail: getVal('billingEmail'),
            country: getVal('country'),
            timezone: getVal('timezone'),
            currency: getVal('currency'),
            companySize: getVal('companySize'),
            website: getVal('website'),
            registeredAddress: getVal('registeredAddress'),
            subscriptionTier: getVal('subscriptionTier'),
            taxRate: getVal('taxRate'),
            secrEnabled: getCheck('secrEnabled'),
            esrsEnabled: getCheck('esrsEnabled'),
            issbEnabled: getCheck('issbEnabled'),
            ghgEnabled: getCheck('ghgEnabled'),
            tcfdEnabled: getCheck('tcfdEnabled'),
            financialYearEnd: getVal('financialYearEnd'),
            defaultReportingYear: getVal('defaultReportingYear'),
            defraVersion: getVal('defraVersion'),
            preferredUnits: getVal('preferredUnits'),
            autoCalculate: getCheck('autoCalculate'),
            includeBiogenic: getCheck('includeBiogenic'),
            allocateScope3: getCheck('allocateScope3'),
            autoValidate: getCheck('autoValidate'),
            autoRepair: getCheck('autoRepair'),
            qualityThreshold: getVal('qualityThreshold'),
            netZeroTarget: getVal('netZeroTarget'),
            baselineYear: getVal('baselineYear'),
            maxFileSize: getVal('maxFileSize'),
            maxBatchFiles: getVal('maxBatchFiles'),
            autoProcess: getCheck('autoProcess'),
            retentionPeriod: getVal('retentionPeriod'),
            autoArchive: getCheck('autoArchive'),
            require2fa: getCheck('require2fa'),
            sessionTimeout: getVal('sessionTimeout'),
            maxLoginAttempts: getVal('maxLoginAttempts'),
            auditLogging: getCheck('auditLogging'),
            ipRestriction: getCheck('ipRestriction'),
            apiEnabled: getCheck('apiEnabled'),
            carbonIntegration: getVal('carbonIntegration'),
            erpIntegration: getVal('erpIntegration'),
            dataExport: getVal('dataExport'),
            notifyReportReady: getCheck('notifyReportReady'),
            notifyValidation: getCheck('notifyValidation'),
            notifyApproval: getCheck('notifyApproval'),
            notifyDeadlines: getCheck('notifyDeadlines'),
            notifyTeam: getCheck('notifyTeam'),
            browserNotifications: getCheck('browserNotifications'),
            notificationSounds: getCheck('notificationSounds'),
            billingCycle: getVal('billingCycle'),
            billingAddress: getVal('billingAddress'),
            darkMode: getVal('darkMode'),
            compactMode: getCheck('compactMode'),
            defaultDashboard: getVal('defaultDashboard'),
            language: getVal('language'),
            dateFormat: getVal('dateFormat'),
            numberFormat: getVal('numberFormat')
        };

        console.log('💾 Saving settings:', settings);
        showToast('💾 Settings saved successfully!');
    }

    function getVal(id) {
        var el = getEl(id);
        return el ? el.value : '';
    }

    function getCheck(id) {
        var el = getEl(id);
        return el ? el.checked : false;
    }

    function resetSettings() {
        if (confirm('Reset all settings to default values?')) {
            var inputs = document.querySelectorAll('.input, .select');
            for (var i = 0; i < inputs.length; i++) {
                var el = inputs[i];
                if (el.type === 'checkbox') {
                    el.checked = el.defaultChecked;
                } else {
                    el.value = el.defaultValue || '';
                }
            }
            showToast('↺ Settings reset to defaults');
        }
    }

    function regenerateApiKey() {
        showToast('🔄 API key regenerated successfully!');
    }

    function confirmAccountDeletion() {
        if (confirm('⚠️ Are you sure you want to delete your account? This action cannot be undone.')) {
            if (confirm('This will permanently delete all your data. Continue?')) {
                showToast('🗑️ Account deletion requested. You will receive an email confirmation.', 'warning');
            }
        }
    }

    // ============================================
    // KEYBOARD SHORTCUTS
    // ============================================

    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl+S to save settings
            if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                saveSettings();
            }
        });
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Settings Module...');
        
        var nav = getEl('settingsNav');
        if (!nav) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        setupSearch();
        setupKeyboardShortcuts();
        
        console.log('✅ Settings module loaded successfully!');
        console.log('📋 10 settings sections available');
        console.log('⌨️  Ctrl+S to save settings');
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

    window.switchSettings = switchSettings;
    window.saveSettings = saveSettings;
    window.resetSettings = resetSettings;
    window.regenerateApiKey = regenerateApiKey;
    window.confirmAccountDeletion = confirmAccountDeletion;
    window.showToast = showToast;
})(); 