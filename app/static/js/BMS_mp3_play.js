/* ==========================================================
   BMS MP3 PLAYER - PRO VERSION (REFINED)
   - Single-page track change (no full reload)
   - Defensive checks
   - Button listeners instead of inline onclick
   - Volume persisted to localStorage
   - Smooth scroll active playlist into view
   - Prevent rapid double-changes
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];
let shuffleMode = false;
let repeatMode = 0; // 0=off, 1=one, 2=all
let isChanging = false;
const CHANGE_LOCK_MS = 350; // block repeated changes for this ms

/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path) {
    try {
        let r = await fetch(path, {cache: "no-store"});
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    } catch (e) {
        console.error("API Error:", e);
        return null;
    }
}

/* ----------------------------------------------------------
   HOME / BACK (keperluan navigasi)
---------------------------------------------------------- */
function goHome() {
    fetch("/auth/role")
        .then(r => r.json())
        .then(d => {
            window.location.href =
                (d && (d.role === "admin" || d.role === "root"))
                    ? "/admin/home"
                    : "/user/home";
        })
        .catch(() => window.location.href = "/user/home");
}

function goBack() {
    if (currentFolderId) {
        window.location.href = `/mp3/?folder=${encodeURIComponent(currentFolderId)}`;
    } else {
        window.location.href = "/mp3/";
    }
}

/* ----------------------------------------------------------
   INIT PLAYER
   mp3Id may be string or number. folderId may be null.
---------------------------------------------------------- */
async function initPlayer(mp3Id, folderId) {
    // defensive
    if (!mp3Id) {
        document.getElementById("trackTitle").textContent = "Tidak ada lagu yang dipilih";
        return;
    }

    currentTrackId = Number(mp3Id) || null;
    currentFolderId = folderId || null;

    // attach button listeners (if present)
    attachControlListeners();

    // fetch single track info (if endpoint exists)
    const trackInfo = await api(`/mp3/info/${currentTrackId}`);
    if (!trackInfo) {
        document.getElementById("trackTitle").textContent = "Error memuat lagu";
    } else {
        fadeTitle(trackInfo.filename || trackInfo.title || `Track #${currentTrackId}`);
    }

    // set up audio
    const audio = document.getElementById("audioPlayer");
    if (!audio) return;

    audio.src = `/mp3/play/${currentTrackId}`;
    audio.currentTime = 0;
    audio.play().catch(()=>{ /* ignore autoplay block */ });

    // load playlist for folder (if folderId provided)
    if (currentFolderId) {
        playlistData = await api(`/mp3/folder/${encodeURIComponent(currentFolderId)}/tracks`) || [];
    } else {
        // try a generic list endpoint or single track list
        playlistData = await api(`/mp3/list`) || [];
    }

    // ensure playlistData is array
    if (!Array.isArray(playlistData)) playlistData = [];

    loadPlaylist();

    // audio events
    audio.onended = handleTrackEnd;
    audio.onplay = () => { /* could add play analytics here */ };

    // restore volume if present in localStorage
    restoreVolume();

    updateRepeatButton();
    updateShuffleButton();
}

/* ----------------------------------------------------------
   Attach listeners to buttons (avoid inline onclick)
---------------------------------------------------------- */
function attachControlListeners() {
    const nextBtn = document.getElementById("nextBtn");
    const prevBtn = document.getElementById("prevBtn");
    const shuffleBtn = document.getElementById("shuffleBtn");
    const repeatBtn = document.getElementById("repeatBtn");
    const reloadBtn = document.getElementById("reloadBtn");

    if (nextBtn) nextBtn.onclick = () => nextTrack();
    if (prevBtn) prevBtn.onclick = () => prevTrack();
    if (shuffleBtn) shuffleBtn.onclick = () => toggleShuffle();
    if (repeatBtn) repeatBtn.onclick = () => toggleRepeat();
    if (reloadBtn) reloadBtn.onclick = () => reloadTrack();

    // keyboard shortcut: space = toggle play/pause
    document.addEventListener("keydown", (e) => {
        if (e.code === "Space" && document.activeElement.tagName !== "INPUT") {
            e.preventDefault();
            const audio = document.getElementById("audioPlayer");
            if (!audio) return;
            if (audio.paused) audio.play();
            else audio.pause();
        }
    });
}

