
// Roles & Permissions Module - SPA Compatible
(function() {

    console.log('🔑 Roles & Permissions JS loaded');

    // ============================================
    // MOCK DATA - Permission Definitions
    // ============================================

    var permissionDefinitions = [
        { id: 'view_dashboard', label: 'View Dashboard', description: 'Access to view the main dashboard', category: 'dashboard', icon: '📊' },
        { id: 'view_reports', label: 'View Reports', description: 'Access to view and export reports', category: 'reports', icon: '📄' },
        { id: 'generate_reports', label: 'Generate Reports', description: 'Create and generate new reports', category: 'reports', icon: '📊' },
        { id: 'view_emissions', label: 'View Emissions Data', description: 'Access to view emissions data', category: 'emissions', icon: '📈' },
        { id: 'edit_emissions', label: 'Edit Emissions Data', description: 'Add, edit, and delete emissions records', category: 'emissions', icon: '✏️' },
        { id: 'upload_documents', label: 'Upload Documents', description: 'Upload and manage documents', category: 'documents', icon: '📤' },
        { id: 'view_documents', label: 'View Documents', description: 'Access to view all documents', category: 'documents', icon: '📁' },
        { id: 'manage_team', label: 'Manage Team', description: 'Add, remove, and manage team members', category: 'team', icon: '👥' },
        { id: 'manage_roles', label: 'Manage Roles', description: 'Create, edit, and delete roles', category: 'team', icon: '🔑' },
        { id: 'manage_facilities', label: 'Manage Facilities', description: 'Add, edit, and delete facilities', category: 'facilities', icon: '🏢' },
        { id: 'manage_assets', label: 'Manage Assets', description: 'Add, edit, and delete assets', category: 'assets', icon: '🚗' },
        { id: 'view_settings', label: 'View Settings', description: 'Access to view organization settings', category: 'settings', icon: '⚙️' },
        { id: 'edit_settings', label: 'Edit Settings', description: 'Modify organization settings', category: 'settings', icon: '🔧' },
        { id: 'view_audit_log', label: 'View Audit Log', description: 'Access to view audit logs', category: 'audit', icon: '📋' },
        { id: 'manage_integrations', label: 'Manage Integrations', description: 'Configure and manage integrations', category: 'integrations', icon: '🔌' },
        { id: 'export_data', label: 'Export Data', description: 'Export data from the system', category: 'data', icon: '📥' }
    ];

    // ============================================
    // MOCK DATA - Roles (7 roles)
    // ============================================

    var roles = [
        { 
            id: 'role_001', 
            name: 'Admin', 
            description: 'Full access to all features and settings. Can manage users, roles, and all data.', 
            color: '#10b981', 
            permissions: ['view_dashboard', 'view_reports', 'generate_reports', 'view_emissions', 'edit_emissions', 'upload_documents', 'view_documents', 'manage_team', 'manage_roles', 'manage_facilities', 'manage_assets', 'view_settings', 'edit_settings', 'view_audit_log', 'manage_integrations', 'export_data'], 
            members: 2, 
            isDefault: false, 
            createdAt: '2025-01-15', 
            createdBy: 'System' 
        },
        { 
            id: 'role_002', 
            name: 'Manager', 
            description: 'Can manage team members, view all data, and generate reports. Cannot manage roles or settings.', 
            color: '#3b82f6', 
            permissions: ['view_dashboard', 'view_reports', 'generate_reports', 'view_emissions', 'edit_emissions', 'view_documents', 'upload_documents', 'manage_team', 'manage_facilities', 'manage_assets', 'export_data'], 
            members: 2, 
            isDefault: false, 
            createdAt: '2025-02-01', 
            createdBy: 'Admin' 
        },
        { 
            id: 'role_003', 
            name: 'Analyst', 
            description: 'Can view and edit emissions data, generate reports, and upload documents. Cannot manage team.', 
            color: '#8b5cf6', 
            permissions: ['view_dashboard', 'view_reports', 'generate_reports', 'view_emissions', 'edit_emissions', 'view_documents', 'upload_documents', 'export_data'], 
            members: 4, 
            isDefault: true, 
            createdAt: '2025-03-01', 
            createdBy: 'Admin' 
        },
        { 
            id: 'role_004', 
            name: 'Staff', 
            description: 'Can view data, upload documents, and manage assigned tasks. Limited edit capabilities.', 
            color: '#f59e0b', 
            permissions: ['view_dashboard', 'view_emissions', 'view_documents', 'upload_documents', 'view_reports'], 
            members: 2, 
            isDefault: false, 
            createdAt: '2025-04-01', 
            createdBy: 'Admin' 
        },
        { 
            id: 'role_005', 
            name: 'Viewer', 
            description: 'Read-only access to all data. Cannot edit, upload, or manage anything.', 
            color: '#6b7280', 
            permissions: ['view_dashboard', 'view_reports', 'view_emissions', 'view_documents', 'view_settings'], 
            members: 2, 
            isDefault: false, 
            createdAt: '2025-05-01', 
            createdBy: 'Admin' 
        },
        { 
            id: 'role_006', 
            name: 'Compliance Officer', 
            description: 'Focus on compliance reporting and regulatory requirements. Full access to compliance data.', 
            color: '#ec4899', 
            permissions: ['view_dashboard', 'view_reports', 'generate_reports', 'view_emissions', 'edit_emissions', 'view_documents', 'upload_documents', 'view_audit_log', 'export_data'], 
            members: 0, 
            isDefault: false, 
            createdAt: '2025-06-01', 
            createdBy: 'Admin' 
        },
        { 
            id: 'role_007', 
            name: 'Sustainability Lead', 
            description: 'Oversee sustainability initiatives and reporting. Full access to emissions and reporting.', 
            color: '#14b8a6', 
            permissions: ['view_dashboard', 'view_reports', 'generate_reports', 'view_emissions', 'edit_emissions', 'view_documents', 'upload_documents', 'manage_facilities', 'manage_assets', 'export_data'], 
            members: 0, 
            isDefault: false, 
            createdAt: '2025-07-01', 
            createdBy: 'Admin' 
        }
    ];

    // ============================================
    // STATE
    // ============================================

    var editingRoleId = null;
    var viewingRoleId = null;
    var currentPage = 1;
    var perPage = 6;
    var toastTimeout = null;
    var filterRole = 'all';
    var filterMember = 'all';
    var filterSearch = '';
    var initAttempts = 0;
    var maxInitAttempts = 20;

    // ============================================
    // DOM REFS
    // ============================================

    function getEl(id) { 
        var el = document.getElementById(id);
        if (!el) {
            console.warn('⚠️ Element not found:', id);
        }
        return el; 
    }

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
    // PERMISSION FUNCTIONS
    // ============================================

    function getPermissionGroups() {
        var groups = {};
        for (var i = 0; i < permissionDefinitions.length; i++) {
            var p = permissionDefinitions[i];
            if (!groups[p.category]) {
                groups[p.category] = [];
            }
            groups[p.category].push(p);
        }
        return groups;
    }

    function renderPermissionGrid(selectedPermissions) {
        selectedPermissions = selectedPermissions || [];
        var container = getEl('permissionGrid');
        if (!container) return;
        
        var groups = getPermissionGroups();
        var groupNames = {
            dashboard: 'Dashboard',
            reports: 'Reports',
            emissions: 'Emissions',
            documents: 'Documents',
            team: 'Team Management',
            facilities: 'Facilities',
            assets: 'Assets',
            settings: 'Settings',
            audit: 'Audit',
            integrations: 'Integrations',
            data: 'Data'
        };
        
        var html = '';
        var groupKeys = Object.keys(groups);
        for (var g = 0; g < groupKeys.length; g++) {
            var key = groupKeys[g];
            var perms = groups[key];
            html += '<div class="permission-group">' +
                '<div class="group-title"><span class="icon">' + (perms[0]?.icon || '📌') + '</span>' + (groupNames[key] || key.charAt(0).toUpperCase() + key.slice(1)) + '</div>';
            
            for (var p = 0; p < perms.length; p++) {
                var perm = perms[p];
                var checked = selectedPermissions.indexOf(perm.id) !== -1 ? 'checked' : '';
                html += '<div class="permission-item">' +
                    '<input type="checkbox" id="perm_' + perm.id + '" value="' + perm.id + '" ' + checked + ' />' +
                    '<label for="perm_' + perm.id + '">' + perm.label + '<span class="desc">' + perm.description + '</span></label>' +
                    '</div>';
            }
            html += '</div>';
        }
        container.innerHTML = html;
    }

    function getSelectedPermissions() {
        var container = getEl('permissionGrid');
        if (!container) return [];
        var checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        var selected = [];
        for (var i = 0; i < checkboxes.length; i++) {
            selected.push(checkboxes[i].value);
        }
        return selected;
    }

    // ============================================
    // STATS
    // ============================================

    function renderStats() {
        var totalRoles = roles.length;
        var totalMembers = 0;
        var defaultRole = '—';
        
        for (var i = 0; i < roles.length; i++) {
            totalMembers += (roles[i].members || 0);
            if (roles[i].isDefault) {
                defaultRole = roles[i].name;
            }
        }
        var totalPerms = permissionDefinitions.length;
        
        var el = getEl('statTotalRoles');
        if (el) el.textContent = totalRoles;
        el = getEl('statTotalMembers');
        if (el) el.textContent = totalMembers;
        el = getEl('statDefaultRole');
        if (el) el.textContent = defaultRole;
        el = getEl('statPermissions');
        if (el) el.textContent = totalPerms;
    }

    // ============================================
    // RENDER ROLES
    // ============================================

    function applyFilters() {
        var roleEl = getEl('roleFilter');
        var memberEl = getEl('memberFilter');
        var searchEl = getEl('searchInput');
        
        filterRole = roleEl ? roleEl.value : 'all';
        filterMember = memberEl ? memberEl.value : 'all';
        filterSearch = searchEl ? searchEl.value.toLowerCase().trim() : '';
        currentPage = 1;
        renderRoles();
    }

    function clearFilters() {
        var roleEl = getEl('roleFilter');
        var memberEl = getEl('memberFilter');
        var searchEl = getEl('searchInput');
        
        if (roleEl) roleEl.value = 'all';
        if (memberEl) memberEl.value = 'all';
        if (searchEl) searchEl.value = '';
        filterRole = 'all';
        filterMember = 'all';
        filterSearch = '';
        currentPage = 1;
        renderRoles();
        showToast('🔄 Filters cleared');
    }

    function renderRoles() {
        console.log('🔑 Rendering roles... Total roles:', roles.length);
        
        var container = getEl('rolesContainer');
        var countEl = getEl('filterCount');
        var paginationEl = getEl('pagination');
        
        // Try harder to find the container
        if (!container) {
            container = document.querySelector('#rolesContainer');
        }
        if (!container) {
            container = document.querySelector('.roles-grid');
        }
        
        if (!container) {
            console.error('❌ rolesContainer element not found!');
            return;
        }
        
        console.log('✅ Found rolesContainer, rendering...');
        
        if (roles.length === 0) {
            console.warn('⚠️ No roles data available!');
        }
        
        var filtered = roles.slice();
        
        if (filterRole !== 'all') {
            filtered = filtered.filter(function(r) { return r.name === filterRole; });
        }
        if (filterMember === 'has') {
            filtered = filtered.filter(function(r) { return r.members > 0; });
        } else if (filterMember === 'none') {
            filtered = filtered.filter(function(r) { return r.members === 0; });
        }
        if (filterSearch) {
            filtered = filtered.filter(function(r) {
                return r.name.toLowerCase().indexOf(filterSearch) !== -1 ||
                    r.description.toLowerCase().indexOf(filterSearch) !== -1;
            });
        }
        
        if (countEl) countEl.textContent = filtered.length + ' roles';
        
        var start = (currentPage - 1) * perPage;
        var pageItems = filtered.slice(start, start + perPage);
        
        if (pageItems.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:60px 20px;grid-column:1/-1;">' +
                '<div style="font-size:48px;margin-bottom:16px;">🔑</div>' +
                '<div style="font-size:18px;font-weight:600;">No roles found</div>' +
                '<div style="font-size:14px;color:hsl(var(--muted-foreground));margin-top:8px;">Create your first role to get started</div>' +
                '<button class="btn btn-primary" style="margin-top:16px;" onclick="showCreateRoleModal()">➕ Create Role</button>' +
                '</div>';
            renderPagination(filtered.length);
            return;
        }
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var role = pageItems[i];
            var permBadges = '';
            var permCount = Math.min(role.permissions.length, 6);
            for (var j = 0; j < permCount; j++) {
                var permId = role.permissions[j];
                var perm = null;
                for (var k = 0; k < permissionDefinitions.length; k++) {
                    if (permissionDefinitions[k].id === permId) {
                        perm = permissionDefinitions[k];
                        break;
                    }
                }
                if (perm) {
                    permBadges += '<span class="badge badge-muted">' + perm.label + '</span>';
                }
            }
            if (role.permissions.length > 6) {
                permBadges += '<span class="badge badge-muted">+' + (role.permissions.length - 6) + ' more</span>';
            }
            
            html +=
                '<div class="role-card" onclick="viewRoleDetail(\'' + role.id + '\')">' +
                '<div class="role-header">' +
                '<div class="role-name">' +
                '<span class="color-dot" style="background:' + role.color + ';"></span>' +
                role.name +
                (role.isDefault ? '<span class="badge badge-muted">⭐ Default</span>' : '') +
                '<span class="badge badge-muted">' + role.members + ' members</span>' +
                '</div>' +
                '<div class="role-actions">' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();viewRoleDetail(\'' + role.id + '\')" title="View Details">👁️</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();editRole(\'' + role.id + '\')" title="Edit Role">✏️</button>' +
                (role.name !== 'Admin' ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();deleteRole(\'' + role.id + '\')" style="color:hsl(var(--destructive));" title="Delete Role">🗑️</button>' : '') +
                '</div>' +
                '</div>' +
                '<div class="role-desc">' + role.description + '</div>' +
                '<div class="role-meta">' +
                '<span>📅 Created ' + role.createdAt + '</span>' +
                '<span>👤 By ' + role.createdBy + '</span>' +
                '<span>🔑 ' + role.permissions.length + ' permissions</span>' +
                '</div>' +
                '<div class="role-permissions">' + permBadges + '</div>' +
                '</div>';
        }
        container.innerHTML = html;
        renderPagination(filtered.length);
    }

    function renderPagination(total) {
        var container = getEl('pagination');
        if (!container) {
            container = document.querySelector('#pagination');
        }
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' roles</div><div class="page-buttons"></div>';
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
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' roles</div><div class="page-buttons">' + btns + '</div>';
    }

    function goToPage(page) {
        var totalPages = Math.ceil(roles.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderRoles();
    }

    // ============================================
    // ROLE CRUD OPERATIONS
    // ============================================

    function showCreateRoleModal() {
        editingRoleId = null;
        var titleEl = getEl('roleModalTitle');
        var subtitleEl = getEl('roleModalSubtitle');
        var nameEl = getEl('roleName');
        var colorEl = getEl('roleColor');
        var descEl = getEl('roleDescription');
        var defaultEl = getEl('roleIsDefault');
        var saveBtn = getEl('roleSaveBtn');
        var modal = getEl('roleModal');
        
        if (titleEl) titleEl.textContent = '🔑 Create Role';
        if (subtitleEl) subtitleEl.textContent = 'Define a new role and its permissions';
        if (nameEl) nameEl.value = '';
        if (colorEl) colorEl.value = '#3b82f6';
        if (descEl) descEl.value = '';
        if (defaultEl) defaultEl.checked = false;
        if (saveBtn) saveBtn.textContent = '💾 Create Role';
        
        renderPermissionGrid([]);
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function editRole(id) {
        var role = null;
        for (var i = 0; i < roles.length; i++) {
            if (roles[i].id === id) { role = roles[i]; break; }
        }
        if (!role) return;
        
        editingRoleId = id;
        var titleEl = getEl('roleModalTitle');
        var subtitleEl = getEl('roleModalSubtitle');
        var nameEl = getEl('roleName');
        var colorEl = getEl('roleColor');
        var descEl = getEl('roleDescription');
        var defaultEl = getEl('roleIsDefault');
        var saveBtn = getEl('roleSaveBtn');
        var modal = getEl('roleModal');
        
        if (titleEl) titleEl.textContent = '✏️ Edit Role: ' + role.name;
        if (subtitleEl) subtitleEl.textContent = 'Modify role details and permissions';
        if (nameEl) nameEl.value = role.name;
        if (colorEl) colorEl.value = role.color;
        if (descEl) descEl.value = role.description;
        if (defaultEl) defaultEl.checked = role.isDefault || false;
        if (saveBtn) saveBtn.textContent = '💾 Update Role';
        
        renderPermissionGrid(role.permissions);
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeRoleModal() {
        var modal = getEl('roleModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
        editingRoleId = null;
    }

    function saveRole() {
        var nameEl = getEl('roleName');
        var colorEl = getEl('roleColor');
        var descEl = getEl('roleDescription');
        var defaultEl = getEl('roleIsDefault');
        
        var name = nameEl ? nameEl.value.trim() : '';
        var color = colorEl ? colorEl.value : '#3b82f6';
        var description = descEl ? descEl.value.trim() : '';
        var isDefault = defaultEl ? defaultEl.checked : false;
        var permissions = getSelectedPermissions();
        
        if (!name) {
            showToast('⚠️ Please enter a role name', 'warning');
            if (nameEl) nameEl.focus();
            return;
        }
        if (!description) {
            showToast('⚠️ Please enter a role description', 'warning');
            if (descEl) descEl.focus();
            return;
        }
        if (permissions.length === 0) {
            showToast('⚠️ Please select at least one permission', 'warning');
            return;
        }
        
        if (editingRoleId) {
            var index = -1;
            for (var i = 0; i < roles.length; i++) {
                if (roles[i].id === editingRoleId) { index = i; break; }
            }
            if (index !== -1) {
                var oldName = roles[index].name;
                roles[index] = {
                    id: roles[index].id,
                    name: name,
                    color: color,
                    description: description,
                    permissions: permissions,
                    members: roles[index].members || 0,
                    isDefault: isDefault,
                    createdAt: roles[index].createdAt,
                    createdBy: roles[index].createdBy,
                    updatedAt: new Date().toISOString().split('T')[0]
                };
                if (isDefault) {
                    for (var j = 0; j < roles.length; j++) {
                        if (j !== index) roles[j].isDefault = false;
                    }
                }
                closeRoleModal();
                renderRoles();
                renderStats();
                showToast('✅ Updated role: ' + name);
            }
        } else {
            var newRole = {
                id: 'role_' + String(roles.length + 1).padStart(3, '0'),
                name: name,
                color: color,
                description: description,
                permissions: permissions,
                members: 0,
                isDefault: isDefault,
                createdAt: new Date().toISOString().split('T')[0],
                createdBy: 'Current User'
            };
            if (isDefault) {
                for (var j = 0; j < roles.length; j++) {
                    roles[j].isDefault = false;
                }
            }
            roles.push(newRole);
            closeRoleModal();
            renderRoles();
            renderStats();
            showToast('✅ Created role: ' + name);
        }
    }

    function viewRoleDetail(id) {
        var role = null;
        for (var i = 0; i < roles.length; i++) {
            if (roles[i].id === id) { role = roles[i]; break; }
        }
        if (!role) return;
        
        viewingRoleId = id;
        var titleEl = getEl('roleDetailTitle');
        var subtitleEl = getEl('roleDetailSubtitle');
        var bodyEl = getEl('roleDetailBody');
        var footerEl = getEl('roleDetailFooter');
        var modal = getEl('roleDetailModal');
        
        if (titleEl) titleEl.textContent = role.name;
        if (subtitleEl) subtitleEl.textContent = role.permissions.length + ' permissions • ' + role.members + ' members';
        
        if (bodyEl) {
            var permHtml = '';
            for (var j = 0; j < role.permissions.length; j++) {
                var permId = role.permissions[j];
                var perm = null;
                for (var k = 0; k < permissionDefinitions.length; k++) {
                    if (permissionDefinitions[k].id === permId) {
                        perm = permissionDefinitions[k];
                        break;
                    }
                }
                if (perm) {
                    permHtml += '<span class="badge badge-primary">' + perm.icon + ' ' + perm.label + '</span>';
                }
            }
            
            var memberNames = ['John Doe', 'Sarah Johnson', 'Mike Roberts', 'Anna Liu', 'Tom Chen'];
            var memberColors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'];
            var memberAvatars = ['JD', 'SJ', 'MR', 'AL', 'TC'];
            
            var membersHtml = '';
            if (role.members > 0) {
                for (var m = 0; m < Math.min(role.members, memberNames.length); m++) {
                    membersHtml += '<div style="display:flex;align-items:center;gap:6px;padding:4px 12px;border-radius:var(--radius);border:1px solid hsl(var(--border));">' +
                        '<div class="avatar avatar-sm" style="background:' + memberColors[m % memberColors.length] + ';">' + memberAvatars[m % memberAvatars.length] + '</div>' +
                        '<span style="font-size:13px;">' + memberNames[m % memberNames.length] + '</span>' +
                        '</div>';
                }
            } else {
                membersHtml = '<div class="text-muted" style="font-size:13px;">No members currently assigned to this role</div>';
            }
            
            bodyEl.innerHTML =
                '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">' +
                '<div style="width:4px;height:48px;border-radius:4px;background:' + role.color + ';"></div>' +
                '<div><div style="font-size:18px;font-weight:700;color:hsl(var(--foreground));">' + role.name + (role.isDefault ? ' <span class="badge badge-muted">⭐ Default</span>' : '') + '</div>' +
                '<div style="font-size:14px;color:hsl(var(--muted-foreground));">' + role.description + '</div></div></div>' +
                
                '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">' +
                '<div style="padding:12px;border-radius:var(--radius);border:1px solid hsl(var(--border));text-align:center;"><div style="font-size:20px;font-weight:700;color:hsl(var(--foreground));">' + role.members + '</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Members</div></div>' +
                '<div style="padding:12px;border-radius:var(--radius);border:1px solid hsl(var(--border));text-align:center;"><div style="font-size:20px;font-weight:700;color:hsl(var(--foreground));">' + role.permissions.length + '</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Permissions</div></div>' +
                '<div style="padding:12px;border-radius:var(--radius);border:1px solid hsl(var(--border));text-align:center;"><div style="font-size:20px;font-weight:700;color:hsl(var(--foreground));">' + role.createdAt + '</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Created</div></div></div>' +
                
                '<div style="margin-bottom:16px;"><h4 style="font-size:14px;font-weight:600;color:hsl(var(--foreground));margin-bottom:8px;">🛡️ Permissions</h4><div style="display:flex;gap:4px;flex-wrap:wrap;">' + permHtml + '</div></div>' +
                
                '<div><h4 style="font-size:14px;font-weight:600;color:hsl(var(--foreground));margin-bottom:8px;">👥 Members with this role</h4><div style="display:flex;gap:8px;flex-wrap:wrap;">' + membersHtml + '</div></div>';
        }
        
        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeRoleDetail()">Close</button>' +
                '<button class="btn btn-outline btn-sm" onclick="editRole(\'' + role.id + '\');closeRoleDetail();">✏️ Edit Role</button>' +
                (role.name !== 'Admin' ? '<button class="btn btn-danger btn-sm" onclick="deleteRole(\'' + role.id + '\');closeRoleDetail();">🗑️ Delete Role</button>' : '');
        }
        
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeRoleDetail() {
        var modal = getEl('roleDetailModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
        viewingRoleId = null;
    }

    function deleteRole(id) {
        var role = null;
        for (var i = 0; i < roles.length; i++) {
            if (roles[i].id === id) { role = roles[i]; break; }
        }
        if (!role) return;
        
        if (role.name === 'Admin') {
            showToast('⚠️ Cannot delete the Admin role', 'warning');
            return;
        }
        if (role.members > 0) {
            showToast('⚠️ Cannot delete role with ' + role.members + ' members assigned', 'warning');
            return;
        }
        
        if (confirm('Are you sure you want to delete the role "' + role.name + '"?')) {
            var index = -1;
            for (var i = 0; i < roles.length; i++) {
                if (roles[i].id === id) { index = i; break; }
            }
            if (index !== -1) {
                roles.splice(index, 1);
                renderRoles();
                renderStats();
                showToast('🗑️ Deleted role: ' + role.name);
            }
        }
    }

    // ============================================
    // INIT - FIXED WITH BETTER DOM DETECTION
    // ============================================

    function initModule() {
        initAttempts++;
        console.log('🚀 Initializing Roles & Permissions Module (attempt ' + initAttempts + ')...');
        
        // Try multiple ways to find the container
        var container = document.getElementById('rolesContainer');
        
        // If not found, try querySelector
        if (!container) {
            container = document.querySelector('#rolesContainer');
        }
        
        // If still not found, try looking for it in the main body
        if (!container) {
            var mainBody = document.querySelector('.main-body');
            if (mainBody) {
                container = mainBody.querySelector('#rolesContainer');
            }
        }
        
        // console.log('  rolesContainer found:', !!container);
        
        if (!container) {
            if (initAttempts < maxInitAttempts) {
                console.log('⏳ rolesContainer not found, retrying in 200ms...');
                setTimeout(initModule, 200);
            } else {
                console.error('❌ Failed to find rolesContainer after ' + maxInitAttempts + ' attempts');
            }
            return;
        }
        
        console.log('✅ Found rolesContainer element');
        console.log('📊 Roles data:', roles.length, 'roles loaded');
        
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
                var roleModal = getEl('roleModal');
                var detailModal = getEl('roleDetailModal');
                if (roleModal && roleModal.classList.contains('show')) {
                    closeRoleModal();
                }
                if (detailModal && detailModal.classList.contains('show')) {
                    closeRoleDetail();
                }
            }
        });
        
        renderStats();
        renderRoles();
        
        console.log('✅ Roles & Permissions module loaded successfully!');
        console.log('🔑 ' + roles.length + ' roles loaded');
        console.log('🛡️ ' + permissionDefinitions.length + ' permissions defined');
    }

    // ============================================
    // START INIT
    // ============================================

    // Try to init immediately
    setTimeout(initModule, 50);

    // Also listen for DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOMContentLoaded fired');
            setTimeout(initModule, 50);
        });
    }

    // Additional fallback: try after window load
    window.addEventListener('load', function() {
        console.log('📄 Window load fired');
        // Check if roles were rendered
        var container = document.getElementById('rolesContainer');
        if (container && container.children.length === 0) {
            console.log('⚠️ Roles not rendered after load, re-initializing...');
            setTimeout(initModule, 100);
        }
    });

    // ============================================
    // MAKE FUNCTIONS GLOBAL // roles_permissions.gs
    // ============================================

    window.applyFilters = applyFilters;
    window.clearFilters = clearFilters;
    window.goToPage = goToPage;
    window.showCreateRoleModal = showCreateRoleModal;
    window.editRole = editRole;
    window.closeRoleModal = closeRoleModal;
    window.saveRole = saveRole;
    window.viewRoleDetail = viewRoleDetail;
    window.closeRoleDetail = closeRoleDetail;
    window.deleteRole = deleteRole;
    window.renderRoles = renderRoles;
    window.renderStats = renderStats;
    window.showToast = showToast;
    window.initModule = initModule;

    // Expose roles data for debugging
    window.__roles = roles;
    window.__permissions = permissionDefinitions;

    console.log('🔑 Roles & Permissions module script loaded');
    console.log('📊 Available roles:', roles.length);
    console.log('💡 Tip: If roles don\'t appear, check that the HTML has <div id="rolesContainer">');
    console.log('💡 Tip: Run initModule() manually in console if needed');

})(); // <-- The closing parenthesis safely locks the scope