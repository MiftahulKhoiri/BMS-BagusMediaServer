/* ==========================================================
   BMS VIDEO PLAYER JS
   Author: Bagus + AI Support
   Fitur:
   - Playlist informasi folder
   - Highlight video yang sedang diputar
   - Tombol kembali ke folder
   - Next / Previous
========================================================== */

// ==========================================================
//  GLOBAL STATE
// ==========================================================

let currentFolderId = null;   // Folder ID yang sedang diputar
let currentVideoId = null;    // Video ID yang sedang diputar
let playlistData = [];        // List video dalam folder


// ==========================================================
// 1) LOAD PLAYLIST DARI BACKEND
// ==========================================================
async function loadPlaylist(folder_id, video_id){
    currentFolderId = folder_id;
    currentVideoId = video_id;

    try {
        let r = await fetch(`/video/folder/${folder_id}/videos`);
        playlistData = await r.json();

        renderPlaylist();
    } catch (e){
        console.error("Gagal load playlist:", e);
    }
}


// ==========================================================
// 2) RENDER PLAYLIST KE HTML
// ==========================================================
function renderPlaylist(){
    const list = document.getElementById("playlist");
    list.innerHTML = "";

    playlistData.forEach(v => {
        let item = document.createElement("div");
        item.className = "playlist-item";

        // Jika ini video yang sedang diputar → highlight
        if(v.id === currentVideoId){
            item.classList.add("playing");
            item.innerHTML = `▶ ${v.filename}`;
        } else {
            item.innerHTML = v.filename;
        }

        // Klik item → play video lain
        item.onclick = () => {
            goToVideo(v.id);
        };

        list.appendChild(item);
    });
}


// ==========================================================
// 3) PINDAH KE VIDEO LAIN (NEXT / PREV / KLIK PLAYLIST)
// ==========================================================
function goToVideo(video_id){
    window.location.href = `/video/watch/${video_id}`;
}


// ==========================================================
// 4) NEXT VIDEO
// ==========================================================
function nextVideo(){
    let currentIndex = playlistData.findIndex(v => v.id === currentVideoId);

    if(currentIndex < playlistData.length - 1){
        let nextId = playlistData[currentIndex + 1].id;
        goToVideo(nextId);
    } else {
        alert("Sudah di video terakhir.");
    }
}


// ==========================================================
// 5) PREVIOUS VIDEO
// ==========================================================
function prevVideo(){
    let currentIndex = playlistData.findIndex(v => v.id === currentVideoId);

    if(currentIndex > 0){
        let prevId = playlistData[currentIndex - 1].id;
        goToVideo(prevId);
    } else {
        alert("Ini video pertama dalam folder.");
    }
}


// ==========================================================
// 6) TOMBOL KEMBALI KE FOLDER
// ==========================================================
function goBackToFolder(folder_id){
    // arahkan kembali ke halaman utama video dengan folder itu terbuka
    window.location.href = `/video/?folder=${folder_id}`;
}