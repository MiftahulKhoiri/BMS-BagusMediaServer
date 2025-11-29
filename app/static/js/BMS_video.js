/* ==========================================================
   BMS VIDEO LIBRARY (JELLYFIN MODE)
   Author: Bagus + AI Support
   Deskripsi:
   - Menampilkan daftar folder
   - Menampilkan daftar video dalam folder
   - Memutar video + playlist
   - Navigasi kembali (tidak kembali ke dashboard)
   ========================================================== */


/* ----------------------------------------------------------
   STATE GLOBAL
   ---------------------------------------------------------- */

// Folder yang sedang dibuka
let currentFolderId = null;
let currentFolderName = null;

// List video dalam folder yang sedang dibuka
let currentVideoList = [];


/* ----------------------------------------------------------
   HELPER: Ambil JSON dari API
   ---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}


/* ==========================================================
   1) SCAN LIBRARY
   - Meminta backend melakukan scan storage
   - Setelah scan selesai → tampilkan folder ulang
   ========================================================== */
async function scanDB(){
    document.getElementById('status').innerHTML = "🔄 Scan berjalan...";

    let res = await fetch("/video/scan-db", { method: "POST" });
    let data = await res.json();

    document.getElementById('status').innerHTML = data.message;

    // Setelah scan selesai → tampilkan daftar folder
    showFolders();
}


/* ==========================================================
   2) TAMPILKAN DAFTAR FOLDER
   - Mengambil data folder dari backend
   - Menampilkan folder dalam bentuk grid
   ---------------------------------------------------------- */
async function showFolders(){
    document.getElementById('status').innerHTML = "Memuat folder...";

    let data = await api("/video/folders");

    currentFolderId = null;
    currentFolderName = null;

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
   - Menampilkan semua video dalam folder
   - Menyimpan state folder + videoList
   ---------------------------------------------------------- */
async function loadVideos(folder_id, folder_name){
    // SIMPAN STATE FOLDER
    currentFolderId = folder_id;
    currentFolderName = folder_name;

    document.getElementById('status').innerHTML = "Memuat video...";

    // AMBIL VIDEO DARI BACKEND
    let data = await api(`/video/folder/${folder_id}/videos`);
    currentVideoList = data;   // SIMPAN UNTUK PLAYLIST

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if(data.length === 0){
        lib.innerHTML = "<div>Folder kosong.</div>";
        return;
    }

    // TAMPILKAN LIST VIDEO
    data.forEach(v => {
        let card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <img src="/video/thumbnail/${v.id}" class="thumb-video">
            <div class="title">${v.filename}</div>
            <div class="sub">${(v.size/1024/1024).toFixed(1)} MB</div>
        `;

        // Klik video → buka player
        card.onclick = ()=> playVideo(v.id, v.filename);

        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML = `📁 Folder: ${folder_name}`;
}


/* ==========================================================
   4) PUTAR VIDEO + TAMPILKAN PLAYLIST
   ---------------------------------------------------------- */
function playVideo(id, title){
    let modal = document.getElementById("playerModal");
    let player = document.getElementById("playerVideo");

    // SET JUDUL
    document.getElementById("playerTitle").innerHTML = title;

    // SET SOURCE VIDEO
    player.src = `/video/play/${id}`;

    // TAMPILKAN MODAL
    modal.style.display = "flex";

    // TAMPILKAN PLAYLIST
    loadPlaylist(id);
}


/* ==========================================================
   5) LOAD PLAYLIST (DAFTAR VIDEO DALAM FOLDER)
   ---------------------------------------------------------- */
function loadPlaylist(currentId){
    let box = document.getElementById("playlist");
    box.innerHTML = "";

    currentVideoList.forEach(v=>{
        let item = document.createElement("div");
        item.className = "playlist-item";

        // Tandai video yang sedang diputar
        item.innerHTML = (v.id === currentId)
            ? `▶ <b>${v.filename}</b>`
            : v.filename;

        item.onclick = ()=> playVideo(v.id, v.filename);

        box.appendChild(item);
    });
}


/* ==========================================================
   6) KEMBALI DARI PLAYER
   - Menutup modal player
   - Kembali ke list video folder yang tadi dibuka
   ========================================================== */
function closePlayer(){
    let modal = document.getElementById("playerModal");
    let player = document.getElementById("playerVideo");

    // STOP VIDEO
    player.pause();
    player.src = "";

    // TUTUP MODAL
    modal.style.display = "none";

    // KEMBALI KE LIST VIDEO FOLDER
    if(currentFolderId){
        loadVideos(currentFolderId, currentFolderName);
    } else {
        showFolders();
    }
}