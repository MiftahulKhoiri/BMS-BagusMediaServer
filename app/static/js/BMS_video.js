/* ==========================================================
   BMS VIDEO LIBRARY (HALAMAN UTAMA)
   Fitur:
   - Folder list
   - Video list per folder
   - Thumbnail video
   - Navigation state
   - Open player page
========================================================== */

let currentFolderId = null;
let currentFolderName = null;


/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    const r = await fetch(path);
    return await r.json();
}


/* ==========================================================
   SCAN DB
========================================================== */
async function scanDB(){
    const status = document.getElementById("status");
    status.innerHTML = "🔍 Scan berjalan...";

    const res = await fetch("/video/scan-db", { method: "POST" });
    const data = await res.json();

    status.innerHTML = data.message;
    showFolders();
}


/* ==========================================================
   TAMPILKAN FOLDER
========================================================== */
async function showFolders(){
    const status = document.getElementById("status");
    const lib = document.getElementById("library");

    status.innerHTML = "📁 Memuat folder...";
    currentFolderId = null;
    currentFolderName = null;

    document.getElementById("backButton").style.display = "none";
    lib.innerHTML = "";

    const data = await api("/video/folders");

    if (!data || data.length === 0) {
        lib.innerHTML = "<div class='empty'>Tidak ada folder video.</div>";
        status.innerHTML = "";
        return;
    }

    data.forEach(f => {
        const card = document.createElement("div");
        card.className = "card folder-card";
        card.onclick = () => loadVideos(f.id, f.folder_name);

        card.innerHTML = `
            <div class="thumb-folder">📁</div>
            <div class="title">${f.folder_name}</div>
            <div class="sub">${f.total_video} video</div>
        `;

        lib.appendChild(card);
    });

    status.innerHTML = "";
}


/* ==========================================================
   TAMPILKAN VIDEO DALAM FOLDER
========================================================== */
async function loadVideos(folder_id, folder_name){
    currentFolderId = folder_id;
    currentFolderName = folder_name;

    const status = document.getElementById("status");
    const lib = document.getElementById("library");

    document.getElementById("backButton").style.display = "block";
    status.innerHTML = "🎬 Memuat video...";
    lib.innerHTML = "";

    const data = await api(`/video/folder/${folder_id}/videos`);

    if (!data || data.length === 0){
        lib.innerHTML = "<div class='empty'>Folder kosong.</div>";
        status.innerHTML = `📁 Folder: ${folder_name}`;
        return;
    }

    data.forEach(v => {
        const card = document.createElement("div");
        card.className = "card video-card";
        card.onclick = () => openVideoPlayer(v.id);

        card.innerHTML = `
            <img 
                src="/video/thumbnail/${v.thumbnail}"
                class="thumb-video"
                alt="thumbnail"
                onerror="this.src='/static/img/video_default.jpg'"
            >
            <div class="title">${v.filename}</div>
            <div class="sub">${(v.size / 1024 / 1024).toFixed(1)} MB</div>
        `;

        lib.appendChild(card);
    });

    status.innerHTML = `📁 Folder: ${folder_name}`;
}


/* ==========================================================
   BUKA HALAMAN PLAYER
========================================================== */
function openVideoPlayer(video_id){
    window.location.href = `/video/watch/${video_id}`;
}


/* ==========================================================
   TOMBOL KEMBALI
========================================================== */
function goBack(){
    showFolders();
}


/* ==========================================================
   AUTO LOAD SAAT HALAMAN DIBUKA
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
    showFolders();
});


/* ======================================================
   HOME BUTTON
====================================================== */
function goHome(){
    fetch("/auth/role")
        .then(r => r.json())
        .then(d => {
            if (d.role === "admin" || d.role === "root") {
                window.location.href = "/admin/home";
            } else {
                window.location.href = "/user/home";
            }
        })
        .catch(() => window.location.href = "/user/home");
}