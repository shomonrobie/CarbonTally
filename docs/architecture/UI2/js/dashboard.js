// ============================================
// CARBONTALLY - SHARED JAVASCRIPT
// ============================================

// ============================================
// THEME CONFIGURATION
// ============================================

const themes = [
    { id: 'forest', name: 'Forest Green', desc: 'Professional & sustainable', preview: { bg: '#1a6b43',
            accent: '#e8f0ec', btnBg: '#1a6b43', btnText: '#ffffff' } },
    { id: 'emerald', name: 'Emerald Green', desc: 'Bold & vibrant', preview: { bg: '#10b981', accent: '#d1fae5',
            btnBg: '#10b981', btnText: '#ffffff' } },
    { id: 'teal', name: 'Teal', desc: 'Modern & corporate', preview: { bg: '#196666', accent: '#d4ecec',
            btnBg: '#196666', btnText: '#ffffff' } },
    { id: 'navy', name: 'Navy Blue', desc: 'Trustworthy & financial', preview: { bg: '#1e3a5f', accent: '#dbe6f0',
            btnBg: '#1e3a5f', btnText: '#ffffff' } },
    { id: 'slate', name: 'Slate Grey', desc: 'Clean & data-focused', preview: { bg: '#2d3748', accent: '#e8eaed',
            btnBg: '#2d3748', btnText: '#ffffff' } },
    { id: 'warm-grey', name: 'Warm Grey', desc: 'Warm & approachable', preview: { bg: '#5a4a3a', accent: '#ede8e3',
            btnBg: '#5a4a3a', btnText: '#ffffff' } },
    { id: 'purple', name: 'Purple', desc: 'Creative & premium', preview: { bg: '#5b3a7a', accent: '#ede6f5',
            btnBg: '#5b3a7a', btnText: '#ffffff' } },
    { id: 'rose', name: 'Rose', desc: 'Warm & distinctive', preview: { bg: '#9e3b6d', accent: '#f5e6ee',
            btnBg: '#9e3b6d', btnText: '#ffffff' } },
    { id: 'carbon', name: 'Carbon Black', desc: 'Ultra-minimalist', preview: { bg: '#262626', accent: '#e8e8e8',
            btnBg: '#262626', btnText: '#ffffff' } }
];

let currentTheme = localStorage.getItem('carbontally-theme') || 'forest';

// ============================================
// THEME FUNCTIONS
// ============================================

function setTheme(themeId) {
    if (!themeId) return;
    currentTheme = themeId;
    document.documentElement.setAttribute('data-theme', themeId);
    localStorage.setItem('carbontally-theme', themeId);

    const theme = themes.find(t => t.id === themeId);
    if (theme) {
        const nameEl = document.getElementById('currentThemeName');
        if (nameEl) nameEl.textContent = theme.name;
    }

    document.querySelectorAll('.theme-option').forEach(el => {
        el.classList.toggle('active', el.dataset.theme === themeId);
    });

    showToast(`Theme changed to ${theme?.name || themeId}`);
}

function showToast(message, type = 'success') {
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.querySelector('.icon').textContent = icons[type] || icons.info;
    document.getElementById('toastMessage').textContent = message;
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

function renderThemeGrid() {
    const grid = document.getElementById('themeGrid');
    if (!grid) return;
    grid.innerHTML = themes.map(theme => `
        <div class="theme-option ${currentTheme === theme.id ? 'active' : ''}" 
             data-theme="${theme.id}"
             onclick="setTheme('${theme.id}');">
            <div class="theme-option-preview" style="background:${theme.preview.accent};">
                <div class="preview-dot" style="background:${theme.preview.bg};"></div>
                <div class="preview-bar" style="background:${theme.preview.bg};"></div>
                <button class="preview-btn" style="background:${theme.preview.btnBg};color:${theme.preview.btnText};">Btn</button>
            </div>
            <div class="theme-option-name">${theme.name}</div>
            <div class="theme-option-desc">${theme.desc}</div>
            <div class="check-mark">✓</div>
        </div>
    `).join('');
}

function openThemeModal() {
    const modal = document.getElementById('themeModal');
    if (!modal) return;
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    renderThemeGrid();
}

function closeThemeModal() {
    const modal = document.getElementById('themeModal');
    if (!modal) return;
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

// ============================================
// SESSION MANAGEMENT
// ============================================

function getUserSession() {
    try {
        const session = localStorage.getItem('carbontally_session');
        return session ? JSON.parse(session) : null;
    } catch {
        return null;
    }
}

function updateUserUI() {
    const session = getUserSession();
    if (session) {
        const avatarEl = document.getElementById('userAvatar');
        const nameEl = document.getElementById('userName');
        const roleEl = document.getElementById('userRole');
        const welcomeEl = document.getElementById('welcomeName');
        if (avatarEl) avatarEl.textContent = session.avatar || 'U';
        if (nameEl) nameEl.textContent = session.name || 'User';
        if (roleEl) roleEl.textContent = session.role || 'User';
        if (welcomeEl) welcomeEl.textContent = session.name?.split(' ')[0] || 'User';
    }
}

function goToDashboard() {
    const session = getUserSession();
    if (session && session.dashboard) {
        window.location.href = session.dashboard;
    } else {
        window.location.href = '../dashboard_analyst.html';
    }
}

function logout() {
    localStorage.removeItem('carbontally_session');
    window.location.href = 'login.html';
}

// ============================================
// SIDEBAR MOBILE TOGGLE
// ============================================

function initMobileMenu() {
    const menuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    if (!menuBtn || !sidebar) return;

    menuBtn.addEventListener('click', function() {
        sidebar.classList.toggle('open');
    });

    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 992) {
            if (!sidebar.contains(e.target) && !menuBtn.contains(e.target) && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        }
    });
}

