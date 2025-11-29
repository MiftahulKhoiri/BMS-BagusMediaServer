/* ==========================================================
   BMS MP3 PLAYER - FIXED VERSION
   Mode A: Player di atas + Playlist scrollable
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];   
let shuffleMode = false;
let repeatMode = false;

/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}


/* ==========================================================
   HOME BUTTON
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
   BACK BUTTON
========================================================== */
function goBack(){
    if(currentFolderId){
        window.location.href = `/mp3/?folder=${currentFolderId}`;
    } else {
        window.location.href = "/mp3/";
    }
}


/* ==========================================================
   INIT PLAYER
========================================================== */
async function initPlayer(mp3Id, folderId){
    currentTrackId = parseInt(mp3Id);
    currentFolderId = folderId;

    // INFO TRACK
    let trackInfo = await api(`/mp3/info/${mp3Id}`);
    document.getElementById("trackTitle").innerHTML = trackInfo.filename;

    let audio = document.getElementById("audioPlayer");

    // SET SOURCE
    audio.src = `/mp3/play/${mp3Id}`;
    audio.play().catch(()=>{});

    // LOAD PLAYLIST
    playlistData = await api(`/mp3/folder/${folderId}/tracks`);

    // TAMPILKAN PLAYLIST
    loadPlaylist();

    // REGISTER EVENT "ended" ulang (agar playlistData sudah terisi)
    audio.onended = handleTrackEnd;
}


/* ==========================================================
   HANDLE TRACK END (Auto Next / Shuffle / Repeat)
========================================================== */
function handleTrackEnd(){

    // Repeat mode
    if(repeatMode){
        changeTrack(currentTrackId);
        return;
    }

    // Shuffle mode
    if(shuffleMode){
        let random = playlistData[Math.floor(Math.random() * playlistData.length)];
        changeTrack(random.id);
        return;
    }

    // Mode normal → next track
    let index = playlistData.findIndex(t => t.id === currentTrackId);
    if(index >= 0 && index < playlistData.length - 1){
        let next = playlistData[index + 1];
        changeTrack(next.id);
        return;
    }
}


/* ==========================================================
   MUAT ULANG PLAYLIST
========================================================== */
function loadPlaylist(){
    let box = document.getElementById("playlist");
    box.innerHTML = "";

    playlistData.forEach(mp3 => {
        let item = document.createElement("div");
        item.className = "playlist-item";

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
   GANTI TRACK (memuat halaman /mp3/watch)
========================================================== */
function changeTrack(id){
    window.location.href = `/mp3/watch/${id}?folder=${currentFolderId}`;
}


/* ==========================================================
   NEXT / PREV BUTTON
========================================================== */
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


/* ==========================================================
   MODE: SHUFFLE & REPEAT
========================================================== */
function toggleShuffle(){
    shuffleMode = !shuffleMode;
    alert(shuffleMode ? "Shuffle ON" : "Shuffle OFF");
}

function toggleRepeat(){
    repeatMode = !repeatMode;
    alert(repeatMode ? "Repeat ON" : "Repeat OFF");
}