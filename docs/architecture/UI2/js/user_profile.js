// User Profile Module - SPA Compatible
(function(){
    console.log('👤 User Profile JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var userProfile = {
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@carbontally.com',
        role: 'Admin',
        department: 'Sustainability',
        joinDate: '2024-01-15',
        status: 'active',
        avatar: 'JD',
        bio: 'Sustainability professional with 10+ years experience in carbon accounting and ESG reporting. Passionate about helping organizations achieve their net-zero goals.',
        location: 'London, UK',
        phone: '+44 20 1234 5678',
        company: 'CarbonTally Ltd',
        jobTitle: 'Senior Sustainability Manager'
    };

    var activityHistory = [
        { title: 'Logged in', desc: 'From IP 192.168.1.1', time: '2 hours ago' },
        { title: 'Uploaded SECR Report', desc: 'Q4 2026 documentation', time: '4 hours ago' },
        { title: 'Approved CSRD Data', desc: 'Verified Scope 2 emissions', time: '1 day ago' },
        { title: 'Sent message to Sarah', desc: 'Regarding SECR review', time: '1 day ago' },
        { title: 'Generated GHG Report', desc: 'Annual emissions inventory', time: '2 days ago' },
        { title: 'Reviewed ISSB findings', desc: '3 data points need attention', time: '2 days ago' },
        { title: 'Exported emission data', desc: 'Q4 2026 emissions export', time: '3 days ago' }
    ];

    var performanceStats = {
        totalReviews: 342,
        accuracyRate: 94.7,
        avgReviewTime: '8.5 min',
        documentsProcessed: 2156,
        complianceScore: 98,
        teamRank: 2
    };

    // ============================================
    // STATE
    // ============================================

    var currentSection = 'profile';
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
    // RENDER FUNCTIONS
    // ============================================

    function renderProfileSidebar() {
        var p = userProfile;
        var sidebar = getEl('profileSidebar');
        if (!sidebar) return;

        sidebar.innerHTML = 
            '<div class="card profile-card">' +
                '<div class="card-content" style="text-align:center;padding:20px;">' +
                    '<div class="profile-avatar">' +
                        '<div class="avatar avatar-lg">' + p.avatar + '</div>' +
                    '</div>' +
                    '<div class="profile-name">' + p.firstName + ' ' + p.lastName + '</div>' +
                    '<div class="profile-role">' + p.jobTitle + ' · ' + p.department + '</div>' +
                    '<div style="margin-top:4px;"><span class="badge badge-success">● Active</span></div>' +
                    '<div style="margin-top:12px;padding-top:12px;border-top:1px solid hsl(var(--border));text-align:left;font-size:13px;color:hsl(var(--muted-foreground));">' +
                        '<div>📧 ' + p.email + '</div>' +
                        '<div>📍 ' + p.location + '</div>' +
                        '<div>📱 ' + p.phone + '</div>' +
                        '<div>🏢 ' + p.company + '</div>' +
                        '<div>📅 Joined ' + p.joinDate + '</div>' +
                    '</div>' +
                    '<div style="margin-top:12px;padding-top:12px;border-top:1px solid hsl(var(--border));text-align:left;font-size:13px;">' + p.bio + '</div>' +
                '</div>' +
            '</div>' +
            '<div class="card" style="margin-top:16px;">' +
                '<div class="card-content" style="padding:8px 12px;">' +
                    '<div class="profile-menu">' +
                        '<button class="profile-menu-item ' + (currentSection === 'profile' ? 'active' : '') + '" onclick="switchSection(\'profile\')">' +
                            '<span class="menu-icon">👤</span> Profile' +
                        '</button>' +
                        '<button class="profile-menu-item ' + (currentSection === 'activity' ? 'active' : '') + '" onclick="switchSection(\'activity\')">' +
                            '<span class="menu-icon">📋</span> Activity History' +
                        '</button>' +
                        '<button class="profile-menu-item ' + (currentSection === 'preferences' ? 'active' : '') + '" onclick="switchSection(\'preferences\')">' +
                            '<span class="menu-icon">⚙️</span> Preferences' +
                        '</button>' +
                        '<button class="profile-menu-item ' + (currentSection === 'security' ? 'active' : '') + '" onclick="switchSection(\'security\')">' +
                            '<span class="menu-icon">🔒</span> Security' +
                        '</button>' +
                    '</div>' +
                '</div>' +
            '</div>';
    }

    function renderProfileContent() {
        var container = getEl('profileContent');
        if (!container) return;

        if (currentSection === 'profile') {
            var stats = performanceStats;
            var activitiesHtml = '';
            for (var i = 0; i < Math.min(5, activityHistory.length); i++) {
                var a = activityHistory[i];
                activitiesHtml += 
                    '<div class="activity-item">' +
                        '<div class="activity-icon">📌</div>' +
                        '<div class="activity-content">' +
                            '<div class="title">' + a.title + '</div>' +
                            '<div class="desc">' + a.desc + '</div>' +
                            '<div class="time">' + a.time + '</div>' +
                        '</div>' +
                    '</div>';
            }

            container.innerHTML = 
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">' +
                    '<div class="card">' +
                        '<div class="card-header"><div class="card-title">📊 Performance Overview</div></div>' +
                        '<div class="card-content">' +
                            '<div class="performance-grid">' +
                                '<div class="performance-item">' +
                                    '<div class="value">' + stats.totalReviews + '</div>' +
                                    '<div class="label">Total Reviews</div>' +
                                '</div>' +
                                '<div class="performance-item">' +
                                    '<div class="value" style="color:hsl(var(--success));">' + stats.accuracyRate + '%</div>' +
                                    '<div class="label">Accuracy Rate</div>' +
                                '</div>' +
                                '<div class="performance-item">' +
                                    '<div class="value" style="color:hsl(var(--warning));">' + stats.avgReviewTime + '</div>' +
                                    '<div class="label">Avg Review Time</div>' +
                                '</div>' +
                                '<div class="performance-item">' +
                                    '<div class="value">' + stats.documentsProcessed + '</div>' +
                                    '<div class="label">Documents Processed</div>' +
                                '</div>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="card">' +
                        '<div class="card-header"><div class="card-title">🏆 Achievements</div></div>' +
                        '<div class="card-content">' +
                            '<div class="achievement-item">' +
                                '<span class="emoji">🥇</span>' +
                                '<div class="info"><div class="title">Top Performer</div><div class="desc">Ranked #' + stats.teamRank + ' in team</div></div>' +
                            '</div>' +
                            '<div class="achievement-item">' +
                                '<span class="emoji">🎯</span>' +
                                '<div class="info"><div class="title">Compliance Expert</div><div class="desc">' + stats.complianceScore + '% compliance score</div></div>' +
                            '</div>' +
                            '<div class="achievement-item">' +
                                '<span class="emoji">📚</span>' +
                                '<div class="info"><div class="title">Knowledge Leader</div><div class="desc">' + stats.documentsProcessed + ' documents reviewed</div></div>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="card">' +
                    '<div class="card-header">' +
                        '<div class="card-title">📈 Recent Activity</div>' +
                        '<span class="badge badge-primary">' + activityHistory.length + ' events</span>' +
                    '</div>' +
                    '<div class="card-content">' +
                        activitiesHtml +
                        '<div style="margin-top:8px;">' +
                            '<button class="btn btn-sm btn-ghost" onclick="switchSection(\'activity\')">View All Activity →</button>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        } else if (currentSection === 'activity') {
            var allActivitiesHtml = '';
            for (var j = 0; j < activityHistory.length; j++) {
                var a2 = activityHistory[j];
                allActivitiesHtml += 
                    '<div class="activity-item">' +
                        '<div class="activity-icon">📌</div>' +
                        '<div class="activity-content">' +
                            '<div class="title">' + a2.title + '</div>' +
                            '<div class="desc">' + a2.desc + '</div>' +
                            '<div class="time">' + a2.time + '</div>' +
                        '</div>' +
                    '</div>';
            }

            container.innerHTML = 
                '<div class="card">' +
                    '<div class="card-header">' +
                        '<div class="card-title">📋 Activity History</div>' +
                        '<span class="badge badge-primary">' + activityHistory.length + ' events</span>' +
                    '</div>' +
                    '<div class="card-content">' +
                        allActivitiesHtml +
                    '</div>' +
                '</div>';
        } else if (currentSection === 'preferences') {
            container.innerHTML = 
                '<div class="card">' +
                    '<div class="card-header"><div class="card-title">⚙️ Preferences</div></div>' +
                    '<div class="card-content">' +
                        '<div class="settings-group">' +
                            '<label>Language</label>' +
                            '<select>' +
                                '<option value="en" selected>English</option>' +
                                '<option value="es">Spanish</option>' +
                                '<option value="fr">French</option>' +
                                '<option value="de">German</option>' +
                            '</select>' +
                        '</div>' +
                        '<div class="settings-group">' +
                            '<label>Timezone</label>' +
                            '<select>' +
                                '<option value="GMT" selected>GMT (UTC+0)</option>' +
                                '<option value="EST">EST (UTC-5)</option>' +
                                '<option value="CET">CET (UTC+1)</option>' +
                                '<option value="PST">PST (UTC-8)</option>' +
                            '</select>' +
                        '</div>' +
                        '<div class="settings-group">' +
                            '<label>Date Format</label>' +
                            '<select>' +
                                '<option value="DD/MM/YYYY" selected>DD/MM/YYYY</option>' +
                                '<option value="MM/DD/YYYY">MM/DD/YYYY</option>' +
                                '<option value="YYYY-MM-DD">YYYY-MM-DD</option>' +
                            '</select>' +
                        '</div>' +
                        '<div style="margin-top:16px;padding-top:16px;border-top:1px solid hsl(var(--border));">' +
                            '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;">' +
                                '<div><div style="font-weight:500;">Email Notifications</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Receive email updates about activity</div></div>' +
                                '<label class="toggle-switch"><input type="checkbox" checked /><span class="toggle-slider"></span></label>' +
                            '</div>' +
                            '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;">' +
                                '<div><div style="font-weight:500;">Push Notifications</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Receive push notifications in browser</div></div>' +
                                '<label class="toggle-switch"><input type="checkbox" /><span class="toggle-slider"></span></label>' +
                            '</div>' +
                        '</div>' +
                        '<div style="margin-top:16px;">' +
                            '<button class="btn btn-primary" onclick="showToast(\'✅ Preferences saved successfully!\')">💾 Save Preferences</button>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        } else if (currentSection === 'security') {
            container.innerHTML = 
                '<div class="card">' +
                    '<div class="card-header"><div class="card-title">🔒 Security Settings</div></div>' +
                    '<div class="card-content">' +
                        '<div class="settings-group">' +
                            '<label>Current Password</label>' +
                            '<input type="password" value="••••••••" disabled />' +
                        '</div>' +
                        '<div class="settings-group">' +
                            '<label>New Password</label>' +
                            '<input type="password" placeholder="Enter new password" />' +
                        '</div>' +
                        '<div class="settings-group">' +
                            '<label>Confirm New Password</label>' +
                            '<input type="password" placeholder="Confirm new password" />' +
                        '</div>' +
                        '<div style="margin-top:16px;padding-top:16px;border-top:1px solid hsl(var(--border));">' +
                            '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;">' +
                                '<div><div style="font-weight:500;">Two-Factor Authentication</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Add an extra layer of security</div></div>' +
                                '<label class="toggle-switch"><input type="checkbox" /><span class="toggle-slider"></span></label>' +
                            '</div>' +
                            '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;">' +
                                '<div><div style="font-weight:500;">Session Management</div><div style="font-size:12px;color:hsl(var(--muted-foreground));">Active sessions: 2</div></div>' +
                                '<button class="btn btn-sm btn-outline" onclick="showToast(\'🔄 All sessions terminated\')">Logout All</button>' +
                            '</div>' +
                        '</div>' +
                        '<div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;">' +
                            '<button class="btn btn-primary" onclick="showToast(\'✅ Password updated successfully!\')">🔑 Update Password</button>' +
                            '<button class="btn btn-danger" onclick="if(confirm(\'Are you sure?\')) showToast(\'🗑️ Account deactivated\')">🗑️ Deactivate Account</button>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        }
    }

    function renderProfile() {
        renderProfileSidebar();
        renderProfileContent();
    }

    // ============================================
    // SECTION SWITCHER
    // ============================================

    function switchSection(section) {
        currentSection = section;
        renderProfile();
    }

    // ============================================
    // EDIT MODAL
    // ============================================

    function openEditModal() {
        var p = userProfile;
        var body = getEl('editModalBody');
        if (!body) return;

        body.innerHTML = 
            '<div class="settings-group">' +
                '<label>First Name <span style="color:hsl(var(--destructive));">*</span></label>' +
                '<input type="text" id="editFirstName" value="' + p.firstName + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Last Name <span style="color:hsl(var(--destructive));">*</span></label>' +
                '<input type="text" id="editLastName" value="' + p.lastName + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Email Address <span style="color:hsl(var(--destructive));">*</span></label>' +
                '<input type="email" id="editEmail" value="' + p.email + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Job Title</label>' +
                '<input type="text" id="editJobTitle" value="' + p.jobTitle + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Department</label>' +
                '<input type="text" id="editDepartment" value="' + p.department + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Company</label>' +
                '<input type="text" id="editCompany" value="' + p.company + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Phone Number</label>' +
                '<input type="text" id="editPhone" value="' + p.phone + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Location</label>' +
                '<input type="text" id="editLocation" value="' + p.location + '" />' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Bio</label>' +
                '<textarea id="editBio" rows="3">' + p.bio + '</textarea>' +
                '<div class="hint">Brief description about yourself</div>' +
            '</div>' +
            '<div class="settings-group">' +
                '<label>Status</label>' +
                '<select id="editStatus">' +
                    '<option value="active"' + (p.status === 'active' ? ' selected' : '') + '>Active</option>' +
                    '<option value="inactive"' + (p.status === 'inactive' ? ' selected' : '') + '>Inactive</option>' +
                    '<option value="suspended"' + (p.status === 'suspended' ? ' selected' : '') + '>Suspended</option>' +
                '</select>' +
            '</div>';

        var modal = getEl('editModal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeEditModal() {
        var modal = getEl('editModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function saveProfile() {
        var firstName = getEl('editFirstName');
        var lastName = getEl('editLastName');
        var email = getEl('editEmail');
        var jobTitle = getEl('editJobTitle');
        var department = getEl('editDepartment');
        var company = getEl('editCompany');
        var phone = getEl('editPhone');
        var location = getEl('editLocation');
        var bio = getEl('editBio');
        var status = getEl('editStatus');

        var fName = firstName ? firstName.value.trim() : '';
        var lName = lastName ? lastName.value.trim() : '';
        var emailVal = email ? email.value.trim() : '';
        var jobTitleVal = jobTitle ? jobTitle.value.trim() : '';
        var deptVal = department ? department.value.trim() : '';
        var companyVal = company ? company.value.trim() : '';
        var phoneVal = phone ? phone.value.trim() : '';
        var locationVal = location ? location.value.trim() : '';
        var bioVal = bio ? bio.value.trim() : '';
        var statusVal = status ? status.value : 'active';

        if (!fName || !lName || !emailVal) {
            showToast('⚠️ Please fill in all required fields', 'warning');
            return;
        }

        userProfile.firstName = fName;
        userProfile.lastName = lName;
        userProfile.email = emailVal;
        userProfile.jobTitle = jobTitleVal || userProfile.jobTitle;
        userProfile.department = deptVal || userProfile.department;
        userProfile.company = companyVal || userProfile.company;
        userProfile.phone = phoneVal || userProfile.phone;
        userProfile.location = locationVal || userProfile.location;
        userProfile.bio = bioVal || userProfile.bio;
        userProfile.status = statusVal;
        userProfile.avatar = fName[0] + lName[0];

        closeEditModal();
        renderProfile();
        showToast('✅ Profile updated successfully!');
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        console.log('🚀 Initializing User Profile Module...');
        
        var sidebar = getEl('profileSidebar');
        if (!sidebar) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        // Modal overlay click to close
        var modal = getEl('editModal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) closeEditModal();
            });
        }
        
        // Escape key to close modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var editModal = getEl('editModal');
                if (editModal && editModal.classList.contains('show')) {
                    closeEditModal();
                }
            }
        });
        
        renderProfile();
        
        console.log('✅ User Profile module loaded successfully!');
        console.log('👤 Showing profile for ' + userProfile.firstName + ' ' + userProfile.lastName);
        console.log('📈 ' + activityHistory.length + ' activities tracked');
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

    window.switchSection = switchSection;
    window.openEditModal = openEditModal;
    window.closeEditModal = closeEditModal;
    window.saveProfile = saveProfile;
    window.renderProfile = renderProfile;
    window.showToast = showToast;
})();