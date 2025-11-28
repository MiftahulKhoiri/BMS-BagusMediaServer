function checkUpdate() {
    document.getElementById("update-status").innerHTML = "⏳ Mengecek pembaruan...";

    fetch("/update/check-update")
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                document.getElementById("update-status").innerHTML = "❌ Error: " + data.error;
                return;
            }

            if (data.update_available) {
                document.getElementById("update-status").innerHTML = "✅ Update tersedia!";
            } else {
                document.getElementById("update-status").innerHTML = "✔ Perangkat lunak sudah versi terbaru.";
            }

            loadCommits();
        });
}

function loadCommits() {
    fetch("/update/latest-commits")
        .then(res => res.json())
        .then(data => {
            const box = document.getElementById("commit-container");
            box.innerHTML = "";

            if (!data.commits) {
                box.innerHTML = `<p>Tidak bisa mengambil commit.</p>`;
                return;
            }

            data.commits.forEach(c => {
                box.innerHTML += `
                    <div class="commit-item">
                        <b>${c.hash}</b> — ${c.message}<br>
                        <small>${c.author} • ${c.time}</small>
                    </div>
                `;
            });
        });
}

function startUpdate() {
    document.getElementById("log").innerHTML = "";
    const protocol = location.protocol === "https:" ? "wss://" : "ws://";
    const ws = new WebSocket(protocol +location.host + "/ws/update");

    ws.onopen = () => {
        addLog("▶ Memulai proses update...");
    };

    ws.onmessage = (evt) => {
        addLog(evt.data);

        if (evt.data.includes("[END]")) {
            addLog("✔ Update selesai.");
        }
    };

    ws.onerror = () => {
        addLog("❌ WebSocket error.");
    };
}

function addLog(text) {
    const logBox = document.getElementById("log");
    logBox.innerHTML += text + "<br>";
    logBox.scrollTop = logBox.scrollHeight;
}