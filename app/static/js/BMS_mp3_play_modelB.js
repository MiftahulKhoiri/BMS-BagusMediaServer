/* ==========================================================
   BMS MP3 PLAYER – MODEL B (FINAL – ROUTE MATCHED)
   ✔ Watch page only
   ✔ Stream from /mp3/play/<id>
   ✔ Info from /mp3/info/<id>
   ✔ Favorite server-based
========================================================== */

/* ---------------- ELEMENT ---------------- */
const audio = document.getElementById("audioPlayer");

const playBtn = document.getElementById("playBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const repeatBtn = document.getElementById("repeatBtn");

const progressBar = document.getElementById("progressBar");
const currentTimeEl = document.getElementById("currentTime");
const durationEl = document.getElementById("duration");

const titleEl = document.getElementById("trackTitle");
const artistEl = document.getElementById("trackArtist");
const coverImg = document.getElementById("coverImg");

const likeBtn = document.getElementById("likeBtn");
const likeCountEl = document.getElementById("likeCount");

/* ---------------- STATE ---------------- */
let currentTrackId = null;
let isPlaying = false;
let shuffleMode = false;
let repeatMode = 0; // 0 off | 1 one | 2 all

/* ---------------- HELPER ---------------- */
async function api(url, options = {}) {
  try {
    const res = await fetch(url, options);
    return await res.json();
  } catch (e) {
    console.error("API ERROR:", e);
    return null;
  }
}

function getTrackIdFromURL() {
  const parts = window.location.pathname.split("/");
  return parts[parts.length - 1];
}

/* ---------------- INIT PLAYER ---------------- */
async function initPlayer() {
  currentTrackId = getTrackIdFromURL();
  if (!currentTrackId) return;

  const info = await api(`/mp3/info/${currentTrackId}`);
  if (!info) return;

  titleEl.textContent = info.filename;
  artistEl.textContent = "BMS";
  coverImg.src = "/static/img/default_cover.jpg";

  // 🔑 STREAM FILE (INI KUNCI)
  audio.src = `/mp3/play/${currentTrackId}`;
  audio.play().catch(() => {});
  isPlaying = true;
  playBtn.textContent = "⏸";

  updateFavorite(info.is_favorite);
}

/* ---------------- PLAY / PAUSE ---------------- */
playBtn.onclick = () => {
  if (isPlaying) {
    audio.pause();
    playBtn.textContent = "▶";
  } else {
    audio.play().catch(() => {});
    playBtn.textContent = "⏸";
  }
  isPlaying = !isPlaying;
};

/* ---------------- NEXT / PREV ----------------
   (sementara reload lagu, nanti folder context)
------------------------------------------------ */
nextBtn.onclick = () => reloadTrack();
prevBtn.onclick = () => reloadTrack();

function reloadTrack() {
  audio.currentTime = 0;
  audio.play().catch(() => {});
}

/* ---------------- SHUFFLE ---------------- */
shuffleBtn.onclick = () => {
  shuffleMode = !shuffleMode;
  shuffleBtn.classList.toggle("active", shuffleMode);
};

/* ---------------- REPEAT ---------------- */
repeatBtn.onclick = () => {
  repeatMode = (repeatMode + 1) % 3;
  repeatBtn.textContent =
    repeatMode === 1 ? "🔂" :
    repeatMode === 2 ? "🔁" : "🔁";
};

/* ---------------- AUTO END ---------------- */
audio.onended = () => {
  if (repeatMode === 1) {
    reloadTrack();
  }
};

/* ---------------- PROGRESS ---------------- */
audio.ontimeupdate = () => {
  progressBar.max = audio.duration || 0;
  progressBar.value = audio.currentTime || 0;

  currentTimeEl.textContent = formatTime(audio.currentTime);
  durationEl.textContent = formatTime(audio.duration);
};

progressBar.oninput = () => {
  audio.currentTime = progressBar.value;
};

function formatTime(sec) {
  if (!sec) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

/* ---------------- FAVORITE ❤️ ---------------- */
function updateFavorite(state) {
  likeBtn.textContent = state ? "❤️" : "🤍";
}

likeBtn.onclick = async () => {
  const res = await api(`/mp3/favorite/${currentTrackId}`, {
    method: "POST"
  });
  if (res?.is_favorite !== undefined) {
    updateFavorite(res.is_favorite);
  }
};

/* ---------------- INIT ---------------- */
initPlayer();