// uploadManager.js
let isPaused = false;
let currentTask = null;
let fileMap = new Map(); // Untuk menyimpan referensi file di memori

// Load queue dari localStorage (hanya metadata, tanpa file)
let uploadQueue = JSON.parse(localStorage.getItem("upload_queue") || "[]");

/* ===============================
   INIT
================================ */
document.addEventListener("DOMContentLoaded", () => {
    // Restore file references jika ada di fileMap
    restoreFileReferences();
    renderQueue();
    updateMainProgress();
    checkForPendingUploads();
});

/* ===============================
   START UPLOAD
================================ */
function startUpload() {
    const input = document.getElementById("file-input");
    const files = input.files;

    if (!files || files.length === 0) {
        alert("Pilih file dulu!");
        return;
    }

    const mode = document.getElementById("mode").value;
    const selectedFiles = mode === "single" ? [files[0]] : Array.from(files);

    selectedFiles.forEach(f => {
        const fileId = generateFileId(f);
        
        // Simpan file di memory map
        fileMap.set(fileId, f);
        
        uploadQueue.push({
            id: fileId,
            name: f.name,
            size: f.size,
            type: f.type,
            session_id: null,
            progress: 0,
            status: "queued",
            retries: 0,
            lastModified: f.lastModified
        });
    });

    saveQueue();
    renderQueue();
    updateMainProgress();
    processQueue();
    
    // Clear input file
    input.value = '';
}

/* ===============================
   QUEUE PROCESSOR
================================ */
async function processQueue() {
    if (currentTask !== null || isPaused) return;

    const task = uploadQueue.find(f => f.status === "queued" || f.status === "paused");
    if (!task) return;

    // Cek apakah file masih ada di memory
    if (!fileMap.has(task.id)) {
        task.status = "waiting_file";
        saveQueue();
        renderQueue();
        return;
    }

    currentTask = task;
    task.status = "uploading";
    saveQueue();
    renderQueue();

    await uploadFile(task);

    currentTask = null;
    // Tunggu sebentar sebelum memproses task berikutnya
    setTimeout(() => processQueue(), 500);
}

/* ===============================
   UPLOAD FILE DENGAN RETRY MECHANISM
================================ */
async function uploadFile(task) {
    const MAX_RETRIES = 3;
    let retryCount = task.retries || 0;
    
    try {
        if (!task.session_id) {
            task.session_id = await startUploadSession(task);
        }

        const chunkSize = 1024 * 1024; // 1MB
        const file = fileMap.get(task.id);
        
        if (!file) {
            throw new Error("File tidak ditemukan di memory");
        }

        let uploaded = Math.floor(task.progress * file.size / 100);
        let chunkIndex = Math.floor(uploaded / chunkSize);

        for (let start = uploaded; start < file.size; start += chunkSize) {
            // Cek pause
            while (isPaused) {
                await wait(1000);
                if (isPaused && task.status !== "paused") {
                    task.status = "paused";
                    saveQueue();
                    renderQueue();
                }
            }

            const chunk = file.slice(start, Math.min(start + chunkSize, file.size));
            
            const success = await sendChunk(task, chunk, chunkIndex);
            
            if (!success) {
                throw new Error(`Gagal mengirim chunk ${chunkIndex}`);
            }

            // Update progress
            task.progress = Math.floor(((start + chunk.size) / file.size) * 100);
            saveQueue();
            
            // Update UI setiap 2 chunk atau jika progress 100%
            if (chunkIndex % 2 === 0 || task.progress === 100) {
                renderQueue();
                updateMainProgress();
            }
            
            chunkIndex++;
        }

        // Finish upload
        await finishUpload(task);
        
        task.progress = 100;
        task.status = "done";
        saveQueue();
        renderQueue();
        updateMainProgress();
        
        // Hapus file dari memory setelah selesai
        fileMap.delete(task.id);

    } catch (error) {
        console.error("Upload error:", error);
        
        if (retryCount < MAX_RETRIES) {
            retryCount++;
            task.retries = retryCount;
            task.status = `retrying (${retryCount}/${MAX_RETRIES})`;
            saveQueue();
            renderQueue();
            
            // Tunggu dengan exponential backoff
            await wait(2000 * retryCount);
            
            // Reset untuk retry
            task.status = "queued";
            currentTask = null;
            return processQueue();
        } else {
            task.status = "failed";
            task.error = error.message;
            saveQueue();
            renderQueue();
            updateMainProgress();
        }
    }
}

/* ===============================
   UPLOAD SESSION FUNCTIONS
================================ */
async function startUploadSession(task) {
    const form = new FormData();
    form.append("name", task.name);
    form.append("total_size", task.size);
    form.append("file_type", task.type);

    const res = await fetch("/upload/upload_chunk/start", {
        method: "POST",
        body: form
    });
    
    if (!res.ok) throw new Error("Failed to start upload session");
    
    const data = await res.json();
    return data.session_id;
}

