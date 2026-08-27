// Upload Data Module - SPA Compatible
(function(){
    console.log('📤 Upload Data JS loaded');

    // ============================================
    // MOCK DATA
    // ============================================

    var mockFiles = [
        { name: 'Utility_Bill_London_Dec2026.pdf', type: 'utility', size: 2450000, status: 'uploaded', records: 12, date: '2026-12-15' },
        { name: 'Fleet_Fuel_Q4_2026.csv', type: 'fuel', size: 1800000, status: 'processing', records: 245, date: '2026-12-14' },
        { name: 'Supplier_Invoice_IT_Equipment.pdf', type: 'scope3', size: 3100000, status: 'review', records: 8, date: '2026-12-13' },
        { name: 'Electricity_Bill_Manchester.xlsx', type: 'utility', size: 1200000, status: 'uploaded', records: 18, date: '2026-12-12' },
        { name: 'Gas_Bill_Birmingham_Q4.pdf', type: 'utility', size: 890000, status: 'processing', records: 6, date: '2026-12-11' },
        { name: 'Scope3_Supplier_Report.csv', type: 'scope3', size: 3200000, status: 'review', records: 156, date: '2026-12-10' },
        { name: 'Fleet_Maintenance_Records.xlsx', type: 'fuel', size: 560000, status: 'approved', records: 34, date: '2026-12-09' },
        { name: 'Renewable_Energy_Certificates.pdf', type: 'document', size: 450000, status: 'approved', records: 0, date: '2026-12-08' },
        { name: 'Water_Bill_Manchester_Q4.pdf', type: 'utility', size: 750000, status: 'uploaded', records: 4, date: '2026-12-07' },
        { name: 'Business_Travel_Expenses_Q4.csv', type: 'scope3', size: 2100000, status: 'processing', records: 89, date: '2026-12-06' }
    ];

    // ============================================
    // STATE
    // ============================================

    var currentMode = 'single';
    var uploadedFiles = [];
    var batchFiles = [];
    var uploadHistory = [];
    var isUploading = false;
    var uploadIdCounter = 0;
    var toastTimeout = null;
    var currentPage = 1;
    var perPage = 5;

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

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    function getFileIcon(filename) {
        var ext = filename.split('.').pop().toLowerCase();
        var icons = {
            'csv': '📊', 'xlsx': '📊', 'xls': '📊',
            'pdf': '📄', 'jpg': '🖼️', 'jpeg': '🖼️',
            'png': '🖼️', 'doc': '📝', 'docx': '📝'
        };
        return icons[ext] || '📁';
    }

    function getStatusBadge(status) {
        var badges = {
            'uploaded': '<span class="badge badge-muted">📤 Uploaded</span>',
            'processing': '<span class="badge badge-warning">⏳ Processing</span>',
            'review': '<span class="badge badge-primary">📝 Review</span>',
            'approved': '<span class="badge badge-success">✅ Approved</span>',
            'rejected': '<span class="badge badge-destructive">❌ Rejected</span>',
            'error': '<span class="badge badge-destructive">❌ Error</span>',
            'complete': '<span class="badge badge-success">✅ Complete</span>'
        };
        return badges[status] || badges.uploaded;
    }

    function getStatusProgress(status) {
        var progress = {
            'uploaded': 0,
            'processing': 45,
            'review': 70,
            'approved': 100,
            'complete': 100,
            'rejected': 100,
            'error': 100
        };
        return progress[status] || 0;
    }

    // ============================================
    // MODE SWITCHER
    // ============================================

    function switchMode(mode) {
        currentMode = mode;
        var btns = document.querySelectorAll('.upload-mode-btn');
        for (var i = 0; i < btns.length; i++) {
            btns[i].classList.toggle('active', btns[i].getAttribute('data-mode') === mode);
        }
        var singleArea = getEl('singleUploadArea');
        var batchArea = getEl('batchUploadArea');
        if (singleArea) singleArea.style.display = mode === 'single' ? 'block' : 'none';
        if (batchArea) batchArea.style.display = mode === 'batch' ? 'block' : 'none';
        updateStats();
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderFileList(files, container, isBatch) {
        if (!container) return;
        
        if (files.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding:20px;"><div style="font-size:32px;margin-bottom:8px;">📭</div><div>No files uploaded yet</div><div style="font-size:13px;">Drop files here or click to browse</div></div>';
            return;
        }

        var html = '';
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var statusBadge = getStatusBadge(file.status);
            var progress = getStatusProgress(file.status);
            var progressClass = file.status === 'error' ? 'error' : (file.status === 'approved' || file.status === 'complete') ? 'success' : '';
            
            html += '<div class="file-item" style="margin-bottom:8px;animation:slideIn 0.3s ease;">' +
                '<div class="file-icon">' + getFileIcon(file.name) + '</div>' +
                '<div class="file-info"><div class="name">' + file.name + '</div><div class="meta">' + formatFileSize(file.size) + ' • ' + (file.records || 0) + ' records • ' + (file.date || 'Today') + '</div></div>' +
                '<div class="file-status">' + statusBadge + '</div>' +
                (file.status !== 'uploaded' ? '<div class="file-progress"><div class="progress-bar"><div class="fill ' + progressClass + '" style="width:' + progress + '%;"></div></div></div>' : '') +
                '<button class="btn btn-ghost btn-sm" onclick="removeFile(' + i + ', ' + (isBatch ? 'true' : 'false') + ')" style="color:hsl(var(--destructive));">✕</button>' +
                '</div>';
        }
        container.innerHTML = html;
    }

    function renderHistory() {
        var tbody = getEl('historyTableBody');
        var paginationEl = getEl('historyPagination');
        if (!tbody) return;
        
        if (uploadHistory.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:32px;"><div style="font-size:32px;margin-bottom:8px;">📭</div><div>No upload history yet</div><div style="font-size:13px;">Start uploading files to see them here</div></td></tr>';
            renderHistoryPagination(0);
            return;
        }

        var start = (currentPage - 1) * perPage;
        var pageItems = uploadHistory.slice(start, start + perPage);

        var html = '';
        for (var i = 0; i < pageItems.length; i++) {
            var item = pageItems[i];
            var progress = getStatusProgress(item.status);
            var progressClass = item.status === 'error' ? 'error' : (item.status === 'approved' || item.status === 'complete') ? 'success' : '';
            
            html += '<tr>' +
                '<td><strong>' + item.name + '</strong></td>' +
                '<td><span class="badge badge-muted">' + item.type + '</span></td>' +
                '<td>' + formatFileSize(item.size) + '</td>' +
                '<td>' + getStatusBadge(item.status) + '</td>' +
                '<td><div class="progress-bar" style="width:100px;"><div class="fill ' + progressClass + '" style="width:' + progress + '%;"></div></div></td>' +
                '<td style="font-size:12px;color:hsl(var(--muted-foreground));">' + (item.date || 'Today') + '</td>' +
                '<td><button class="btn btn-ghost btn-sm" onclick="viewHistoryItem(\'' + item.id + '\')">👁️</button><button class="btn btn-ghost btn-sm" onclick="downloadHistoryItem(\'' + item.id + '\')">⬇️</button><button class="btn btn-ghost btn-sm" onclick="removeHistoryItem(\'' + item.id + '\')" style="color:hsl(var(--destructive));">✕</button></td>' +
                '</tr>';
        }
        tbody.innerHTML = html;
        renderHistoryPagination(uploadHistory.length);
    }

    function renderHistoryPagination(total) {
        var container = getEl('historyPagination');
        if (!container) return;
        
        var totalPages = Math.ceil(total / perPage);
        if (totalPages <= 1) {
            container.innerHTML = '<div class="page-info">Showing ' + total + ' items</div><div class="page-buttons"></div>';
            return;
        }
        
        var startItem = (currentPage - 1) * perPage + 1;
        var endItem = Math.min(currentPage * perPage, total);
        
        var btns = '<button class="page-btn" onclick="goToHistoryPage(' + (currentPage - 1) + ')" ' + (currentPage <= 1 ? 'disabled' : '') + '>‹</button>';
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            btns += '<button class="page-btn" onclick="goToHistoryPage(1)">1</button>';
            if (startPage > 2) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
        }
        for (var i = startPage; i <= endPage; i++) {
            btns += '<button class="page-btn ' + (i === currentPage ? 'active' : '') + '" onclick="goToHistoryPage(' + i + ')">' + i + '</button>';
        }
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) btns += '<span style="padding:0 4px;color:hsl(var(--muted-foreground));">…</span>';
            btns += '<button class="page-btn" onclick="goToHistoryPage(' + totalPages + ')">' + totalPages + '</button>';
        }
        btns += '<button class="page-btn" onclick="goToHistoryPage(' + (currentPage + 1) + ')" ' + (currentPage >= totalPages ? 'disabled' : '') + '>›</button>';
        
        container.innerHTML = '<div class="page-info">Showing ' + startItem + '-' + endItem + ' of ' + total + ' items</div><div class="page-buttons">' + btns + '</div>';
    }

    function goToHistoryPage(page) {
        var totalPages = Math.ceil(uploadHistory.length / perPage);
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderHistory();
    }

    function updateStats() {
        var files = currentMode === 'single' ? uploadedFiles : batchFiles;
        var total = files.length;
        var totalSize = 0, processed = 0, pending = 0;
        
        for (var i = 0; i < files.length; i++) {
            totalSize += files[i].size;
            if (files[i].status === 'approved' || files[i].status === 'complete' || files[i].status === 'rejected') {
                processed++;
            }
            if (files[i].status === 'uploaded' || files[i].status === 'processing') {
                pending++;
            }
        }

        var totalEl = getEl('totalFiles');
        var totalSizeEl = getEl('totalSize');
        var processedEl = getEl('processedFiles');
        var pendingEl = getEl('pendingFiles');
        
        if (totalEl) totalEl.textContent = total;
        if (totalSizeEl) totalSizeEl.textContent = formatFileSize(totalSize);
        if (processedEl) processedEl.textContent = processed;
        if (pendingEl) pendingEl.textContent = pending;
    }

    // ============================================
    // FILE MANAGEMENT
    // ============================================

    function addFile(file, isBatch) {
        var fileObj = {
            id: 'file_' + (++uploadIdCounter),
            name: file.name,
            size: file.size,
            type: getEl('dataTypeSelect') ? getEl('dataTypeSelect').value : 'fuel',
            status: 'uploaded',
            records: Math.floor(Math.random() * 200) + 5,
            date: new Date().toISOString().split('T')[0],
            progress: 0
        };

        if (isBatch) {
            batchFiles.push(fileObj);
            renderFileList(batchFiles, getEl('batchFileListContainer'), true);
        } else {
            uploadedFiles.push(fileObj);
            renderFileList(uploadedFiles, getEl('fileListContainer'), false);
        }
        updateStats();
        showToast('📤 ' + file.name + ' added to upload queue');
    }

    function removeFile(index, isBatch) {
        var removed;
        if (isBatch) {
            removed = batchFiles.splice(index, 1)[0];
            renderFileList(batchFiles, getEl('batchFileListContainer'), true);
        } else {
            removed = uploadedFiles.splice(index, 1)[0];
            renderFileList(uploadedFiles, getEl('fileListContainer'), false);
        }
        updateStats();
        showToast('🗑️ Removed ' + removed.name);
    }

    function clearAllFiles() {
        if (currentMode === 'single') {
            uploadedFiles = [];
            renderFileList(uploadedFiles, getEl('fileListContainer'), false);
        } else {
            batchFiles = [];
            renderFileList(batchFiles, getEl('batchFileListContainer'), true);
        }
        updateStats();
        showToast('🗑️ All files cleared');
    }

    function loadMockData() {
        var files = [];
        for (var i = 0; i < mockFiles.length; i++) {
            var f = mockFiles[i];
            files.push({
                id: 'mock_' + (++uploadIdCounter),
                name: f.name,
                size: f.size,
                type: f.type,
                status: f.status,
                records: f.records,
                date: f.date || new Date().toISOString().split('T')[0],
                progress: 0
            });
        }

        if (currentMode === 'single') {
            uploadedFiles = files.slice(0, 3);
            renderFileList(uploadedFiles, getEl('fileListContainer'), false);
        } else {
            batchFiles = files;
            renderFileList(batchFiles, getEl('batchFileListContainer'), true);
        }

        for (var j = 0; j < files.length; j++) {
            uploadHistory.push({ ...files[j] });
        }
        renderHistory();
        updateStats();
        showToast('🧪 Loaded ' + files.length + ' mock files');
    }

    // ============================================
    // UPLOAD SIMULATION
    // ============================================

    function startUpload() {
        var files = currentMode === 'single' ? uploadedFiles : batchFiles;
        if (files.length === 0) {
            showToast('⚠️ No files to upload. Add some files first.', 'warning');
            return;
        }

        if (isUploading) {
            showToast('⏳ Upload already in progress', 'warning');
            return;
        }

        isUploading = true;
        var uploadBtn = getEl('uploadBtn');
        if (uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="spinner"></span> Uploading...';
        }
        showToast('⏳ Starting upload...', 'info');

        var completed = 0;
        var total = files.length;

        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var steps = [
                { status: 'processing', progress: 30, delay: 1000 },
                { status: 'processing', progress: 60, delay: 2000 },
                { status: 'review', progress: 80, delay: 3000 },
                { status: Math.random() > 0.2 ? 'approved' : 'rejected', progress: 100, delay: 4000 }
            ];

            for (var s = 0; s < steps.length; s++) {
                (function(file, step, idx) {
                    setTimeout(function() {
                        file.status = step.status;
                        file.progress = step.progress;

                        if (currentMode === 'single') {
                            renderFileList(uploadedFiles, getEl('fileListContainer'), false);
                        } else {
                            renderFileList(batchFiles, getEl('batchFileListContainer'), true);
                        }
                        updateStats();

                        if (step.status === 'approved' || step.status === 'rejected') {
                            var historyItem = {
                                id: 'history_' + Date.now() + '_' + idx,
                                name: file.name,
                                size: file.size,
                                type: file.type,
                                status: file.status,
                                records: file.records,
                                date: new Date().toISOString().split('T')[0],
                                progress: file.progress
                            };
                            uploadHistory.push(historyItem);
                            renderHistory();

                            completed++;
                            if (completed === total) {
                                isUploading = false;
                                if (uploadBtn) {
                                    uploadBtn.disabled = false;
                                    uploadBtn.innerHTML = '⬆️ Upload Files';
                                }
                                var successCount = 0;
                                for (var j = 0; j < files.length; j++) {
                                    if (files[j].status === 'approved') successCount++;
                                }
                                showToast('✅ Upload complete! ' + successCount + '/' + total + ' files approved');
                            }
                        }
                    }, step.delay);
                })(file, steps[s], i);
            }
        }
    }

    // ============================================
    // HISTORY ACTIONS
    // ============================================

    function viewHistoryItem(id) {
        var item = null;
        for (var i = 0; i < uploadHistory.length; i++) {
            if (uploadHistory[i].id === id) { item = uploadHistory[i]; break; }
        }
        if (item) {
            showToast('📄 Viewing: ' + item.name + ' (' + item.status + ')');
        }
    }

    function downloadHistoryItem(id) {
        var item = null;
        for (var i = 0; i < uploadHistory.length; i++) {
            if (uploadHistory[i].id === id) { item = uploadHistory[i]; break; }
        }
        if (item) {
            showToast('⬇️ Downloading: ' + item.name);
            setTimeout(function() {
                showToast('✅ ' + item.name + ' downloaded successfully!');
            }, 1500);
        }
    }

    function removeHistoryItem(id) {
        var newHistory = [];
        for (var i = 0; i < uploadHistory.length; i++) {
            if (uploadHistory[i].id !== id) {
                newHistory.push(uploadHistory[i]);
            }
        }
        uploadHistory = newHistory;
        renderHistory();
        showToast('🗑️ Item removed from history');
    }

    function refreshHistory() {
        renderHistory();
        showToast('🔄 History refreshed');
    }

    function clearHistory() {
        if (uploadHistory.length === 0) return;
        if (confirm('Clear all upload history?')) {
            uploadHistory = [];
            renderHistory();
            showToast('🗑️ History cleared');
        }
    }

    function downloadTemplate() {
        showToast('📋 Downloading template file...');
        setTimeout(function() {
            showToast('✅ Template downloaded successfully!');
        }, 1000);
    }

    // ============================================
    // DROP ZONE SETUP
    // ============================================

    function setupDropZone(zone, input, isBatch) {
        if (!zone || !input) return;
        
        zone.addEventListener('click', function() { input.click(); });

        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', function() {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            zone.classList.remove('dragover');
            var files = e.dataTransfer.files;
            if (isBatch) {
                for (var i = 0; i < files.length; i++) {
                    addFile(files[i], true);
                }
            } else {
                if (files.length > 0) addFile(files[0], false);
            }
        });

        input.addEventListener('change', function() {
            var files = input.files;
            if (isBatch) {
                for (var i = 0; i < files.length; i++) {
                    addFile(files[i], true);
                }
            } else {
                if (files.length > 0) addFile(files[0], false);
            }
            input.value = '';
        });
    }

    // ============================================
    // INIT
    // ============================================

    function initModule() {
        console.log('🚀 Initializing Upload Data Module...');
        
        var dropZone = getEl('dropZone');
        var fileInput = getEl('fileInput');
        var batchDropZone = getEl('batchDropZone');
        var batchFileInput = getEl('batchFileInput');
        
        if (!dropZone) {
            console.log('⏳ Waiting for DOM elements...');
            setTimeout(initModule, 100);
            return;
        }
        
        setupDropZone(dropZone, fileInput, false);
        setupDropZone(batchDropZone, batchFileInput, true);
        
        renderFileList([], getEl('fileListContainer'), false);
        renderFileList([], getEl('batchFileListContainer'), true);
        renderHistory();
        updateStats();
        
        console.log('✅ Upload Data module loaded successfully!');
        console.log('📄 Single and batch upload support');
        console.log('🧪 Click "Load Mock Data" to test with sample files');
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

    window.switchMode = switchMode;
    window.loadMockData = loadMockData;
    window.startUpload = startUpload;
    window.clearAllFiles = clearAllFiles;
    window.removeFile = removeFile;
    window.renderHistory = renderHistory;
    window.refreshHistory = refreshHistory;
    window.clearHistory = clearHistory;
    window.removeHistoryItem = removeHistoryItem;
    window.viewHistoryItem = viewHistoryItem;
    window.downloadHistoryItem = downloadHistoryItem;
    window.downloadTemplate = downloadTemplate;
    window.goToHistoryPage = goToHistoryPage;
    window.showToast = showToast;
})();