/* ==========================================================
   BMS MP3 PLAYER
   Mode A: Player di atas + Playlist scrollable
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];   // Semua MP3 dalam folder

/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}


/* ==========================================================
   HOME BUTTON
   Auto detect role → arahkan ke home yg benar
========================================================== */
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


/* ==========================================================
   KEMBALI KE FOLDER MP3
========================================================== */
function goBack(){
    if(currentFolderId){
        window.location.href = `/mp3?folder=${currentFolderId}`;
    } else {
        window.location.href = "/mp3";
    }
}


/* ==========================================================
   INIT PLAYER
========================================================== */
async function initPlayer(mp3Id, folderId){
    currentTrackId = parseInt(mp3Id);
    currentFolderId = folderId;

    // 1. Ambil info track yang sedang diputar
    let trackInfo = await api(`/mp3/info/${mp3Id}`);
    document.getElementById("trackTitle").innerHTML = trackInfo.filename;

    let audio = document.getElementById("audioPlayer");
    audio.src = `/mp3/play/${mp3Id}`;
    audio.play().catch(()=>{});

    // 2. Ambil playlist folder
    playlistData = await api(`/mp3/folder/${folderId}/tracks`);

    // 3. Render playlist
    loadPlaylist();
}


/* ==========================================================
   RENDER PLAYLIST
========================================================== */
function loadPlaylist(){
    let box = document.getElementById("playlist");
    box.innerHTML = "";

    playlistData.forEach(mp3 => {
        let item = document.createElement("div");
        item.className = "playlist-item";

        // Tandai track yg sedang diputar
        if(mp3.id === currentTrackId){
            item.classList.add("active");
            item.innerHTML = `▶ ${mp3.filename}`;
        } else {
            item.innerHTML = mp3.filename;
        }

        item.onclick = ()=> changeTrack(mp3.id);

        box.appendChild(item);
    });
}


/* ==========================================================
   GANTI LAGU (Next dari playlist)
========================================================== */
function changeTrack(id){
    window.location.href = `/mp3/watch/${id}?folder=${currentFolderId}`;
}


/* ==========================================================
   AUTO NEXT TRACK
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
    let audio = document.getElementById("audioPlayer");

    if(!audio) return;

    audio.addEventListener("ended", ()=>{
        let index = playlistData.findIndex(t => t.id === currentTrackId);
        if(index >= 0 && index < playlistData.length - 1){
            let next = playlistData[index + 1];
            changeTrack(next.id);
        }
    });
});

function nextTrack(){
    let index = playlistData.findIndex(t => t.id === currentTrackId);
    if(index < playlistData.length - 1){
        let next = playlistData[index + 1];
        changeTrack(next.id);
    }
}

function prevTrack(){
    let index = playlistData.findIndex(t => t.id === currentTrackId);
    if(index > 0){
        let prev = playlistData[index - 1];
        changeTrack(prev.id);
    }
}