let uploads = {}; // session per file

function startMultiUpload() {
    let files = document.getElementById("fileInput").files;
    if (!files.length) return alert("Pilih file dulu!");

    document.getElementById("upload-list").innerHTML = "";

    [...files].forEach(file => {
        createUploadCard(file);
        startUpload(file);
    });
}

function createUploadCard(file) {
    let html = `
        <div class="file-item" id="file-${file.name}">
            <strong>${file.name}</strong>
            <div class="progress-bar">
                <div class="progress-inner" id="progress-${file.name}"></div>
            </div>
            <p id="status-${file.name}">Menunggu...</p>
            <button onclick="cancelUpload('${file.name}')">Batalkan</button>
        </div>
    `;
    document.getElementById("upload-list").innerHTML += html;
}

async function startUpload(file) {
    document.getElementById(`status-${file.name}`).innerText = "Inisialisasi...";

    // ==== START SESSION ====
    let form = new FormData();
    form.append("name", file.name);
    form.append("total_size", file.size);
    form.append("file_md5", "");

    let startRes = await fetch("/filemanager/upload_chunk/start", {
        method: "POST",
        body: form
    });

    let startData = await startRes.json();

    if (!startData.session_id) {
        document.getElementById(`status-${file.name}`).innerText = "Gagal start!";
        return;
    }

    uploads[file.name] = {
        session_id: startData.session_id,
        chunk_size: startData.recommended_chunk_size,
        index: 0,
        uploading: true
    };

    uploadChunks(file);
}

async function uploadChunks(file) {
    let up = uploads[file.name];
    let chunkSize = up.chunk_size;

    while (up.uploading) {
        let start = up.index * chunkSize;
        let end = Math.min(start + chunkSize, file.size);

        let chunk = file.slice(start, end);

        let form = new FormData();
        form.append("session_id", up.session_id);
        form.append("chunk_index", up.index);
        form.append("total_chunks", Math.ceil(file.size / chunkSize));
        form.append("chunk", chunk);

        let res = await fetch("/filemanager/upload_chunk/append", {
            method: "POST",
            body: form
        });

        let json = await res.json();

        if (json.error) {
            document.getElementById(`status-${file.name}`).innerText =
                "Error: " + json.error;
            up.uploading = false;
            return;
        }

        // Progress update
        document.getElementById(`progress-${file.name}`).style.width =
            json.progress + "%";

        document.getElementById(`status-${file.name}`).innerText =
            "Uploaded: " + json.progress + "%";

        up.index++;

        if (end >= file.size) break;

        await new Promise(r => setTimeout(r, 30));
    }

    finishUpload(file);
}

async function finishUpload(file) {
    let up = uploads[file.name];

    let form = new FormData();
    form.append("session_id", up.session_id);
    form.append("final_filename", file.name);

    let res = await fetch("/filemanager/upload_chunk/finish", {
        method: "POST",
        body: form
    });

    let json = await res.json();

    if (json.status === "finished") {
        document.getElementById(`progress-${file.name}`).style.width = "100%";
        document.getElementById(`status-${file.name}`).innerText = "Selesai ✓";
    } else {
        document.getElementById(`status-${file.name}`).innerText = "Gagal finish!";
    }

    up.uploading = false;
}

async function cancelUpload(filename) {
    let up = uploads[filename];
    if (!up) return;

    up.uploading = false;

    let form = new FormData();
    form.append("session_id", up.session_id);

    await fetch("/filemanager/upload_chunk/cancel", {
        method: "POST",
        body: form
    });

    document.getElementById(`status-${filename}`).innerText = "Dibatalkan!";
    document.getElementById(`progress-${filename}`).style.width = "0%";
}