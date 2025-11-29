/* ==========================================================
   BMS MP3 PLAYER - FIXED VERSION
   Mode A: Player di atas + Playlist scrollable
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

    // UPDATE UI MODE (agar icon sesuai state terakhir)
    updateRepeatButton();
    updateShuffleButton();
}


/* ==========================================================
   HANDLE TRACK END (Auto Next / Shuffle / Repeat)
========================================================== */
function handleTrackEnd(){

    // =============================
    // 🔁 1) REPEAT ONE
    // =============================
    if(repeatMode === 1){
        changeTrack(currentTrackId);
        return;
    }

    let index = playlistData.findIndex(t => t.id === currentTrackId);

    // =============================
    // 🔀 SHUFFLE
    // =============================
    if(shuffleMode){
        let random = playlistData[Math.floor(Math.random() * playlistData.length)];
        changeTrack(random.id);
        return;
    }

    // =============================
    // 🔁 2) REPEAT ALL
    // =============================
    if(repeatMode === 2){
        if(index === playlistData.length - 1){
            // Jika di akhir playlist → kembali ke awal
            let first = playlistData[0];
            changeTrack(first.id);
            return;
        } else {
            // lanjut ke lagu berikutnya
            let next = playlistData[index + 1];
            changeTrack(next.id);
            return;
        }
    }

    // =============================
    // ▶ MODE NORMAL (TIDAK REPEAT)
    // =============================
    if(index < playlistData.length - 1){
        let next = playlistData[index + 1];
        changeTrack(next.id);
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
   MODE: SHUFFLE + ICON
========================================================== */
function toggleShuffle(){
    shuffleMode = !shuffleMode;

    updateShuffleButton();

    alert(shuffleMode ? "Shuffle ON" : "Shuffle OFF");
}

function updateShuffleButton(){
    let btn = document.getElementById("shuffleBtn");
    if(!btn) return;

    if(shuffleMode){
        btn.classList.add("active");
        btn.innerHTML = "🔀✨ Shuffle ON";
    } else {
        btn.classList.remove("active");
        btn.innerHTML = "🔀 Shuffle";
    }
}


/* ==========================================================
   MODE: REPEAT (OFF / ONE / ALL)
========================================================== */
function toggleRepeat(){
    repeatMode++;

    if(repeatMode > 2){
        repeatMode = 0;
    }

    updateRepeatButton();
}

function updateRepeatButton(){
    let btn = document.getElementById("repeatBtn");
    if(!btn) return;

    btn.classList.remove("active");

    if(repeatMode === 0){
        btn.innerHTML = "🔁 Repeat OFF";
    }
    else if(repeatMode === 1){
        btn.innerHTML = "🔂 Repeat ONE";
        btn.classList.add("active");
    }
    else if(repeatMode === 2){
        btn.innerHTML = "🔁∞ Repeat ALL";
        btn.classList.add("active");
    }
}

/* ==========================================================
   VOLUME CONTROL
========================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const audio = document.getElementById("audioPlayer");
    const slider = document.getElementById("volumeSlider");
    const icon = document.getElementById("volumeIcon");

    if(!audio || !slider) return;

    // Volume default
    audio.volume = 1.0;

    slider.addEventListener("input", () => {
        let v = slider.value / 100;
        audio.volume = v;

        if(v === 0){
            icon.innerHTML = "🔇";
        }
        else if(v < 0.4){
            icon.innerHTML = "🔈";
        }
        else if(v < 0.7){
            icon.innerHTML = "🔉";
        }
        else{
            icon.innerHTML = "🔊";
        }
    });
});