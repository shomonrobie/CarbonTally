
    // Messaging & Chat Module - SPA Compatible
(function() {

    console.log('💬 Messaging & Chat JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var currentUser = { id: 'user1', name: 'John Doe', avatar: 'JD', status: 'online' };

    var users = [
        { id: 'user2', name: 'Sarah Johnson', avatar: 'SJ', status: 'online', role: 'Sustainability Officer' },
        { id: 'user3', name: 'Mike Chen', avatar: 'MC', status: 'online', role: 'Data Analyst' },
        { id: 'user4', name: 'Emma Wilson', avatar: 'EW', status: 'away', role: 'Compliance Manager' },
        { id: 'user5', name: 'Alex Rivera', avatar: 'AR', status: 'offline', role: 'Analyst' },
        { id: 'user6', name: 'Tom Harris', avatar: 'TH', status: 'online', role: 'Developer' },
        { id: 'user7', name: 'Lisa Park', avatar: 'LP', status: 'away', role: 'Product Manager' },
    ];

    var conversations = [
        { id: 'c1', name: 'Sarah Johnson', participants: ['user1', 'user2'], lastMessage: 'The SECR report is ready for review', time: '2 min ago', unread: 2 },
        { id: 'c2', name: 'Compliance Team', participants: ['user1', 'user2', 'user3', 'user4'], lastMessage: 'CSRD data has been validated', time: '1 hour ago', unread: 0, isGroup: true },
        { id: 'c3', name: 'Mike Chen', participants: ['user1', 'user3'], lastMessage: 'Can you check the Q4 emissions data?', time: '3 hours ago', unread: 1 },
        { id: 'c4', name: 'Emma Wilson', participants: ['user1', 'user4'], lastMessage: 'ISSB disclosure needs your input', time: '5 hours ago', unread: 0 },
        { id: 'c5', name: 'Development Team', participants: ['user1', 'user5', 'user6'], lastMessage: 'API integration is complete', time: '1 day ago', unread: 0, isGroup: true },
        { id: 'c6', name: 'Alex Rivera', participants: ['user1', 'user5'], lastMessage: 'Thanks for the clarification!', time: '2 days ago', unread: 0 },
        { id: 'c7', name: 'Lisa Park', participants: ['user1', 'user7'], lastMessage: 'Product roadmap updated', time: '3 days ago', unread: 0 },
    ];

    var messages = {
        'c1': [
            { id: 'm1', senderId: 'user2', text: 'Hi John, the SECR report is ready for review.', time: '2 min ago', type: 'received' },
            { id: 'm2', senderId: 'user2', text: 'Can you take a look at the Scope 3 calculations?', time: '1 min ago', type: 'received' },
        ],
        'c2': [
            { id: 'm3', senderId: 'user2', text: 'CSRD data has been validated for Q4 2026.', time: '1 hour ago', type: 'received' },
            { id: 'm4', senderId: 'user3', text: 'Great! I\'ll update the dashboard.', time: '59 min ago', type: 'received' },
            { id: 'm5', senderId: 'user1', text: 'Thanks team, excellent work!', time: '58 min ago', type: 'sent' },
            { id: 'm6', senderId: 'user4', text: 'I\'ll prepare the final documentation.', time: '55 min ago', type: 'received' },
        ],
        'c3': [
            { id: 'm7', senderId: 'user3', text: 'Can you check the Q4 emissions data?', time: '3 hours ago', type: 'received' },
            { id: 'm8', senderId: 'user1', text: 'Sure, I\'ll review it now.', time: '2 hours ago', type: 'sent' },
            { id: 'm9', senderId: 'user3', text: 'I\'ve uploaded the new fuel consumption figures.', time: '1 hour ago', type: 'received' },
        ],
        'c4': [
            { id: 'm10', senderId: 'user4', text: 'ISSB disclosure needs your input on S1 disclosures.', time: '5 hours ago', type: 'received' },
            { id: 'm11', senderId: 'user1', text: 'I\'ll look at it first thing tomorrow.', time: '4 hours ago', type: 'sent' },
        ],
        'c5': [
            { id: 'm12', senderId: 'user6', text: 'API integration is complete and deployed to staging.', time: '1 day ago', type: 'received' },
            { id: 'm13', senderId: 'user1', text: 'Great work! When can we deploy to production?', time: '23 hours ago', type: 'sent' },
            { id: 'm14', senderId: 'user6', text: 'After testing, probably tomorrow.', time: '22 hours ago', type: 'received' },
        ],
        'c6': [
            { id: 'm15', senderId: 'user5', text: 'Thanks for the clarification on the extraction logic!', time: '2 days ago', type: 'received' },
            { id: 'm16', senderId: 'user1', text: 'You\'re welcome! Let me know if you need more help.', time: '2 days ago', type: 'sent' },
        ],
        'c7': [
            { id: 'm17', senderId: 'user7', text: 'Product roadmap updated for next quarter.', time: '3 days ago', type: 'received' },
            { id: 'm18', senderId: 'user1', text: 'Looks good! I\'ll share with the team.', time: '3 days ago', type: 'sent' },
        ],
    };

    // ============================================
    // STATE
    // ============================================

    var activeConversationId = 'c1';
    var toastTimeout = null;
    var typingTimeout = null;

    // ============================================
    // DOM REFS (lazy loaded)
    // ============================================

    function getEl(id) {
        return document.getElementById(id);
    }

    function getConversationList() { return getEl('conversationList'); }
    function getMessagesContainer() { return getEl('messagesContainer'); }
    function getChatHeader() { return getEl('chatHeader'); }
    function getMessageInput() { return getEl('messageInput'); }
    function getSendBtn() { return getEl('sendBtn'); }
    function getConvoCount() { return getEl('convoCount'); }

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

    function getUser(id) {
        if (id === 'user1') return currentUser;
        for (var i = 0; i < users.length; i++) {
            if (users[i].id === id) return users[i];
        }
        return { name: 'Unknown', avatar: '??', status: 'offline' };
    }

    function getConversationName(conv) {
        if (conv.isGroup) return conv.name;
        for (var i = 0; i < conv.participants.length; i++) {
            if (conv.participants[i] !== 'user1') {
                var user = getUser(conv.participants[i]);
                return user.name;
            }
        }
        return conv.name;
    }

    function getOtherParticipant(conv) {
        for (var i = 0; i < conv.participants.length; i++) {
            if (conv.participants[i] !== 'user1') {
                return conv.participants[i];
            }
        }
        return null;
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderConversations() {
        var container = getConversationList();
        var countEl = getConvoCount();
        if (!container) return;

        var html = '';
        for (var i = 0; i < conversations.length; i++) {
            var conv = conversations[i];
            var name = getConversationName(conv);
            var otherId = getOtherParticipant(conv);
            var user = getUser(otherId);
            var isActive = activeConversationId === conv.id;
            var statusDot = user.status === 'online' ? '🟢' : user.status === 'away' ? '🟡' : '⚪';
            var avatar = conv.isGroup ? '👥' : (user.avatar || '??');

            html += '<div class="chat-conversation-item ' + (isActive ? 'active' : '') + '" data-id="' + conv.id + '">' +
                '<div class="avatar avatar-sm">' + avatar + '</div>' +
                '<div class="chat-info">' +
                '<div class="name">' + name + ' <span class="online-indicator ' + user.status + '"></span></div>' +
                '<div class="preview">' + conv.lastMessage + '</div>' +
                '<div class="time">' + conv.time + '</div>' +
                '</div>' +
                (conv.unread > 0 ? '<span class="badge badge-destructive">' + conv.unread + '</span>' : '') +
                '</div>';
        }

        container.innerHTML = html;
        if (countEl) countEl.textContent = conversations.length;

        // Click handlers
        var items = document.querySelectorAll('.chat-conversation-item');
        for (var j = 0; j < items.length; j++) {
            items[j].addEventListener('click', function() {
                var id = this.getAttribute('data-id');
                switchConversation(id);
            });
        }
    }

    function renderMessages(conversationId) {
        var container = getMessagesContainer();
        var header = getChatHeader();
        if (!container || !header) return;

        var conv = null;
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === conversationId) {
                conv = conversations[i];
                break;
            }
        }
        if (!conv) return;

        var msgs = messages[conversationId] || [];
        var name = getConversationName(conv);
        var otherId = getOtherParticipant(conv);
        var user = getUser(otherId);
        var statusText = user.status === 'online' ? 'Online' : user.status === 'away' ? 'Away' : 'Offline';

        // Header
        var avatar = conv.isGroup ? '👥' : (user.avatar || '??');
        header.innerHTML =
            '<div class="avatar avatar-sm">' + avatar + '</div>' +
            '<div style="flex:1;">' +
            '<div style="font-weight:600;font-size:14px;">' + name + '</div>' +
            '<div class="presence-status">' +
            '<span class="online-indicator ' + user.status + '"></span>' +
            '<span>' + (conv.isGroup ? 'Group conversation' : statusText) + '</span>' +
            (conv.isGroup ? '<span style="margin-left:8px;font-size:11px;color:hsl(var(--muted-foreground));">' + conv.participants.length + ' members</span>' : '') +
            '</div>' +
            '</div>' +
            '<button class="btn btn-sm btn-ghost" onclick="showToast(\'📞 Calling...\')">📞</button>' +
            '<button class="btn btn-sm btn-ghost" onclick="showToast(\'📹 Video call...\')">📹</button>';

        // Messages
        if (msgs.length === 0) {
            container.innerHTML =
                '<div class="chat-empty">' +
                '<span style="font-size:48px;opacity:0.3;">💬</span>' +
                '<p>No messages yet. Start the conversation!</p>' +
                '</div>';
            return;
        }

        var html = '';
        for (var j = 0; j < msgs.length; j++) {
            var msg = msgs[j];
            var isSent = msg.type === 'sent' || msg.senderId === 'user1';
            var sender = getUser(msg.senderId);
            html += '<div class="chat-message ' + (isSent ? 'sent' : 'received') + '">' +
                (!isSent ? '<div class="msg-sender">' + sender.name + '</div>' : '') +
                msg.text +
                '<span class="msg-time">' + msg.time + '</span>' +
                '</div>';
        }

        container.innerHTML = html;
        container.scrollTop = container.scrollHeight;
    }

    function switchConversation(id) {
        activeConversationId = id;
        // Mark as read
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === id) {
                conversations[i].unread = 0;
                break;
            }
        }
        renderConversations();
        renderMessages(id);
    }

    // ============================================
    // SEND MESSAGE
    // ============================================

    function sendMessage() {
        var input = getMessageInput();
        if (!input) return;
        var text = input.value.trim();
        if (!text) return;

        var conv = null;
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === activeConversationId) {
                conv = conversations[i];
                break;
            }
        }
        if (!conv) return;

        // Add message
        if (!messages[activeConversationId]) messages[activeConversationId] = [];
        messages[activeConversationId].push({
            id: 'm' + Date.now(),
            senderId: 'user1',
            text: text,
            time: 'Just now',
            type: 'sent'
        });

        conv.lastMessage = text;
        conv.time = 'Just now';
        input.value = '';

        renderMessages(activeConversationId);
        renderConversations();

        // Simulate typing indicator and reply
        showTypingIndicator();

        // Auto-reply after delay
        if (typingTimeout) clearTimeout(typingTimeout);
        typingTimeout = setTimeout(function() {
            hideTypingIndicator();
            var replies = [
                'Thanks for the update!',
                'I\'ll review that and get back to you.',
                'Great, I\'ll handle that.',
                'Let me check the data.',
                'Sounds good!',
                'I\'ll follow up on this.',
                'Thanks, John!',
                'I\'ll prepare the documentation.',
                'Got it!',
                'Perfect, I\'ll take a look.'
            ];
            var reply = replies[Math.floor(Math.random() * replies.length)];
            var otherId = getOtherParticipant(conv);
            var otherUser = getUser(otherId);

            if (!messages[activeConversationId]) messages[activeConversationId] = [];
            messages[activeConversationId].push({
                id: 'm' + Date.now(),
                senderId: otherId || 'user2',
                text: reply,
                time: 'Just now',
                type: 'received'
            });
            conv.lastMessage = reply;
            conv.time = 'Just now';

            renderMessages(activeConversationId);
            renderConversations();
            typingTimeout = null;
        }, 1500 + Math.random() * 1000);
    }

    // ============================================
    // TYPING INDICATOR
    // ============================================

    function showTypingIndicator() {
        var container = getMessagesContainer();
        if (!container) return;
        
        var existing = document.getElementById('typingIndicator');
        if (existing) return;

        var otherId = null;
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === activeConversationId) {
                otherId = getOtherParticipant(conversations[i]);
                break;
            }
        }
        var user = getUser(otherId);

        var indicator = document.createElement('div');
        indicator.className = 'chat-message received';
        indicator.id = 'typingIndicator';
        indicator.innerHTML =
            '<div class="msg-sender">' + (user.name || 'Someone') + ' is typing</div>' +
            '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        container.appendChild(indicator);
        container.scrollTop = container.scrollHeight;
    }

    function hideTypingIndicator() {
        var el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    // ============================================
    // UI ACTIONS
    // ============================================

    function newConversation() {
        showToast('📝 New conversation dialog opening...');
    }

    function showTeam() {
        var teamNames = '';
        for (var i = 0; i < users.length; i++) {
            teamNames += users[i].name + ' (' + users[i].role + ')\n';
        }
        showToast('👥 Team members:\n' + teamNames);
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        // console.log('🚀 Initializing Messaging & Chat Module...');
        
        var container = getMessagesContainer();
        if (!container) {
            // console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }

        // Set up event listeners
        var sendBtn = getSendBtn();
        var input = getMessageInput();
        
        if (sendBtn) {
            sendBtn.addEventListener('click', sendMessage);
            console.log('  Send button listener attached');
        }
        
        if (input) {
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            console.log('  Input listener attached');
        }

        // Initial render
        renderConversations();
        renderMessages(activeConversationId);

        // Simulate typing for demo
        setInterval(function() {
            if (Math.random() > 0.7 && activeConversationId) {
                var conv = null;
                for (var i = 0; i < conversations.length; i++) {
                    if (conversations[i].id === activeConversationId) {
                        conv = conversations[i];
                        break;
                    }
                }
                if (conv && !document.getElementById('typingIndicator')) {
                    showTypingIndicator();
                    if (typingTimeout) clearTimeout(typingTimeout);
                    typingTimeout = setTimeout(function() {
                        hideTypingIndicator();
                        typingTimeout = null;
                    }, 2000 + Math.random() * 1000);
                }
            }
        }, 10000);

        console.log('✅ Messaging & Chat module loaded successfully!');
        console.log('📱 ' + conversations.length + ' conversations loaded');
        console.log('⌨️  Type a message and press Enter to send');
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

    window.switchConversation = switchConversation;
    window.sendMessage = sendMessage;
    window.showTypingIndicator = showTypingIndicator;
    window.hideTypingIndicator = hideTypingIndicator;
    window.newConversation = newConversation;
    window.showTeam = showTeam;
    window.showToast = showToast;
})(); 