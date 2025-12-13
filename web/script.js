function startDownload() {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();

    if (!url) {
        showToast("Please enter a valid URL", true);
        return;
    }

    const btn = document.getElementById('downloadBtn');
    btn.disabled = true;
    btn.querySelector('.btn-text').textContent = "Starting...";

    const statusContainer = document.getElementById('statusContainer');
    statusContainer.classList.add('visible');

    // Reset progress
    updateProgress(0);
    updateStatus("Initializing...");

    // Call Python backend
    // pywebview inserts 'pywebview' object
    if (window.pywebview) {
        window.pywebview.api.download_video(url).catch(err => {
            showToast("Error: " + err, true);
            resetUI();
        });
    } else {
        console.error("PyWebView API not found. Are you running inside the app?");
        showToast("Backend not connected", true);
        resetUI();
    }
}

// Functions called by Python
function updateProgress(percent) {
    const bar = document.getElementById('progressBar');
    const text = document.getElementById('progressPercent');
    bar.style.width = percent + '%';
    text.textContent = Math.round(percent) + '%';
}

function updateStatus(message) {
    document.getElementById('statusText').textContent = message;
}

function downloadComplete(path) {
    showToast("Download Complete!", false);
    updateStatus("Saved to: " + path);
    updateProgress(100);
    resetUI();
    document.getElementById('urlInput').value = ""; // clear input
}

function downloadError(msg) {
    showToast("Error: " + msg, true);
    updateStatus("Failed.");
    document.getElementById('progressBar').style.background = '#ff4757'; // red
    setTimeout(resetUI, 3000);
}

function resetUI() {
    const btn = document.getElementById('downloadBtn');
    btn.disabled = false;
    btn.querySelector('.btn-text').textContent = "Download";

    const bar = document.getElementById('progressBar');
    // bar.style.background = ... (reset gradient if changed on error)
    // Actually simpler to just remove inline style:
    bar.style.background = '';
}

function showToast(msg, isError) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.background = isError ? '#ff4757' : '#2ed573';
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Initialize on load
window.addEventListener('pywebviewready', function () {
    window.pywebview.api.init().then(response => {
        updateFolderPath(response.download_folder);
    }).catch(err => {
        console.error("Failed to init", err);
    });
});

function changeFolder() {
    if (window.pywebview) {
        window.pywebview.api.choose_directory().then(newPath => {
            if (newPath) {
                updateFolderPath(newPath);
            }
        });
    } else {
        showToast("Backend not available", true);
    }
}

function updateFolderPath(path) {
    const el = document.getElementById('folderPath');
    // Truncate if very long for display
    let displayPath = path;
    if (displayPath.length > 30) {
        // Keep start and end for better context (e.g. C:\Users\...\Downloads)
        displayPath = path.slice(0, 10) + "..." + path.slice(-15);
    }
    el.textContent = displayPath;
    el.title = path;
}
