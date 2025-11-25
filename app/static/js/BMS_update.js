// ========================
//  NOTIFIKASI
// ========================
function showNotify(msg) {
    const box = document.getElementById("notifyBox");
    box.innerText = msg;
    box.style.display = "block";

    setTimeout(() => {
        box.style.display = "none";
    }, 3000);
}


// ========================
//  UPDATE OTAOMATIS
// ========================
function runUpdate() {
    fetch("/tools/update/run")
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showNotify("❌ " + data.error);
                return;
            }

            if (data.notify) showNotify("✔ " + data.notify);

            let text = "";

            if (data.updated) {
                text += "=== UPDATE BERHASIL ===\n";
                text += data.git_output + "\n\n";
                text += data.pip_output + "\n";
            } else {
                text += "=== TIDAK ADA PEMBARUAN ===\n";
                text += data.message + "\n";
            }

            document.getElementById("logBox").innerText = text;
        });
}


// ========================
//  UPDATE MANUAL
// ========================
function runManualUpdate() {
    fetch("/tools/update/manual")
        .then(res => res.json())
        .then(data => {

            if (data.notify)
                showNotify("✔ " + data.notify);

            document.getElementById("logBox").innerText =
                "=== UPDATE MANUAL ===\n" + data.pip_output;
        });
}


// ========================
//  RESTART SERVER
// ========================
function restartServer() {
    fetch("/tools/restart")
        .then(res => res.json())
        .then(data => {
            showNotify("🔁 Restart diminta");
            document.getElementById("logBox").innerText =
                "=== RESTART ===\n" + data.message;
        });
}


// ========================
//  LOAD LOG
// ========================
function loadLog() {
    fetch("/tools/log")
        .then(res => res.json())
        .then(data => {
            document.getElementById("logBox").innerText = data.log;
        });
}


// ========================
//  CLEAR LOG
// ========================
function clearLog() {
    fetch("/tools/log/clear")
        .then(res => res.json())
        .then(() => {
            showNotify("🧹 Log dibersihkan");
            document.getElementById("logBox").innerText = "Log dibersihkan!";
        });
}