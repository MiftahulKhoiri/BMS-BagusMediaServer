/* ==========================================================
   BMS VIDEO PLAYER JS (MODE A)
   Playlist di bawah video, scrollable
========================================================== */

let playlist = [];
let currentVideoId = null;
let currentFolderId = null;

/* ------------------------------
   LOAD PLAYER DAN PLAYLIST
------------------------------ */
async function initializePlayer(videoId, folderId){
    currentVideoId = parseInt(videoId);
    currentFolderId = parseInt(folderId);

    // SET VIDEO SOURCE
    document.getElementById("playerVideo").src =
        `/video/play/${currentVideoId}`;

    // Ambil playlist
    let r = await fetch(`/video/folder/${folderId}/videos`);
    playlist = await r.json();

    // Update judul
    let current = playlist.find(v => v.id === currentVideoId);
    document.getElementById("videoTitle").innerText =
        current ? current.filename : "Memuat...";

    // Tampilkan playlist
    renderPlaylist();
}

/* ------------------------------
   TAMPILKAN PLAYLIST
------------------------------ */
function renderPlaylist(){
    let box = document.getElementById("playlist");
    box.innerHTML = "";

    playlist.forEach(v => {
        let div = document.createElement("div");
        div.className = "playlist-item";

        if(v.id === currentVideoId){
            div.classList.add("playing");
            div.innerHTML = `▶ ${v.filename}`;
        } else {
            div.innerHTML = v.filename;
        }

        div.onclick = () => {
            window.location.href =
                `/video/watch/${v.id}?folder=${currentFolderId}`;
        };

        box.appendChild(div);
    });
}

/* ------------------------------
   TOMBOL KEMBALI
------------------------------ */
function goBackToFolder(){
    window.location.href = `/video/?folder=${currentFolderId}`;
}