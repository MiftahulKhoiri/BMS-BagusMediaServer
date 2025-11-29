/* ==========================================================
   BMS MP3 PLAYER - CLEAN & FIXED VERSION
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];   
let shuffleMode = false;
let repeatMode = 0;

/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}

/* ----------------------------------------------------------
   HOME
---------------------------------------------------------- */
function goHome(){
    fetch("/auth/role")
    .then(r => r.json())
    .then(d => {
        window.location.href = (d.role === "admin" || d.role === "root")
            ? "/admin/home"
            : "/user/home";
    })
    .catch(() => window.location.href = "/user/home");
}

/* ----------------------------------------------------------
   KEMBALI
---------------------------------------------------------- */
function goBack(){
    if(currentFolderId){
        window.location.href = `/mp3/?folder=${currentFolderId}`;
    } else {
        window.location.href = "/mp3/";
    }
}

/* ----------------------------------------------------------
   INIT PLAYER
---------------------------------------------------------- */
async function initPlayer(mp3Id, folderId){
    currentTrackId = parseInt(mp3Id);
    currentFolderId = folderId;

    let trackInfo = await api(`/mp3/info/${mp3Id}`);
    document.getElementById("trackTitle").innerHTML = trackInfo.filename;

    let audio = document.getElementById("audioPlayer");
    audio.src = `/mp3/play/${mp3Id}`;
    audio.play().catch(()=>{});

    // Load playlist folder
    playlistData = await api(`/mp3/folder/${folderId}/tracks`);
    loadPlaylist();

    // Auto next handler
    audio.onended = handleTrackEnd;

    // Update buttons state
    updateRepeatButton();
    updateShuffleButton();
}

/* ----------------------------------------------------------
   HANDLE AUTO NEXT / SHUFFLE / REPEAT
---------------------------------------------------------- */
function handleTrackEnd(){

    if(repeatMode === 1){
        changeTrack(currentTrackId);
        return;
    }

    let index = playlistData.findIndex(t => t.id === currentTrackId);

    if(shuffleMode){
        let r = playlistData[Math.floor(Math.random() * playlistData.length)];
        changeTrack(r.id);
        return;
    }

    if(repeatMode === 2){
        if(index === playlistData.length - 1){
            changeTrack(playlistData[0].id);
        } else {
            changeTrack(playlistData[index + 1].id);
        }
        return;
    }

    if(index < playlistData.length - 1){
        changeTrack(playlistData[index + 1].id);
    }
}

/* ----------------------------------------------------------
   LOAD PLAYLIST UI
---------------------------------------------------------- */
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

/* ----------------------------------------------------------
   GANTI TRACK
---------------------------------------------------------- */
function changeTrack(id){
    window.location.href = `/mp3/watch/${id}?folder=${currentFolderId}`;
}

/* ----------------------------------------------------------
   NEXT / PREV
---------------------------------------------------------- */
function nextTrack(){
    let i = playlistData.findIndex(t => t.id === currentTrackId);
    if(i < playlistData.length - 1){
        changeTrack(playlistData[i + 1].id);
    }
}

function prevTrack(){
    let i = playlistData.findIndex(t => t.id === currentTrackId);
    if(i > 0){
        changeTrack(playlistData[i - 1].id);
    }
}

/* ----------------------------------------------------------
   SHUFFLE
---------------------------------------------------------- */
function toggleShuffle(){
    shuffleMode = !shuffleMode;
    updateShuffleButton();
}

function updateShuffleButton(){
    let btn = document.getElementById("shuffleBtn");
    if(!btn) return;

    if(shuffleMode){
        btn.classList.add("active");
        btn.innerHTML = "🔀";
    } else {
        btn.classList.remove("active");
        btn.innerHTML = "🔀";
    }
}

/* ----------------------------------------------------------
   REPEAT (0 = OFF, 1 = ONE, 2 = ALL)
---------------------------------------------------------- */
function toggleRepeat(){
    repeatMode++;
    if(repeatMode > 2) repeatMode = 0;
    updateRepeatButton();
}

function updateRepeatButton(){
    let btn = document.getElementById("repeatBtn");
    if(!btn) return;

    btn.classList.remove("active");

    if(repeatMode === 0){
        btn.innerHTML = "🔁";
    }
    else if(repeatMode === 1){
        btn.innerHTML = "🔂";
        btn.classList.add("active");
    }
    else if(repeatMode === 2){
        btn.innerHTML = "🔁";
        btn.classList.add("active");
    }
}

/* ----------------------------------------------------------
   RELOAD (ulang lagu)
---------------------------------------------------------- */
function reloadTrack(){
    changeTrack(currentTrackId);
}

/* ----------------------------------------------------------
   VOLUME SYSTEM
---------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    const audio = document.getElementById("audioPlayer");
    const slider = document.getElementById("volumeSlider");
    const icon = document.getElementById("volumeIcon");

    if(!audio || !slider) return;

    slider.addEventListener("input", () => {
        let v = slider.value / 100;
        audio.volume = v;

        icon.innerHTML =
            v === 0 ? "🔇" :
            v < 0.4 ? "🔈" :
            v < 0.7 ? "🔉" :
            "🔊";
    });
});