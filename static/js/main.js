async function loadDatasetInfo() {
    const res = await fetch('/api/data/info');
    const data = await res.json();
    const infoBox = document.getElementById('datasetInfo');
    if (data.loaded) {
        infoBox.innerHTML = `<div class="mb-1"><strong>${data.name}</strong></div><div>${data.shape[0]} rows × ${data.shape[1]} cols</div>`;
        const meta = document.getElementById('headerMeta');
        if (meta) meta.textContent = `${data.name} | ${data.shape[0]} rows`;
    } else {
        infoBox.innerHTML = '<em>No dataset loaded</em>';
    }
}

document.getElementById('fileInput')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    const status = document.getElementById('uploadStatus');
    status.textContent = 'Uploading...';
    const res = await fetch('/api/data/upload', {method: 'POST', body: form});
    const data = await res.json();
    if (data.error) {
        status.textContent = 'Error: ' + data.error;
        status.className = 'text-danger';
    } else {
        status.textContent = `Loaded: ${data.name}`;
        status.className = 'text-success';
        loadDatasetInfo();
        window.location.reload();
    }
});
