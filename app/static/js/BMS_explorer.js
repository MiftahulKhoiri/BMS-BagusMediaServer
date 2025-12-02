// BMS Explorer Premium JS
let currentPath = "/storage/emulated/0/BMS/";
let selectedFile = null;
let draggingElement = null;

document.addEventListener("DOMContentLoaded", () => {
    initUI();
    loadFiles(currentPath);
});

function initUI() {
    document.getElementById("refreshBtn").onclick = () => loadFiles(currentPath);
    document.getElementById("uploadBtn").onclick = () => document.getElementById("fileInput").click();
    document.getElementById("fileInput").onchange = handleFilesSelected;
    document.getElementById("zipBtn").onclick = zipCurrent;
    document.getElementById("unzipBtn").onclick = unzipPrompt;

    // action menu buttons
    document.getElementById("actPreview").onclick = previewSelected;
    document.getElementById("actOpen").onclick = downloadSelected;
    document.getElementById("actMove").onclick = movePrompt;
    document.getElementById("actRename").onclick = renamePrompt;
    document.getElementById("actDelete").onclick = deleteSelected;

    // drop zone
    const dz = document.getElementById("dropZone");
    dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("dragover"); });
    dz.addEventListener("dragleave", (e) => { dz.classList.remove("dragover"); });
    dz.addEventListener("drop", (e) => {
        e.preventDefault(); dz.classList.remove("dragover");
        const files = Array.from(e.dataTransfer.files);
        uploadFiles(files);
    });
}