/* ----------------------------------------------------------
   HANDLE AUTO NEXT / SHUFFLE / REPEAT
---------------------------------------------------------- */
function handleTrackEnd() {
    if (isChanging) return;
    lockChange();

    if (repeatMode === 1) {
        // repeat single
        playTrackById(currentTrackId);
        return;
    }

    const index = playlistData.findIndex(t => Number(t.id) === Number(currentTrackId));

    if (shuffleMode && playlistData.length > 1) {
        // pick a different random track (try few times)
        let r;
        if (playlistData.length === 2) {
            r = playlistData[(index === 0) ? 1 : 0];
        } else {
            do {
                r = playlistData[Math.floor(Math.random() * playlistData.length)];
            } while (r && Number(r.id) === Number(currentTrackId));
        }
        if (r) changeTrack(r.id);
        return;
    }

    if (repeatMode === 2 && playlistData.length > 0) {
        // loop all
        if (index === playlistData.length - 1) {
            changeTrack(playlistData[0].id);
        } else {
            changeTrack(playlistData[index + 1].id);
        }
        return;
    }

    if (index < playlistData.length - 1 && index !== -1) {
        changeTrack(playlistData[index + 1].id);
    } else {
        // end of list — stop or do nothing
    }
}

/* ----------------------------------------------------------
   LOAD PLAYLIST
---------------------------------------------------------- */
function loadPlaylist() {
    const box = document.getElementById("playlist");
    if (!box) return;

    box.innerHTML = "";

    playlistData.forEach(mp3 => {
        const item = document.createElement("div");
        item.className = "playlist-item";
        item.dataset.id = mp3.id;

        const titleText = mp3.filename || mp3.title || `Track ${mp3.id}`;

        if (Number(mp3.id) === Number(currentTrackId)) {
            item.classList.add("active");
            item.innerHTML = `▶ ${escapeHtml(titleText)}`;
        } else {
            item.innerHTML = escapeHtml(titleText);
        }

        // click handler
        item.addEventListener("click", () => {
            // simple click animation
            item.style.transform = "scale(0.97)";
            setTimeout(() => item.style.transform = "", 140);
            changeTrack(mp3.id);
        });

        box.appendChild(item);
    });

    // scroll active into view
    scrollActiveIntoView();
}

/* ----------------------------------------------------------
   SAFE CHANGE TRACK (single-page: update audio src, title, URL)
---------------------------------------------------------- */
function changeTrack(id) {
    if (!id) return;
    if (isChanging) return;
    lockChange();

    // If requested track is already current -> just play/pause
    if (Number(id) === Number(currentTrackId)) {
        playTrackById(id);
        return;
    }

    // update audio src and UI
    playTrackById(id);

    // update browser URL (pushState) so refresh keeps current track
    try {
        const newUrl = `/mp3/watch/${encodeURIComponent(id)}${currentFolderId ? `?folder=${encodeURIComponent(currentFolderId)}` : ''}`;
        history.pushState({track: id}, '', newUrl);
    } catch (e) {
        // ignore pushState errors on some environments
    }
}

/* ----------------------------------------------------------
   Play track by ID: set audio.src, update title, playlist highlight
---------------------------------------------------------- */
async function playTrackById(id) {
    const audio = document.getElementById("audioPlayer");
    if (!audio) return;

    // set src to stream endpoint
    audio.pause();
    audio.currentTime = 0;
    audio.src = `/mp3/play/${encodeURIComponent(id)}`;

    // optimistic title update: try to find in playlistData
    const found = playlistData.find(t => Number(t.id) === Number(id));
    if (found) {
        fadeTitle(found.filename || found.title || `Track ${found.id}`);
    } else {
        // try to fetch info
        const info = await api(`/mp3/info/${id}`);
        if (info && (info.filename || info.title)) fadeTitle(info.filename || info.title);
        else fadeTitle(`Track ${id}`);
    }

    currentTrackId = Number(id);

    // update playlist highlight
    updatePlaylistActive();

    // start playing (catch autoplay block)
    audio.play().catch(()=>{});

    // ensure active item visible
    scrollActiveIntoView();
}

/* ----------------------------------------------------------
   NEXT / PREV
---------------------------------------------------------- */
function nextTrack() {
    if (isChanging) return;
    lockChange();

    const idx = playlistData.findIndex(t => Number(t.id) === Number(currentTrackId));
    if (idx === -1 || idx >= playlistData.length - 1) {
        // if repeat all active, go to first
        if (repeatMode === 2 && playlistData.length > 0) {
            changeTrack(playlistData[0].id);
        }
        return;
    }
    changeTrack(playlistData[idx + 1].id);
}

