let playlist = [];
let currentIndex = 0;
let repeatMode = "none";  // none, one, all
let shuffleMode = false;

const audio = document.getElementById("audioPlayer");
const playlistHTML = document.getElementById("playlistContainer");
const songTitle = document.getElementById("songTitle");
const songIndex = document.getElementById("songIndex");


// =============================================
// 🔥 1. LOAD PLAYLIST DARI SERVER
// =============================================
async function loadPlaylist() {
    const res = await fetch("/mp3/scan");
    const data = await res.json();

    playlist = data.files;
    renderPlaylist();
    updateInfo();
}


// =============================================
// 🔥 2. RENDER PLAYLIST DI HTML
// =============================================
function renderPlaylist() {
    playlistHTML.innerHTML = "";

    playlist.forEach((path, index) => {
        let name = path.split("/").pop();

        let li = document.createElement("li");
        li.textContent = name;
        li.onclick = () => playSong(index);

        playlistHTML.appendChild(li);
    });
}


// =============================================
// 🔥 3. MEMUTAR LAGU
// =============================================
function playSong(index) {
    currentIndex = index;

    const file = playlist[currentIndex];
    const name = file.split("/").pop();

    audio.src = "/mp3/play?file=" + encodeURIComponent(file);
    audio.play();

    document.getElementById("btnPlay").style.display = "none";
    document.getElementById("btnPause").style.display = "inline-block";

    songTitle.textContent = name;
    updateInfo();
}


// =============================================
// 🔥 4. NEXT, PREV
// =============================================
function nextSong() {
    if (shuffleMode) {
        currentIndex = Math.floor(Math.random() * playlist.length);
    } else {
        currentIndex++;
        if (currentIndex >= playlist.length) currentIndex = 0;
    }
    playSong(currentIndex);
}

function prevSong() {
    currentIndex--;
    if (currentIndex < 0) currentIndex = playlist.length - 1;
    playSong(currentIndex);
}


// =============================================
// 🔥 5. AUTO NEXT
// =============================================
audio.onended = () => {
    if (repeatMode === "one") {
        playSong(currentIndex);
    } else if (repeatMode === "all") {
        nextSong();
    }
};


// =============================================
// 🔥 6. TOMBOL PLAY/PAUSE
// =============================================
document.getElementById("btnPlay").onclick = () => {
    audio.play();
    document.getElementById("btnPlay").style.display = "none";
    document.getElementById("btnPause").style.display = "inline-block";
};

document.getElementById("btnPause").onclick = () => {
    audio.pause();
    document.getElementById("btnPause").style.display = "none";
    document.getElementById("btnPlay").style.display = "inline-block";
};


// =============================================
// 🔥 7. MODE REPEAT
// =============================================
document.getElementById("btnRepeatOne").onclick = () => {
    repeatMode = "one";
    alert("Repeat One aktif");
};

document.getElementById("btnRepeatAll").onclick = () => {
    repeatMode = "all";
    alert("Repeat All aktif");
};


// =============================================
// 🔥 8. SHUFFLE
// =============================================
document.getElementById("btnShuffle").onclick = () => {
    shuffleMode = !shuffleMode;
    alert(shuffleMode ? "Shuffle ON" : "Shuffle OFF");
};


// =============================================
// 🔥 9. NEXT / PREV BUTTONS
// =============================================
document.getElementById("btnNext").onclick = nextSong;
document.getElementById("btnPrev").onclick = prevSong;


// =============================================
// 🔥 10. INFO PLAYLIST
// =============================================
function updateInfo() {
    songIndex.textContent =
        (currentIndex + 1) + " / " + playlist.length;
}


// =============================================
// 🔥 11. LOAD AWAL
// =============================================
loadPlaylist();