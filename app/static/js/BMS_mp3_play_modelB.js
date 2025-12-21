const audio = document.getElementById("audioPlayer");
const playBtn = document.getElementById("playBtn");
const progressBar = document.getElementById("progressBar");
const currentTime = document.getElementById("currentTime");
const duration = document.getElementById("duration");

const params = new URLSearchParams(location.search);
const trackId = params.get("id");

audio.src = `/mp3/play/${trackId}`;
audio.play();

playBtn.onclick = () => {
  if(audio.paused){
    audio.play();
    playBtn.textContent="⏸";
  }else{
    audio.pause();
    playBtn.textContent="▶";
  }
};

audio.ontimeupdate = () => {
  progressBar.value = (audio.currentTime / audio.duration) * 100 || 0;
  currentTime.textContent = format(audio.currentTime);
  duration.textContent = format(audio.duration);
};

progressBar.oninput = () => {
  audio.currentTime = (progressBar.value / 100) * audio.duration;
};

function format(sec){
  if(!sec) return "0:00";
  const m = Math.floor(sec/60);
  const s = Math.floor(sec%60).toString().padStart(2,"0");
  return `${m}:${s}`;
}