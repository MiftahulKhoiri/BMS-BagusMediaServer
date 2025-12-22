/* ==========================================================
   BMS MP3 PLAYER – MODEL B (FOLDER CONTEXT)
   ✔ Next / Prev dalam folder
   ✔ Back navigation
   ✔ Resume play (mini-player logic)
========================================================== */

const audio = document.getElementById("audioPlayer");

/* UI */
const playBtn = document.getElementById("playBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const repeatBtn = document.getElementById("repeatBtn");

const progressBar = document.getElementById("progressBar");
const currentTimeEl = document.getElementById("currentTime");
const durationEl = document.getElementById("duration");

const titleEl = document.getElementById("trackTitle");
const artistEl = document.getElementById("trackArtist");

/* STATE */
let playlist = [];
let currentIndex = 0;
let isPlaying = false;
let repeatMode = 0;

/* ---------------- HELPERS ---------------- */
async function api(url) {
  const res = await fetch(url);
  return await res.json();
}

function getTrackIdFromURL() {
  return window.location.pathname.split("/").pop();
}

/* ---------------- INIT ---------------- */
async function initPlayer() {
  playlist = JSON.parse(localStorage.getItem("bms_playlist") || "[]");

  const trackId = Number(getTrackIdFromURL());
  currentIndex = playlist.findIndex(t => t.id === trackId);

  if (currentIndex === -1) {
    // fallback jika direct access
    const info = await api(`/mp3/info/${trackId}`);
    playlist = [{ id: trackId, filename: info.filename }];
    currentIndex = 0;
  }

  loadTrack(currentIndex);
}

/* ---------------- LOAD TRACK ---------------- */
async function loadTrack(index) {
  const track = playlist[index];
  if (!track) return;

  currentIndex = index;
  localStorage.setItem("bms_current", track.id);

  const info = await api(`/mp3/info/${track.id}`);

  titleEl.textContent = info.filename;
  artistEl.textContent = "BMS";

  audio.src = `/mp3/play/${track.id}`;
  audio.play().catch(() => {});
  isPlaying = true;
  playBtn.textContent = "⏸";
}

/* ---------------- CONTROLS ---------------- */
playBtn.onclick = () => {
  if (isPlaying) {
    audio.pause();
    playBtn.textContent = "▶";
  } else {
    audio.play();
    playBtn.textContent = "⏸";
  }
  isPlaying = !isPlaying;
};

nextBtn.onclick = () => {
  if (currentIndex < playlist.length - 1) {
    loadTrack(currentIndex + 1);
  }
};

prevBtn.onclick = () => {
  if (currentIndex > 0) {
    loadTrack(currentIndex - 1);
  }
};

repeatBtn.onclick = () => {
  repeatMode = (repeatMode + 1) % 2;
  repeatBtn.classList.toggle("active", repeatMode === 1);
};

/* ---------------- AUTO END ---------------- */
audio.onended = () => {
  if (repeatMode === 1) {
    loadTrack(currentIndex);
  } else if (currentIndex < playlist.length - 1) {
    loadTrack(currentIndex + 1);
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
};

/* ---------------- BACK BUTTON ---------------- */
function goBack() {
  const folder = localStorage.getItem("bms_folder");
  if (folder) {
    window.location.href = `/mp3/folder/${folder}`;
  } else {
    window.location.href = "/mp3";
  }
}

document.querySelector(".icon-btn").onclick = goBack;

/* ---------------- INIT ---------------- */
initPlayer();