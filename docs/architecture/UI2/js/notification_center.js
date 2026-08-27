    // Notification Center Module - SPA Compatible
(function() {
    console.log('🔔 Notification Center JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var notifications = [
        {
            id: 'notif_001',
            type: 'report_ready',
            title: 'SECR Report 2026 Ready',
            message: 'Your SECR report for 2026 has been generated and is ready for review.',
            priority: 'high',
            is_read: false,
            read_at: null,
            link: '/reports/secr-2026',
            sent_via: ['email', 'push'],
            email_sent: true,
            email_sent_at: '2026-12-15T14:30:00Z',
            push_sent: true,
            push_sent_at: '2026-12-15T14:30:00Z',
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-15T14:30:00Z',
            metadata: { report_id: 'rpt_001', year: 2026, pages: 45 }
        },
        {
            id: 'notif_002',
            type: 'validation_needed',
            title: 'Data Validation Required',
            message: 'Fleet fuel data for Q4 2026 requires validation. 12 records need review.',
            priority: 'high',
            is_read: false,
            read_at: null,
            link: '/validation-queue',
            sent_via: ['email'],
            email_sent: true,
            email_sent_at: '2026-12-15T13:00:00Z',
            push_sent: false,
            push_sent_at: null,
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-15T13:00:00Z',
            metadata: { records: 12, file_id: 'file_002', scope: 'Scope 1' }
        },
        {
            id: 'notif_003',
            type: 'approval_required',
            title: 'Document Approval Required',
            message: 'Sarah Johnson has submitted a new document for approval: Supplier_Invoice_IT_Equipment.pdf',
            priority: 'medium',
            is_read: false,
            read_at: null,
            link: '/documents/approval',
            sent_via: ['email', 'push'],
            email_sent: true,
            email_sent_at: '2026-12-15T11:30:00Z',
            push_sent: true,
            push_sent_at: '2026-12-15T11:30:00Z',
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-15T11:30:00Z',
            metadata: { document_id: 'doc_003', submitted_by: 'Sarah Johnson', type: 'scope3' }
        },
        {
            id: 'notif_004',
            type: 'deadline_approaching',
            title: 'SECR Deadline Approaching',
            message: 'SECR report deadline is approaching (Dec 31, 2026). Please ensure all data is submitted.',
            priority: 'high',
            is_read: true,
            read_at: '2026-12-14T16:00:00Z',
            link: '/reports/deadlines',
            sent_via: ['email', 'push'],
            email_sent: true,
            email_sent_at: '2026-12-14T08:00:00Z',
            push_sent: true,
            push_sent_at: '2026-12-14T08:00:00Z',
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-14T08:00:00Z',
            metadata: { deadline: '2026-12-31', days_remaining: 16 }
        },
        {
            id: 'notif_005',
            type: 'team_update',
            title: 'New Team Member Added',
            message: 'Emma Martinez has joined the team as a Sustainability Analyst.',
            priority: 'medium',
            is_read: true,
            read_at: '2026-12-14T10:00:00Z',
            link: '/team',
            sent_via: ['email'],
            email_sent: true,
            email_sent_at: '2026-12-13T09:30:00Z',
            push_sent: false,
            push_sent_at: null,
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-13T09:30:00Z',
            metadata: { user_id: 'user_012', role: 'Analyst', department: 'Sustainability' }
        },
        {
            id: 'notif_006',
            type: 'system_update',
            title: 'System Update v2.4.1 Deployed',
            message: 'A new system update has been deployed with enhanced reporting features.',
            priority: 'low',
            is_read: true,
            read_at: '2026-12-13T14:00:00Z',
            link: '/settings/system',
            sent_via: ['email', 'push'],
            email_sent: true,
            email_sent_at: '2026-12-13T09:00:00Z',
            push_sent: true,
            push_sent_at: '2026-12-13T09:00:00Z',
            is_dismissed: true,
            dismissed_at: '2026-12-13T10:00:00Z',
            created_at: '2026-12-13T09:00:00Z',
            metadata: { version: '2.4.1', features: ['SECR templates', 'Improved validation'] }
        },
        {
            id: 'notif_007',
            type: 'document_uploaded',
            title: 'New Document Uploaded',
            message: 'Mike Roberts uploaded a new document: Business_Travel_Expenses_Q4.csv',
            priority: 'low',
            is_read: true,
            read_at: '2026-12-12T15:00:00Z',
            link: '/documents',
            sent_via: ['email'],
            email_sent: true,
            email_sent_at: '2026-12-12T12:00:00Z',
            push_sent: false,
            push_sent_at: null,
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-12T12:00:00Z',
            metadata: { file_id: 'file_005', file_type: 'csv', data_type: 'scope3' }
        },
        {
            id: 'notif_008',
            type: 'approval_required',
            title: 'Bulk Approval Required',
            message: '3 documents are pending approval. Please review them at your earliest convenience.',
            priority: 'medium',
            is_read: false,
            read_at: null,
            link: '/documents/approval',
            sent_via: ['email', 'push'],
            email_sent: true,
            email_sent_at: '2026-12-11T16:00:00Z',
            push_sent: true,
            push_sent_at: '2026-12-11T16:00:00Z',
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-11T16:00:00Z',
            metadata: { pending_count: 3, documents: ['doc_004', 'doc_007', 'doc_009'] }
        },
        {
            id: 'notif_009',
            type: 'validation_needed',
            title: 'Scope 3 Data Validation',
            message: 'Scope 3 supplier data requires validation. 156 records need review.',
            priority: 'high',
            is_read: false,
            read_at: null,
            link: '/validation-queue',
            sent_via: ['email'],
            email_sent: true,
            email_sent_at: '2026-12-10T10:00:00Z',
            push_sent: false,
            push_sent_at: null,
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-10T10:00:00Z',
            metadata: { records: 156, file_id: 'file_006', suppliers: 23 }
        },
        {
            id: 'notif_010',
            type: 'report_ready',
            title: 'CSRD Report Ready',
            message: 'Your CSRD compliance report has been generated and is ready for review.',
            priority: 'medium',
            is_read: true,
            read_at: '2026-12-09T14:30:00Z',
            link: '/reports/csrd-2026',
            sent_via: ['email', 'push'],
            email_sent: true,
            email_sent_at: '2026-12-09T14:30:00Z',
            push_sent: true,
            push_sent_at: '2026-12-09T14:30:00Z',
            is_dismissed: false,
            dismissed_at: null,
            created_at: '2026-12-09T14:30:00Z',
            metadata: { report_id: 'rpt_002', year: 2026, pages: 32 }
        }
    ];

    var emailLogs = [
        { id: 'email_001', recipient: 'john.doe@carbontally.com', subject: 'SECR Report 2026 Ready', type: 'report_ready', status: 'delivered', sent_at: '2026-12-15T14:30:00Z', delivered_at: '2026-12-15T14:30:05Z', opened_at: '2026-12-15T14:35:00Z', error_message: null },
        { id: 'email_002', recipient: 'sarah.johnson@carbontally.com', subject: 'Data Validation Required - Q4 Fleet Fuel', type: 'validation_needed', status: 'delivered', sent_at: '2026-12-15T13:00:00Z', delivered_at: '2026-12-15T13:00:03Z', opened_at: '2026-12-15T13:15:00Z', error_message: null },
        { id: 'email_003', recipient: 'mike.roberts@carbontally.com', subject: 'Document Approval Required', type: 'approval_required', status: 'delivered', sent_at: '2026-12-15T11:30:00Z', delivered_at: '2026-12-15T11:30:04Z', opened_at: null, error_message: null },
        { id: 'email_004', recipient: 'anna.liu@carbontally.com', subject: 'SECR Deadline Approaching', type: 'deadline_approaching', status: 'delivered', sent_at: '2026-12-14T08:00:00Z', delivered_at: '2026-12-14T08:00:06Z', opened_at: '2026-12-14T09:00:00Z', error_message: null },
        { id: 'email_005', recipient: 'tom.chen@carbontally.com', subject: 'New Team Member Added', type: 'team_update', status: 'failed', sent_at: '2026-12-13T09:30:00Z', delivered_at: null, opened_at: null, error_message: 'Recipient mailbox full' },
        { id: 'email_006', recipient: 'emma.martinez@carbontally.com', subject: 'Welcome to CarbonTally', type: 'team_update', status: 'delivered', sent_at: '2026-12-13T09:31:00Z', delivered_at: '2026-12-13T09:31:02Z', opened_at: '2026-12-13T10:00:00Z', error_message: null }
    ];

    var deliveryStatus = [
        { notification_id: 'notif_001', channel: 'email', status: 'delivered', sent_at: '2026-12-15T14:30:00Z', delivered_at: '2026-12-15T14:30:05Z' },
        { notification_id: 'notif_001', channel: 'push', status: 'delivered', sent_at: '2026-12-15T14:30:00Z', delivered_at: '2026-12-15T14:30:02Z' },
        { notification_id: 'notif_002', channel: 'email', status: 'delivered', sent_at: '2026-12-15T13:00:00Z', delivered_at: '2026-12-15T13:00:03Z' },
        { notification_id: 'notif_003', channel: 'email', status: 'pending', sent_at: '2026-12-15T11:30:00Z', delivered_at: null },
        { notification_id: 'notif_003', channel: 'push', status: 'delivered', sent_at: '2026-12-15T11:30:00Z', delivered_at: '2026-12-15T11:30:01Z' },
        { notification_id: 'notif_004', channel: 'email', status: 'delivered', sent_at: '2026-12-14T08:00:00Z', delivered_at: '2026-12-14T08:00:06Z' }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentTab = 'inbox';
    var currentFilters = { type: 'all', priority: 'all', read: 'all' };
    var toastTimeout = null;

    // ============================================
    // DOM REFS (lazy loaded)
    // ============================================

    function getEl(id) { return document.getElementById(id); }
    function getNotifStats() { return getEl('notifStats'); }
    function getNotificationList() { return getEl('notificationList'); }
    function getEmailLogsList() { return getEl('emailLogsList'); }
    function getDeliveryStatusList() { return getEl('deliveryStatusList'); }
    function getNotifCount() { return getEl('notifCount'); }
    function getUnreadBadge() { return getEl('unreadBadge'); }
    function getSearchInput() { return getEl('searchInput'); }

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
    // HELPERS
    // ============================================

    function getPriorityIcon(priority) {
        var icons = { 'high': '🔴', 'medium': '🟡', 'low': '🟢' };
        return icons[priority] || '🟢';
    }

    function getTypeIcon(type) {
        var icons = {
            'report_ready': '📊',
            'validation_needed': '✅',
            'approval_required': '📝',
            'deadline_approaching': '⏰',
            'team_update': '👥',
            'system_update': '⚙️',
            'document_uploaded': '📄'
        };
        return icons[type] || '📌';
    }

    function getTypeLabel(type) {
        var labels = {
            'report_ready': 'Report Ready',
            'validation_needed': 'Validation Needed',
            'approval_required': 'Approval Required',
            'deadline_approaching': 'Deadline Approaching',
            'team_update': 'Team Update',
            'system_update': 'System Update',
            'document_uploaded': 'Document Uploaded'
        };
        return labels[type] || type;
    }

    function formatTime(dateStr) {
        var date = new Date(dateStr);
        var now = new Date();
        var diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
        if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
        if (diff < 172800000) return 'Yesterday';
        return date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
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

        if (tab === 'inbox') renderNotifications();
        else if (tab === 'email-logs') renderEmailLogs();
        else if (tab === 'delivery') renderDeliveryStatus();
    }

    // ============================================
    // STATS
    // ============================================

    function renderStats() {
        var container = getNotifStats();
        if (!container) return;
        
        var total = notifications.length;
        var unread = 0, high = 0, medium = 0, low = 0, emailSent = 0;
        
        for (var i = 0; i < notifications.length; i++) {
            var n = notifications[i];
            if (!n.is_read) unread++;
            if (n.priority === 'high') high++;
            if (n.priority === 'medium') medium++;
            if (n.priority === 'low') low++;
            if (n.email_sent) emailSent++;
        }

        container.innerHTML =
            '<div class="notification-stat"><span class="icon">🔔</span><div class="value">' + total + '</div><div class="label">Total</div></div>' +
            '<div class="notification-stat"><span class="icon">📬</span><div class="value">' + unread + '</div><div class="label">Unread</div></div>' +
            '<div class="notification-stat"><span class="icon">🔴</span><div class="value">' + high + '</div><div class="label">High Priority</div></div>' +
            '<div class="notification-stat"><span class="icon">📧</span><div class="value">' + emailSent + '</div><div class="label">Email Sent</div></div>';

        var badge = getUnreadBadge();
        if (badge) badge.textContent = unread;
    }

    // ============================================
    // NOTIFICATION FUNCTIONS
    // ============================================

    function applyFilters() {
        var typeEl = getEl('typeFilter');
        var priorityEl = getEl('priorityFilter');
        var readEl = getEl('readFilter');
        
        currentFilters.type = typeEl ? typeEl.value : 'all';
        currentFilters.priority = priorityEl ? priorityEl.value : 'all';
        currentFilters.read = readEl ? readEl.value : 'all';
        renderNotifications();
    }

    function clearFilters() {
        var typeEl = getEl('typeFilter');
        var priorityEl = getEl('priorityFilter');
        var readEl = getEl('readFilter');
        
        if (typeEl) typeEl.value = 'all';
        if (priorityEl) priorityEl.value = 'all';
        if (readEl) readEl.value = 'all';
        
        currentFilters.type = 'all';
        currentFilters.priority = 'all';
        currentFilters.read = 'all';
        renderNotifications();
        showToast('🔄 Filters cleared');
    }

    function renderNotifications() {
        var container = getNotificationList();
        var countEl = getNotifCount();
        var searchEl = getSearchInput();
        
        if (!container) return;
        
        var searchTerm = searchEl ? searchEl.value.toLowerCase().trim() : '';
        var filtered = [];
        
        for (var i = 0; i < notifications.length; i++) {
            var n = notifications[i];
            if (currentFilters.type !== 'all' && n.type !== currentFilters.type) continue;
            if (currentFilters.priority !== 'all' && n.priority !== currentFilters.priority) continue;
            if (currentFilters.read === 'unread' && n.is_read) continue;
            if (currentFilters.read === 'read' && !n.is_read) continue;
            if (searchTerm) {
                var match = n.title.toLowerCase().indexOf(searchTerm) !== -1 || n.message.toLowerCase().indexOf(searchTerm) !== -1;
                if (!match) continue;
            }
            filtered.push(n);
        }

        // Sort by created_at (newest first)
        filtered.sort(function(a, b) {
            return new Date(b.created_at) - new Date(a.created_at);
        });

        if (countEl) countEl.textContent = filtered.length + ' notifications';

        if (filtered.length === 0) {
            container.innerHTML =
                '<div class="text-center text-muted" style="padding:60px 20px;">' +
                '<div style="font-size:48px;margin-bottom:16px;">📭</div>' +
                '<div style="font-size:18px;font-weight:600;">No notifications</div>' +
                '<div style="font-size:14px;color:hsl(var(--muted-foreground));margin-top:8px;">You\'re all caught up! Check back later for new notifications.</div>' +
                '</div>';
            return;
        }

        var html = '';
        for (var j = 0; j < filtered.length; j++) {
            var n = filtered[j];
            var isUnread = !n.is_read;
            html +=
                '<div class="notification-item ' + (isUnread ? 'unread' : '') + '" onclick="openDetail(\'' + n.id + '\')">' +
                '<div class="notif-icon">' + getTypeIcon(n.type) + '</div>' +
                '<div class="notif-content">' +
                '<div class="title">' +
                n.title +
                (isUnread ? '<span class="badge badge-primary" style="font-size:9px;">NEW</span>' : '') +
                (n.priority === 'high' ? '<span class="badge badge-destructive" style="font-size:9px;">High Priority</span>' : '') +
                '</div>' +
                '<div class="message">' + n.message + '</div>' +
                '<div class="meta">' +
                '<span>' + getTypeLabel(n.type) + '</span>' +
                '<span>' + getPriorityIcon(n.priority) + ' ' + n.priority.charAt(0).toUpperCase() + n.priority.slice(1) + '</span>' +
                '<span>' + formatTime(n.created_at) + '</span>' +
                (n.sent_via.indexOf('email') !== -1 ? '<span class="badge badge-muted">📧 Email</span>' : '') +
                (n.sent_via.indexOf('push') !== -1 ? '<span class="badge badge-muted">📱 Push</span>' : '') +
                '</div>' +
                '</div>' +
                '<div class="notif-actions">' +
                (isUnread ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();markRead(\'' + n.id + '\')" title="Mark as Read">✅</button>' : '') +
                (!n.is_dismissed ? '<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();dismissNotification(\'' + n.id + '\')" title="Dismiss" style="color:hsl(var(--muted-foreground));">✕</button>' : '') +
                '</div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    // ============================================
    // NOTIFICATION ACTIONS
    // ============================================

    function markRead(id) {
        for (var i = 0; i < notifications.length; i++) {
            if (notifications[i].id === id) {
                notifications[i].is_read = true;
                notifications[i].read_at = new Date().toISOString();
                break;
            }
        }
        renderNotifications();
        renderStats();
        showToast('✅ Marked as read');
    }

    function markAllRead() {
        for (var i = 0; i < notifications.length; i++) {
            notifications[i].is_read = true;
            notifications[i].read_at = new Date().toISOString();
        }
        renderNotifications();
        renderStats();
        showToast('✅ All notifications marked as read');
    }

    function dismissNotification(id) {
        for (var i = 0; i < notifications.length; i++) {
            if (notifications[i].id === id) {
                notifications[i].is_dismissed = true;
                notifications[i].dismissed_at = new Date().toISOString();
                break;
            }
        }
        renderNotifications();
        showToast('🗑️ Notification dismissed');
    }

    function refreshNotifications() {
        showToast('🔄 Refreshing notifications...');
        setTimeout(function() {
            renderNotifications();
            renderStats();
            showToast('✅ Notifications refreshed');
        }, 800);
    }

    // ============================================
    // DETAIL MODAL
    // ============================================

    function openDetail(id) {
        var n = null;
        for (var i = 0; i < notifications.length; i++) {
            if (notifications[i].id === id) { n = notifications[i]; break; }
        }
        if (!n) return;

        if (!n.is_read) {
            n.is_read = true;
            n.read_at = new Date().toISOString();
            renderNotifications();
            renderStats();
        }

        var titleEl = getEl('detailTitle');
        var subtitleEl = getEl('detailSubtitle');
        var bodyEl = getEl('detailBody');
        var footerEl = getEl('detailFooter');
        var modal = getEl('detailModal');
        
        if (titleEl) titleEl.textContent = n.title;
        if (subtitleEl) subtitleEl.textContent = getTypeLabel(n.type) + ' • ' + n.priority.toUpperCase() + ' Priority';

        if (bodyEl) {
            var metaHtml = '';
            for (var key in n.metadata) {
                if (n.metadata.hasOwnProperty(key)) {
                    var val = n.metadata[key];
                    metaHtml += '<div><div style="font-size:10px;color:hsl(var(--muted-foreground));">' + key.replace(/_/g, ' ').toUpperCase() + '</div><div style="font-size:13px;font-weight:500;color:hsl(var(--foreground));">' + (typeof val === 'object' ? JSON.stringify(val) : val) + '</div></div>';
                }
            }

            bodyEl.innerHTML =
                '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">' +
                '<div style="font-size:32px;">' + getTypeIcon(n.type) + '</div>' +
                '<div><div style="font-size:16px;font-weight:600;color:hsl(var(--foreground));">' + n.title + '</div><div style="font-size:14px;color:hsl(var(--muted-foreground));">' + n.message + '</div></div>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
                '<div class="detail-row"><span class="label">Type</span><span class="value">' + getTypeLabel(n.type) + '</span></div>' +
                '<div class="detail-row"><span class="label">Priority</span><span class="value">' + getPriorityIcon(n.priority) + ' ' + n.priority.charAt(0).toUpperCase() + n.priority.slice(1) + '</span></div>' +
                '<div class="detail-row"><span class="label">Status</span><span class="value">' + (n.is_read ? '✅ Read' : '📬 Unread') + '</span></div>' +
                '<div class="detail-row"><span class="label">Dismissed</span><span class="value">' + (n.is_dismissed ? '✅ Yes' : '❌ No') + '</span></div>' +
                '<div class="detail-row"><span class="label">Sent Via</span><span class="value">' + n.sent_via.join(', ') + '</span></div>' +
                '<div class="detail-row"><span class="label">Created</span><span class="value">' + new Date(n.created_at).toLocaleString() + '</span></div>' +
                (n.email_sent ? '<div class="detail-row"><span class="label">Email Sent</span><span class="value">' + new Date(n.email_sent_at).toLocaleString() + '</span></div>' : '') +
                (n.push_sent ? '<div class="detail-row"><span class="label">Push Sent</span><span class="value">' + new Date(n.push_sent_at).toLocaleString() + '</span></div>' : '') +
                (n.read_at ? '<div class="detail-row"><span class="label">Read At</span><span class="value">' + new Date(n.read_at).toLocaleString() + '</span></div>' : '') +
                (n.dismissed_at ? '<div class="detail-row"><span class="label">Dismissed At</span><span class="value">' + new Date(n.dismissed_at).toLocaleString() + '</span></div>' : '') +
                (n.link ? '<div class="detail-row" style="grid-column:1/-1;"><span class="label">Link</span><span class="value"><a href="' + n.link + '" style="color:hsl(var(--primary));text-decoration:none;">' + n.link + '</a></span></div>' : '') +
                '</div>' +
                (Object.keys(n.metadata).length > 0 ? '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:hsl(var(--foreground));margin-bottom:4px;">📊 Metadata</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px;background:hsl(var(--muted));border-radius:var(--radius));">' + metaHtml + '</div></div>' : '');
        }

        if (footerEl) {
            footerEl.innerHTML =
                '<button class="btn btn-ghost btn-sm" onclick="closeDetail()">Close</button>' +
                (!n.is_dismissed ? '<button class="btn btn-outline btn-sm" onclick="dismissNotification(\'' + n.id + '\');closeDetail();">🗑️ Dismiss</button>' : '') +
                (n.link ? '<button class="btn btn-primary btn-sm" onclick="window.location.href=\'' + n.link + '\'">🔗 Go to Link</button>' : '');
        }

        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeDetail() {
        var modal = getEl('detailModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    // ============================================
    // EMAIL LOGS
    // ============================================

    function renderEmailLogs() {
        var container = getEmailLogsList();
        if (!container) return;

        if (emailLogs.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:40px 20px;"><div style="font-size:32px;margin-bottom:8px;">📧</div><div>No email logs found</div><div style="font-size:13px;">Email logs will appear here as emails are sent</div></div>';
            return;
        }

        var html = '';
        for (var i = 0; i < emailLogs.length; i++) {
            var log = emailLogs[i];
            var isDelivered = log.status === 'delivered';
            html +=
                '<div class="email-log-item">' +
                '<div style="font-size:20px;">' + (isDelivered ? '✅' : '❌') + '</div>' +
                '<div class="email-info">' +
                '<div class="recipient">' + log.recipient + '</div>' +
                '<div class="subject">' + log.subject + '</div>' +
                '<div class="meta">' +
                '<span>📂 ' + log.type.replace('_', ' ').toUpperCase() + '</span>' +
                '<span>📅 ' + new Date(log.sent_at).toLocaleString() + '</span>' +
                (log.delivered_at ? '<span>✅ Delivered: ' + new Date(log.delivered_at).toLocaleString() + '</span>' : '') +
                (log.opened_at ? '<span>👁️ Opened: ' + new Date(log.opened_at).toLocaleString() + '</span>' : '') +
                (log.error_message ? '<span class="badge badge-destructive">' + log.error_message + '</span>' : '') +
                '</div>' +
                '</div>' +
                '<div style="flex-shrink:0;"><span class="badge ' + (isDelivered ? 'badge-success' : 'badge-destructive') + '">' + (isDelivered ? '✅ Delivered' : '❌ Failed') + '</span></div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    // ============================================
    // DELIVERY STATUS
    // ============================================

    function renderDeliveryStatus() {
        var container = getDeliveryStatusList();
        if (!container) return;

        if (deliveryStatus.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:40px 20px;"><div style="font-size:32px;margin-bottom:8px;">📊</div><div>No delivery status data</div><div style="font-size:13px;">Delivery status will appear here as notifications are sent</div></div>';
            return;
        }

        var html = '';
        for (var i = 0; i < deliveryStatus.length; i++) {
            var d = deliveryStatus[i];
            var isDelivered = d.status === 'delivered';
            var isPending = d.status === 'pending';
            html +=
                '<div class="email-log-item">' +
                '<div style="font-size:20px;">' + (isDelivered ? '✅' : isPending ? '⏳' : '❌') + '</div>' +
                '<div class="email-info">' +
                '<div class="recipient">' + d.channel.toUpperCase() + ' - Notification ' + d.notification_id + '</div>' +
                '<div class="meta">' +
                '<span>📅 Sent: ' + new Date(d.sent_at).toLocaleString() + '</span>' +
                (d.delivered_at ? '<span>✅ Delivered: ' + new Date(d.delivered_at).toLocaleString() + '</span>' : '') +
                (isPending ? '<span class="badge badge-warning">⏳ Pending</span>' : '') +
                '</div>' +
                '</div>' +
                '<div style="flex-shrink:0;"><span class="badge ' + (isDelivered ? 'badge-success' : isPending ? 'badge-warning' : 'badge-destructive') + '">' + (isDelivered ? '✅ Delivered' : isPending ? '⏳ Pending' : '❌ Failed') + '</span></div>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    // ============================================
    // SETTINGS
    // ============================================

    function saveNotificationSettings() {
        showToast('💾 Notification settings saved successfully!');
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Notification Center Module...');
        
        var container = getNotificationList();
        if (!container) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }

        // Search input listener
        var searchEl = getSearchInput();
        if (searchEl) {
            searchEl.addEventListener('input', function() {
                if (currentTab === 'inbox') renderNotifications();
            });
        }

        // Escape key to close modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var modal = getEl('detailModal');
                if (modal && modal.classList.contains('show')) {
                    closeDetail();
                }
            }
        });

        // Initial render
        renderStats();
        renderNotifications();
        renderEmailLogs();
        renderDeliveryStatus();

        console.log('✅ Notification Center module loaded successfully!');
        console.log('📊 ' + notifications.length + ' notifications loaded');
        console.log('🔍 Ctrl+F to search, Ctrl+R to refresh');
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
    window.applyFilters = applyFilters;
    window.clearFilters = clearFilters;
    window.markRead = markRead;
    window.markAllRead = markAllRead;
    window.dismissNotification = dismissNotification;
    window.refreshNotifications = refreshNotifications;
    window.openDetail = openDetail;
    window.closeDetail = closeDetail;
    window.saveNotificationSettings = saveNotificationSettings;
    window.showToast = showToast;
})(); 