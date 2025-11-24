// =============================================
//   BMS UPDATE PANEL JS
// =============================================

document.addEventListener("DOMContentLoaded", () => {
    loadUpdateLog();
});


// =============================================
// 🔄 Jalankan Update (git pull)
// =============================================
function runUpdate() {
    showLoading("Menjalankan update server...");

    fetch("/tools/update")
        .then(r => r.json())
        .then(data => {
            hideLoading();

            if (data.error) {
                BMSnotify("Gagal update: " + data.error, "error");
                return;
            }

            BMSnotify("Update selesai!", "success");
            loadUpdateLog();
        })
        .catch(() => {
            hideLoading();
            BMSnotify("Koneksi error!", "error");
        });
}


// =============================================
// 📦 Install Package
// =============================================
function installPkg() {
    let pkg = document.getElementById("pkgName").value.trim();
    if (!pkg) {
        BMSnotify("Nama package kosong!", "error");
        return;
    }

    showLoading("Install package: " + pkg);

    let form = new FormData();
    form.append("package", pkg);

    fetch("/tools/install", {
        method: "POST",
        body: form
    })
        .then(r => r.json())
        .then(data => {
            hideLoading();

            if (data.error) {
                BMSnotify("Gagal install: " + data.error, "error");
                return;
            }

            BMSnotify("Install selesai!", "success");
            loadUpdateLog();
        })
        .catch(() => {
            hideLoading();
            BMSnotify("Koneksi error!", "error");
        });
}


// =============================================
// 🔁 Restart Server (simulasi)
// =============================================
function runRestart() {
    showLoading("Restart server...");

    fetch("/tools/restart")
        .then(r => r.json())
        .then(data => {
            hideLoading();
            BMSnotify("Server restart (simulasi)!", "info");
        })
        .catch(() => {
            hideLoading();
            BMSnotify("Error koneksi!", "error");
        });
}


// =============================================
// ⛔ Shutdown Server (simulasi)
// =============================================
function runShutdown() {
    if (!confirm("Yakin mau shutdown server?")) return;

    showLoading("Shutdown server...");

    fetch("/tools/shutdown")
        .then(r => r.json())
        .then(data => {
            hideLoading();
            BMSnotify("Server shutdown!", "error");
        })
        .catch(() => {
            hideLoading();
            BMSnotify("Error koneksi!", "error");
        });
}


// =============================================
// 📜 Load Log Update
// =============================================
function loadUpdateLog() {

    fetch("/tools/log")
        .then(r => r.json())
        .then(data => {
            let box = document.getElementById("updateLog");
            box.textContent = data.log || "Log kosong.";
            box.scrollTop = box.scrollHeight;
        })
        .catch(() => {
            BMSnotify("Gagal memuat log!", "error");
        });
}


// =============================================
// 🧹 Clear Log
// =============================================
function clearUpdateLog() {

    fetch("/tools/log/clear")
        .then(r => r.json())
        .then(() => {
            BMSnotify("Log dibersihkan!", "info");
            loadUpdateLog();
        });
}


// =============================================
// ⏳ Loader efek
// =============================================
function showLoading(msg = "Loading...") {
    let box = document.getElementById("update-loading");

    if (box) {
        box.style.display = "block";
        box.innerText = msg;
    }
}

function hideLoading() {
    let box = document.getElementById("update-loading");

    if (box) {
        box.style.display = "none";
    }
}