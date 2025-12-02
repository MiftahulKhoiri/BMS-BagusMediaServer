document.addEventListener("DOMContentLoaded", () => {
    const cpuBar = document.getElementById("cpuBar");
    const ramBar = document.getElementById("ramBar");
    const diskBar = document.getElementById("diskBar");

    const cpuLabel = document.getElementById("cpuLabel");
    const ramLabel = document.getElementById("ramLabel");
    const diskLabel = document.getElementById("diskLabel");

    const osInfo = document.getElementById("osInfo");
    const pythonInfo = document.getElementById("pythonInfo");
    const bootInfo = document.getElementById("bootInfo");
    const uptimeInfo = document.getElementById("uptimeInfo");

    const infoCpu = document.getElementById("infoCpu");
    const infoRam = document.getElementById("infoRam");
    const infoDisk = document.getElementById("infoDisk");
    const infoUptime = document.getElementById("infoUptime");
    const infoLastUpdate = document.getElementById("infoLastUpdate");

    const refreshBtn = document.getElementById("refreshBtn");

    function fetchSystemInfo() {
        fetch("/system/info")
            .then(res => res.json())
            .then(data => {
                // CPU
                const cpuUsage = data.cpu_usage ?? data.cpu ?? 0;
                cpuBar.style.width = `${cpuUsage}%`;
                cpuLabel.textContent = `${cpuUsage}%`;

                // RAM
                const ramTotal = data.ram_total || 0;
                const ramUsed = data.ram_used || 0;
                const ramPercent = ramTotal ? Math.round((ramUsed / ramTotal) * 100) : 0;

                ramBar.style.width = `${ramPercent}%`;
                ramLabel.textContent = `${ramUsed} / ${ramTotal} GB (${ramPercent}%)`;

                // Disk
                const diskTotal = data.disk_total || 0;
                const diskUsed = data.disk_used || 0;
                const diskPercent = diskTotal ? Math.round((diskUsed / diskTotal) * 100) : 0;

                diskBar.style.width = `${diskPercent}%`;
                diskLabel.textContent = `${diskUsed} / ${diskTotal} GB (${diskPercent}%)`;

                // Top badges
                osInfo.textContent = `OS: ${data.os || "-"}`;
                pythonInfo.textContent = `Python: ${data.python || "-"}`;
                bootInfo.textContent = `Boot: ${data.boot_time || "-"}`;
                uptimeInfo.textContent = `Uptime: ${data.uptime_hours || 0} jam`;

                // Detail info
                infoCpu.textContent = `CPU: ${cpuUsage}%`;
                infoRam.textContent = `RAM: ${ramUsed} / ${ramTotal} GB`;
                infoDisk.textContent = `Disk: ${diskUsed} / ${diskTotal} GB`;
                infoUptime.textContent = `Uptime: ${data.uptime_hours || 0} jam`;

                const now = new Date();
                infoLastUpdate.textContent = `Last update: ${now.toLocaleTimeString()}`;
            })
            .catch(err => {
                infoLastUpdate.textContent = `Error fetch: ${err}`;
            });
    }

    // first load
    fetchSystemInfo();

    // manual refresh
    refreshBtn.addEventListener("click", fetchSystemInfo);

    // auto refresh setiap 5 detik
    setInterval(fetchSystemInfo, 5000);
});