/* ==========================================================
   BMS MP3 PLAYER - PRO VERSION (STABIL, RESPONSIF)
   - Player smooth
   - Control bar stabil
   - Repeat / Shuffle ikon update real-time
   - Prevent error saat auto next
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];
let shuffleMode = false;
let repeatMode = 0;   // 0=off, 1=one, 2=all
let isChanging = false;   // 🔥 prevent double next


/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    try {
        let r = await fetch(path);
        return await r.json();
    } catch (e){
        console.error("API Error:", e);
        return null;
    }
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
   BACK
---------------------------------------------------------- */
function goBack(){
    if (currentFolderId){
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
    if(!trackInfo){
        document.getElementById("trackTitle").innerHTML = "Error memuat lagu";
        return;
    }

fadeTitle(trackInfo.filename);

    let audio = document.getElementById("audioPlayer");
    audio.src = `/mp3/play/${mp3Id}`;

    // Mainkan lagu
    audio.play().catch(()=>{});

    // Ambil playlist
    playlistData = await api(`/mp3/folder/${folderId}/tracks`);
    if(!playlistData) playlistData = [];

    loadPlaylist();

    // Auto next handler (dipasang ulang)
    audio.onended = handleTrackEnd;

    updateRepeatButton();
    updateShuffleButton();
}


/* ----------------------------------------------------------
   HANDLE AUTO NEXT / REPEAT / SHUFFLE
---------------------------------------------------------- */
function handleTrackEnd(){

    if(isChanging) return;       // 🔥 cegah double next
    isChanging = true;
    setTimeout(()=> isChanging = false, 400);

    // REPEAT ONE
    if(repeatMode === 1){
        changeTrack(currentTrackId);
        return;
    }

    let index = playlistData.findIndex(t => t.id === currentTrackId);

    // SHUFFLE
    if(shuffleMode){
        let r = playlistData[Math.floor(Math.random() * playlistData.length)];
        changeTrack(r.id);
        return;
    }

    // REPEAT ALL
    if(repeatMode === 2){
        if(index === playlistData.length - 1){
            changeTrack(playlistData[0].id);
        } else {
            changeTrack(playlistData[index + 1].id);
        }
        return;
    }

    // NORMAL MODE
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
            item.style.transition = "0.3s";
            item.innerHTML = `▶ ${mp3.filename}`;
        }
        else {
            item.innerHTML = mp3.filename;
        }

        item.onclick = () => {
    item.style.transform = "scale(0.95)";
    setTimeout(() => changeTrack(mp3.id), 120);
};
    });
}


/* ----------------------------------------------------------
   GANTI TRACK
---------------------------------------------------------- */
function changeTrack(id){

    // Tambah smooth resetting
    let audio = document.getElementById("audioPlayer");
    audio.pause();
    audio.currentTime = 0;

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
   SHUFFLE BUTTON
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
        btn.innerHTML = "🔀";     // Ikon tetap, style berubah
    } else {
        btn.classList.remove("active");
        btn.innerHTML = "🔀";
    }
}


/* ----------------------------------------------------------
   REPEAT BUTTON
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
        btn.innerHTML = "🔁";   // repeat off
    }
    else if(repeatMode === 1){
        btn.classList.add("active");
        btn.innerHTML = "🔂";   // repeat one
    }
    else if(repeatMode === 2){
        btn.classList.add("active");
        btn.innerHTML = "🔁";   // repeat all (ikon sama)
    }
}


/* ----------------------------------------------------------
   RELOAD TRACK
---------------------------------------------------------- */
function reloadTrack(){
    changeTrack(currentTrackId);
}


/* ----------------------------------------------------------
   VOLUME SYSTEM
---------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    const audio  = document.getElementById("audioPlayer");
    const slider = document.getElementById("volumeSlider");
    const icon   = document.getElementById("volumeIcon");

    if(!audio || !slider) return;

    audio.volume = slider.value / 100;

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

function fadeTitle(text){
    const title = document.getElementById("trackTitle");

    // Mulai fade-out
    title.classList.add("fade-out");

    setTimeout(() => {
        title.innerHTML = text;
        title.classList.remove("fade-out");
    }, 300); // waktu fade-out
}