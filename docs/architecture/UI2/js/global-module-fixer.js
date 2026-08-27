// ============================================
// GLOBAL MODULE FIXER - Standalone Script
// ============================================

(function() {
    'use strict';
    
    console.log('🔧 Global Module Fixer loaded');
    
    var GlobalModuleFixer = {
        enabled: true,
        fixedModules: {},
        fixAttempts: {},
        
        // ============================================
        // MOCK DATA FOR ALL MODULES
        // ============================================
        mockData: {
            // Facilities
            facilities: [
                { id: 'f1', name: 'London Headquarters', type: 'office', location: 'London, UK', city: 'London', country: 'UK', address: '123 Oxford Street', area: 45000, assets: 12, status: 'active', createdAt: '2024-01-15', updatedAt: '2026-01-15' },
                { id: 'f2', name: 'Manchester Distribution Center', type: 'warehouse', location: 'Manchester, UK', city: 'Manchester', country: 'UK', address: '456 Industrial Estate', area: 120000, assets: 8, status: 'active', createdAt: '2024-03-20', updatedAt: '2026-01-14' },
                { id: 'f3', name: 'Berlin Manufacturing Plant', type: 'manufacturing', location: 'Berlin, DE', city: 'Berlin', country: 'DE', address: '789 Production Strasse', area: 85000, assets: 45, status: 'active', createdAt: '2024-06-10', updatedAt: '2026-01-13' },
                { id: 'f4', name: 'Paris Retail Store', type: 'retail', location: 'Paris, FR', city: 'Paris', country: 'FR', address: '321 Champs-Élysées', area: 2500, assets: 3, status: 'active', createdAt: '2024-08-01', updatedAt: '2026-01-12' },
                { id: 'f5', name: 'Amsterdam Data Center', type: 'data_center', location: 'Amsterdam, NL', city: 'Amsterdam', country: 'NL', address: '654 Cloud Boulevard', area: 32000, assets: 78, status: 'active', createdAt: '2024-09-15', updatedAt: '2026-01-11' },
                { id: 'f6', name: 'Birmingham Office', type: 'office', location: 'Birmingham, UK', city: 'Birmingham', country: 'UK', address: '987 Business Park', area: 18000, assets: 6, status: 'maintenance', createdAt: '2024-10-20', updatedAt: '2026-01-10' },
                { id: 'f7', name: 'Madrid Research Lab', type: 'laboratory', location: 'Madrid, ES', city: 'Madrid', country: 'ES', address: '147 Calle de la Ciencia', area: 15000, assets: 34, status: 'active', createdAt: '2024-11-05', updatedAt: '2026-01-09' },
                { id: 'f8', name: 'Milan Warehouse', type: 'warehouse', location: 'Milan, IT', city: 'Milan', country: 'IT', address: '258 Via Logistico', area: 95000, assets: 15, status: 'inactive', createdAt: '2024-12-01', updatedAt: '2025-12-01' },
                { id: 'f9', name: 'Frankfurt Data Center', type: 'data_center', location: 'Frankfurt, DE', city: 'Frankfurt', country: 'DE', address: '369 Server Strasse', area: 28000, assets: 56, status: 'active', createdAt: '2025-01-15', updatedAt: '2026-01-08' },
                { id: 'f10', name: 'Glasgow Office', type: 'office', location: 'Glasgow, UK', city: 'Glasgow', country: 'UK', address: '741 Finance Street', area: 12000, assets: 4, status: 'active', createdAt: '2025-02-20', updatedAt: '2026-01-07' },
                { id: 'f11', name: 'Barcelona Innovation Hub', type: 'office', location: 'Barcelona, ES', city: 'Barcelona', country: 'ES', address: '852 Innovation Avenue', area: 22000, assets: 9, status: 'maintenance', createdAt: '2025-03-10', updatedAt: '2026-01-06' },
                { id: 'f12', name: 'Rotterdam Port Facility', type: 'warehouse', location: 'Rotterdam, NL', city: 'Rotterdam', country: 'NL', address: '963 Harbor Road', area: 150000, assets: 22, status: 'active', createdAt: '2025-04-01', updatedAt: '2026-01-05' },
                { id: 'f13', name: 'Lyon Manufacturing', type: 'manufacturing', location: 'Lyon, FR', city: 'Lyon', country: 'FR', address: '147 Industrial Zone', area: 62000, assets: 38, status: 'active', createdAt: '2025-05-15', updatedAt: '2026-01-04' },
                { id: 'f14', name: 'Dublin Tech Hub', type: 'office', location: 'Dublin, IE', city: 'Dublin', country: 'IE', address: '258 Tech Park', area: 16000, assets: 5, status: 'active', createdAt: '2025-06-20', updatedAt: '2026-01-03' },
                { id: 'f15', name: 'Rome Retail Store', type: 'retail', location: 'Rome, IT', city: 'Rome', country: 'IT', address: '369 Via del Corso', area: 1800, assets: 2, status: 'inactive', createdAt: '2025-07-10', updatedAt: '2025-12-10' }
            ],
            
            // Exports
            exportItems: [
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
            ],
            
            // Extracted Data
            extractedEntries: [
                { id: 'e1', type: 'fuel', data: { fuel_type: 'Diesel', quantity: 12450, unit: 'litres', co2e: 32.4 }, progress: 100, status: 'validated', batch: 'BATCH-2026-01', lastUpdated: '2026-01-15' },
                { id: 'e2', type: 'utility', data: { utility: 'Electricity', consumption: 4500, unit: 'kWh', co2e: 1.8 }, progress: 100, status: 'completed', batch: 'BATCH-2026-01', lastUpdated: '2026-01-14' },
                { id: 'e3', type: 'scope3', data: { category: 'Business Travel', distance: 1200, unit: 'km', co2e: 0.6 }, progress: 45, status: 'in-progress', batch: 'BATCH-2026-02', lastUpdated: '2026-01-13' },
                { id: 'e4', type: 'document', data: { document: 'Invoice #234', amount: 1200, currency: 'GBP' }, progress: 20, status: 'draft', batch: null, lastUpdated: '2026-01-12' },
                { id: 'e5', type: 'fuel', data: { fuel_type: 'Petrol', quantity: 8700, unit: 'litres', co2e: 19.2 }, progress: 100, status: 'validated', batch: 'BATCH-2026-01', lastUpdated: '2026-01-11' },
                { id: 'e6', type: 'utility', data: { utility: 'Natural Gas', consumption: 3200, unit: 'therms', co2e: 16.8 }, progress: 70, status: 'in-progress', batch: 'BATCH-2026-02', lastUpdated: '2026-01-10' },
                { id: 'e7', type: 'scope3', data: { category: 'Purchased Goods', value: 45000, currency: 'GBP', co2e: 8.2 }, progress: 100, status: 'validated', batch: 'BATCH-2026-03', lastUpdated: '2026-01-09' },
                { id: 'e8', type: 'document', data: { document: 'Utility Statement', period: 'Q4 2026' }, progress: 10, status: 'draft', batch: null, lastUpdated: '2026-01-08' },
                { id: 'e9', type: 'fuel', data: { fuel_type: 'Jet Fuel', quantity: 5600, unit: 'litres', co2e: 14.6 }, progress: 100, status: 'completed', batch: 'BATCH-2026-02', lastUpdated: '2026-01-07' },
                { id: 'e10', type: 'utility', data: { utility: 'Water', consumption: 2200, unit: 'm³', co2e: 1.2 }, progress: 60, status: 'in-progress', batch: 'BATCH-2026-03', lastUpdated: '2026-01-06' },
                { id: 'e11', type: 'scope3', data: { category: 'Waste Disposal', tonnes: 12, co2e: 4.5 }, progress: 100, status: 'validated', batch: 'BATCH-2026-01', lastUpdated: '2026-01-05' },
                { id: 'e12', type: 'document', data: { document: 'Fleet Report', vehicle_count: 25 }, progress: 50, status: 'in-progress', batch: 'BATCH-2026-03', lastUpdated: '2026-01-04' }
            ]
        },
        
        // ============================================
        // MODULE CONFIGURATIONS
        // ============================================
        moduleConfigs: {
            'facilities': {
                dataKey: 'facilities',
                filteredKey: 'filteredFacilities',
                containerId: 'facilityTableBody',
                filterFunc: 'applyFilters',
                renderFunc: 'renderTable',
                statsFunc: 'renderStats',
                initFunc: 'initModule',
                needsFiltered: false
            },
            'exports': {
                dataKey: 'exportItems',
                filteredKey: 'filteredExports',
                containerId: 'exportTableBody',
                filterFunc: 'applyFilters',
                renderFunc: 'renderTable',
                statsFunc: 'renderStats',
                initFunc: 'initModule',
                needsFiltered: true
            },
            'extracted': {
                dataKey: 'entries',
                filteredKey: 'filteredEntries',
                containerId: 'dataTableBody',
                filterFunc: 'filterData',
                renderFunc: 'renderTable',
                statsFunc: 'renderStats',
                initFunc: 'initModule',
                needsFiltered: true
            }
        },
        
        // ============================================
        // CORE FIXER FUNCTIONS
        // ============================================
        
        // Fix a specific module
        fixModule: function(moduleId) {
            if (this.fixedModules[moduleId]) {
                console.log('✅ Module already fixed:', moduleId);
                return true;
            }
            
            console.log('🔧 Fixing module:', moduleId);
            var config = this.moduleConfigs[moduleId];
            if (!config) {
                console.warn('⚠️ No configuration found for:', moduleId);
                return false;
            }
            
            var success = false;
            
            // 1. Ensure data exists globally
            if (!window[config.dataKey] && this.mockData[config.dataKey]) {
                console.log('  📊 Injecting mock data for:', moduleId);
                window[config.dataKey] = this.mockData[config.dataKey];
                success = true;
            }
            
            // 2. Ensure filtered data exists if needed
            if (config.needsFiltered && !window[config.filteredKey]) {
                console.log('  📊 Injecting filtered data for:', moduleId);
                window[config.filteredKey] = window[config.dataKey] ? window[config.dataKey].slice() : [];
                success = true;
            }
            
            // 3. Check if container exists
            var container = document.getElementById(config.containerId);
            if (!container) {
                console.log('  ⏳ Container not found, will retry...');
                setTimeout(function() {
                    GlobalModuleFixer.fixModule(moduleId);
                }, 200);
                return false;
            }
            
            // 4. Render data if container is empty
            if (container.children.length === 0 && window[config.dataKey] && window[config.dataKey].length > 0) {
                console.log('  📋 Container is empty, rendering data...');
                
                // Try render function
                if (typeof window[config.renderFunc] === 'function') {
                    try {
                        var data = window[config.needsFiltered] ? window[config.filteredKey] : window[config.dataKey];
                        window[config.renderFunc](data);
                        success = true;
                        console.log('  ✅ Render function called successfully');
                    } catch(e) {
                        console.warn('  ⚠️ Error calling render function:', e.message);
                    }
                }
                
                // Try filter function
                if (typeof window[config.filterFunc] === 'function') {
                    try {
                        window[config.filterFunc]();
                        success = true;
                        console.log('  ✅ Filter function called successfully');
                    } catch(e) {
                        console.warn('  ⚠️ Error calling filter function:', e.message);
                    }
                }
                
                // Try stats function
                if (typeof window[config.statsFunc] === 'function') {
                    try {
                        var data = window[config.needsFiltered] ? window[config.filteredKey] : window[config.dataKey];
                        window[config.statsFunc](data);
                        success = true;
                        console.log('  ✅ Stats function called successfully');
                    } catch(e) {
                        console.warn('  ⚠️ Error calling stats function:', e.message);
                    }
                }
            }
            
            // 5. Try init function
            if (typeof window[config.initFunc] === 'function') {
                try {
                    window[config.initFunc]();
                    success = true;
                    console.log('  ✅ Init function called successfully');
                } catch(e) {
                    console.warn('  ⚠️ Error calling init function:', e.message);
                }
            }
            
            if (success) {
                this.fixedModules[moduleId] = true;
                console.log('✅ Module fixed:', moduleId);
            } else {
                console.warn('⚠️ Could not fully fix module:', moduleId);
            }
            
            return success;
        },
        
        // Fix all modules
        fixAllModules: function() {
            console.log('🔧 Fixing all modules...');
            var moduleIds = Object.keys(this.moduleConfigs);
            for (var i = 0; i < moduleIds.length; i++) {
                this.fixModule(moduleIds[i]);
            }
            console.log('✅ All modules fixed!');
        },
        
        // Auto-fix on module load with retries
        autoFix: function(moduleId) {
            var attempts = this.fixAttempts[moduleId] || 0;
            attempts++;
            this.fixAttempts[moduleId] = attempts;
            
            if (attempts > 5) {
                console.log('⚠️ Max attempts reached for:', moduleId);
                return;
            }
            
            var success = this.fixModule(moduleId);
            
            if (!success) {
                console.log('⏳ Retrying in 200ms... (attempt ' + attempts + ')');
                var self = this;
                setTimeout(function() {
                    self.autoFix(moduleId);
                }, 200);
            } else {
                this.fixAttempts[moduleId] = 0;
            }
        },
        
        // Initialize the fixer
        init: function() {
            console.log('🚀 Global Module Fixer initialized');
            
            // Fix modules that are already loaded
            var currentModule = window.location.hash.replace('#', '') || 'dashboard';
            if (currentModule !== 'dashboard' && currentModule !== '') {
                setTimeout(function() {
                    GlobalModuleFixer.autoFix(currentModule);
                }, 300);
            }
            
            // Listen for hash changes
            window.addEventListener('hashchange', function() {
                var moduleId = window.location.hash.replace('#', '');
                if (moduleId && moduleId !== 'dashboard') {
                    setTimeout(function() {
                        GlobalModuleFixer.autoFix(moduleId);
                    }, 400);
                }
            });
            
            // Listen for custom event from SPA
            document.addEventListener('module-loaded', function(e) {
                if (e.detail && e.detail.moduleId) {
                    setTimeout(function() {
                        GlobalModuleFixer.autoFix(e.detail.moduleId);
                    }, 300);
                }
            });
            
            console.log('✅ Global Module Fixer ready');
            console.log('📦 Available modules to fix:', Object.keys(this.moduleConfigs).join(', '));
        }
    };
    
    // Make available globally
    window.GlobalModuleFixer = GlobalModuleFixer;
    
    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            GlobalModuleFixer.init();
        });
    } else {
        GlobalModuleFixer.init();
    }
    
    // Also init on window load
    window.addEventListener('load', function() {
        setTimeout(function() {
            var currentModule = window.location.hash.replace('#', '') || 'dashboard';
            if (currentModule !== 'dashboard' && currentModule !== '') {
                GlobalModuleFixer.autoFix(currentModule);
            }
        }, 1000);
    });
    
})();