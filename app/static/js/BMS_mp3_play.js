/* ==========================================================
   BMS MP3 PLAYER – FINAL STABLE VERSION
   Semua tombol diperbaiki:
   - Prev / Next
   - Shuffle
   - Repeat
   - Reload
   - Favorite (auto insert)
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];
let shuffleMode = false;
let repeatMode = 0;
let isChanging = false;

/* ----------------------- API Helper ---------------------- */
async function api(path, options = {}) {
    try {
        const res = await fetch(path, options);
        return await res.json();
    } catch (e) {
        console.error("API ERROR:", e);
        return null;
    }
}

/* ----------------------- INIT PLAYER ---------------------- */
async function initPlayer(trackId, folderId) {
    currentTrackId = Number(trackId);
    currentFolderId = folderId || null;

    // Load track info
    const info = await api(`/mp3/info/${currentTrackId}`);
    if (info?.filename) {
        updateTitle(info.filename);
    }

    // Set audio source
    const audio = document.getElementById("audioPlayer");
    audio.src = `/mp3/play/${currentTrackId}`;
    audio.play().catch(() => {});
    audio.onended = handleTrackEnd;

    // Load playlist
    if (currentFolderId) {
        playlistData = await api(`/mp3/folder/${currentFolderId}/tracks`);
    } else {
        playlistData = [];
    }

    renderPlaylist();
    attachControlListeners();
    updateRepeatButton();
    updateShuffleButton();
    createFavoriteButton(info);
}

/* ----------------------- UPDATE TITLE ---------------------- */
function updateTitle(text) {
    const title = document.getElementById("trackTitle");
    title.textContent = text;
}

/* ----------------------- PLAYLIST RENDER ---------------------- */
function renderPlaylist() {
    const box = document.getElementById("playlist");
    box.innerHTML = "";

    playlistData.forEach(mp3 => {
        const div = document.createElement("div");
        div.className = "playlist-item";
        div.dataset.id = mp3.id;

        if (mp3.id === currentTrackId) {
            div.classList.add("active");
            div.textContent = `▶ ${mp3.filename}`;
        } else {
            div.textContent = mp3.filename;
        }

        div.onclick = () => changeTrack(mp3.id);
        box.appendChild(div);
    });
}

/* ----------------------- CHANGE TRACK ---------------------- */
function changeTrack(id) {
    if (isChanging) return;
    isChanging = true;
    setTimeout(() => (isChanging = false), 300);

    currentTrackId = id;

    const audio = document.getElementById("audioPlayer");
    audio.src = `/mp3/play/${id}`;
    audio.play().catch(() => {});

    updateActivePlaylist();
    updateFavoriteState(id);
}

function updateActivePlaylist() {
    const items = document.querySelectorAll(".playlist-item");
    items.forEach(el => {
        if (Number(el.dataset.id) === Number(currentTrackId)) {
            el.classList.add("active");
            el.textContent = `▶ ${el.textContent.replace("▶", "").trim()}`;
        } else {
            el.classList.remove("active");
            el.textContent = el.textContent.replace("▶", "").trim();
        }
    });
}

/* ----------------------- NEXT / PREV ---------------------- */
function nextTrack() {
    const index = playlistData.findIndex(t => t.id === currentTrackId);
    if (index < playlistData.length - 1) {
        changeTrack(playlistData[index + 1].id);
    }
}

function prevTrack() {
    const index = playlistData.findIndex(t => t.id === currentTrackId);
    if (index > 0) {
        changeTrack(playlistData[index - 1].id);
    }
}

/* ----------------------- SHUFFLE ---------------------- */
function toggleShuffle() {
    shuffleMode = !shuffleMode;
    updateShuffleButton();
}

function updateShuffleButton() {
    const btn = document.getElementById("shuffleBtn");
    btn.classList.toggle("active", shuffleMode);
}

/* ----------------------- REPEAT ---------------------- */
function toggleRepeat() {
    repeatMode = (repeatMode + 1) % 3;
    updateRepeatButton();
}

function updateRepeatButton() {
    const btn = document.getElementById("repeatBtn");
    btn.classList.remove("active");

    if (repeatMode === 1) {
        btn.textContent = "🔂"; // repeat one
        btn.classList.add("active");
    } else if (repeatMode === 2) {
        btn.textContent = "🔁"; // repeat all
        btn.classList.add("active");
    } else {
        btn.textContent = "🔁";
    }
}

/* ----------------------- RELOAD ---------------------- */
function reloadTrack() {
    changeTrack(currentTrackId);
}

/* ----------------------- AUTO NEXT HANDLING ---------------------- */
function handleTrackEnd() {
    const index = playlistData.findIndex(t => t.id === currentTrackId);

    if (repeatMode === 1) {
        changeTrack(currentTrackId);
        return;
    }

    if (shuffleMode) {
        const random = playlistData[Math.floor(Math.random() * playlistData.length)];
        changeTrack(random.id);
        return;
    }

    if (repeatMode === 2) {
        if (index === playlistData.length - 1) changeTrack(playlistData[0].id);
        else changeTrack(playlistData[index + 1].id);
        return;
    }

    if (index < playlistData.length - 1) {
        changeTrack(playlistData[index + 1].id);
    }
}

/* ----------------------- FAVORITE BUTTON ---------------------- */
function createFavoriteButton(info) {
    const row = document.getElementById("controlRow");

    // Jika sudah ada, return
    if (document.getElementById("favBtn")) return;

    const btn = document.createElement("button");
    btn.id = "favBtn";
    btn.className = "ctrl-btn";
    btn.textContent = info?.is_favorite ? "❤️" : "🤍";

    btn.onclick = async () => {
        const res = await api(`/mp3/favorite/${currentTrackId}`, { method: "POST" });
        btn.textContent = res.is_favorite ? "❤️" : "🤍";
    };

    row.appendChild(btn);
}

async function updateFavoriteState(id) {
    const info = await api(`/mp3/info/${id}`);
    const btn = document.getElementById("favBtn");
    if (btn) btn.textContent = info?.is_favorite ? "❤️" : "🤍";
}

/* ----------------------- ATTACH BUTTON EVENTS ---------------------- */
function attachControlListeners() {
    document.getElementById("nextBtn").onclick = nextTrack;
    document.getElementById("prevBtn").onclick = prevTrack;
    document.getElementById("shuffleBtn").onclick = toggleShuffle;
    document.getElementById("repeatBtn").onclick = toggleRepeat;
    document.getElementById("reloadBtn").onclick = reloadTrack;
}