// ============================================
// FINESE 2 — Core JavaScript
// ============================================

// Toast notifications
function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const iconSvg = type === 'success' 
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>'
        : type === 'error'
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    
    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Dataset info loader
async function loadDatasetInfo() {
    try {
        const res = await fetch('/api/data/info');
        const data = await res.json();
        const card = document.getElementById('datasetCard');
        const badge = document.getElementById('datasetBadge');
        
        if (data.loaded) {
            card.innerHTML = `
                <div class="dataset-info">
                    <div class="dataset-name" title="${data.name}">${data.name}</div>
                    <div class="dataset-meta">${data.shape[0].toLocaleString()} rows · ${data.shape[1]} columns</div>
                    <div class="dataset-shape">
                        <span class="shape-badge">${data.shape[0]} R</span>
                        <span class="shape-badge">${data.shape[1]} C</span>
                    </div>
                </div>
            `;
            if (badge) {
                badge.style.display = 'inline-flex';
                badge.textContent = data.name;
            }
        } else {
            card.innerHTML = `
                <div class="dataset-empty">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                    </svg>
                    <span>No dataset loaded</span>
                </div>
            `;
            if (badge) badge.style.display = 'none';
        }
    } catch (e) {
        console.error('Failed to load dataset info:', e);
    }
}

// File upload handling
function initUpload() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');
    const status = document.getElementById('uploadStatus');
    
    if (!zone || !input) return;
    
    zone.addEventListener('click', () => input.click());
    
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) handleFileUpload(files[0]);
    });
    
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });
}

async function handleFileUpload(file) {
    const status = document.getElementById('uploadStatus');
    if (!status) return;
    
    status.textContent = 'Uploading...';
    status.className = 'upload-status';
    
    const form = new FormData();
    form.append('file', file);
    
    try {
        const res = await fetch('/api/data/upload', {
            method: 'POST',
            body: form
        });
        
        const data = await res.json();
        
        if (data.error) {
            status.textContent = `Error: ${data.error}`;
            status.className = 'upload-status error';
            showToast(data.error, 'error');
        } else {
            status.textContent = `✓ Loaded: ${data.name}`;
            status.className = 'upload-status success';
            showToast(`Dataset "${data.name}" loaded successfully!`, 'success');
            loadDatasetInfo();
            setTimeout(() => window.location.reload(), 1000);
        }
    } catch (e) {
        status.textContent = 'Upload failed';
        status.className = 'upload-status error';
        showToast('Upload failed. Please try again.', 'error');
        console.error('Upload error:', e);
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    loadDatasetInfo();
    initUpload();
});
