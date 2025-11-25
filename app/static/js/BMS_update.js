// ================================
// 🔄 Jalankan Update (git pull + auto install)
// ================================
function runUpdate() {
    const logBox = document.getElementById("logBox");
    logBox.innerHTML = "Memproses update...";

    fetch("/tools/update/run")
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                logBox.innerHTML = "❌ ERROR: " + data.error;
            } else {
                let txt = "=== HASIL UPDATE ===\n\n";
                txt += ">>> Git Pull Output:\n" + data.git_output + "\n\n";
                txt += ">>> Install Output:\n" + data.install_output + "\n";
                logBox.innerHTML = txt;
            }
        });
}


// ================================
// 🔁 Restart Server
// ================================
function restartServer() {
    fetch("/tools/restart")
        .then(r => r.json())
        .then(data => {
            document.getElementById("logBox").innerHTML =
                "=== RESTART SERVER ===\n" + data.message;
        });
}


// ================================
// 📜 Load Log
// ================================
function loadLog() {
    fetch("/tools/log")
        .then(r => r.json())
        .then(data => {
            document.getElementById("logBox").innerHTML =
                data.log || "(Log kosong)";
        });
}


// ================================
// 🧹 Clear Log
// ================================
function clearLog() {
    fetch("/tools/log/clear")
        .then(r => r.json())
        .then(() => {
            document.getElementById("logBox").innerHTML =
                "(Log telah dibersihkan)";
        });
}