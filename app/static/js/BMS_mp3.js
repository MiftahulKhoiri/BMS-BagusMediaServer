/* ==========================================================
   BMS MP3 LIBRARY – CLEAN MODE
   Browse Folder → List MP3 → Play
========================================================== */

let currentFolderId = null;
let currentFolderName = null;

/* ----------------------------------------------------------
   Helper API JSON
---------------------------------------------------------- */
async function api(url){
    const res = await fetch(url);
    if (!res.ok) throw new Error("API error");
    return await res.json();
}

/* ==========================================================
   HOME BUTTON
========================================================== */
function goHome(){
    fetch("/auth/role")
        .then(r => r.json())
        .then(d => {
            if (d.role === "admin" || d.role === "root") {
                location.href = "/admin/home";
            } else {
                location.href = "/user/home";
            }
        })
        .catch(() => location.href = "/user/home");
}

/* ==========================================================
   SCAN MP3
========================================================== */
async function scanMP3(){
    const status = document.getElementById("status");
    try {
        status.innerHTML = "🔍 Scan MP3 berjalan...";
        const res = await fetch("/mp3/scan-db", { method: "POST" });
        const data = await res.json();
        status.innerHTML = data.message || "✅ Scan selesai";
        showFolders();
    } catch (e){
        status.innerHTML = "❌ Scan gagal";
    }
}

/* ==========================================================
   TAMPILKAN FOLDER
========================================================== */
async function showFolders(){
    const lib = document.getElementById("library");
    const status = document.getElementById("status");
    const backBtn = document.getElementById("backButton");

    currentFolderId = null;
    currentFolderName = null;

    backBtn.style.display = "none";
    status.innerHTML = "📁 Memuat folder...";
    lib.innerHTML = "";

    try {
        const data = await api("/mp3/folders");

        if (!data || data.length === 0){
            lib.innerHTML = "<div>Tidak ada folder MP3.</div>";
            status.innerHTML = "";
            return;
        }

        data.forEach(f => {
            const card = document.createElement("div");
            card.className = "card";
            card.onclick = () => loadMp3Files(f.id, f.folder_name);

            card.innerHTML = `
                <div class="thumb-folder">📁</div>
                <div class="title">${f.folder_name}</div>
                <div class="sub">${f.total_mp3} file</div>
            `;

            lib.appendChild(card);
        });

        status.innerHTML = "";
    } catch (e){
        status.innerHTML = "❌ Gagal memuat folder";
    }
}

/* ==========================================================
   TAMPILKAN FILE MP3
========================================================== */
async function loadMp3Files(folderId, folderName){
    const lib = document.getElementById("library");
    const status = document.getElementById("status");
    const backBtn = document.getElementById("backButton");

    currentFolderId = folderId;
    currentFolderName = folderName;

    backBtn.style.display = "block";
    status.innerHTML = "🎵 Memuat MP3...";
    lib.innerHTML = "";

    try {
        const data = await api(`/mp3/folder/${folderId}/tracks`);

        if (!data || data.length === 0){
            lib.innerHTML = "<div>Folder kosong.</div>";
            status.innerHTML = `📁 Folder: ${folderName}`;
            return;
        }

        data.forEach(mp3 => {
            const card = document.createElement("div");
            card.className = "card";
            card.onclick = () => openMp3Player(mp3.id);

            card.innerHTML = `
                <div class="thumb-mp3">🎵</div>
                <div class="title">${mp3.filename}</div>
                <div class="sub">${(mp3.size / 1024 / 1024).toFixed(1)} MB</div>
            `;

            lib.appendChild(card);
        });

        status.innerHTML = `📁 Folder: ${folderName}`;
    } catch (e){
        status.innerHTML = "❌ Gagal memuat MP3";
    }
}

/* ==========================================================
   BUKA MP3 PLAYER
========================================================== */
function openMp3Player(mp3Id){
    location.href = `/mp3/watch/${mp3Id}?folder=${currentFolderId}`;
}

/* ==========================================================
   BACK BUTTON
========================================================== */
function goBack(){
    showFolders();
}

/* ==========================================================
   INIT PAGE
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
    showFolders();
});