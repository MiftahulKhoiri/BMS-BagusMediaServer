/* ==========================================================
   BMS MP3 PLAYER – FIX NEXT / PREV + NEXT LIST
   ✔ Playlist dari folder
   ✔ Next / Prev BENAR
   ✔ List "BERIKUTNYA" tampil
========================================================== */

const audio = document.getElementById("audioPlayer");

/* UI */
const playBtn = document.getElementById("playBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");

const progressBar = document.getElementById("progressBar");
const currentTimeEl = document.getElementById("currentTime");
const durationEl = document.getElementById("duration");

const titleEl = document.getElementById("trackTitle");
const artistEl = document.getElementById("trackArtist");

const nextList = document.getElementById("nextList");

/* STATE */
let playlist = [];
let currentIndex = 0;
let isPlaying = false;

/* ---------------- HELPERS ---------------- */
async function api(url) {
  const res = await fetch(url);
  return await res.json();
}

function getTrackId() {
  return Number(window.location.pathname.split("/").pop());
}

function getFolderId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("folder");
}

/* ---------------- INIT ---------------- */
async function initPlayer() {
  const trackId = getTrackId();
  const folderId = getFolderId();

  if (!folderId) {
    console.error("Folder ID tidak ada");
    return;
  }

  playlist = await api(`/mp3/folder/${folderId}/tracks`);
  currentIndex = playlist.findIndex(t => t.id === trackId);

  if (currentIndex === -1) currentIndex = 0;

  loadTrack(currentIndex);
  renderNextList();
}

/* ---------------- LOAD TRACK ---------------- */
async function loadTrack(index) {
  const track = playlist[index];
  if (!track) return;

  currentIndex = index;

  titleEl.textContent = track.filename;
  artistEl.textContent = "BMS";

  audio.src = `/mp3/play/${track.id}`;
  audio.play().catch(() => {});
  isPlaying = true;
  playBtn.textContent = "⏸";

  highlightNextList();
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

/* ---------------- AUTO NEXT ---------------- */
audio.onended = () => {
  if (currentIndex < playlist.length - 1) {
    loadTrack(currentIndex + 1);
  }
};

/* ---------------- NEXT LIST ---------------- */
function renderNextList() {
  nextList.innerHTML = "";

  playlist.forEach((track, i) => {
    const div = document.createElement("div");
    div.className = "next-item";
    div.textContent = track.filename;

    div.onclick = () => loadTrack(i);
    nextList.appendChild(div);
  });
}

function highlightNextList() {
  document.querySelectorAll(".next-item").forEach((el, i) => {
    el.classList.toggle("active", i === currentIndex);
  });
}

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

/* ---------------- INIT ---------------- */
initPlayer();

const tabNext = document.getElementById("tabNext");
const nextList = document.getElementById("nextList");

tabNext.onclick = () => {
  nextList.classList.toggle("hidden");
};