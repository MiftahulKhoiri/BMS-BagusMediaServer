function loadLog() {
    fetch("/logger/read")
        .then(r => r.json())
        .then(data => {
            let box = document.getElementById("logBox");
            box.textContent = data.log || "Log kosong.";
            box.scrollTop = box.scrollHeight;
        })
        .catch(() => {
            document.getElementById("logBox").textContent = "Gagal memuat log!";
        });
}

function clearLog() {
    if (!confirm("Hapus semua log?")) return;

    fetch("/logger/clear")
        .then(r => r.json())
        .then(() => loadLog());
}

// auto load saat halaman dibuka
loadLog();