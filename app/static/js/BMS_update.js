/* ======================================================
    🔥 GLOBAL DOM ELEMENTS
====================================================== */
const checkBtn = document.getElementById("checkBtn");
const updateBtn = document.getElementById("updateBtn");
const checkResult = document.getElementById("checkResult");
const commitList = document.getElementById("commitList");
const updateStatus = document.getElementById("updateStatus");
const progressBar = document.getElementById("progressBar");
const bar = progressBar.querySelector("div");
const wsLabel = document.getElementById("wsStatus");


/* ======================================================
    🔥 CEK UPDATE ONLINE
====================================================== */
async function checkUpdate() {
    checkResult.innerHTML = "⏳ Mengecek pembaruan...";
    updateBtn.disabled = true;

    try {
        const res = await fetch("/update/check-api");
        const data = await res.json();

        if (!data.success) {
            checkResult.innerHTML = "⚠️ Gagal cek update!";
            return;
        }

        checkResult.innerHTML = `
            <b>Versi Lokal:</b> ${data.local_version}<br>
            <b>Commit Lokal:</b> ${data.local_commit}<br>
            <b>Commit Remote:</b> ${data.remote_commit}<br>
            <b>Status:</b> ${
                data.update_available ? "<span style='color:#28a745'>Update tersedia</span>" :
                                        "<span style='color:#ff4444'>Sudah versi terbaru</span>"
            }
        `;

        if (data.update_available) {
            updateBtn.disabled = false;
        }

    } catch (err) {
        checkResult.innerHTML = "❌ Error saat memeriksa update";
    }
}

checkBtn.addEventListener("click", checkUpdate);


/* ======================================================
    🔥 FETCH COMMIT TERBARU GITHUB
====================================================== */
async function loadCommits() {
    commitList.innerHTML = "<p class='loading'>Mengambil daftar commit...</p>";

    try {
        const res = await fetch(
            "https://api.github.com/repos/MiftahulKhoiri/BMS-BagusMediaServer/commits?per_page=5"
        );
        const data = await res.json();

        if (!Array.isArray(data)) {
            commitList.innerHTML = "⚠️ Tidak bisa memuat commit";
            return;
        }

        commitList.innerHTML = data.map((c) => `
            <div class="commit-item">
                <b>${c.sha.substring(0, 7)}</b><br>
                ${c.commit.message}<br>
                <small>${c.commit.author.name} — ${c.commit.author.date}</small>
                <hr>
            </div>
        `).join("");

    } catch (err) {
        commitList.innerHTML = "❌ Error saat mengambil commit!";
    }
}

loadCommits();


/* ======================================================
    🔥 MULAI DOWNLOAD & UPDATE
====================================================== */
updateBtn.addEventListener("click", async () => {
    updateStatus.innerHTML = "⏳ Memulai download update...";
    progressBar.style.display = "block";
    bar.style.width = "10%";

    try {
        const res = await fetch("/update/start-download");
        const data = await res.json();

        if (!data.success) {
            updateStatus.innerHTML += "<br>❌ Gagal download update!";
            return;
        }

        updateStatus.innerHTML += "<br>📦 Download selesai, menerapkan update...";
        bar.style.width = "40%";

        // Apply update
        const res2 = await fetch("/update/apply-update");
        const apply = await res2.json();

        if (!apply.success) {
            updateStatus.innerHTML =
                `❌ Update gagal pada tahap: ${apply.step}<br>Error: ${apply.error}`;
            return;
        }

        bar.style.width = "100%";
        updateStatus.innerHTML = "<b>✅ UPDATE BERHASIL!</b>";

    } catch (err) {
        updateStatus.innerHTML = "❌ Error saat melakukan update!";
    }
});


/* ======================================================
    🔥 WEBSOCKET REAL-TIME UPDATE
====================================================== */
function initWebSocket() {
    const ws = new WebSocket("ws://" + window.location.host + "/update/ws");

    ws.onopen = () => {
        wsLabel.textContent = "Connected";
        wsLabel.style.color = "#28d7ff";
    };

    ws.onclose = () => {
        wsLabel.textContent = "Disconnected";
        wsLabel.style.color = "#ff4444";

        // Reconnect otomatis
        setTimeout(initWebSocket, 2000);
    };

    ws.onmessage = (msg) => {
        let data = {};
        try { data = JSON.parse(msg.data); } catch {}

        handleLiveUpdate(data);
    };
}

initWebSocket();


/* ======================================================
    🔥 HANDLE LIVE PROGRESS
====================================================== */
function handleLiveUpdate(data) {
    progressBar.style.display = "block";

    if (data.type === "download_complete") {
        bar.style.width = "30%";
        updateStatus.innerHTML += "✔️ Download selesai<br>";
    }

    if (data.type === "extracting") {
        bar.style.width = "50%";
        updateStatus.innerHTML += "📦 Extracting...<br>";
    }

    if (data.type === "backup") {
        bar.style.width = "70%";
        updateStatus.innerHTML += "🗄 Backup...<br>";
    }

    if (data.type === "replace") {
        bar.style.width = "90%";
        updateStatus.innerHTML += "🔁 Mengganti file...<br>";
    }

    if (data.type === "update_applied") {
        bar.style.width = "100%";
        updateStatus.innerHTML += "<b>✅ Update berhasil diterapkan!</b><br>";
    }

    if (data.type === "rollback") {
        bar.style.width = "100%";
        updateStatus.innerHTML += "<b>⚠️ Update gagal, rollback berhasil.</b><br>";
    }
}