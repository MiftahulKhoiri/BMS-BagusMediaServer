/* ==========================================================
   BMS MP3 LIBRARY (FOLDER & FILE LIST)
   Mode: Clean, Elegant, Neon Green
========================================================== */

let currentFolderId = null;
let currentFolderName = null;

/* ----------------------------------------------------------
   Helper GET JSON
---------------------------------------------------------- */
async function api(path){
    let r = await fetch(path);
    return await r.json();
}

/* ==========================================================
   HOME BUTTON
   - Admin/Root  → /admin/home
   - User biasa  → /user/home
========================================================== */
function goHome(){
    fetch("/auth/role")
        .then(r => r.json())
        .then(d => {
            if (d.role === "admin" || d.role === "root") {
                window.location.href = "/admin/home";
            } else {
                window.location.href = "/user/home";
            }
        })
        .catch(() => window.location.href = "/user/home");
}

/* ==========================================================
   SCAN MP3 KE LIBRARY
========================================================== */
async function scanMP3(){
    document.getElementById("status").innerHTML = "🔍 Scan berjalan...";

    let res = await fetch("/mp3/scan-db", { method: "POST" });
    let data = await res.json();

    document.getElementById("status").innerHTML = data.message;

    // setelah scan, tampilkan ulang folder
    showFolders();
}

/* ==========================================================
   TAMPILKAN LIST SEMUA FOLDER MP3
========================================================== */
async function showFolders(){
    document.getElementById("status").innerHTML = "📁 Memuat folder...";

    currentFolderId = null;
    currentFolderName = null;

    // sembunyikan tombol back
    document.getElementById("backButton").style.display = "none";

    let data = await api("/mp3/folders");

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if (!data || data.length === 0) {
        lib.innerHTML = "<div>Tidak ada folder MP3.</div>";
        return;
    }

    // tampilkan card folder
    data.forEach(f => {
        let card = document.createElement("div");
        card.className = "card";

        card.onclick = ()=> loadMp3Files(f.id, f.folder_name);

        card.innerHTML = `
            <div class="thumb-folder">📁</div>
            <div class="title">${f.folder_name}</div>
            <div class="sub">${f.total_mp3} file</div>
        `;

        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML = "";
}

/* ==========================================================
   TAMPILKAN LIST FILE MP3 DALAM FOLDER
========================================================== */
async function loadMp3Files(folder_id, folder_name){
    currentFolderId = folder_id;
    currentFolderName = folder_name;

    document.getElementById("status").innerHTML = "🎵 Memuat file MP3...";

    // tampilkan tombol back
    document.getElementById("backButton").style.display = "block";

    let data = await api(`/mp3/folder/${folder_id}/tracks`);

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if (!data || data.length === 0){
        lib.innerHTML = "<div>Folder kosong.</div>";
        return;
    }

    // tampilkan MP3 files
    data.forEach(mp3 => {
        let card = document.createElement("div");
        card.className = "card";

        // klik file → masuk player
        card.onclick = ()=> openMp3Player(mp3.id);

        card.innerHTML = `
            <div class="thumb-mp3">🎵</div>
            <div class="title">${mp3.filename}</div>
            <div class="sub">${(mp3.size/1024/1024).toFixed(1)} MB</div>
        `;

        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML =
        `📁 Folder: ${folder_name}`;
}

/* ==========================================================
   BUKA MP3 PLAYER (halaman terpisah)
========================================================== */
function openMp3Player(mp3_id){
    window.location.href =
        `/mp3/watch/${mp3_id}?folder=${currentFolderId}`;
}

/* ==========================================================
   TOMBOL KEMBALI KE LIST FOLDER ATAU FILE
========================================================== */
function goBack(){
    if(currentFolderId){
        showFolders();
    } else {
        showFolders();
    }
}

/* ==========================================================
   AUTO DETECT SAAT PAGE LOAD
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const folderId = params.get("folder");
    const folderName = params.get("name");

    if (folderId) {
        loadMp3Files(folderId, folderName || "Folder");
    } else {
        showFolders();
    }
});

async function api(url){
  const res = await fetch(url);
  return await res.json();
}

const folderListEl = document.getElementById("folderList");
const playBtn = document.getElementById("playSelectedBtn");

let selectedFolders = [];

// load folder list
async function loadFolders(){
  const folders = await api("/mp3/folders");

  folderListEl.innerHTML = "";
  folders.forEach(f => {
    const div = document.createElement("div");
    div.className = "folder-item";

    div.innerHTML = `
      <input type="checkbox" value="${f.id}">
      <span>${f.folder_name} (${f.total_mp3})</span>
    `;

    const checkbox = div.querySelector("input");
    checkbox.onchange = () => {
      if(checkbox.checked){
        selectedFolders.push(f.id);
      }else{
        selectedFolders = selectedFolders.filter(x => x !== f.id);
      }
    };

    folderListEl.appendChild(div);
  });
}

// klik putar
playBtn.onclick = () => {
  if(selectedFolders.length === 0){
    alert("Pilih minimal 1 folder");
    return;
  }

  const ids = selectedFolders.join(",");
  // arahkan ke player (track pertama akan auto play)
  location.href = `/mp3/watch/0?folders=${ids}`;
};

loadFolders();