async function sendChunk(task, chunk, chunkIndex) {
    const form = new FormData();
    form.append("session_id", task.session_id);
    form.append("chunk_index", chunkIndex);
    form.append("chunk", chunk);
    form.append("total_chunks", Math.ceil(task.size / (1024 * 1024)));

    const res = await fetch("/upload/upload_chunk/append", {
        method: "POST",
        body: form
    });
    
    if (!res.ok) {
        const error = await res.text();
        throw new Error(`Chunk append failed: ${error}`);
    }
    
    return true;
}

async function finishUpload(task) {
    const form = new FormData();
    form.append("session_id", task.session_id);
    form.append("final_filename", task.name);

    const res = await fetch("/upload/upload_chunk/finish", {
        method: "POST",
        body: form
    });
    
    if (!res.ok) throw new Error("Failed to finish upload");
    
    return true;
}

/* ===============================
   CONTROL FUNCTIONS
================================ */
function pauseUpload() {
    isPaused = true;
    if (currentTask) {
        currentTask.status = "paused";
        saveQueue();
        renderQueue();
    }
    showNotification("Upload dijeda");
}

function resumeUpload() {
    isPaused = false;
    showNotification("Upload dilanjutkan");
    processQueue();
}

function restartUpload() {
    if (!confirm("Restart semua upload? Progress akan direset ke 0.")) {
        return;
    }
    
    isPaused = true;
    
    // Cancel current task
    if (currentTask) {
        currentTask.progress = 0;
        currentTask.status = "queued";
        currentTask.session_id = null;
        currentTask.retries = 0;
        currentTask = null;
    }
    
    // Reset all tasks
    uploadQueue.forEach(task => {
        task.progress = 0;
        task.status = "queued";
        task.session_id = null;
        task.retries = 0;
        task.error = null;
    });
    
    saveQueue();
    renderQueue();
    updateMainProgress();
    
    setTimeout(() => {
        isPaused = false;
        processQueue();
        showNotification("Upload di-restart");
    }, 500);
}

function removeFromQueue(index) {
    if (!confirm("Hapus file ini dari antrian?")) return;
    
    const task = uploadQueue[index];
    
    // Jika task sedang diupload, cancel dulu
    if (currentTask === task) {
        currentTask = null;
    }
    
    // Hapus file dari memory
    if (task.id) {
        fileMap.delete(task.id);
    }
    
    // Hapus dari queue
    uploadQueue.splice(index, 1);
    
    saveQueue();
    renderQueue();
    updateMainProgress();
    
    // Lanjutkan queue jika ada task lain
    if (currentTask === null) {
        processQueue();
    }
    
    showNotification("File dihapus dari antrian");
}

function clearCompleted() {
    const completedCount = uploadQueue.filter(t => t.status === "done").length;
    
    if (completedCount === 0) {
        alert("Tidak ada upload yang selesai");
        return;
    }
    
    if (!confirm(`Hapus ${completedCount} file yang sudah selesai dari daftar?`)) {
        return;
    }
    
    // Hapus hanya yang status done
    uploadQueue = uploadQueue.filter(task => {
        if (task.status === "done") {
            // Hapus dari memory
            fileMap.delete(task.id);
            return false;
        }
        return true;
    });
    
    saveQueue();
    renderQueue();
    updateMainProgress();
    showNotification(`${completedCount} file dihapus`);
}

/* ===============================
   UI FUNCTIONS
================================ */
function renderQueue() {
    const box = document.getElementById("status");
    
    if (uploadQueue.length === 0) {
        box.innerHTML = '<div class="empty-queue">Tidak ada file dalam antrian</div>';
        return;
    }
    
    box.innerHTML = '';
    
    uploadQueue.forEach((task, index) => {
        const statusClass = getStatusClass(task.status);
        const statusText = getStatusText(task.status);
        const fileSize = formatBytes(task.size);
        const isCurrent = currentTask === task;
        
        box.innerHTML += `
            <div class="queue-item ${isCurrent ? 'current' : ''}">
                <div class="queue-header">
                    <span class="file-name">${task.name}</span>
                    <span class="file-size">${fileSize}</span>
                    <button class="remove-btn" onclick="removeFromQueue(${index})" title="Hapus dari antrian">
                        ✕
                    </button>
                </div>
                
                <div class="progress-container">
                    <div class="progress-fill" style="width: ${task.progress}%"></div>
                </div>
                
                <div class="queue-footer">
                    <span class="status ${statusClass}">${statusText}</span>
                    <span class="progress-text">${task.progress}%</span>
                    ${task.error ? `<span class="error">Error: ${task.error}</span>` : ''}
                </div>
            </div>
        `;
    });
}

