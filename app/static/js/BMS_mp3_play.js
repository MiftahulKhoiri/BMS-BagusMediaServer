/* ==========================================================
   BMS MP3 PLAYER - FINAL (FAVORITE IN CONTROL BAR)
   - Favorite toggle (control bar)
   - Resume last position (localStorage)
   - Single-page track change (no reload)
   - Volume persisted
   - Smooth scroll active item
   - Defensive checks + no-inline onclick
========================================================== */

let currentFolderId = null;
let currentTrackId = null;
let playlistData = [];
let shuffleMode = false;
let repeatMode = 0; // 0=off,1=one,2=all
let isChanging = false;
const CHANGE_LOCK_MS = 350;

// LocalStorage keys
const LS_TRACK_ID  = "bms_last_track_id";
const LS_TRACK_POS = "bms_last_track_position";
const LS_FOLDER_ID = "bms_last_folder_id";
const LS_VOLUME    = "bms_volume";

/* ---------------------------
   Helper fetch JSON
---------------------------- */
async function api(path, opts = {}) {
    try {
        const r = await fetch(path, Object.assign({cache: "no-store"}, opts));
        if (!r.ok) {
            // try to parse error json
            let txt = await r.text().catch(()=>"");
            throw new Error(`HTTP ${r.status} ${txt}`);
        }
        return await r.json();
    } catch (e) {
        console.error("API Error:", e);
        return null;
    }
}

/* ---------------------------
   NAVIGATION
---------------------------- */
function goHome(){
    fetch("/auth/role")
        .then(r => r.json())
        .then(d => {
            window.location.href =
                (d && (d.role === "admin" || d.role === "root"))
                    ? "/admin/home"
                    : "/user/home";
        })
        .catch(()=> window.location.href = "/user/home");
}

function goBack(){
    if (currentFolderId) window.location.href = `/mp3/?folder=${encodeURIComponent(currentFolderId)}`;
    else window.location.href = "/mp3/";
}

/* ---------------------------
   INIT PLAYER (with resume)
   mp3Id may be string/number
---------------------------- */
async function initPlayer(mp3Id, folderId){
    // try resume if mp3Id not provided
    const resumeId = localStorage.getItem(LS_TRACK_ID);
    const resumePos = Number(localStorage.getItem(LS_TRACK_POS)) || 0;
    const resumeFolder = localStorage.getItem(LS_FOLDER_ID);

    if (!mp3Id && resumeId) {
        mp3Id = resumeId;
        folderId = folderId || resumeFolder;
    }

    if (!mp3Id) {
        const titleEl = document.getElementById("trackTitle");
        if (titleEl) titleEl.textContent = "Tidak ada lagu yang dipilih";
        return;
    }

    currentTrackId = Number(mp3Id);
    currentFolderId = folderId || null;

    attachControlListeners(); // will also create favorite button if needed

    // fetch track info
    const trackInfo = await api(`/mp3/info/${currentTrackId}`);
    if (!trackInfo) {
        const titleEl = document.getElementById("trackTitle");
        if (titleEl) titleEl.textContent = "Error memuat lagu";
    } else {
        fadeTitle(trackInfo.filename || trackInfo.title || `Track ${currentTrackId}`);
    }

    const audio = document.getElementById("audioPlayer");
    if (!audio) return;

    audio.src = `/mp3/play/${currentTrackId}`;
    audio.currentTime = 0;

    // resume position if matches
    if (resumeId && Number(resumeId) === Number(currentTrackId) && resumePos > 1) {
        audio.currentTime = resumePos;
        console.log(`Resuming ${currentTrackId} at ${resumePos}s`);
    }

    // load playlist
    if (currentFolderId) {
        playlistData = await api(`/mp3/folder/${encodeURIComponent(currentFolderId)}/tracks`) || [];
    } else {
        playlistData = await api(`/mp3/list`) || [];
    }
    if (!Array.isArray(playlistData)) playlistData = [];

    // render playlist & update favorite state on control
    loadPlaylist();
    updateFavoriteButtonFromInfo(trackInfo);

    // events
    audio.onended = handleTrackEnd;
    audio.onplay = () => { /* could increment analytics here */ };

    // periodically save last position
    setupPositionSaver();

    restoreVolume();
    updateRepeatButton();
    updateShuffleButton();
}

