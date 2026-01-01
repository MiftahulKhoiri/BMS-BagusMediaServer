let isPaused = false;
let currentTask = null;
let uploadQueue = JSON.parse(localStorage.getItem("upload_queue") || "[]");

/* ===============================
   INIT
================================ */
document.addEventListener("DOMContentLoaded", () => {
    initMode();
    renderQueue();
    resumePendingUploads();
});

/* ===============================
   MODE (single / multi)
================================ */
function initMode() {
    const mode = document.getElementById("mode");
    const input = document.getElementById("file-input");

    function update() {
        input.multiple = (mode.value === "multi");
        input.value = "";
    }
    update();
    mode.addEventListener("change", update);
}

/* ===============================
   START UPLOAD
================================ */
function startUpload() {
    const files = document.getElementById("file-input").files;
    if (!files || files.length === 0) {
        alert("Pilih file dulu!");
        return;
    }

    for (let f of files) {
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
    if (currentTask || uploadQueue.length === 0) return;

    currentTask = uploadQueue.find(f => f.status === "queue" || f.status === "uploading");
    if (!currentTask) return;

    currentTask.status = "uploading";
    saveQueue();
    renderQueue();

    await uploadFile(currentTask);

    currentTask = null;
    processQueue();
}

/* ===============================
   UPLOAD FILE (RESUMABLE)
================================ */
async function uploadFile(task) {
    try {
        // START SESSION (jika belum ada)
        if (!task.session_id) {
            const form = new FormData();
            form.append("name", task.name);
            form.append("total_size", task.size);

            const res = await fetch("/upload/upload_chunk/start", { method: "POST", body: form });
            const data = await res.json();
            task.session_id = data.session_id;
        }

        const chunkSize = 1024 * 1024;
        let uploaded = task.progress / 100 * task.size;
        let chunkIndex = Math.floor(uploaded / chunkSize);

        // CHUNK LOOP
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
            renderQueue();

            chunkIndex++;
        }

        // FINISH
        const finish = new FormData();
        finish.append("session_id", task.session_id);
        finish.append("final_filename", task.name);

        await fetch("/upload/upload_chunk/finish", { method: "POST", body: finish });

        task.status = "done";
        task.progress = 100;
        saveQueue();
        renderQueue();

    } catch (e) {
        console.error(e);
        task.status = "paused";
        saveQueue();
    }
}

/* ===============================
   RESUME AFTER REFRESH
================================ */
async function resumePendingUploads() {
    for (let task of uploadQueue) {
        if (task.session_id && task.status !== "done") {
            const res = await fetch(`/upload/upload_chunk/status?session_id=${task.session_id}`);
            const data = await res.json();
            if (data.exists) {
                task.progress = Math.floor((data.received / data.total) * 100);
                task.status = "uploading";
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
   UI RENDER QUEUE
================================ */
function renderQueue() {
    const box = document.getElementById("status");
    box.innerHTML = "";

    uploadQueue.forEach(f => {
        box.innerHTML += `
            <div style="margin-bottom:6px">
                ${f.name}
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