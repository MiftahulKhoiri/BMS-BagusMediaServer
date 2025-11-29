/* ==========================================================
   BMS VIDEO LIBRARY (HALAMAN UTAMA)
   Fitur:
   - Folder list
   - Video list per folder
   - Navigation state
   - Open external player page
========================================================== */


let currentFolderId = null;
let currentFolderName = null;


/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}


/* ==========================================================
   SCAN DB
========================================================== */
async function scanDB(){
    document.getElementById("status").innerHTML = "🔍 Scan berjalan...";
    let res = await fetch("/video/scan-db", { method: "POST" });
    let data = await res.json();

    document.getElementById("status").innerHTML = data.message;
    showFolders();
}


/* ==========================================================
   TAMPILKAN FOLDER
========================================================== */
async function showFolders(){
    document.getElementById("status").innerHTML = "📁 Memuat folder...";

    currentFolderId = null;
    currentFolderName = null;

    document.getElementById("backButton").style.display = "none";

    let data = await api("/video/folders");

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if (!data || data.length === 0) {
        lib.innerHTML = "<div>Tidak ada folder video.</div>";
        return;
    }

    data.forEach(f => {
        let card = document.createElement("div");
        card.className = "card";
        card.onclick = () => loadVideos(f.id, f.folder_name);

        card.innerHTML = `
            <div class="thumb-folder">📁</div>
            <div class="title">${f.folder_name}</div>
            <div class="sub">${f.total_video} video</div>
        `;

        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML = "";
}


/* ==========================================================
   TAMPILKAN VIDEO DALAM FOLDER
========================================================== */
async function loadVideos(folder_id, folder_name){
    currentFolderId = folder_id;
    currentFolderName = folder_name;

    document.getElementById("backButton").style.display = "block";
    document.getElementById("status").innerHTML = "🎬 Memuat video...";

    let data = await api(`/video/folder/${folder_id}/videos`);

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if (!data || data.length === 0){
        lib.innerHTML = "<div>Folder kosong.</div>";
        return;
    }

    data.forEach(v=>{
        let card = document.createElement("div");
        card.className = "card";
        card.onclick = () => openVideoPlayer(v.id);

        card.innerHTML = `
            <img src="/video/thumbnail/${v.id}" class="thumb-video">
            <div class="title">${v.filename}</div>
            <div class="sub">${(v.size/1024/1024).toFixed(1)} MB</div>
        `;

        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML = `📁 Folder: ${folder_name}`;
}


/* ==========================================================
   BUKA HALAMAN PLAYER (watch/<id>)
========================================================== */
function openVideoPlayer(video_id){
    window.location.href = `/video/watch/${video_id}`;
}


/* ==========================================================
   TOMBOL KEMBALI
========================================================== */
function goBack(){
    if(currentFolderId){
        showFolders();
    } else {
        showFolders();
    }
}