function updateMainProgress() {
    const progressBar = document.getElementById("progress-bar");
    
    if (uploadQueue.length === 0) {
        progressBar.style.width = '0%';
        return;
    }
    
    // Hitung rata-rata progress
    const totalProgress = uploadQueue.reduce((sum, task) => sum + task.progress, 0);
    const avgProgress = Math.floor(totalProgress / uploadQueue.length);
    
    progressBar.style.width = `${avgProgress}%`;
    
    // Update warna berdasarkan progress
    if (avgProgress < 30) {
        progressBar.style.backgroundColor = '#ff4444';
    } else if (avgProgress < 70) {
        progressBar.style.backgroundColor = '#ffaa00';
    } else {
        progressBar.style.backgroundColor = '#00ff9c';
    }
}

function getStatusClass(status) {
    const statusMap = {
        'queued': 'queued',
        'uploading': 'uploading',
        'paused': 'paused',
        'done': 'done',
        'failed': 'failed',
        'retrying': 'retrying',
        'waiting_file': 'waiting'
    };
    return statusMap[status] || 'queued';
}

function getStatusText(status) {
    const textMap = {
        'queued': 'Dalam antrian',
        'uploading': 'Mengupload...',
        'paused': 'Dijeda',
        'done': 'Selesai',
        'failed': 'Gagal',
        'retrying': 'Mencoba ulang...',
        'waiting_file': 'Menunggu file'
    };
    return textMap[status] || status;
}

/* ===============================
   UTILITY FUNCTIONS
================================ */
function generateFileId(file) {
    return `${file.name}-${file.size}-${file.lastModified}-${Date.now()}`;
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showNotification(message, type = 'info') {
    // Buat notifikasi sederhana
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ff4444' : '#00ff9c'};
        color: #000;
        padding: 10px 20px;
        border-radius: 5px;
        z-index: 1000;
        font-weight: bold;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}

function restoreFileReferences() {
    // Cek localStorage untuk file yang belum selesai
    // Note: File tidak bisa disimpan di localStorage, jadi hanya metadata
    uploadQueue.forEach(task => {
        if (task.status !== 'done' && task.status !== 'failed') {
            task.status = 'waiting_file';
            task.error = 'File perlu dipilih ulang setelah refresh';
        }
    });
}

function checkForPendingUploads() {
    const pending = uploadQueue.filter(t => 
        t.status === 'uploading' || t.status === 'queued'
    ).length;
    
    if (pending > 0) {
        if (confirm(`Ada ${pending} upload yang tertunda. Lanjutkan?`)) {
            processQueue();
        }
    }
}

/* ===============================
   STORAGE FUNCTIONS
================================ */
function saveQueue() {
    // Simpan hanya metadata, tanpa file
    const queueToSave = uploadQueue.map(task => ({
        id: task.id,
        name: task.name,
        size: task.size,
        type: task.type,
        session_id: task.session_id,
        progress: task.progress,
        status: task.status,
        retries: task.retries,
        error: task.error,
        lastModified: task.lastModified
    }));
    
    localStorage.setItem("upload_queue", JSON.stringify(queueToSave));
}

/* ===============================
   EVENT LISTENERS TAMBAHAN
================================ */
window.addEventListener('beforeunload', (e) => {
    const hasActiveUploads = uploadQueue.some(task => 
        task.status === 'uploading' || task.status === 'queued'
    );
    
    if (hasActiveUploads && !isPaused) {
        e.preventDefault();
        e.returnValue = 'Ada upload yang sedang berjalan. Yakin ingin meninggalkan halaman?';
    }
});

// Tambahkan CSS untuk notifikasi
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .queue-item {
        border: 1px solid #333;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background: #1a1a1a;
    }
    
    .queue-item.current {
        border-color: #00ff9c;
        box-shadow: 0 0 10px rgba(0, 255, 156, 0.3);
    }
    
    .queue-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .file-name {
        flex: 1;
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .file-size {
        margin: 0 10px;
        color: #888;
        font-size: 0.9em;
    }
    
    .remove-btn {
        background: #ff4444;
        border: none;
        color: white;
        border-radius: 3px;
        cursor: pointer;
        padding: 3px 8px;
        font-size: 12px;
    }
    
    .remove-btn:hover {
        background: #ff6666;
    }
    
    .progress-container {
        height: 6px;
        background: #222;
        border-radius: 3px;
        overflow: hidden;
        margin: 5px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: #00ff9c;
        transition: width 0.3s ease;
    }
    
    .queue-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8em;
        color: #888;
    }
    
    .status {
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.8em;
    }
    
    .status.queued { background: #666; color: #fff; }
    .status.uploading { background: #0066cc; color: #fff; }
    .status.paused { background: #ffaa00; color: #000; }
    .status.done { background: #00cc66; color: #000; }
    .status.failed { background: #ff4444; color: #fff; }
    .status.retrying { background: #ff8800; color: #000; }
    .status.waiting { background: #888; color: #fff; }
    
    .progress-text {
        font-weight: bold;
    }
    
    .error {
        color: #ff4444;
        font-size: 0.8em;
        max-width: 200px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .empty-queue {
        text-align: center;
        color: #888;
        padding: 20px;
    }
    
    .btn-group {
        margin-top: 10px;
    }
    
    .btn-group button {
        margin: 0 5px;
    }
`;
document.head.appendChild(style);