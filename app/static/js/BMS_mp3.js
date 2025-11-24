// =============================
//   BMS MP3 PLAYER
// =============================

let mp3Audio = new Audio();
let mp3List = [];
let mp3Index = 0;

// Load daftar MP3 dari server
function loadMP3List() {
    fetch("/mp3/list")
        .then(r => r.json())
        .then(data => {
            mp3List = data.files || [];
            if (mp3List.length > 0) {
                loadMP3(0);
            } else {
                document.getElementById("mp3Title").innerText = "Tidak ada file MP3.";
            }
        });
}

// Load file MP3 berdasarkan index
function loadMP3(i) {
    if (mp3List.length === 0) return;

    mp3Index = i;
    let file = mp3List[i];
    
    mp3Audio.src = "/mp3/play?file=" + encodeURIComponent(file);
    mp3Audio.play();

    document.getElementById("mp3Title").innerText = file;
}

// Control
function mp3Play() { mp3Audio.play(); }
function mp3Pause() { mp3Audio.pause(); }

function mp3Next() {
    if (mp3List.length === 0) return;
    mp3Index = (mp3Index + 1) % mp3List.length;
    loadMP3(mp3Index);
}

function mp3Prev() {
    if (mp3List.length === 0) return;
    mp3Index = (mp3Index - 1 + mp3List.length) % mp3List.length;
    loadMP3(mp3Index);
}

// Auto next ketika musik selesai
mp3Audio.onended = () => mp3Next();

// Auto load playlist saat halaman siap
document.addEventListener("DOMContentLoaded", loadMP3List);