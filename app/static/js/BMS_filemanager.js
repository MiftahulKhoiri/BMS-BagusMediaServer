// ============================================
//  BMS FILE MANAGER - CLIENT SIDE
// ============================================

let currentPath = "/storage/emulated/0/BMS/";

document.addEventListener("DOMContentLoaded", () => {
    loadFolder(currentPath);
});


// ==========================================
// 🔄 Load Folder
// ==========================================
function loadFolder(path) {
    fetch(`/filemanager/list?path=` + encodeURIComponent(path))
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            currentPath = data.current;
            document.getElementById("fm-current-path").innerText = currentPath;

            let box = document.getElementById("fm-list");
            box.innerHTML = "";

            data.items.forEach(item => {
                let div = document.createElement("div");
                div.className = "fm-item";

                let icon = item.is_dir ? "📁" : "📄";

                div.innerHTML = `
                    <span onclick="itemClick('${item.path}', ${item.is_dir})">${icon} ${item.name}</span>
                    <div class="actions">
                        <button onclick="downloadItem('${item.path}')">⬇</button>
                        <button onclick="renameItem('${item.path}')">✏</button>
                        <button onclick="deleteItem('${item.path}')">🗑</button>
                    </div>
                `;

                box.appendChild(div);
            });
        })
        .catch(() => {
            alert("Gagal memuat folder!");
        });
}


// ==========================================
// 📂 Klik Item
// ==========================================
function itemClick(path, isDir) {
    if (isDir) {
        loadFolder(path);
    } else {
        alert("Gunakan tombol download untuk mengambil file!");
    }
}


// ==========================================
// 🔙 Back Folder
// ==========================================
function goBack() {
    let parent = currentPath.split("/").slice(0, -1).join("/");
    if (!parent) return;
    loadFolder(parent);
}


// ==========================================
// 🗑 Delete
// ==========================================
function deleteItem(path) {
    if (!confirm("Hapus item ini?")) return;

    let form = new FormData();
    form.append("path", path);

    fetch("/filemanager/delete", { method: "POST", body: form })
        .then(r => r.text())
        .then(msg => {
            alert(msg);
            loadFolder(currentPath);
        });
}


// ==========================================
// ✏ Rename
// ==========================================
function renameItem(oldPath) {
    let newName = prompt("Nama baru:");
    if (!newName) return;

    let folder = oldPath.split("/").slice(0, -1).join("/");
    let newPath = folder + "/" + newName;

    let form = new FormData();
    form.append("old", oldPath);
    form.append("new", newPath);

    fetch("/filemanager/rename", { method: "POST", body: form })
        .then(r => r.text())
        .then(msg => {
            alert(msg);
            loadFolder(currentPath);
        });
}


// ==========================================
// 📁 Create Folder
// ==========================================
function createFolder() {
    let name = prompt("Nama folder baru:");
    if (!name) return;

    let full = currentPath + "/" + name;

    let form = new FormData();
    form.append("path", full);

    fetch("/filemanager/mkdir", { method: "POST", body: form })
        .then(r => r.text())
        .then(msg => {
            alert(msg);
            loadFolder(currentPath);
        });
}


// ==========================================
// ⬇ Download File
// ==========================================
function downloadItem(path) {
    window.location.href = "/filemanager/download?path=" + encodeURIComponent(path);
}


// ==========================================
// 🔄 Refresh
// ==========================================
function refreshFolder() {
    loadFolder(currentPath);
}