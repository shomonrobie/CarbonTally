// Team Management Module - SPA Compatible
(function(){
    console.log('👥 Team Management JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var members = [
        { id: 'mem_001', name: 'John Doe', email: 'john.doe@carbontally.com', role: 'admin', department: 'Sustainability', status: 'active', joined: '2025-01-15', lastActive: '2026-12-15', avatar: 'JD', permissions: ['full_access'], reviewsCompleted: 156, accuracyRate: 98.5, workload: 12 },
        { id: 'mem_002', name: 'Sarah Johnson', email: 'sarah.johnson@carbontally.com', role: 'manager', department: 'Operations', status: 'active', joined: '2025-03-10', lastActive: '2026-12-14', avatar: 'SJ', permissions: ['view_all', 'edit_data', 'manage_team'], reviewsCompleted: 89, accuracyRate: 96.2, workload: 8 },
        { id: 'mem_003', name: 'Mike Roberts', email: 'mike.roberts@carbontally.com', role: 'analyst', department: 'Compliance', status: 'active', joined: '2025-06-01', lastActive: '2026-12-13', avatar: 'MR', permissions: ['view_all', 'edit_data'], reviewsCompleted: 234, accuracyRate: 97.8, workload: 15 },
        { id: 'mem_004', name: 'Anna Liu', email: 'anna.liu@carbontally.com', role: 'analyst', department: 'Finance', status: 'active', joined: '2025-08-15', lastActive: '2026-12-12', avatar: 'AL', permissions: ['view_all', 'edit_data'], reviewsCompleted: 167, accuracyRate: 95.4, workload: 10 },
        { id: 'mem_005', name: 'Tom Chen', email: 'tom.chen@carbontally.com', role: 'viewer', department: 'IT', status: 'active', joined: '2025-09-01', lastActive: '2026-12-11', avatar: 'TC', permissions: ['view_all'], reviewsCompleted: 0, accuracyRate: 0, workload: 0 },
        { id: 'mem_006', name: 'Emma Martinez', email: 'emma.martinez@carbontally.com', role: 'staff', department: 'Sustainability', status: 'active', joined: '2025-10-20', lastActive: '2026-12-14', avatar: 'EM', permissions: ['view_all', 'edit_data', 'upload_files'], reviewsCompleted: 45, accuracyRate: 92.1, workload: 5 },
        { id: 'mem_007', name: 'David Kim', email: 'david.kim@carbontally.com', role: 'admin', department: 'Sustainability', status: 'active', joined: '2025-02-01', lastActive: '2026-12-14', avatar: 'DK', permissions: ['full_access'], reviewsCompleted: 312, accuracyRate: 99.2, workload: 18 },
        { id: 'mem_008', name: 'Lisa Patel', email: 'lisa.patel@carbontally.com', role: 'manager', department: 'Operations', status: 'active', joined: '2025-04-15', lastActive: '2026-12-13', avatar: 'LP', permissions: ['view_all', 'edit_data', 'manage_team'], reviewsCompleted: 78, accuracyRate: 94.7, workload: 7 },
        { id: 'mem_009', name: 'James Wilson', email: 'james.wilson@carbontally.com', role: 'analyst', department: 'Compliance', status: 'active', joined: '2025-07-01', lastActive: '2026-12-12', avatar: 'JW', permissions: ['view_all', 'edit_data'], reviewsCompleted: 198, accuracyRate: 96.9, workload: 13 },
        { id: 'mem_010', name: 'Maria Garcia', email: 'maria.garcia@carbontally.com', role: 'analyst', department: 'Finance', status: 'active', joined: '2025-09-15', lastActive: '2026-12-11', avatar: 'MG', permissions: ['view_all', 'edit_data'], reviewsCompleted: 123, accuracyRate: 95.8, workload: 9 },
        { id: 'mem_011', name: 'Alex Turner', email: 'alex.turner@carbontally.com', role: 'viewer', department: 'HR', status: 'active', joined: '2025-11-01', lastActive: '2026-12-10', avatar: 'AT', permissions: ['view_all'], reviewsCompleted: 0, accuracyRate: 0, workload: 0 },
        { id: 'mem_012', name: 'Rachel Brown', email: 'rachel.brown@carbontally.com', role: 'staff', department: 'Sustainability', status: 'active', joined: '2025-12-01', lastActive: '2026-12-14', avatar: 'RB', permissions: ['view_all', 'edit_data', 'upload_files'], reviewsCompleted: 34, accuracyRate: 91.3, workload: 4 }
    ];

    var invitations = [
        { id: 'inv_001', email: 'new.hire@company.com', role: 'analyst', department: 'Sustainability', status: 'pending', sent: '2026-12-10', expires: '2027-01-10', message: 'Welcome to CarbonTally!' },
        { id: 'inv_002', email: 'consultant@firm.com', role: 'viewer', department: 'Compliance', status: 'pending', sent: '2026-12-12', expires: '2027-01-12', message: 'Please review our compliance data.' },
        { id: 'inv_003', email: 'partner@vendor.com', role: 'staff', department: 'Operations', status: 'pending', sent: '2026-12-13', expires: '2027-01-13', message: 'Let\'s collaborate on the upcoming project.' }
    ];

    var roles = [
        { id: 'role_001', name: 'Admin', description: 'Full access to all features and settings', permissions: ['full_access'], members: 2, color: '#10b981' },
        { id: 'role_002', name: 'Manager', description: 'Can manage team and view all data', permissions: ['view_all', 'edit_data', 'manage_team'], members: 2, color: '#3b82f6' },
        { id: 'role_003', name: 'Analyst', description: 'Can view and edit emissions data', permissions: ['view_all', 'edit_data'], members: 4, color: '#8b5cf6' },
        { id: 'role_004', name: 'Staff', description: 'Can view data and upload files', permissions: ['view_all', 'edit_data', 'upload_files'], members: 2, color: '#f59e0b' },
        { id: 'role_005', name: 'Viewer', description: 'Read-only access to all data', permissions: ['view_all'], members: 2, color: '#6b7280' }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentTab = 'members';
    var sortField = 'name';
    var sortDirection = 'asc';
    var currentPage = 1;
    var perPage = 5;
    var toastTimeout = null;
    var selectedMemberId = null;

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
    // NAVIGATION
    // ============================================

    function navigateToRoles() {
        // Navigate to roles & permissions module
        if (typeof loadModule === 'function') {
            loadModule('roles');
            showToast('🔑 Navigating to Roles & Permissions');
        } else {
            showToast('🔑 Roles & Permissions module', 'info');
        }
    }

    // ============================================
    // HELPERS
    // ============================================

    function getRoleBadge(role) {
        var badges = {
            'admin': '<span class="badge badge-success">👑 Admin</span>',
            'manager': '<span class="badge badge-primary">📋 Manager</span>',
            'analyst': '<span class="badge badge-warning">📊 Analyst</span>',
            'staff': '<span class="badge badge-muted">👤 Staff</span>',
            'viewer': '<span class="badge badge-muted">👁️ Viewer</span>'
        };
        return badges[role] || badges.viewer;
    }

    function getStatusBadge(status) {
        var badges = {
            'active': '<span class="badge badge-success">🟢 Active</span>',
            'inactive': '<span class="badge badge-muted">⚪ Inactive</span>',
            'pending': '<span class="badge badge-warning">🟡 Pending</span>',
            'suspended': '<span class="badge badge-destructive">🔴 Suspended</span>'
        };
        return badges[status] || badges.active;
    }

    function getInitials(name) {
        return name.split(' ').map(function(n) { return n[0]; }).join('').toUpperCase().slice(0, 2);
    }

    function getRandomColor(name) {
        var colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#14b8a6', '#f97316', '#6366f1'];
        var hash = 0;
        for (var i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        return colors[Math.abs(hash) % colors.length];
    }

    // ============================================
    // TAB FUNCTIONS
    // ============================================

    function switchTab(tab) {
        currentTab = tab;
        var tabs = document.querySelectorAll('.tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.toggle('active', tabs[i].getAttribute('data-tab') === tab);
        }
        var sections = document.querySelectorAll('[id^="tab-"]');
        for (var j = 0; j < sections.length; j++) {
            sections[j].style.display = sections[j].id === 'tab-' + tab ? 'block' : 'none';
        }
        
        if (tab === 'members') renderMembers();
        else if (tab === 'invitations') renderInvitations();
        else if (tab === 'staff') renderStaffMetrics();
        else if (tab === 'roles') renderRoles();
    }

    // ============================================
    // TEAM STATS
    // ============================================

    function renderTeamStats() {
        var total = members.length;
        var active = 0, admins = 0;
        for (var i = 0; i < members.length; i++) {
            if (members[i].status === 'active') active++;
            if (members[i].role === 'admin') admins++;
        }
        var pending = invitations.length;

        var stats = document.querySelectorAll('.team-stat');
        if (stats[0]) stats[0].innerHTML = '<span class="icon">👥</span><div class="value">' + total + '</div><div class="label">Total Members</div>';
        if (stats[1]) stats[1].innerHTML = '<span class="icon">🟢</span><div class="value">' + active + '</div><div class="label">Active</div>';
        if (stats[2]) stats[2].innerHTML = '<span class="icon">👑</span><div class="value">' + admins + '</div><div class="label">Admins</div>';
        if (stats[3]) stats[3].innerHTML = '<span class="icon">📨</span><div class="value">' + pending + '</div><div class="label">Pending Invitations</div>';
    }

    // ============================================
    // MEMBER FUNCTIONS
    // ============================================

    function renderMembers() {
        var container = getEl('memberList');
        var countEl = getEl('memberCount');
        var paginationEl = getEl('memberPagination');
        if (!container) return;
        
        var searchTerm = getEl('searchInput') ? getEl('searchInput').value.toLowerCase().trim() : '';
        var roleFilter = getEl('roleFilter') ? getEl('roleFilter').value : 'all';
        var statusFilter = getEl('statusFilter') ? getEl('statusFilter').value : 'all';
        var deptFilter = getEl('deptFilter') ? getEl('deptFilter').value : 'all';
        
        var filtered = members.slice();
        
        if (roleFilter !== 'all') {
            filtered = filtered.filter(function(m) { return m.role === roleFilter; });
        }
        if (statusFilter !== 'all') {
            filtered = filtered.filter(function(m) { return m.status === statusFilter; });
        }
        if (deptFilter !== 'all') {
            filtered = filtered.filter(function(m) { return m.department === deptFilter; });
        }
        if (searchTerm) {
            filtered = filtered.filter(function(m) {
                return m.name.toLowerCase().indexOf(searchTerm) !== -1 ||
                    m.email.toLowerCase().indexOf(searchTerm) !== -1 ||
                    m.department.toLowerCase().indexOf(searchTerm) !== -1 ||
                    m.role.toLowerCase().indexOf(searchTerm) !== -1;
            });
        }
        
        // Sort
        filtered.sort(function(a, b) {
            var valA = a[sortField] || '';
            var valB = b[sortField] || '';
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
        
        if (countEl) countEl.textContent = filtered.length + ' members';
        
        var start = (currentPage - 1) * perPage;
        var pageItems = filtered.slice(start, start + perPage);
        
        if (pageItems.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:40px 20px;"><div style="font-size:32px;margin-bottom:8px;">👤</div><div>No members found</div><div style="font-size:13px;">Try adjusting your search or invite new members</div></div>';
            renderMemberPagination(filtered.length);
            return;
        }
        
        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var m = pageItems[i];
            html +=
                '<div class="member-item" onclick="viewMemberDetail(\'' + m.id + '\')">' +
                '<div class="avatar" style="background:' + getRandomColor(m.name) + ';">' + (m.avatar || getInitials(m.name)) + '</div>' +
                '<div class="member-info"><div class="name">' + m.name + '</div><div class="email">' + m.email + '</div>' +
                '<div class="meta"><span>🏢 ' + m.department + '</span><span>📅 Joined ' + m.joined + '</span><span>📊 ' + (m.reviewsCompleted || 0) + ' reviews</span><span>🎯 ' + (m.accuracyRate || 0) + '% accuracy</span></div></div>' +
                '<div class="member-role">' + getRoleBadge(m.role) + getStatusBadge(m.status) + '</div>' +
                '<div class="member-actions">' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();viewMemberDetail(\'' + m.id + '\')" title="View Details">👁️</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();editMember(\'' + m.id + '\')" title="Edit">✏️</button>' +
                (m.role !== 'admin' ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();removeMember(\'' + m.id + '\')" style="color:hsl(var(--destructive));" title="Remove">✕</button>' : '') +
                '</div></div>';
        }
        container.innerHTML = html;
        renderMemberPagination(filtered.length);
    }

    function renderMemberPagination(total) {
        var container = getEl('memberPagination');
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' members</div><div class="page-buttons"></div>';
            return;
        }
        
        var startItem = (currentPage - 1) * perPage + 1;
        var endItem = Math.min(currentPage * perPage, total);
        
        var btns = '<button class="page-btn" onclick="goToMemberPage(' + (currentPage - 1) + ')" ' + (currentPage <= 1 ? 'disabled' : '') + '>‹</button>';
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            btns += '<button class="page-btn" onclick="goToMemberPage(1)">1</button>';
            if (startPage > 2) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
        }
        for (var i = startPage; i <= endPage; i++) {
            btns += '<button class="page-btn ' + (i === currentPage ? 'active' : '') + '" onclick="goToMemberPage(' + i + ')">' + i + '</button>';
        }
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
            btns += '<button class="page-btn" onclick="goToMemberPage(' + totalPages + ')">' + totalPages + '</button>';
        }
        btns += '<button class="page-btn" onclick="goToMemberPage(' + (currentPage + 1) + ')" ' + (currentPage >= totalPages ? 'disabled' : '') + '>›</button>';
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' members</div><div class="page-buttons">' + btns + '</div>';
    }

    function goToMemberPage(page) {
        var totalPages = Math.ceil(members.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderMembers();
    }

    function sortMembers(field) {
        if (sortField === field) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortField = field;
            sortDirection = 'asc';
        }
        currentPage = 1;
        renderMembers();
    }

    function clearMemberFilters() {
        var roleEl = getEl('roleFilter');
        var statusEl = getEl('statusFilter');
        var deptEl = getEl('deptFilter');
        var searchEl = getEl('searchInput');
        if (roleEl) roleEl.value = 'all';
        if (statusEl) statusEl.value = 'all';
        if (deptEl) deptEl.value = 'all';
        if (searchEl) searchEl.value = '';
        currentPage = 1;
        renderMembers();
        showToast('🔄 Filters cleared');
    }

    function viewMemberDetail(id) {
        var member = null;
        for (var i = 0; i < members.length; i++) {
            if (members[i].id === id) { member = members[i]; break; }
        }
        if (!member) return;
        
        selectedMemberId = id;
        var titleEl = getEl('memberDetailTitle');
        var subtitleEl = getEl('memberDetailSubtitle');
        var bodyEl = getEl('memberDetailBody');
        var footerEl = getEl('memberDetailFooter');
        var modal = getEl('memberDetailModal');
        
        if (titleEl) titleEl.textContent = member.name;
        if (subtitleEl) subtitleEl.textContent = member.role.toUpperCase() + ' • ' + member.department;
        
        if (bodyEl) {
            var permHtml = '';
            for (var j = 0; j < member.permissions.length; j++) {
                permHtml += '<span class="badge badge-muted">' + member.permissions[j].replace('_', ' ').toUpperCase() + '</span>';
            }
            
            bodyEl.innerHTML =
                '<div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">' +
                '<div class="avatar avatar-lg" style="background:' + getRandomColor(member.name) + ';font-size:24px;">' + (member.avatar || getInitials(member.name)) + '</div>' +
                '<div><div style="font-size:18px;font-weight:700;color:hsl(var(--foreground));">' + member.name + '</div><div style="font-size:14px;color:hsl(var(--muted-foreground));">' + member.email + '</div></div></div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
                '<div class="detail-row"><span class="label">Role</span><span class="value">' + getRoleBadge(member.role) + '</span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + getStatusBadge(member.status) + '</span></div>' +
                '<div class="detail-row"><span class="label">Department</span><span class="value">' + member.department + '</span></div>' +
                '<div class="detail-row"><span class="label">Joined</span><span class="value">' + member.joined + '</span></div>' +
                '<div class="detail-row"><span class="label">Last Active</span><span class="value">' + member.lastActive + '</span></div>' +
                '<div class="detail-row"><span class="label">Workload</span><span class="value">' + (member.workload || 0) + ' reviews</span></div>' +
                '<div class="detail-row"><span class="label">Reviews Completed</span><span class="value">' + (member.reviewsCompleted || 0) + '</span></div>' +
                '<div class="detail-row"><span class="label">Accuracy Rate</span><span class="value">' + (member.accuracyRate || 0) + '%</span></div></div>' +
                '<div style="margin-top:12px;"><span style="font-weight:500;color:hsl(var(--muted-foreground));font-size:13px;">Permissions:</span><div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:4px;">' + permHtml + '</div></div>';
        }
        
        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeMemberDetail()">Close</button>' +
                '<button class="btn btn-outline btn-sm" onclick="editMember(\'' + member.id + '\');closeMemberDetail();">✏️ Edit</button>' +
                (member.role !== 'admin' ? '<button class="btn btn-danger btn-sm" onclick="removeMember(\'' + member.id + '\');closeMemberDetail();">🗑️ Remove</button>' : '');
        }
        
        if (modal) modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeMemberDetail() {
        var modal = getEl('memberDetailModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function editMember(id) {
        var member = null;
        for (var i = 0; i < members.length; i++) {
            if (members[i].id === id) { member = members[i]; break; }
        }
        if (member) {
            showToast('✏️ Editing ' + member.name, 'info');
        }
    }

    function removeMember(id) {
        var member = null;
        for (var i = 0; i < members.length; i++) {
            if (members[i].id === id) { member = members[i]; break; }
        }
        if (!member) return;
        if (member.role === 'admin') {
            showToast('⚠️ Cannot remove admin user', 'warning');
            return;
        }
        if (confirm('Are you sure you want to remove ' + member.name + ' from the team?')) {
            var newMembers = [];
            for (var i = 0; i < members.length; i++) {
                if (members[i].id !== id) {
                    newMembers.push(members[i]);
                }
            }
            members = newMembers;
            renderMembers();
            renderTeamStats();
            showToast('🗑️ Removed ' + member.name + ' from team');
        }
    }

    // ============================================
    // INVITATION FUNCTIONS
    // ============================================

    function renderInvitations() {
        var container = getEl('invitationList');
        var badge = getEl('inviteBadge');
        if (!container) return;
        
        if (invitations.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:40px 20px;"><div style="font-size:32px;margin-bottom:8px;">📨</div><div>No pending invitations</div><div style="font-size:13px;">Send invitations to new team members</div></div>';
            if (badge) badge.textContent = '0';
            return;
        }
        
        var html = '';
        for (var i = 0; i < invitations.length; i++) {
            var inv = invitations[i];
            html +=
                '<div class="member-item">' +
                '<div style="display:flex;align-items:center;gap:12px;flex:1;">' +
                '<div style="font-size:28px;">📨</div>' +
                '<div class="member-info"><div class="name">' + inv.email + '</div>' +
                '<div class="meta"><span>🎯 ' + inv.role + '</span><span>🏢 ' + inv.department + '</span><span>📅 Sent ' + inv.sent + '</span><span>⏰ Expires ' + inv.expires + '</span></div>' +
                '<div style="font-size:12px;color:hsl(var(--muted-foreground));margin-top:2px;">"' + inv.message + '"</div></div></div>' +
                '<div style="display:flex;gap:4px;flex-shrink:0;"><span class="badge badge-warning">⏳ Pending</span>' +
                '<button class="btn btn-ghost btn-sm" onclick="resendInvite(\'' + inv.id + '\')" title="Resend">📤</button>' +
                '<button class="btn btn-ghost btn-sm" onclick="cancelInvite(\'' + inv.id + '\')" style="color:hsl(var(--destructive));" title="Cancel">✕</button></div></div>';
        }
        container.innerHTML = html;
        if (badge) badge.textContent = invitations.length;
    }

    function resendInvite(id) {
        var inv = null;
        for (var i = 0; i < invitations.length; i++) {
            if (invitations[i].id === id) { inv = invitations[i]; break; }
        }
        if (inv) {
            showToast('📨 Resent invitation to ' + inv.email);
        }
    }

    function cancelInvite(id) {
        if (confirm('Cancel this invitation?')) {
            var index = -1;
            var email = '';
            for (var i = 0; i < invitations.length; i++) {
                if (invitations[i].id === id) { index = i; email = invitations[i].email; break; }
            }
            if (index !== -1) {
                invitations.splice(index, 1);
                renderInvitations();
                showToast('🗑️ Cancelled invitation to ' + email);
            }
        }
    }

    function showInviteModal() {
        var modal = getEl('inviteModal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            var emailEl = getEl('inviteEmail');
            var msgEl = getEl('inviteMessage');
            if (emailEl) emailEl.value = '';
            if (msgEl) msgEl.value = '';
        }
    }

    function closeInviteModal() {
        var modal = getEl('inviteModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function sendInvite() {
        var emailEl = getEl('inviteEmail');
        var roleEl = getEl('inviteRole');
        var deptEl = getEl('inviteDepartment');
        var msgEl = getEl('inviteMessage');
        
        var email = emailEl ? emailEl.value.trim() : '';
        var role = roleEl ? roleEl.value : 'analyst';
        var department = deptEl ? deptEl.value : 'Sustainability';
        var message = msgEl ? msgEl.value.trim() || 'Welcome to CarbonTally!' : 'Welcome to CarbonTally!';
        
        if (!email) {
            showToast('⚠️ Please enter an email address', 'warning');
            if (emailEl) emailEl.focus();
            return;
        }
        if (email.indexOf('@') === -1) {
            showToast('⚠️ Please enter a valid email address', 'warning');
            if (emailEl) emailEl.focus();
            return;
        }
        
        for (var i = 0; i < invitations.length; i++) {
            if (invitations[i].email === email) {
                showToast('⚠️ An invitation has already been sent to this email', 'warning');
                return;
            }
        }
        for (var j = 0; j < members.length; j++) {
            if (members[j].email === email) {
                showToast('⚠️ This email is already a team member', 'warning');
                return;
            }
        }
        
        var newInvite = {
            id: 'inv_' + String(invitations.length + 1).padStart(3, '0'),
            email: email,
            role: role,
            department: department,
            status: 'pending',
            sent: new Date().toISOString().split('T')[0],
            expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            message: message
        };
        
        invitations.push(newInvite);
        closeInviteModal();
        renderInvitations();
        renderTeamStats();
        showToast('📨 Invitation sent to ' + email);
    }

    // ============================================
    // STAFF METRICS
    // ============================================

    function renderStaffMetrics() {
        var container = getEl('staffMetrics');
        if (!container) return;
        
        var totalReviews = 0, totalAccuracy = 0, totalWorkload = 0, activeCount = 0;
        for (var i = 0; i < members.length; i++) {
            var m = members[i];
            totalReviews += (m.reviewsCompleted || 0);
            totalAccuracy += (m.accuracyRate || 0);
            totalWorkload += (m.workload || 0);
            if (m.status === 'active') activeCount++;
        }
        var avgAccuracy = members.length > 0 ? totalAccuracy / members.length : 0;
        var avgWorkload = members.length > 0 ? totalWorkload / members.length : 0;
        
        var topPerformers = members.slice().filter(function(m) { return m.reviewsCompleted > 0; });
        topPerformers.sort(function(a, b) { return b.reviewsCompleted - a.reviewsCompleted; });
        topPerformers = topPerformers.slice(0, 3);
        
        var html =
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:16px;margin-bottom:20px;">' +
            '<div class="staff-metric-card"><div class="value">' + totalReviews + '</div><div class="label">Total Reviews</div></div>' +
            '<div class="staff-metric-card"><div class="value">' + avgAccuracy.toFixed(1) + '%</div><div class="label">Avg Accuracy</div></div>' +
            '<div class="staff-metric-card"><div class="value">' + avgWorkload.toFixed(1) + '</div><div class="label">Avg Workload</div></div>' +
            '<div class="staff-metric-card"><div class="value">' + activeCount + '</div><div class="label">Active Members</div></div></div>' +
            
            '<div style="margin-bottom:16px;"><h4 style="font-size:14px;font-weight:600;color:hsl(var(--foreground));margin-bottom:8px;">🏆 Top Performers</h4>';
        
        for (var j = 0; j < topPerformers.length; j++) {
            var m = topPerformers[j];
            html +=
                '<div class="member-item" style="margin-bottom:4px;padding:8px 12px;">' +
                '<div class="avatar avatar-sm" style="background:' + getRandomColor(m.name) + ';">' + (m.avatar || getInitials(m.name)) + '</div>' +
                '<div class="member-info"><div class="name">' + m.name + '</div><div class="meta">' + m.role + ' • ' + m.department + '</div></div>' +
                '<div style="display:flex;gap:16px;font-size:12px;"><span>📊 ' + m.reviewsCompleted + ' reviews</span><span>🎯 ' + m.accuracyRate + '% accuracy</span><span>⏳ ' + m.workload + ' workload</span></div></div>';
        }
        
        html += '</div><div><h4 style="font-size:14px;font-weight:600;color:hsl(var(--foreground));margin-bottom:8px;">📊 Workload Distribution</h4><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;">';
        
        for (var k = 0; k < members.length; k++) {
            var m = members[k];
            if (m.status !== 'active') continue;
            var pct = Math.min((m.workload || 0) / 20 * 100, 100);
            var color = m.workload > 15 ? 'hsl(var(--destructive))' : m.workload > 10 ? 'hsl(var(--warning))' : 'hsl(var(--success))';
            html +=
                '<div style="padding:8px 12px;border-radius:var(--radius);border:1px solid hsl(var(--border));">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-size:13px;font-weight:500;">' + m.name + '</span><span style="font-size:12px;font-weight:600;">' + (m.workload || 0) + '</span></div>' +
                '<div class="progress-bar" style="margin-top:4px;"><div class="fill" style="width:' + pct + '%;background:' + color + ';"></div></div></div>';
        }
        
        html += '</div></div>';
        container.innerHTML = html;
    }

    // ============================================
    // ROLES FUNCTIONS
    // ============================================

    function renderRoles() {
        var container = getEl('rolesList');
        if (!container) return;
        
        var html = '';
        for (var i = 0; i < roles.length; i++) {
            var role = roles[i];
            var permHtml = '';
            for (var j = 0; j < role.permissions.length; j++) {
                permHtml += '<span class="badge badge-muted">' + role.permissions[j].replace('_', ' ').toUpperCase() + '</span>';
            }
            html +=
                '<div class="member-item">' +
                '<div style="display:flex;align-items:center;gap:12px;flex:1;">' +
                '<div style="width:4px;height:32px;border-radius:4px;background:' + role.color + ';flex-shrink:0;"></div>' +
                '<div class="member-info"><div class="name">' + role.name + '</div><div class="meta">' + role.description + '</div>' +
                '<div style="display:flex;gap:4px;margin-top:4px;flex-wrap:wrap;">' + permHtml + '</div></div></div>' +
                '<div style="display:flex;gap:12px;align-items:center;flex-shrink:0;">' +
                '<span class="badge badge-muted">' + role.members + ' members</span>' +
                '<button class="btn btn-ghost btn-sm" onclick="navigateToRoles()" title="Manage Roles">🔑</button>' +
                '</div></div>';
        }
        container.innerHTML = html;
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        //console.log('🚀 Initializing Team Management Module...');
        
        var container = getEl('memberList');
        if (!container) {
            //console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
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
                var inviteModal = getEl('inviteModal');
                var detailModal = getEl('memberDetailModal');
                if (inviteModal && inviteModal.classList.contains('show')) {
                    closeInviteModal();
                }
                if (detailModal && detailModal.classList.contains('show')) {
                    closeMemberDetail();
                }
            }
            // Ctrl+I to open invite modal
            if (e.key === 'i' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                showInviteModal();
            }
        });
        
        renderTeamStats();
        renderMembers();
        renderInvitations();
        renderStaffMetrics();
        renderRoles();
        
        console.log('✅ Team Management module loaded successfully!');
        console.log('👥 ' + members.length + ' members loaded');
        console.log('📨 ' + invitations.length + ' invitations pending');
        console.log('⌨️  Ctrl+I to open invite modal');
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

    window.switchTab = switchTab;
    window.renderMembers = renderMembers;
    window.sortMembers = sortMembers;
    window.clearMemberFilters = clearMemberFilters;
    window.goToMemberPage = goToMemberPage;
    window.viewMemberDetail = viewMemberDetail;
    window.closeMemberDetail = closeMemberDetail;
    window.editMember = editMember;
    window.removeMember = removeMember;
    window.showInviteModal = showInviteModal;
    window.closeInviteModal = closeInviteModal;
    window.sendInvite = sendInvite;
    window.resendInvite = resendInvite;
    window.cancelInvite = cancelInvite;
    window.renderInvitations = renderInvitations;
    window.renderStaffMetrics = renderStaffMetrics;
    window.renderRoles = renderRoles;
    window.renderTeamStats = renderTeamStats;
    window.navigateToRoles = navigateToRoles;
    window.showToast = showToast;
})(); 