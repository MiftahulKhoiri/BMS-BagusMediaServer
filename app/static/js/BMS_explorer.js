let currentPath = "/storage/emulated/0/BMS/";
let selectedFile = null;

document.addEventListener("DOMContentLoaded", () => {
    loadFiles(currentPath);
    document.getElementById("refreshBtn").onclick = () => loadFiles(currentPath);
});


// ======================================================
// 📂 Load file dari backend
// ======================================================
function loadFiles(path) {
    document.getElementById("fileArea").innerHTML = "<p class='loading'>Loading...</p>";

    fetch(`/filemanager/list?path=${encodeURIComponent(path)}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            currentPath = data.current;
            renderBreadcrumb(currentPath);
            renderFiles(data.items);
        });
}


// ======================================================
// 📌 Render breadcrumb
// ======================================================
function renderBreadcrumb(path) {
    document.getElementById("breadcrumb").innerText = path;
}


// ======================================================
// 🖼️ Render daftar file untuk touchscreen
// ======================================================
function renderFiles(items) {
    const area = document.getElementById("fileArea");
    area.innerHTML = "";

    items.forEach(item => {

        let div = document.createElement("div");
        div.classList.add("file-item");

        div.innerHTML = `
            <div class='file-icon'>${item.is_dir ? "📁" : "📄"}</div>
            <div class='file-name'>${item.name}</div>
        `;

        // Tap
        div.onclick = () => {
            if (item.is_dir) {
                loadFiles(item.path);
            } else {
                selectedFile = item.path;
                openMenu();
            }
        };

        // Long-press
        let pressTimer;
        div.onmousedown = () => {
            pressTimer = setTimeout(() => {
                selectedFile = item.path;
                openMenu();
            }, 550);
        };

        div.onmouseup = () => clearTimeout(pressTimer);
        div.onmouseleave = () => clearTimeout(pressTimer);

        area.appendChild(div);
    });
}


// ======================================================
// 🔽 Floating Menu
// ======================================================
function openMenu() {
    document.getElementById("actionMenu").classList.remove("hidden");
}

function closeMenu() {
    document.getElementById("actionMenu").classList.add("hidden");
}


// ======================================================
// 📄 OPEN FILE
// ======================================================
function openFile() {
    window.location.href = `/filemanager/download?path=${encodeURIComponent(selectedFile)}`;
}


// ======================================================
// ✏ RENAME FILE
// ======================================================
function renameFile() {
    let newName = prompt("Masukkan nama baru:");
    if (!newName) return;

    fetch("/filemanager/rename", {
        method: "POST",
        body: new FormData()
            .append("old", selectedFile)
            .append("new", selectedFile.replace(/[^\/]+$/, newName))
    });

    alert("Berhasil!");
    closeMenu();
    loadFiles(currentPath);
}


// ======================================================
// 🗑 DELETE FILE
// ======================================================
function deleteFile() {
    if (!confirm("Yakin ingin menghapus?")) return;

    let form = new FormData();
    form.append("path", selectedFile);

    fetch("/filemanager/delete", { method: "POST", body: form });

    alert("Berhasil dihapus!");
    closeMenu();
    loadFiles(currentPath);
}