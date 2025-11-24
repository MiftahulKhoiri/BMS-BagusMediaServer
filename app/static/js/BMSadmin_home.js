// ==========================================
// BMS ADMIN PANEL – FRONTEND CONTROL SCRIPT
// ==========================================

// Memperbarui log ke dalam textarea
function appendLog(text) {
    const logArea = document.getElementById("logArea");
    logArea.value += "\n" + text;
    logArea.scrollTop = logArea.scrollHeight;  // auto scroll ke bawah
}

// Kirim perintah ke backend Flask
function sendCommand(cmd) {
    appendLog(`[CLIENT] Mengirim perintah: ${cmd.toUpperCase()}...`);

    fetch(`/admin/${cmd}`, { method: "POST" })
        .then(response => response.text())
        .then(data => {
            appendLog(`[SERVER] ${data}`);
        })
        .catch(error => {
            appendLog(`[ERROR] ${error}`);
        });
}

// ==============================
// Koneksi tombol → perintah API
// ==============================
document.addEventListener("DOMContentLoaded", () => {

    const btnUpdate = document.querySelector(".btn-update");
    const btnInstall = document.querySelector(".btn-install");
    const btnRestart = document.querySelector(".btn-restart");

    if (btnUpdate) btnUpdate.onclick = () => sendCommand("update");
    if (btnInstall) btnInstall.onclick = () => sendCommand("install");
    if (btnRestart) btnRestart.onclick = () => sendCommand("restart");

});