let isPaused = false;
let isRestart = false;

// ===============================
// START UPLOAD
// ===============================
function startUpload() {
    isPaused = false;
    isRestart = false;

    let mode = document.getElementById("mode").value;
    let files = document.getElementById("file-input").files;

    if (files.length === 0) {
        alert("Pilih file dulu!");
        return;
    }

    if (mode === "single") {
        uploadSingle(files[0]);
    } else {
        uploadMulti(files);
    }
}

// ===============================
// PAUSE / RESUME / RESTART
// ===============================
function pauseUpload() {
    isPaused = true;
    document.getElementById("status").innerText = "Upload dijeda...";
}

function resumeUpload() {
    isPaused = false;
    document.getElementById("status").innerText = "Upload dilanjutkan...";
}

function restartUpload() {
    isRestart = true;
    document.getElementById("status").innerText = "Upload diulang...";
}


// ===============================
// MULTI UPLOAD — Sequential
// ===============================
async function uploadMulti(files) {
    for (let i = 0; i < files.length; i++) {
        if (isRestart) break;

        document.getElementById("status").innerText =
            `Upload file ${i + 1} dari ${files.length}: ${files[i].name}`;

        await uploadSingle(files[i]);
    }

    if (!isRestart)
        document.getElementById("status").innerText = "SEMUA FILE SELESAI!";
}


// ===============================
// UPLOAD SINGLE FILE (Chunk)
// ===============================
async function uploadSingle(file) {
    updateProgress(0);

    let startForm = new FormData();
    startForm.append("name", file.name);
    startForm.append("total_size", file.size);

    let startRes = await fetch("/upload/upload_chunk/start", {
        method: "POST",
        body: startForm
    });

    let startData = await startRes.json();
    let session_id = startData.session_id;

    let chunkSize = 1024 * 1024;
    let chunkIndex = 0;

    for (let start = 0; start < file.size; start += chunkSize) {

        while (isPaused) {
            await wait(200);
        }
        if (isRestart) return;

        let chunk = file.slice(start, start + chunkSize);

        let form = new FormData();
        form.append("session_id", session_id);
        form.append("chunk_index", chunkIndex);
        form.append("chunk", chunk);

        let res = await fetch("/upload/upload_chunk/append", {
            method: "POST",
            body: form
        });

        let data = await res.json();
        updateProgress(data.progress);

        chunkIndex++;
        await wait(50);
    }

    let finishForm = new FormData();
    finishForm.append("session_id", session_id);
    finishForm.append("final_filename", file.name);

    await fetch("/upload/upload_chunk/finish", {
        method: "POST",
        body: finishForm
    });

    document.getElementById("status").innerText = `${file.name} selesai!`;
}


// ===============================
// UTIL
// ===============================
function updateProgress(p) {
    document.getElementById("progress-bar").style.width = p + "%";
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}