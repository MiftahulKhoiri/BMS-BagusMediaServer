let isPaused = false;
let isRestart = false;

/* ===============================
   INIT MODE (PENTING!)
   atur multiple SEBELUM pilih file
================================ */
document.addEventListener("DOMContentLoaded", () => {
    const modeSelect = document.getElementById("mode");
    const fileInput = document.getElementById("file-input");

    function updateMode() {
        if (modeSelect.value === "multi") {
            fileInput.multiple = true;
        } else {
            fileInput.multiple = false;
        }
        // reset file biar tidak nyangkut
        fileInput.value = "";
    }

    updateMode();
    modeSelect.addEventListener("change", updateMode);
});

/* ===============================
   START UPLOAD
================================ */
function startUpload() {
    isPaused = false;
    isRestart = false;

    const mode = document.getElementById("mode").value;
    const fileInput = document.getElementById("file-input");
    const files = fileInput.files;

    if (!files || files.length === 0) {
        alert("Pilih file dulu!");
        return;
    }

    if (mode === "single") {
        uploadSingle(files[0]);
    } else {
        uploadMulti(files);
    }
}

/* ===============================
   PAUSE / RESUME / RESTART
================================ */
function pauseUpload() {
    isPaused = true;
    setStatus("⏸ Upload dijeda...");
}

function resumeUpload() {
    isPaused = false;
    setStatus("▶ Upload dilanjutkan...");
}

function restartUpload() {
    isRestart = true;
    isPaused = false;
    updateProgress(0);
    setStatus("↺ Upload diulang...");
}

/* ===============================
   MULTI UPLOAD (SEQUENTIAL)
================================ */
async function uploadMulti(files) {
    for (let i = 0; i < files.length; i++) {
        if (isRestart) return;

        setStatus(`⬆ Upload ${i + 1} / ${files.length}: ${files[i].name}`);
        await uploadSingle(files[i]);
    }

    if (!isRestart) {
        setStatus("✅ Semua file selesai!");
    }
}

/* ===============================
   UPLOAD SINGLE FILE (CHUNK)
================================ */
async function uploadSingle(file) {
    try {
        updateProgress(0);

        // === START SESSION ===
        const startForm = new FormData();
        startForm.append("name", file.name);
        startForm.append("total_size", file.size);

        const startRes = await fetch("/upload/upload_chunk/start", {
            method: "POST",
            body: startForm
        });

        if (!startRes.ok) throw new Error("Gagal start upload");

        const startData = await startRes.json();
        const session_id = startData.session_id;

        const chunkSize = 1024 * 1024; // 1 MB
        let chunkIndex = 0;

        // === SEND CHUNKS ===
        for (let start = 0; start < file.size; start += chunkSize) {

            while (isPaused) {
                await wait(200);
            }
            if (isRestart) return;

            const chunk = file.slice(start, start + chunkSize);

            const form = new FormData();
            form.append("session_id", session_id);
            form.append("chunk_index", chunkIndex);
            form.append("chunk", chunk);

            const res = await fetch("/upload/upload_chunk/append", {
                method: "POST",
                body: form
            });

            if (!res.ok) throw new Error("Chunk gagal dikirim");

            const data = await res.json();
            updateProgress(data.progress || 0);

            chunkIndex++;
            await wait(50);
        }

        // === FINISH ===
        const finishForm = new FormData();
        finishForm.append("session_id", session_id);
        finishForm.append("final_filename", file.name);

        await fetch("/upload/upload_chunk/finish", {
            method: "POST",
            body: finishForm
        });

        setStatus(`✅ ${file.name} selesai`);
        updateProgress(100);

    } catch (err) {
        console.error(err);
        setStatus("❌ Upload gagal");
    }
}

/* ===============================
   UTIL
================================ */
function updateProgress(p) {
    const bar = document.getElementById("progress-bar");
    bar.style.width = p + "%";
}

function setStatus(text) {
    document.getElementById("status").innerText = text;
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}