/* ---------------------------
   Create/attach control listeners and favorite button
---------------------------- */
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

    // create favorite button in control row if not exists
    ensureFavoriteButton();

    // keyboard space toggles play/pause (unless input focused)
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

/* ---------------------------
   Ensure Favorite Button exists in control row (and attach handler)
---------------------------- */
function ensureFavoriteButton(){
    const controlRow = document.querySelector(".control-row");
    if (!controlRow) return;

    // check if favorite button already exists by id
    let favBtn = document.getElementById("favBtn");
    if (!favBtn) {
        favBtn = document.createElement("button");
        favBtn.id = "favBtn";
        favBtn.className = "ctrl-btn";
        favBtn.title = "Favorite";
        favBtn.innerHTML = "🤍"; // default empty heart
        // append to control row (put before reload if present)
        const reload = document.getElementById("reloadBtn");
        if (reload) controlRow.insertBefore(favBtn, reload);
        else controlRow.appendChild(favBtn);
    }

    favBtn.onclick = async () => {
        if (!currentTrackId) return;
        // optimistic toggle UI lock
        favBtn.disabled = true;
        const res = await api(`/mp3/favorite/${encodeURIComponent(currentTrackId)}`, { method: "POST" });
        favBtn.disabled = false;
        if (!res) {
            console.warn("Gagal toggle favorite");
            return;
        }
        // backend returns {status:"ok", is_favorite: 0|1}
        const state = Number(res.is_favorite || 0);
        updateFavBtnVisual(state);
        // also update playlist item if present
        syncPlaylistFavorite(currentTrackId, state);
    };
}

/* ---------------------------
   Update favorite button from track info
---------------------------- */
function updateFavoriteButtonFromInfo(trackInfo) {
    const favBtn = document.getElementById("favBtn");
    if (!favBtn) return;
    if (!trackInfo) {
        favBtn.innerHTML = "🤍";
        favBtn.classList.remove("active");
        return;
    }
    const isFav = Number(trackInfo.is_favorite || 0);
    updateFavBtnVisual(isFav);
}

/* ---------------------------
   Visual update of fav button
---------------------------- */
function updateFavBtnVisual(state) {
    const favBtn = document.getElementById("favBtn");
    if (!favBtn) return;
    if (Number(state) === 1) {
        favBtn.innerHTML = "❤️";
        favBtn.classList.add("active");
    } else {
        favBtn.innerHTML = "🤍";
        favBtn.classList.remove("active");
    }
}

/* ---------------------------
   Sync playlist item favorite (optional small badge)
---------------------------- */
function syncPlaylistFavorite(trackId, state) {
    const item = document.querySelector(`.playlist-item[data-id='${trackId}']`);
    if (!item) return;
    // add small heart at end of item (or update)
    let badge = item.querySelector(".fav-badge");
    if (!badge && Number(state) === 1) {
        badge = document.createElement("span");
        badge.className = "fav-badge";
        badge.style.marginLeft = "8px";
        badge.textContent = "♥";
        item.appendChild(badge);
    } else if (badge && Number(state) === 0) {
        badge.remove();
    }
}

/* ---------------------------
   Handle End / Next logic
---------------------------- */
function handleTrackEnd(){
    if (isChanging) return;
    lockChange();

    if (repeatMode === 1) {
        playTrackById(currentTrackId);
        return;
    }

    const index = playlistData.findIndex(t => Number(t.id) === Number(currentTrackId));

    if (shuffleMode && playlistData.length > 1) {
        let r;
        if (playlistData.length === 2) r = playlistData[(index === 0) ? 1 : 0];
        else {
            do { r = playlistData[Math.floor(Math.random() * playlistData.length)]; }
            while (r && Number(r.id) === Number(currentTrackId));
        }
        if (r) changeTrack(r.id);
        return;
    }

    if (repeatMode === 2 && playlistData.length > 0) {
        if (index === playlistData.length - 1) changeTrack(playlistData[0].id);
        else changeTrack(playlistData[index + 1].id);
        return;
    }

    if (index < playlistData.length - 1 && index !== -1) changeTrack(playlistData[index + 1].id);
}

