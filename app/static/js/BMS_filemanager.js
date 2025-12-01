let currentPath = "";

window.onload = () => {
    loadTree();
    loadList("/");
};

function api(url) {
    return fetch(url).then(r => r.json());
}

// =============================
//  LOAD FOLDER TREE (Sidebar)
// =============================
function loadTree() {
    api("/filemanager/list").then(res => {
        let html = "";
        res.items.forEach(i => {
            if (i.is_dir) html += `<li onclick="loadList('${i.path}')">📁 ${i.name}</li>`;
        });
        document.getElementById("folder-tree").innerHTML = html;
    });
}

// =============================
//  LOAD FILE LIST
// =============================
function loadList(path) {
    api("/filemanager/list?path=" + path).then(res => {
        currentPath = res.current;
        document.getElementById("fm-path").innerText = res.current;

        let html = "";
        res.items.forEach(f => {
            html += `
            <div class="fm-item" onclick="openItem('${f.path}', ${f.is_dir})">
                <div class="icon">${f.is_dir ? "📁" : "📄"}</div>
                <div>${f.name}</div>
            </div>`;
        });

        document.getElementById("fm-list").innerHTML = html;
    });
}

function refreshList() {
    loadList(currentPath);
}

function goUp() {
    let up = currentPath.split("/").slice(0, -1).join("/");
    loadList(up === "" ? "/" : up);
}

// =============================
// OPEN FILE OR FOLDER
// =============================
function openItem(path, isDir) {
    if (isDir) return loadList(path);
    preview(path);
}

// =============================
// PREVIEW FILE
// =============================
function preview(path) {
    fetch(`/filemanager/edit?path=${path}`)
        .then(r => r.json())
        .then(res => {
            document.getElementById("preview-content").innerText = res.content;
            document.getElementById("fm-preview").classList.remove("hidden");
        });
}

function closePreview() {
    document.getElementById("fm-preview").classList.add("hidden");
}

// =============================
// UPLOAD FILE
// =============================
function openUpload() {
    document.getElementById("upload-input").click();
}

function uploadFiles() {
    let files = document.getElementById("upload-input").files;

    [...files].forEach(file => {
        let form = new FormData();
        form.append("file", file);
        form.append("target", currentPath);

        fetch("/filemanager/upload", {
            method: "POST",
            body: form
        }).then(() => refreshList());
    });
}

// =============================
// MAKING FOLDER
// =============================
function makeFolder() {
    let name = prompt("Nama Folder:");
    if (!name) return;

    let form = new FormData();
    form.append("path", currentPath + "/" + name);

    fetch("/filemanager/mkdir", { method: "POST", body: form })
        .then(() => refreshList());
}