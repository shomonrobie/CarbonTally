// Facility Management Module - SPA Compatible
(function() {

    console.log('🏭 Facility Management JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var facilities = [
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
    ];

    // ============================================
    // STATE
    // ============================================

    var filteredFacilities = [];
    var currentPage = 1;
    var perPage = 5;
    var currentSort = { field: 'name', direction: 'asc' };
    var editingId = null;
    var viewingId = null;
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

    var typeIcons = {
        'office': '🏢', 'warehouse': '🏗️', 'manufacturing': '🏭',
        'retail': '🛍️', 'data_center': '💻', 'laboratory': '🔬'
    };

    var typeLabels = {
        'office': 'Office', 'warehouse': 'Warehouse', 'manufacturing': 'Manufacturing',
        'retail': 'Retail', 'data_center': 'Data Center', 'laboratory': 'Laboratory'
    };

    function getStatusBadge(status) {
        var map = {
            'active': '<span class="badge badge-success">● Active</span>',
            'inactive': '<span class="badge badge-muted">● Inactive</span>',
            'maintenance': '<span class="badge badge-warning">🔧 Maintenance</span>'
        };
        return map[status] || status;
    }

    function getTypeIcon(type) { return typeIcons[type] || '🏢'; }
    function getTypeLabel(type) { return typeLabels[type] || type; }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderStats(data) {
        var totalEl = getEl('statTotal');
        var activeEl = getEl('statActive');
        var inactiveEl = getEl('statInactive');
        var areaEl = getEl('statArea');
        var countriesEl = getEl('statCountries');
        var assetsEl = getEl('statAssets');

        if (!totalEl) return;

        var active = 0, inactive = 0, area = 0, assets = 0;
        var countries = {};
        for (var i = 0; i < data.length; i++) {
            var f = data[i];
            if (f.status === 'active') active++;
            else if (f.status === 'inactive') inactive++;
            area += (f.area || 0);
            assets += (f.assets || 0);
            countries[f.country] = true;
        }
        
        totalEl.textContent = data.length;
        if (activeEl) activeEl.textContent = active;
        if (inactiveEl) inactiveEl.textContent = inactive;
        if (areaEl) areaEl.textContent = area.toLocaleString();
        if (countriesEl) countriesEl.textContent = Object.keys(countries).length;
        if (assetsEl) assetsEl.textContent = assets;
    }

    function renderTable(data) {
        var tbody = getEl('facilityTableBody');
        var countEl = getEl('facilityCount');
        var filterEl = getEl('filterCount');
        var paginationEl = getEl('pagination');

        if (!tbody) return;

        var start = (currentPage - 1) * perPage;
        var pageItems = data.slice(start, start + perPage);

        if (pageItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:hsl(var(--muted-foreground));">📭 No facilities found</td></tr>';
            if (countEl) countEl.textContent = '0';
            if (filterEl) filterEl.textContent = '0 facilities';
            renderPagination(data.length);
            return;
        }

        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var f = pageItems[i];
            html += '<tr>' +
                '<td><div style="display:flex;align-items:center;gap:10px;"><span class="facility-type-icon">' + getTypeIcon(f.type) + '</span><div><div style="font-weight:500;">' + f.name + '</div><div style="font-size:11px;color:hsl(var(--muted-foreground));">' + f.address + '</div></div></div></td>' +
                '<td><span class="badge badge-secondary">' + getTypeLabel(f.type) + '</span></td>' +
                '<td><div>' + f.city + '</div><div style="font-size:11px;color:hsl(var(--muted-foreground));">' + f.country + '</div></td>' +
                '<td style="text-align:right;">' + (f.area || 0).toLocaleString() + '</td>' +
                '<td style="text-align:center;">' + (f.assets || 0) + '</td>' +
                '<td>' + getStatusBadge(f.status) + '</td>' +
                '<td style="font-size:12px;color:hsl(var(--muted-foreground));">' + f.createdAt + '</td>' +
                '<td><div style="display:flex;gap:4px;flex-wrap:wrap;"><button class="btn btn-sm btn-ghost" onclick="editFacility(\'' + f.id + '\')" title="Edit">✏️</button><button class="btn btn-sm btn-ghost" onclick="viewFacility(\'' + f.id + '\')" title="View">👁️</button><button class="btn btn-sm btn-danger" onclick="deleteFacility(\'' + f.id + '\')" title="Delete">🗑️</button></div></td>' +
                '</tr>';
        }

        tbody.innerHTML = html;
        if (countEl) countEl.textContent = data.length;
        if (filterEl) filterEl.textContent = data.length + ' facilities';
        renderPagination(data.length);
    }

    function renderPagination(total) {
        var container = getEl('pagination');
        if (!container) return;

        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' facilities</div><div class="page-buttons"></div>';
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

        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' facilities</div><div class="page-buttons">' + btns + '</div>';
    }

    // ============================================
    // FILTER FUNCTIONS
    // ============================================

    function applyFilters() {
        var typeEl = getEl('filterType');
        var statusEl = getEl('filterStatus');
        var countryEl = getEl('filterCountry');
        var searchEl = getEl('globalSearch');
        
        var type = typeEl ? typeEl.value : 'all';
        var status = statusEl ? statusEl.value : 'all';
        var country = countryEl ? countryEl.value : 'all';
        var search = searchEl ? searchEl.value.toLowerCase().trim() : '';

        var filtered = [];
        for (var i = 0; i < facilities.length; i++) {
            var f = facilities[i];
            if (type !== 'all' && f.type !== type) continue;
            if (status !== 'all' && f.status !== status) continue;
            if (country !== 'all' && f.country !== country) continue;
            if (search) {
                var match = f.name.toLowerCase().indexOf(search) !== -1 ||
                        f.location.toLowerCase().indexOf(search) !== -1 ||
                        f.city.toLowerCase().indexOf(search) !== -1 ||
                        f.address.toLowerCase().indexOf(search) !== -1;
                if (!match) continue;
            }
            filtered.push(f);
        }

        // Sort
        filtered.sort(function(a, b) {
            var aVal = a[currentSort.field] || '';
            var bVal = b[currentSort.field] || '';
            if (typeof aVal === 'string') {
                return currentSort.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }
            return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        });

        filteredFacilities = filtered;
        currentPage = 1;
        
        renderStats(facilities);
        renderTable(filtered);
    }

    function clearFilters() {
        var typeEl = getEl('filterType');
        var statusEl = getEl('filterStatus');
        var countryEl = getEl('filterCountry');
        var searchEl = getEl('globalSearch');
        
        if (typeEl) typeEl.value = 'all';
        if (statusEl) statusEl.value = 'all';
        if (countryEl) countryEl.value = 'all';
        if (searchEl) searchEl.value = '';
        
        currentPage = 1;
        applyFilters();
        showToast('🔄 Filters cleared');
    }

    // ============================================
    // SORTING
    // ============================================

    function sortBy(field) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = field === 'createdAt' ? 'desc' : 'asc';
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
        
        applyFilters();
    }

    // ============================================
    // PAGINATION
    // ============================================

    function goToPage(page) {
        var totalPages = Math.ceil(filteredFacilities.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderTable(filteredFacilities);
    }

    // ============================================
    // FACILITY CRUD
    // ============================================

    function openFacilityModal(facilityId) {
        editingId = facilityId || null;
        var modal = getEl('facilityModal');
        var title = getEl('modalTitle');
        
        if (editingId) {
            var facility = null;
            for (var i = 0; i < facilities.length; i++) {
                if (facilities[i].id === editingId) { facility = facilities[i]; break; }
            }
            if (facility) {
                if (title) title.textContent = '✏️ Edit Facility';
                var nameEl = getEl('facilityName');
                var typeEl = getEl('facilityType');
                var countryEl = getEl('facilityCountry');
                var cityEl = getEl('facilityCity');
                var addressEl = getEl('facilityAddress');
                var areaEl = getEl('facilityArea');
                var statusEl = getEl('facilityStatus');
                if (nameEl) nameEl.value = facility.name;
                if (typeEl) typeEl.value = facility.type;
                if (countryEl) countryEl.value = facility.country;
                if (cityEl) cityEl.value = facility.city;
                if (addressEl) addressEl.value = facility.address;
                if (areaEl) areaEl.value = facility.area || '';
                if (statusEl) statusEl.value = facility.status;
            }
        } else {
            if (title) title.textContent = '🏗️ Add Facility';
            var nameEl = getEl('facilityName');
            var typeEl = getEl('facilityType');
            var countryEl = getEl('facilityCountry');
            var cityEl = getEl('facilityCity');
            var addressEl = getEl('facilityAddress');
            var areaEl = getEl('facilityArea');
            var statusEl = getEl('facilityStatus');
            if (nameEl) nameEl.value = '';
            if (typeEl) typeEl.value = 'office';
            if (countryEl) countryEl.value = 'UK';
            if (cityEl) cityEl.value = '';
            if (addressEl) addressEl.value = '';
            if (areaEl) areaEl.value = '';
            if (statusEl) statusEl.value = 'active';
        }
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeFacilityModal() {
        var modal = getEl('facilityModal');
        if (modal) modal.classList.remove('show');
        document.body.style.overflow = '';
        editingId = null;
    }

    function saveFacility() {
        var nameEl = getEl('facilityName');
        var typeEl = getEl('facilityType');
        var countryEl = getEl('facilityCountry');
        var cityEl = getEl('facilityCity');
        var addressEl = getEl('facilityAddress');
        var areaEl = getEl('facilityArea');
        var statusEl = getEl('facilityStatus');
        
        var name = nameEl ? nameEl.value.trim() : '';
        var type = typeEl ? typeEl.value : 'office';
        var country = countryEl ? countryEl.value : 'UK';
        var city = cityEl ? cityEl.value.trim() : '';
        var address = addressEl ? addressEl.value.trim() : '';
        var area = parseInt(areaEl ? areaEl.value : 0) || 0;
        var status = statusEl ? statusEl.value : 'active';

        if (!name) {
            showToast('⚠️ Please enter a facility name', 'warning');
            if (nameEl) nameEl.focus();
            return;
        }

        if (editingId) {
            var facility = null;
            for (var i = 0; i < facilities.length; i++) {
                if (facilities[i].id === editingId) { facility = facilities[i]; break; }
            }
            if (facility) {
                facility.name = name;
                facility.type = type;
                facility.country = country;
                facility.city = city || facility.city;
                facility.address = address || facility.address;
                facility.area = area;
                facility.status = status;
                facility.location = (city || facility.city) + ', ' + country;
                facility.updatedAt = new Date().toISOString().slice(0, 10);
                showToast('✅ Facility updated successfully!');
            }
        } else {
            var newFacility = {
                id: 'f' + (facilities.length + 1),
                name: name,
                type: type,
                country: country,
                city: city || 'Unknown',
                address: address || 'N/A',
                area: area,
                assets: 0,
                status: status,
                location: (city || 'Unknown') + ', ' + country,
                createdAt: new Date().toISOString().slice(0, 10),
                updatedAt: new Date().toISOString().slice(0, 10)
            };
            facilities.push(newFacility);
            showToast('✅ Facility added successfully!');
        }

        closeFacilityModal();
        applyFilters();
    }

    function editFacility(id) {
        closeViewModal();
        openFacilityModal(id);
    }

    function viewFacility(id) {
        var facility = null;
        for (var i = 0; i < facilities.length; i++) {
            if (facilities[i].id === id) { facility = facilities[i]; break; }
        }
        if (!facility) return;

        viewingId = id;
        var modal = getEl('viewModal');
        var title = getEl('viewModalTitle');
        var body = getEl('viewModalBody');

        if (title) title.textContent = '🏭 ' + facility.name;

        if (body) {
            body.innerHTML = 
                '<div class="view-detail-row"><span class="label">Name</span><span class="value">' + facility.name + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Type</span><span class="value">' + getTypeLabel(facility.type) + ' ' + getTypeIcon(facility.type) + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Location</span><span class="value">' + facility.location + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Address</span><span class="value">' + facility.address + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Area</span><span class="value">' + (facility.area || 0).toLocaleString() + ' sq ft</span></div>' +
                '<div class="view-detail-row"><span class="label">Assets</span><span class="value">' + (facility.assets || 0) + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Status</span><span class="value">' + getStatusBadge(facility.status) + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Created</span><span class="value">' + facility.createdAt + '</span></div>' +
                '<div class="view-detail-row"><span class="label">Last Updated</span><span class="value">' + facility.updatedAt + '</span></div>';
        }

        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeViewModal() {
        var modal = getEl('viewModal');
        if (modal) modal.classList.remove('show');
        document.body.style.overflow = '';
        viewingId = null;
    }

    function editFromView() {
        if (viewingId) {
            closeViewModal();
            openFacilityModal(viewingId);
        }
    }

    function deleteFacility(id) {
        var facility = null;
        for (var i = 0; i < facilities.length; i++) {
            if (facilities[i].id === id) { facility = facilities[i]; break; }
        }
        if (!facility) return;

        if (confirm('Are you sure you want to delete "' + facility.name + '"?')) {
            var newFacilities = [];
            for (var i = 0; i < facilities.length; i++) {
                if (facilities[i].id !== id) {
                    newFacilities.push(facilities[i]);
                }
            }
            facilities = newFacilities;
            applyFilters();
            showToast('🗑️ Facility deleted successfully!');
        }
    }

    function refreshData() {
        showToast('🔄 Refreshing facility data...');
        setTimeout(function() {
            applyFilters();
            showToast('✅ Data refreshed successfully!');
        }, 500);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        console.log('🚀 Initializing Facility Management Module...');
        
        var tbody = getEl('facilityTableBody');
        if (!tbody) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Set up event listeners
        var applyBtn = getEl('applyFiltersBtn');
        if (applyBtn) applyBtn.addEventListener('click', applyFilters);
        
        var clearBtn = getEl('clearFiltersBtn');
        if (clearBtn) clearBtn.addEventListener('click', clearFilters);
        
        var searchEl = getEl('globalSearch');
        if (searchEl) {
            searchEl.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') applyFilters();
            });
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
                var facilityModal = getEl('facilityModal');
                var viewModal = getEl('viewModal');
                if (facilityModal && facilityModal.classList.contains('show')) {
                    closeFacilityModal();
                }
                if (viewModal && viewModal.classList.contains('show')) {
                    closeViewModal();
                }
            }
        });
        
        // Initial render
        filteredFacilities = facilities.slice();
        applyFilters();
        
        console.log('✅ Facility Management module loaded successfully!');
        console.log('🏭 ' + facilities.length + ' facilities loaded');
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
    window.sortBy = sortBy;
    window.goToPage = goToPage;
    window.openFacilityModal = openFacilityModal;
    window.closeFacilityModal = closeFacilityModal;
    window.saveFacility = saveFacility;
    window.editFacility = editFacility;
    window.viewFacility = viewFacility;
    window.closeViewModal = closeViewModal;
    window.editFromView = editFromView;
    window.deleteFacility = deleteFacility;
    window.refreshData = refreshData;
    window.showToast = showToast;
})(); // <-- End of the IIFE wrapper