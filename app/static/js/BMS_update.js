// BMS_update_realtime.js
(() => {
  const btnConnect = document.getElementById("btnConnect");
  const btnStop = document.getElementById("btnStop");
  const btnCheck = document.getElementById("btnCheck");
  const logbox = document.getElementById("logbox");
  const statusText = document.getElementById("statusText");
  const projRoot = document.getElementById("projRoot");

  // tampilkan PROJECT_ROOT jika tersedia via API (opsional)
  fetch("/update/check-update")
    .then(r => r.json())
    .then(j => {
      projRoot.textContent = j.output ? "(hasil git status tersedia)" : "(tidak diambil)";
    }).catch(()=>{ projRoot.textContent = "(tidak tersedia)"; });

  let ws = null;

  function appendLog(txt) {
    const now = new Date().toLocaleString();
    logbox.textContent += now + " — " + txt + "\n";
    logbox.scrollTop = logbox.scrollHeight;
  }

  function setStatus(s) {
    statusText.textContent = "Status: " + s;
  }

  btnConnect.addEventListener("click", () => {
    if (ws) {
      appendLog("WebSocket sudah aktif");
      return;
    }

    setStatus("Membuka koneksi WebSocket...");
    const proto = (location.protocol === "https:") ? "wss" : "ws";
    // path ws harus sama dengan yang didaftarkan: /ws/update
    const url = `${proto}://${location.host}/ws/update`;
    ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus("Terhubung — Menjalankan git pull...");
      appendLog("[WS] connected: " + url);
      btnConnect.disabled = true;
      btnStop.disabled = false;
    };

    ws.onmessage = (evt) => {
      // pesan teks langsung
      appendLog(evt.data);
      // jika pesan penanda DONE atau END, ubah status
      if (evt.data && (evt.data.startsWith("[DONE]") || evt.data.startsWith("[END]"))) {
        setStatus("Selesai");
        try { ws.close(); } catch(e){}
      }
    };

    ws.onerror = (err) => {
      appendLog("[WS ERROR] " + (err && err.message ? err.message : JSON.stringify(err)));
      setStatus("Error WS");
    };

    ws.onclose = (ev) => {
      appendLog("[WS] koneksi ditutup");
      ws = null;
      btnConnect.disabled = false;
      btnStop.disabled = true;
      if (statusText.textContent.indexOf("Selesai") === -1) setStatus("Idle");
    };
  });

  btnStop.addEventListener("click", () => {
    if (!ws) return;
    appendLog("[WS] Meminta penutupan koneksi...");
    try { ws.close(); } catch(e){}
  });

  btnCheck.addEventListener("click", async () => {
    setStatus("Memeriksa update (HTTP)...");
    appendLog("[HTTP] Memeriksa update...");
    try {
      const r = await fetch("/update/check-update");
      const j = await r.json();
      appendLog("[HTTP] Response: " + (j.update_available ? "Update tersedia" : "Sudah terbaru"));
      setStatus(j.update_available ? "Update tersedia" : "Sudah terbaru");
    } catch (e) {
      appendLog("[HTTP ERROR] " + e);
      setStatus("Gagal cek");
    }
  });

})();

function loadCommits() {
    fetch("/update/latest-commits")
        .then(r => r.json())
        .then(data => {
            const box = document.getElementById("commitList");
            box.innerHTML = "";

            if (!data.commits) {
                box.innerHTML = "<li>Gagal mengambil commit.</li>";
                return;
            }

            data.commits.forEach(c => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <div class="commit-hash">${c.hash}</div>
                    <div>${c.message}</div>
                    <small>${c.author} — ${c.time}</small>
                `;
                box.appendChild(li);
            });
        });
}

// Jalankan saat halaman dimuat
loadCommits();