// ==================== Load folder ====================
function loadFiles(path) {
    const area = document.getElementById("fileArea");
    area.innerHTML = "<p class='loading'>Loading...</p>";

    fetch(`/filemanager/list?path=${encodeURIComponent(path)}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert(data.error); return; }
            currentPath = data.current;
            renderBreadcrumb(currentPath);
            renderFiles(data.items);
        })
        .catch(err => { alert("Gagal memuat folder"); console.error(err); });
}

function renderBreadcrumb(path) {
    document.getElementById("breadcrumb").innerText = path;
}

// ==================== Render files ====================
function renderFiles(items) {
    const area = document.getElementById("fileArea");
    area.innerHTML = "";

    items.forEach(item => {
        const div = document.createElement("div");
        div.className = "file-item";
        div.draggable = true;

        div.innerHTML = `
            <div class='file-icon'>${item.is_dir ? "📁" : iconForFile(item.name)}</div>
            <div class='file-name' title='${item.name}'>${item.name}</div>
        `;

        // Tap / click
        div.onclick = () => {
            if (item.is_dir) {
                loadFiles(item.path);
            } else {
                selectedFile = item.path;
                openMenuAt(div);
            }
        };

        // Long press for touch
        let pressTimer;
        div.onpointerdown = () => {
            pressTimer = setTimeout(() => {
                selectedFile = item.path;
                openMenuAt(div);
            }, 600);
        };
        div.onpointerup = () => clearTimeout(pressTimer);
        div.onpointerleave = () => clearTimeout(pressTimer);

        // Drag & Drop for move
        div.ondragstart = (e) => {
            draggingElement = item;
            div.classList.add("dragging");
            e.dataTransfer.setData("text/plain", item.path);
        };
        div.ondragend = () => {
            draggingElement = null;
            div.classList.remove("dragging");
        };

        // If folder, allow drop into folder to move
        if (item.is_dir) {
            div.ondragover = (e) => { e.preventDefault(); div.classList.add("dragging"); };
            div.ondragleave = () => { div.classList.remove("dragging"); };
            div.ondrop = (e) => {
                e.preventDefault();
                div.classList.remove("dragging");
                const source = e.dataTransfer.getData("text/plain");
                const dest = item.path + "/" + source.split("/").pop();
                moveItem(source, dest);
            };
        }

        area.appendChild(div);
    });
}

function iconForFile(name) {
    const ext = name.split(".").pop().toLowerCase();
    if (["png","jpg","jpeg","gif","webp"].includes(ext)) return "🖼️";
    if (["mp4","mkv","webm","avi","mov"].includes(ext)) return "🎬";
    if (["mp3","wav","ogg"].includes(ext)) return "🎵";
    if (["zip","rar"].includes(ext)) return "🗜️";
    if (["txt","log","md","json","py","js","html","css"].includes(ext)) return "📄";
    return "📄";
}

// ==================== Action menu ====================
function openMenuAt(element) {
    const menu = document.getElementById("actionMenu");
    menu.style.left = (element.getBoundingClientRect().left + 10) + "px";
    menu.style.top = (element.getBoundingClientRect().bottom + 10) + "px";
    menu.classList.remove("hidden");
}
function closeMenu() { document.getElementById("actionMenu").classList.add("hidden"); }

// ==================== Preview ====================
function previewSelected() {
    if (!selectedFile) return alert("Pilih file dulu");
    closeMenu();
    const modal = document.getElementById("previewModal");
    const body = document.getElementById("previewBody");
    body.innerHTML = "";

    // determine type by extension
    const ext = selectedFile.split(".").pop().toLowerCase();
    const url = `/filemanager/raw?path=${encodeURIComponent(selectedFile)}`;

    if (["png","jpg","jpeg","gif","webp"].includes(ext)) {
        const img = document.createElement("img");
        img.style.maxWidth = "100%";
        img.src = url;
        body.appendChild(img);
    } else if (["mp4","webm","mkv","avi","mov"].includes(ext)) {
        const v = document.createElement("video");
        v.controls = true; v.src = url; v.style.width = "100%";
        body.appendChild(v);
    } else if (["mp3","wav","ogg"].includes(ext)) {
        const a = document.createElement("audio");
        a.controls = true; a.src = url; body.appendChild(a);
    } else if (["txt","log","md","json","py","js","html","css"].includes(ext)) {
        fetch(url).then(r => r.text()).then(t => {
            const pre = document.createElement("pre");
            pre.style.maxHeight = "70vh";
            pre.style.overflow = "auto";
            pre.textContent = t;
            body.appendChild(pre);
        });
    } else {
        body.innerHTML = "<p>Preview tidak tersedia untuk jenis file ini.</p>";
    }

    modal.classList.remove("hidden");
}
function closePreview() { document.getElementById("previewModal").classList.add("hidden"); }

// ==================== Download ====================
function downloadSelected() {
    if (!selectedFile) return alert("Pilih file dulu");
    closeMenu();
    window.location.href = `/filemanager/download?path=${encodeURIComponent(selectedFile)}`;
}

// ==================== Delete ====================
function deleteSelected() {
    if (!selectedFile) return alert("Pilih file dulu");
    if (!confirm("Yakin ingin menghapus?")) return;
    const form = new FormData(); form.append("path", selectedFile);
    fetch("/filemanager/delete", { method: "POST", body: form })
        .then(r => r.json()).then(j => {
            if (j.error) alert("Error: " + j.error); else alert("Terhapus");
            loadFiles(currentPath);
        });
    closeMenu();
}

// ==================== Rename ====================
function renamePrompt() {
    if (!selectedFile) return alert("Pilih file dulu");
    const newName = prompt("Nama baru:", selectedFile.split("/").pop());
    if (!newName) return;
    const folder = selectedFile.split("/").slice(0, -1).join("/");
    const newPath = folder + "/" + newName;
    const form = new FormData(); form.append("old", selectedFile); form.append("new", newPath);
    fetch("/filemanager/rename", { method: "POST", body: form })
        .then(r => r.json()).then(j => {
            if (j.error) alert("Error: " + j.error); else alert("Rename sukses");
            loadFiles(currentPath);
        });
    closeMenu();
}

// ==================== Move ====================
function movePrompt() {
    if (!selectedFile) return alert("Pilih file dulu");
    const dest = prompt("Pindah ke folder (path penuh):", currentPath);
    if (!dest) return;
    const newPath = dest.replace(/\/$/, "") + "/" + selectedFile.split("/").pop();
    moveItem(selectedFile, newPath);
    closeMenu();
}

function moveItem(oldPath, newPath) {
    const form = new FormData(); form.append("old", oldPath); form.append("new", newPath);
    fetch("/filemanager/move", { method: "POST", body: form })
        .then(r => r.json()).then(j => {
            if (j.error) alert("Error: " + j.error); else alert("Dipindah");
            loadFiles(currentPath);
        });
}

// ==================== Upload ====================
function handleFilesSelected(e) {
    const files = Array.from(e.target.files || []);
    uploadFiles(files);
}

function uploadFiles(files) {
    if (!files || files.length === 0) return;
    files.forEach(file => {
        const form = new FormData();
        form.append("file", file);
        form.append("target", currentPath);
        fetch("/filemanager/upload", { method: "POST", body: form })
            .then(r => r.json()).then(j => {
                if (j.error) alert("Upload error: " + j.error);
                loadFiles(currentPath);
            }).catch(err => {
                alert("Upload gagal");
                console.error(err);
            });
    });
}

// ==================== Zip/Unzip ====================
function zipCurrent() {
    const name = prompt("Nama zip (tanpa .zip):", "archive");
    if (!name) return;
    const form = new FormData(); form.append("path", currentPath); form.append("name", name);
    fetch("/filemanager/zip", { method: "POST", body: form })
        .then(r => r.json()).then(j => {
            if (j.error) alert("Error: " + j.error); else alert("Zip dibuat: " + j.zip);
            loadFiles(currentPath);
        });
}

function unzipPrompt() {
    const zipfile = prompt("Path file zip (penuh) atau gunakan file di folder (masukkan nama.zip):");
    if (!zipfile) return;
    // if no slash => interpret as currentPath/name
    let full = zipfile.includes("/") ? zipfile : currentPath.replace(/\/$/, "") + "/" + zipfile;
    const form = new FormData(); form.append("path", full);
    fetch("/filemanager/unzip", { method: "POST", body: form })
        .then(r => r.json()).then(j => {
            if (j.error) alert("Error: " + j.error); else alert("Unzip ke: " + j.dest);
            loadFiles(currentPath);
        });
}