// ============================================
// MODULE SEARCH
// ============================================

function initModuleSearch() {
    const searchInput = document.getElementById('moduleSearch');
    if (!searchInput) return;
    searchInput.addEventListener('input', function() {
        // Override in specific modules
        console.log('Search:', this.value);
    });
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Apply theme
    setTheme(currentTheme);
    renderThemeGrid();
    updateUserUI();
    initMobileMenu();
    initModuleSearch();

    // Theme event listeners
    const themeToggle = document.getElementById('themeToggle');
    const themeModalClose = document.getElementById('themeModalClose');
    const closeThemeBtn = document.getElementById('closeThemeBtn');
    const resetThemeBtn = document.getElementById('resetThemeBtn');
    const themeModal = document.getElementById('themeModal');

    if (themeToggle) themeToggle.addEventListener('click', openThemeModal);
    if (themeModalClose) themeModalClose.addEventListener('click', closeThemeModal);
    if (closeThemeBtn) closeThemeBtn.addEventListener('click', closeThemeModal);
    if (themeModal) {
        themeModal.addEventListener('click', function(e) {
            if (e.target === this) closeThemeModal();
        });
    }
    if (resetThemeBtn) {
        resetThemeBtn.addEventListener('click', function() {
            setTheme('forest');
            renderThemeGrid();
            showToast('Reset to Forest Green theme');
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && themeModal?.classList.contains('show')) {
            closeThemeModal();
        }

        if (themeModal?.classList.contains('show')) {
            const themeIds = themes.map(t => t.id);
            const currentIndex = themeIds.indexOf(currentTheme);
            let newIndex = currentIndex;

            if (e.key === 'ArrowRight') {
                newIndex = (currentIndex + 1) % themeIds.length;
                e.preventDefault();
            } else if (e.key === 'ArrowLeft') {
                newIndex = (currentIndex - 1 + themeIds.length) % themeIds.length;
                e.preventDefault();
            }

            if (newIndex !== currentIndex) {
                setTheme(themeIds[newIndex]);
                renderThemeGrid();
            }
        }

        // Ctrl+Backspace to go to dashboard
        if (e.key === 'Backspace' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            goToDashboard();
        }
    });

    // Log initialization
    const isModule = document.querySelector('.module-container') !== null;
    const isDashboard = document.querySelector('.sidebar') !== null;

    if (isModule) {
        console.log('📄 Module page loaded (content-only)');
        console.log('← Click "Dashboard" or use Ctrl+Backspace to return');
    }
    if (isDashboard) {
        console.log('📊 Dashboard page loaded (full navigation)');
    }
    console.log('🎨 Theme system initialized');
    console.log('⌨️  Ctrl+Backspace to return to dashboard');
});

// ============================================
// MODULE NAVIGATION
// ============================================

function goToDashboard() {
    const session = getUserSession();
    if (session && session.dashboard) {
        // Check if we're in a subdirectory
        const path = window.location.pathname;
        if (path.includes('/modules/')) {
            window.location.href = '../' + session.dashboard;
        } else {
            window.location.href = session.dashboard;
        }
    } else {
        // Default to analyst dashboard
        const path = window.location.pathname;
        if (path.includes('/modules/')) {
            window.location.href = '../dashboard_analyst.html';
        } else {
            window.location.href = 'dashboard_analyst.html';
        }
    }
}