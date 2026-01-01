<script>
let isPaused = false;
let currentTask = null;

let uploadQueue = JSON.parse(localStorage.getItem("upload_queue") || "[]");

/* ===============================
   INIT
================================ */
document.addEventListener("DOMContentLoaded", () => {
    renderQueue();
    resumePendingUploads();
});

/* ===============================
   START UPLOAD (FIXED)
================================ */
function startUpload() {
    const input = document.getElementById("file-input");
    const files = input.files;

    if (!files || files.length === 0) {
        alert("Pilih file dulu!");
        return;
    }

    // 🔥 RESET STATE (WAJIB)
    currentTask = null;

    const mode = document.getElementById("mode").value;
    const selectedFiles =
        mode === "single" ? [files[0]] : Array.from(files);

    for (let f of selectedFiles) {
        uploadQueue.push({
            name: f.name,
            size: f.size,
            file: f,
            session_id: null,
            progress: 0,
            status: "queued"
        });
    }

    saveQueue();
    renderQueue();
    processQueue();
}

/* ===============================
   QUEUE PROCESSOR
================================ */
async function processQueue() {
    if (currentTask !== null) return;

    const task = uploadQueue.find(f => f.status === "queued");
    if (!task) return;

    if (!task.file) {
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
    processQueue();
}

/* ===============================
   UPLOAD FILE
================================ */
async function uploadFile(task) {
    try {
        if (!task.session_id) {
            const form = new FormData();
            form.append("name", task.name);
            form.append("total_size", task.size);

            const res = await fetch("/upload/upload_chunk/start", {
                method: "POST",
                body: form
            });
            const data = await res.json();
            task.session_id = data.session_id;
            saveQueue();
        }

        const chunkSize = 1024 * 1024;
        let uploaded = Math.floor(task.progress * task.size / 100);
        let chunkIndex = Math.floor(uploaded / chunkSize);

        for (let start = uploaded; start < task.size; start += chunkSize) {
            while (isPaused) await wait(300);

            const chunk = task.file.slice(start, start + chunkSize);

            const form = new FormData();
            form.append("session_id", task.session_id);
            form.append("chunk_index", chunkIndex);
            form.append("chunk", chunk);

            const res = await fetch("/upload/upload_chunk/append", {
                method: "POST",
                body: form
            });
            const data = await res.json();

            task.progress = data.progress;
            saveQueue();

            if (chunkIndex % 3 === 0) renderQueue();
            chunkIndex++;
        }

        const finish = new FormData();
        finish.append("session_id", task.session_id);
        finish.append("final_filename", task.name);

        await fetch("/upload/upload_chunk/finish", {
            method: "POST",
            body: finish
        });

        task.progress = 100;
        task.status = "done";
        saveQueue();
        renderQueue();

    } catch (e) {
        console.error(e);
        task.status = "paused";
        saveQueue();
        renderQueue();
    }
}

/* ===============================
   RESUME AFTER REFRESH
================================ */
async function resumePendingUploads() {
    for (let task of uploadQueue) {
        if (task.session_id && task.status !== "done") {
            const res = await fetch(
                `/upload/upload_chunk/status?session_id=${task.session_id}`
            );
            const data = await res.json();

            if (data.exists && data.received < data.total) {
                task.progress = Math.floor(
                    (data.received / data.total) * 100
                );
                task.status = "queued";
            } else {
                task.status = "done";
            }
        }
    }

    saveQueue();
    renderQueue();
    processQueue();
}

/* ===============================
   PAUSE / RESUME
================================ */
function pauseUpload() {
    isPaused = true;
}
function resumeUpload() {
    isPaused = false;
}

/* ===============================
   UI
================================ */
function renderQueue() {
    const box = document.getElementById("status");
    box.innerHTML = "";

    uploadQueue.forEach(f => {
        box.innerHTML += `
            <div style="margin-bottom:8px">
                <b>${f.name}</b>
                <div style="height:6px;background:#222">
                    <div style="width:${f.progress}%;height:6px;background:#00ff9c"></div>
                </div>
                <small>${f.status} (${f.progress}%)</small>
            </div>
        `;
    });
}

/* ===============================
   STORAGE
================================ */
function saveQueue() {
    localStorage.setItem("upload_queue", JSON.stringify(uploadQueue));
}

/* ===============================
   UTIL
================================ */
function wait(ms) {
    return new Promise(r => setTimeout(r, ms));
}
</script>