/* ---------------------------
   Load playlist into DOM
---------------------------- */
function loadPlaylist(){
    const box = document.getElementById("playlist");
    if (!box) return;
    box.innerHTML = "";

    playlistData.forEach(mp3 => {
        const item = document.createElement("div");
        item.className = "playlist-item";
        item.dataset.id = mp3.id;
        item.dataset.title = mp3.filename || mp3.title || `Track ${mp3.id}`;

        const titleText = item.dataset.title;

        // show heart badge if is_favorite present
        if (Number(mp3.is_favorite || 0) === 1) {
            item.innerHTML = `▶ ${escapeHtml(titleText)} <span class="fav-badge">♥</span>`;
        } else {
            if (Number(mp3.id) === Number(currentTrackId)) item.innerHTML = `▶ ${escapeHtml(titleText)}`;
            else item.innerHTML = escapeHtml(titleText);
        }

        item.addEventListener("click", () => {
            item.style.transform = "scale(0.97)";
            setTimeout(() => item.style.transform = "", 140);
            changeTrack(mp3.id);
        });

        box.appendChild(item);
    });

    scrollActiveIntoView();
}

/* ---------------------------
   changeTrack (single-page)
---------------------------- */
function changeTrack(id){
    if (!id) return;
    if (isChanging) return;
    lockChange();

    if (Number(id) === Number(currentTrackId)) {
        playTrackById(id);
        return;
    }

    playTrackById(id);

    try {
        const newUrl = `/mp3/watch/${encodeURIComponent(id)}${currentFolderId ? `?folder=${encodeURIComponent(currentFolderId)}` : ''}`;
        history.pushState({track: id}, '', newUrl);
    } catch {}
}

/* ---------------------------
   playTrackById: update src, title, UI
---------------------------- */
async function playTrackById(id){
    const audio = document.getElementById("audioPlayer");
    if (!audio) return;

    audio.pause();
    audio.currentTime = 0;
    audio.src = `/mp3/play/${encodeURIComponent(id)}`;

    // optimistic title from playlist
    const found = playlistData.find(t => Number(t.id) === Number(id));
    if (found) fadeTitle(found.filename || found.title || `Track ${found.id}`);
    else {
        const info = await api(`/mp3/info/${id}`);
        fadeTitle(info?.filename || info?.title || `Track ${id}`);
        // update favorite button if info present
        updateFavoriteButtonFromInfo(info);
    }

    currentTrackId = Number(id);
    // update saved last track id and reset last pos
    localStorage.setItem(LS_TRACK_ID, currentTrackId);
    localStorage.setItem(LS_TRACK_POS, 0);

    updatePlaylistActive();
    audio.play().catch(()=>{});
    scrollActiveIntoView();
}

/* ---------------------------
   Next / Prev
---------------------------- */
function nextTrack(){
    if (isChanging) return;
    lockChange();
    const idx = playlistData.findIndex(t => Number(t.id) === Number(currentTrackId));
    if (idx === -1 || idx >= playlistData.length - 1) {
        if (repeatMode === 2 && playlistData.length > 0) changeTrack(playlistData[0].id);
        return;
    }
    changeTrack(playlistData[idx + 1].id);
}

function prevTrack(){
    if (isChanging) return;
    lockChange();
    const idx = playlistData.findIndex(t => Number(t.id) === Number(currentTrackId));
    if (idx > 0) changeTrack(playlistData[idx - 1].id);
}

/* ---------------------------
   Shuffle / Repeat buttons
---------------------------- */
function toggleShuffle(){ shuffleMode = !shuffleMode; updateShuffleButton(); }
function updateShuffleButton(){
    const btn = document.getElementById("shuffleBtn");
    if (!btn) return;
    btn.classList.toggle("active", shuffleMode);
    btn.innerHTML = "🔀";
}

function toggleRepeat(){ repeatMode = (repeatMode + 1) % 3; updateRepeatButton(); }
function updateRepeatButton(){
    const btn = document.getElementById("repeatBtn");
    if (!btn) return;
    btn.classList.remove("active");
    if (repeatMode === 0) { btn.innerHTML = "🔁"; btn.classList.remove("active"); }
    else if (repeatMode === 1) { btn.innerHTML = "🔂"; btn.classList.add("active"); }
    else if (repeatMode === 2) { btn.innerHTML = "🔁"; btn.classList.add("active"); }
}

