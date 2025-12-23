/* ==========================================================
   BMS MP3 PLAYER – FINAL STABLE (MULTI FOLDER + REPEAT FIX)
========================================================== */

/* ================= ELEMENT ================= */
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

const nextList = document.getElementById("nextList");
const tabNext = document.getElementById("tabNext");

/* ================= STATE ================= */
let playlist = [];
let currentIndex = 0;
let isPlaying = false;

/*
 repeatMode:
 0 = off
 1 = ulang 1
 2 = ulang semua
*/
let shuffleMode = localStorage.getItem("bms_shuffle") === "1";
let repeatMode = Number(localStorage.getItem("bms_repeat") || 0);

/* ================= HELPERS ================= */
async function api(url) {
  const res = await fetch(url);
  return await res.json();
}

function getTrackId() {
  const v = Number(location.pathname.split("/").pop());
  return isNaN(v) ? null : v;
}

function getFolderId() {
  return new URLSearchParams(location.search).get("folder");
}

/* ================= BLUR BACKGROUND SYNC ================= */
function updateBackgroundFromCover() {
  if (!coverImg.src) return;
  document.documentElement.style.setProperty(
    "--cover-bg",
    `url('${coverImg.src}')`
  );
}

/* ================= PLAYER STATE ================= */
function loadPlayerState() {
  shuffleBtn.classList.toggle("active", shuffleMode);

  repeatBtn.classList.remove("active");

  if (repeatMode === 1) {
    repeatBtn.textContent = "🔂"; // repeat one
    repeatBtn.classList.add("active");
  } else if (repeatMode === 2) {
    repeatBtn.textContent = "🔁"; // repeat all
    repeatBtn.classList.add("active");
  } else {
    repeatBtn.textContent = "🔁"; // off
  }
}

/* ================= INIT ================= */
async function initPlayer() {
  const folderIds = new URLSearchParams(location.search).get("folders");
  const trackId = getTrackId();

  // 🔥 MULTI FOLDER MODE
  if (folderIds) {
    playlist = await api(`/mp3/tracks/by-folders?folders=${folderIds}`);
    if (!playlist.length) return;
    currentIndex = 0;
  }
  // 🔥 SINGLE FOLDER MODE
  else {
    const folderId = getFolderId();
    if (!folderId) return;

    playlist = await api(`/mp3/folder/${folderId}/tracks`);
    if (!playlist.length) return;

    currentIndex = playlist.findIndex(t => t.id === trackId);
    if (currentIndex < 0) currentIndex = 0;
  }

  loadPlayerState();
  renderNextList();
  loadTrack(currentIndex);
}

/* ================= LOAD TRACK ================= */
function loadTrack(index) {
  const track = playlist[index];
  if (!track) return;

  currentIndex = index;

  titleEl.textContent = track.filename;
  artistEl.textContent = "BMS";

  if (track.filepath) {
    coverImg.src = "/mp3/thumbnail/" + encodeURIComponent(track.filepath);
    applyAccentColor(track.filepath);
  } else {
    coverImg.src = "/static/img/default_cover.jpg";
  }

  coverImg.onload = updateBackgroundFromCover;

  audio.src = `/mp3/play/${track.id}`;
  audio.play().catch(() => {});
  isPlaying = true;
  playBtn.textContent = "⏸";

  highlightNext();
}

/* ================= CONTROLS ================= */
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

nextBtn.onclick = () => playNext();
prevBtn.onclick = () => playPrev();

/* ================= SHUFFLE ================= */
shuffleBtn.onclick = () => {
  shuffleMode = !shuffleMode;
  localStorage.setItem("bms_shuffle", shuffleMode ? "1" : "0");
  loadPlayerState();
};

/* ================= REPEAT ================= */
repeatBtn.onclick = () => {
  repeatMode = (repeatMode + 1) % 3;
  localStorage.setItem("bms_repeat", repeatMode);
  loadPlayerState();
};

/* ================= PLAY LOGIC ================= */
function playNext() {
  if (shuffleMode) {
    loadTrack(Math.floor(Math.random() * playlist.length));
    return;
  }

  if (currentIndex < playlist.length - 1) {
    loadTrack(currentIndex + 1);
  } else if (repeatMode === 2) {
    loadTrack(0); // repeat all
  }
}

function playPrev() {
  if (audio.currentTime > 3) {
    audio.currentTime = 0;
    return;
  }
  if (currentIndex > 0) {
    loadTrack(currentIndex - 1);
  }
}

/* ================= AUTO END ================= */
audio.onended = () => {
  if (repeatMode === 1) {
    loadTrack(currentIndex); // repeat one
    return;
  }
  playNext();
};

/* ================= PROGRESS ================= */
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
  if (!sec || isNaN(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

/* ================= NEXT LIST ================= */
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

function highlightNext() {
  document.querySelectorAll(".next-item").forEach((el, i) => {
    el.classList.toggle("active", i === currentIndex);
  });
}

/* ================= DROPDOWN ================= */
tabNext.onclick = () => {
  nextList.classList.toggle("hidden");
};

/* ================= ACCENT COLOR ================= */
async function applyAccentColor(filepath) {
  try {
    const res = await fetch("/mp3/color/" + encodeURIComponent(filepath));
    const data = await res.json();
    if (data.color) {
      document.documentElement.style.setProperty(
        "--accent-color",
        data.color
      );
    }
  } catch (e) {}
}

/* ================= START ================= */
initPlayer();