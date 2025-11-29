/* ==========================================================
   BMS VIDEO LIBRARY (JELLYFIN MODE)
   Author: Bagus + AI Support
   Deskripsi:
   - Menampilkan daftar folder
   - Menampilkan daftar video dalam folder
   - Memutar video + playlist
   - Navigasi kembali (Back)
   ========================================================== */


/* ----------------------------------------------------------
   STATE GLOBAL
---------------------------------------------------------- */
let currentFolderId = null;      // Folder yang sedang dibuka
let currentFolderName = null;
let currentVideoList = [];       // List video dari folder aktif



/* ----------------------------------------------------------
   HELPER: Ambil JSON dari API
---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}



/* ==========================================================
   1) SCAN LIBRARY
========================================================== */
async function scanDB(){
    document.getElementById('status').innerHTML = "🔄 Scan berjalan...";

    let res = await fetch("/video/scan-db", { method: "POST" });
    let data = await res.json();

    document.getElementById('status').innerHTML = data.message;

    showFolders();
}



/* ==========================================================
   2) TAMPILKAN DAFTAR FOLDER
========================================================== */
async function showFolders(){
    document.getElementById('status').innerHTML = "Memuat folder...";

    let data = await api("/video/folders");

    // RESET STATE
    currentFolderId = null;
    currentFolderName = null;
    currentVideoList = [];

    // Sembunyikan tombol back
    document.getElementById("backButton").style.display = "none";

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if(data.length === 0){
        lib.innerHTML = "<div>Tidak ada folder berisi video.</div>";
        return;
    }

    data.forEach(f => {
        let card = document.createElement("div");
        card.className = "card";
        card.onclick = ()=> loadVideos(f.id, f.folder_name);

        card.innerHTML = `
            <div class="thumb-folder">📁</div>
            <div class="title">${f.folder_name}</div>
            <div class="sub">${f.total_video} video</div>
        `;

        lib.appendChild(card);
    });

    document.getElementById('status').innerHTML = "";
}



/* ==========================================================
   3) TAMPILKAN VIDEO DI DALAM FOLDER
========================================================== */
async function loadVideos(folder_id, folder_name){

    // Simpan state folder
    currentFolderId = folder_id;
    currentFolderName = folder_name;

    // Tampilkan tombol back
    document.getElementById("backButton").style.display = "block";

    document.getElementById('status').innerHTML = "Memuat video...";

    let data = await api(`/video/folder/${folder_id}/videos`);
    currentVideoList = data;

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if(data.length === 0){
        lib.innerHTML = "<div>Folder kosong.</div>";
        return;
    }

    data.forEach(v => {
        let card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <img src="/video/thumbnail/${v.id}" class="thumb-video">
            <div class="title">${v.filename}</div>
            <div class="sub">${(v.size/1024/1024).toFixed(1)} MB</div>
        `;

        card.onclick = ()=> playVideo(v.id, v.filename);

        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML = `📁 Folder: ${folder_name}`;
}



/* ==========================================================
   4) PLAYER VIDEO + PLAYLIST
========================================================== */
function playVideo(id, title){
    let modal = document.getElementById("playerModal");
    let player = document.getElementById("playerVideo");

    document.getElementById("playerTitle").innerHTML = title;

    player.src = `/video/play/${id}`;
    modal.style.display = "flex";

    loadPlaylist(id);
}



/* ==========================================================
   5) PLAYLIST DALAM FOLDER YANG SAMA
========================================================== */
function loadPlaylist(currentId){
    let box = document.getElementById("playlist");
    box.innerHTML = "";

    currentVideoList.forEach(v=>{
        let item = document.createElement("div");
        item.className = "playlist-item";

        // Tandai yang sedang diputar
        item.innerHTML = (v.id === currentId)
            ? `▶ <b>${v.filename}</b>`
            : v.filename;

        item.onclick = ()=> playVideo(v.id, v.filename);

        box.appendChild(item);
    });
}



/* ==========================================================
   6) TUTUP PLAYER → KEMBALI KE LIST VIDEO
========================================================== */
function closePlayer(){
    let modal = document.getElementById("playerModal");
    let player = document.getElementById("playerVideo");

    player.pause();
    player.src = "";
    modal.style.display = "none";

    // Kembali ke folder saat player ditutup
    if(currentFolderId){
        loadVideos(currentFolderId, currentFolderName);
    } else {
        showFolders();
    }
}



/* ==========================================================
   7) TOMBOL BACK (KEMBALI)
   - Jika dalam folder → kembali ke daftar folder
   - Jika tidak dalam folder → fallback showFolders()
========================================================== */
function goBack(){
    if(currentFolderId){
        // sedang melihat list video → kembali ke folder list
        currentFolderId = null;
        currentFolderName = null;
        currentVideoList = [];

        showFolders();
    } else {
        showFolders();
    }
}