console.log("Admin JS Loaded v1.1");
async function loadStats() {
    try {
        const response = await fetch('/api/admin/stats');
        const data = await response.json();

        document.getElementById('stat-movies').innerText = data.total_movies;

        // Update Limit UI
        const limitDisplay = document.getElementById('limit-value-display');
        const limitInput = document.getElementById('limit-input');
        const limitSlider = document.getElementById('limit-slider');

        if (data.upload_speed_limit > 0) {
            limitDisplay.innerText = `${data.upload_speed_limit} MB/s`;
            limitInput.value = data.upload_speed_limit;
            limitSlider.value = data.upload_speed_limit > 10 ? 10 : data.upload_speed_limit;
        } else {
            limitDisplay.innerText = "Unlimited";
            limitInput.value = 0;
            limitSlider.value = 0;
        }

        const uploadInfo = data.upload_status;
        const uploadStat = document.getElementById('stat-upload');
        const uploadSpeed = document.getElementById('stat-speed');
        const progressBar = document.getElementById('progress-bar-container');
        const progressFill = document.getElementById('progress-bar-fill');

        if (uploadInfo.is_uploading) {
            uploadStat.innerHTML = `<span class="text-primary animate-pulse text-sm">${uploadInfo.progress.status}</span>`;
            if (uploadInfo.progress.percent !== undefined) {
                progressBar.classList.remove('hidden');
                progressFill.style.width = `${uploadInfo.progress.percent}%`;
            }
            if (uploadInfo.progress.speed_mb !== undefined) {
                uploadSpeed.classList.remove('hidden');
                uploadSpeed.innerText = `${uploadInfo.progress.speed_mb} MB/s`;
            }
        } else {
            uploadStat.innerText = uploadInfo.progress.status || "Idle";
            progressBar.classList.add('hidden');
            uploadSpeed.classList.add('hidden');
        }
    } catch (e) {
        console.error("Stats Error:", e);
    }
}

async function loadMovies() {
    try {
        const response = await fetch('/api/admin/movies');
        const movies = await response.json();
        const container = document.getElementById('movie-list');
        const mobileContainer = document.getElementById('movie-list-mobile');

        // Populate Table (Desktop)
        container.innerHTML = movies.map(m => `
            <tr class="hover:bg-white/2 transition-colors">
                <td class="px-6 py-4 text-sm font-mono text-white/40">#${m.id}</td>
                <td class="px-6 py-4 text-sm font-bold">${m.title}</td>
                <td class="px-6 py-4 text-[10px] font-mono text-white/30 truncate max-w-[150px]">${m.file_id}</td>
                <td class="px-6 py-4 text-sm text-white/50">${m.release_year}</td>
                <td class="px-6 py-4 text-right">
                    <button onclick="deleteMovie(${m.id})" class="p-2 hover:bg-red-500/10 text-red-500/50 hover:text-red-500 rounded-lg transition-all">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </td>
            </tr>
        `).join('');

        // Populate Cards (Mobile)
        mobileContainer.innerHTML = movies.map(m => `
            <div class="p-5 flex justify-between items-center group active:bg-white/5 transition-all">
                <div class="flex-1 min-w-0 pr-4">
                    <h4 class="font-bold text-sm truncate mb-1">${m.title}</h4>
                    <div class="flex items-center gap-2 text-[10px] text-white/30 font-mono">
                        <span class="bg-white/5 px-1.5 py-0.5 rounded">ID: ${m.id}</span>
                        <span>${m.release_year || '2024'}</span>
                    </div>
                </div>
                <button onclick="deleteMovie(${m.id})" class="w-10 h-10 flex items-center justify-center rounded-xl bg-red-500/10 text-red-500">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            </div>
        `).join('');

        document.getElementById('sync-time').innerText = `Last synced: ${new Date().toLocaleTimeString()}`;
    } catch (e) {
        console.error("Load Movies Error:", e);
    }
}

async function deleteMovie(id) {
    const message = "Are you sure you want to remove this movie from the library?";
    console.log("DEBUG: deleteMovie called for ID:", id);

    const executeDelete = async () => {
        try {
            const response = await fetch(`/api/admin/movies/${id}`, { method: 'DELETE' });
            if (response.ok) {
                loadMovies();
                loadStats();
                if (window.Telegram?.WebApp) {
                    window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                }
                alert("Xóa thành công!");
            } else {
                const err = await response.json();
                console.error("Delete failed:", err);
                alert("Lỗi xóa: " + (err.detail || "Không rõ lỗi"));
            }
        } catch (e) {
            console.error("Delete Request Error:", e);
            alert("Lỗi kết nối khi xóa phim.");
        }
    };

    if (window.Telegram?.WebApp?.showConfirm) {
        window.Telegram.WebApp.showConfirm(message, (confirmed) => {
            if (confirmed) executeDelete();
        });
    } else {
        if (confirm(message)) {
            executeDelete();
        }
    }
}

async function startScan() {
    const pathInput = document.getElementById('scan-path');
    const path = pathInput.value;
    if (!path) return alert("Please enter a path!");

    const btn = document.getElementById('btn-start-scan');
    btn.disabled = true;
    btn.innerText = "Processing...";

    try {
        const response = await fetch('/api/admin/upload/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });

        if (response.ok) {
            alert("Scan started successfully!");
            document.getElementById('upload-modal').classList.add('hidden');
            pathInput.value = "";
        } else {
            const err = await response.json();
            alert(`Error: ${err.detail}`);
        }
    } catch (e) {
        alert("Request failed.");
    } finally {
        btn.disabled = false;
        btn.innerText = "Start Scanning & Uploading";
    }
}

window.cleanupDuplicates = async function (event) {
    if (!confirm("Bạn có chắc chắn muốn xóa các phim trùng tên và kích thước không?\nHành động này sẽ xóa file trên Telegram và dữ liệu trên web.")) {
        return;
    }

    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Cleaning...`;

    try {
        const response = await fetch('/api/admin/cleanup/duplicates', {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            const data = result.data;
            alert(`Đã dọn dẹp xong!\n- Tìm thấy: ${data.duplicates_found} bản trùng\n- Đã xóa Telegram: ${data.telegram_deleted}\n- Đã xóa DB: ${data.db_deleted}`);
            loadMovies();
            loadStats();
        } else {
            const err = await response.json();
            alert(`Lỗi: ${err.detail || "Không thể dọn dẹp"}`);
        }
    } catch (e) {
        console.error("Cleanup Error:", e);
        alert("Lỗi kết nối khi dọn dẹp.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

async function saveSpeedLimit() {
    const limitInput = document.getElementById('limit-input');
    const limit = parseFloat(limitInput.value) || 0;

    try {
        const response = await fetch('/api/admin/config/upload-limit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: limit })
        });

        if (response.ok) {
            alert("Speed limit updated!");
            loadStats();
        } else {
            alert("Failed to update speed limit.");
        }
    } catch (e) {
        alert("Request failed.");
    }
}

// Slider and Input Sync
document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('limit-slider');
    const input = document.getElementById('limit-input');

    if (slider && input) {
        slider.addEventListener('input', (e) => {
            input.value = e.target.value;
        });

        input.addEventListener('input', (e) => {
            slider.value = e.target.value;
        });
    }
});

// Polling for updates
setInterval(loadStats, 3000);
setInterval(loadMovies, 10000);

// Init
loadStats();
loadMovies();
