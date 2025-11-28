async function api(path){
    let r = await fetch(path);
    return await r.json();
}

/* ===========================
   SCAN LIBRARY
=========================== */
async function scanDB(){
    document.getElementById('status').innerHTML = "🔄 Scan berjalan...";
    let res = await fetch("/video/scan-db", { method: "POST" });
    let data = await res.json();
    document.getElementById('status').innerHTML = data.message;
    showFolders();
}

/* ===========================
   TAMPILKAN FOLDER
=========================== */
async function showFolders(){
    document.getElementById('status').innerHTML = "Memuat folder...";
    let data = await api("/video/folders");

    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if(data.length === 0){
        lib.innerHTML = "<div>Tidak ada folder berisi video.</div>";
        return;
    }

    data.forEach(f => {
        let card = document.createElement("div");
        card.className = "card";
        card.onclick = ()=> loadVideos(f.id, f.folder_name);

        card.innerHTML = `
            <div class="thumb-folder">📁</div>
            <div class="title">${f.folder_name}</div>
            <div class="sub">${f.total_video} video</div>
        `;

        lib.appendChild(card);
    });

    document.getElementById('status').innerHTML = "";
}

/* ===========================
   TAMPILKAN VIDEO PER FOLDER
=========================== */
async function loadVideos(folder_id, folder_name){
    document.getElementById('status').innerHTML = "Memuat video...";

    let data = await api(`/video/folder/${folder_id}/videos`);
    const lib = document.getElementById("library");
    lib.innerHTML = "";

    if(data.length === 0){
        lib.innerHTML = "<div>Folder kosong.</div>";
        return;
    }

    data.forEach(v => {
        let card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <img src="/video/thumbnail/${v.id}" class="thumb-video">
            <div class="title">${v.filename}</div>
            <div class="sub">${(v.size/1024/1024).toFixed(1)} MB</div>
        `;

        card.onclick = ()=> playVideo(v.id, v.filename);
        lib.appendChild(card);
    });

    document.getElementById("status").innerHTML = `📁 Folder: ${folder_name}`;
}

/* ===========================
   PLAYER
=========================== */
function playVideo(id, title){
    let modal = document.getElementById("playerModal");
    let player = document.getElementById("playerVideo");

    document.getElementById("playerTitle").innerHTML = title;
    player.src = `/video/play/${id}`;
    modal.style.display = "flex";
}

function closePlayer(){
    let modal = document.getElementById("playerModal");
    let player = document.getElementById("playerVideo");

    player.pause();
    player.src = "";
    modal.style.display = "none";
}