function prevTrack() {
    if (isChanging) return;
    lockChange();

    const idx = playlistData.findIndex(t => Number(t.id) === Number(currentTrackId));
    if (idx > 0) changeTrack(playlistData[idx - 1].id);
}

/* ----------------------------------------------------------
   SHUFFLE
---------------------------------------------------------- */
function toggleShuffle() {
    shuffleMode = !shuffleMode;
    updateShuffleButton();
}

function updateShuffleButton() {
    const btn = document.getElementById("shuffleBtn");
    if (!btn) return;
    btn.classList.toggle("active", shuffleMode);
    btn.innerHTML = "🔀";
}

/* ----------------------------------------------------------
   REPEAT
---------------------------------------------------------- */
function toggleRepeat() {
    repeatMode++;
    if (repeatMode > 2) repeatMode = 0;
    updateRepeatButton();
}

function updateRepeatButton() {
    const btn = document.getElementById("repeatBtn");
    if (!btn) return;

    btn.classList.remove("active");
    if (repeatMode === 0) {
        btn.innerHTML = "🔁";
        btn.classList.remove("active");
    } else if (repeatMode === 1) {
        btn.innerHTML = "🔂"; // repeat one
        btn.classList.add("active");
    } else if (repeatMode === 2) {
        btn.innerHTML = "🔁"; // repeat all (active)
        btn.classList.add("active");
    }
}

/* ----------------------------------------------------------
   RELOAD
---------------------------------------------------------- */
function reloadTrack() {
    if (!currentTrackId) return;
    playTrackById(currentTrackId);
}

/* ----------------------------------------------------------
   VOLUME
---------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    const audio = document.getElementById("audioPlayer");
    const slider = document.getElementById("volumeSlider");
    const icon = document.getElementById("volumeIcon");

    if (!audio || !slider) return;

    // load saved volume
    const saved = localStorage.getItem("bms_volume");
    const vol = (saved !== null) ? Number(saved) : (slider.value ? Number(slider.value) : 100);
    slider.value = vol;
    audio.volume = Math.max(0, Math.min(1, vol / 100));

    updateVolumeIcon(audio.volume, icon);

    slider.addEventListener("input", () => {
        const v = slider.value / 100;
        audio.volume = v;
        localStorage.setItem("bms_volume", slider.value);
        updateVolumeIcon(v, icon);
    });
});

function updateVolumeIcon(v, iconEl) {
    if (!iconEl) return;
    iconEl.textContent =
        v === 0 ? "🔇" :
        v < 0.4 ? "🔈" :
        v < 0.7 ? "🔉" :
                  "🔊";
}

/* ----------------------------------------------------------
   FADE TITLE
---------------------------------------------------------- */
function fadeTitle(text) {
    const title = document.getElementById("trackTitle");
    if (!title) return;

    title.classList.add("fade-out");

    setTimeout(() => {
        title.textContent = text;
        title.classList.remove("fade-out");
    }, 260);
}

/* ----------------------------------------------------------
   UPDATE PLAYLIST HIGHLIGHT & SCROLL
---------------------------------------------------------- */
function updatePlaylistActive() {
    const items = document.querySelectorAll(".playlist-item");
    items.forEach(it => {
        if (Number(it.dataset.id) === Number(currentTrackId)) {
            it.classList.add("active");
            it.innerHTML = `▶ ${escapeHtml(it.textContent.replace(/^▶\s*/, '').trim())}`;
        } else {
            it.classList.remove("active");
            // restore plain text (avoid multiple ▶)
            const original = it.dataset.title || it.textContent;
            // keep existing content but ensure no leading "▶"
            it.innerHTML = escapeHtml((original || it.textContent).toString().replace(/^▶\s*/, '').trim());
        }
    });
}

/* Scroll active playlist item into view (smooth) */
function scrollActiveIntoView() {
    const active = document.querySelector(".playlist-item.active");
    if (active) {
        // prefer closest scrollable parent (#playlist)
        const scroller = document.getElementById("playlist");
        if (scroller) {
            const top = active.offsetTop - scroller.offsetTop - (scroller.clientHeight / 2) + (active.clientHeight / 2);
            scroller.scrollTo({ top, behavior: "smooth" });
        } else {
            active.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }
}

/* ----------------------------------------------------------
   UTILS
---------------------------------------------------------- */
function lockChange() {
    isChanging = true;
    setTimeout(() => { isChanging = false; }, CHANGE_LOCK_MS);
}

function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}