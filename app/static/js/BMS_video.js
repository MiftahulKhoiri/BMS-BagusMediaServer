// =============================
//   BMS VIDEO PLAYER
// =============================

let videoPlayer;
let videoList = [];
let videoIndex = 0;

document.addEventListener("DOMContentLoaded", () => {
    videoPlayer = document.getElementById("videoPlayer");
    loadVideoList();
});

// Ambil list video dari server
function loadVideoList() {
    fetch("/video/list")
        .then(r => r.json())
        .then(data => {
            videoList = data.files || [];

            if (videoList.length > 0) {
                loadVideo(0);
            } else {
                document.getElementById("videoTitle").innerText = "Tidak ada file video.";
            }
        });
}

// Load video berdasarkan index
function loadVideo(i) {
    if (videoList.length === 0) return;

    videoIndex = i;
    let file = videoList[i];
    
    videoPlayer.src = "/video/play?file=" + encodeURIComponent(file);
    videoPlayer.play();

    document.getElementById("videoTitle").innerText = file;
}

// Control
function videoPlay() { videoPlayer.play(); }
function videoPause() { videoPlayer.pause(); }

function videoNext() {
    if (videoList.length === 0) return;
    videoIndex = (videoIndex + 1) % videoList.length;
    loadVideo(videoIndex);
}

function videoPrev() {
    if (videoList.length === 0) return;
    videoIndex = (videoIndex - 1 + videoList.length) % videoList.length;
    loadVideo(videoIndex);
}

function videoFullscreen() {
    if (videoPlayer.requestFullscreen) {
        videoPlayer.requestFullscreen();
    }
}