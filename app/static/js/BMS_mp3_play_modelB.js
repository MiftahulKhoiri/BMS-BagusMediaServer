/* ==========================================================
   BMS MP3 PLAYER – MODEL B (API + LIST)
   ✔ Playlist dari Flask API
   ✔ List Lagu UI
   ✔ Play / Pause / Next / Prev
   ✔ Shuffle / Repeat
   ✔ Progress & Time
========================================================== */

/* ------------------ ELEMENT ------------------ */
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
const saveBtn = document.getElementById("saveBtn");

/* ------------------ STATE ------------------ */
let playlist = [];
let currentIndex = 0;
let isPlaying = false;
let shuffleMode = false;
let repeatMode = 0; // 0 off | 1 one | 2 all

/* ------------------ API ------------------ */
async function api(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (e) {
    console.error("API ERROR", e);
    return [];
  }
}

/* ------------------ PLAYLIST ------------------ */
async function loadPlaylist() {
  playlist = await api("/mp3/list");
  renderSongList();
  if (playlist.length > 0) loadTrack(0);
}

/* ------------------ RENDER LIST ------------------ */
function renderSongList() {
  let box = document.getElementById("songList");
  if (!box) {
    box = document.createElement("div");
    box.id = "songList";
    box.className = "song-list";
    document.querySelector(".player-app").appendChild(box);
  }

  box.innerHTML = "";

  playlist.forEach((song, index) => {
    const div = document.createElement("div");
    div.className = "song-item";
    div.textContent = song.title;

    div.onclick = () => loadTrack(index);
    box.appendChild(div);
  });

  updateActiveSong();
}

function updateActiveSong() {
  document.querySelectorAll(".song-item").forEach((el, i) => {
    el.classList.toggle("active", i === currentIndex);
  });
}

/* ------------------ CORE ------------------ */
function loadTrack(index) {
  const track = playlist[index];
  if (!track) return;

  currentIndex = index;
  audio.src = track.src;
  titleEl.textContent = track.title;
  artistEl.textContent = track.artist || "BMS";
  coverImg.src = track.cover || "/static/img/default_cover.jpg";

  playAudio();
  updateActiveSong();
}

function playAudio() {
  audio.play().catch(() => {});
  isPlaying = true;
  playBtn.textContent = "⏸";
}

function pauseAudio() {
  audio.pause();
  isPlaying = false;
  playBtn.textContent = "▶";
}

/* ------------------ CONTROLS ------------------ */
playBtn.onclick = () => {
  isPlaying ? pauseAudio() : playAudio();
};

nextBtn.onclick = () => {
  if (shuffleMode) {
    currentIndex = Math.floor(Math.random() * playlist.length);
  } else {
    currentIndex++;
    if (currentIndex >= playlist.length) {
      if (repeatMode === 2) currentIndex = 0;
      else return;
    }
  }
  loadTrack(currentIndex);
};

prevBtn.onclick = () => {
  currentIndex--;
  if (currentIndex < 0) currentIndex = 0;
  loadTrack(currentIndex);
};

shuffleBtn.onclick = () => {
  shuffleMode = !shuffleMode;
  shuffleBtn.classList.toggle("active", shuffleMode);
};

repeatBtn.onclick = () => {
  repeatMode = (repeatMode + 1) % 3;
  repeatBtn.textContent =
    repeatMode === 1 ? "🔂" :
    repeatMode === 2 ? "🔁" : "🔁";
};

/* ------------------ AUTO NEXT ------------------ */
audio.onended = () => {
  if (repeatMode === 1) {
    playAudio();
    return;
  }
  nextBtn.click();
};

/* ------------------ PROGRESS ------------------ */
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

/* ------------------ LIKE & SAVE ------------------ */
let likes = Number(localStorage.getItem("bms_like") || 0);
likeCountEl.textContent = likes;

likeBtn.onclick = () => {
  likes++;
  likeCountEl.textContent = likes;
  localStorage.setItem("bms_like", likes);
};

saveBtn.onclick = () => {
  localStorage.setItem("bms_saved_track", currentIndex);
  alert("Lagu disimpan 👍");
};

/* ------------------ INIT ------------------ */
loadPlaylist();