/* ---------------------------
   Reload current track
---------------------------- */
function reloadTrack(){ if (currentTrackId) playTrackById(currentTrackId); }

/* ---------------------------
   Volume restore/save
---------------------------- */
function restoreVolume(){
    const audio = document.getElementById("audioPlayer");
    const slider = document.getElementById("volumeSlider");
    const icon = document.getElementById("volumeIcon");
    if (!audio || !slider) return;

    let saved = localStorage.getItem(LS_VOLUME);
    if (saved === null) saved = 100;
    slider.value = saved;
    audio.volume = Math.max(0, Math.min(1, Number(saved)/100));
    updateVolumeIcon(audio.volume, icon);

    slider.addEventListener("input", () => {
        const v = slider.value / 100;
        audio.volume = v;
        localStorage.setItem(LS_VOLUME, slider.value);
        updateVolumeIcon(v, icon);
    });
}
function updateVolumeIcon(v, iconEl){
    if (!iconEl) return;
    iconEl.textContent =
        v === 0 ? "🔇" :
        v < 0.4 ? "🔈" :
        v < 0.7 ? "🔉" :
                  "🔊";
}

/* ---------------------------
   Position saver (resume)
   saves every 1s only when playing
---------------------------- */
function setupPositionSaver(){
    const audio = document.getElementById("audioPlayer");
    if (!audio) return;
    // clear any previous interval by resetting property
    if (setupPositionSaver._interval) clearInterval(setupPositionSaver._interval);

    setupPositionSaver._interval = setInterval(() => {
        try {
            if (!audio || audio.paused) return;
            if (!currentTrackId) return;
            // save every 1s (floor seconds)
            localStorage.setItem(LS_TRACK_ID, currentTrackId);
            localStorage.setItem(LS_TRACK_POS, Math.floor(audio.currentTime));
            if (currentFolderId) localStorage.setItem(LS_FOLDER_ID, currentFolderId);
        } catch(e){}
    }, 1000);
}

/* ---------------------------
   Fade title
---------------------------- */
function fadeTitle(text){
    const title = document.getElementById("trackTitle");
    if (!title) return;
    title.classList.add("fade-out");
    setTimeout(() => {
        title.textContent = text;
        title.classList.remove("fade-out");
    }, 260);
}

/* ---------------------------
   Update playlist highlight & fav badges
---------------------------- */
function updatePlaylistActive(){
    const items = document.querySelectorAll(".playlist-item");
    items.forEach(it => {
        const id = Number(it.dataset.id);
        if (id === Number(currentTrackId)) {
            it.classList.add("active");
            // ensure leading arrow
            if (!it.textContent.trim().startsWith("▶")) {
                it.innerHTML = `▶ ${escapeHtml(it.dataset.title || it.textContent)}`;
            }
        } else {
            it.classList.remove("active");
            // restore plain text and keep fav-badge if present
            const hasBadge = !!it.querySelector(".fav-badge");
            it.textContent = it.dataset.title || it.textContent;
            if (hasBadge) {
                const badge = document.createElement("span");
                badge.className = "fav-badge";
                badge.style.marginLeft = "8px";
                badge.textContent = "♥";
                it.appendChild(badge);
            }
        }
    });
}

/* ---------------------------
   Scroll active into view
---------------------------- */
function scrollActiveIntoView(){
    const active = document.querySelector(".playlist-item.active");
    if (!active) return;
    const scroller = document.getElementById("playlist") || document.documentElement;
    const top = active.offsetTop - (scroller.clientHeight / 2) + (active.clientHeight / 2);
    scroller.scrollTo({ top, behavior: "smooth" });
}

/* ---------------------------
   Lock change to prevent rapid double-change
---------------------------- */
function lockChange(){
    isChanging = true;
    setTimeout(() => { isChanging = false; }, CHANGE_LOCK_MS);
}

/* ---------------------------
   Utility escape
---------------------------- */
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* ---------------------------
   Expose initPlayer globally (used by HTML)
---------------------------- */
window.initPlayer = initPlayer;