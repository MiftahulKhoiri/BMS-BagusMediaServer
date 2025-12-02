// =======================================
//   BMS SYSTEM INFO REALTIME
// =======================================

let sysRefreshRate = 2000; // ms

document.addEventListener("DOMContentLoaded", () => {
    loadSystemInfo();
    setInterval(loadSystemInfo, sysRefreshRate);
});


// =======================================
// 🔄 Load data dari server
// =======================================
function loadSystemInfo() {

    fetch("/system/info")
        .then(r => r.json())
        .then(data => {

            // CPU
            document.getElementById("cpu-usage").innerText = data.cpu + "%";

            // RAM
            document.getElementById("ram-total").innerText = data.ram_total + " MB";
            document.getElementById("ram-used").innerText = data.ram_used + " MB";
            document.getElementById("ram-free").innerText = data.ram_free + " MB";

            // Storage
            document.getElementById("disk-total").innerText = data.disk_total + " GB";
            document.getElementById("disk-used").innerText = data.disk_used + " GB";
            document.getElementById("disk-free").innerText = data.disk_free + " GB";

            // System info
            document.getElementById("sys-os").innerText = data.os;
            document.getElementById("sys-python").innerText = data.python;
            document.getElementById("sys-uptime").innerText = data.uptime;

            // Warna CPU alarm
            updateCPUAlert(data.cpu);
        })
        .catch(() => {
            console.log("Error mengambil system info!");
        });
}


// =======================================
// 🚨 Warna CPU jika tinggi
// =======================================
function updateCPUAlert(cpu) {
    let cpuBox = document.getElementById("cpu-box");

    if (cpu >= 80) {
        cpuBox.style.color = "#ff5555";      // merah
        cpuBox.style.textShadow = "0 0 10px #ff0000";
    } else if (cpu >= 50) {
        cpuBox.style.color = "#ffaa00";      // kuning
        cpuBox.style.textShadow = "0 0 5px #ffaa00";
    } else {
        cpuBox.style.color = "#00ff88";      // hijau
        cpuBox.style.textShadow = "none";
    }
}