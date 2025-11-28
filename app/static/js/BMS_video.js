(function () {

    const player = document.getElementById("mainPlayer");
    const playPauseBtn = document.getElementById("playPauseBtn");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const progress = document.getElementById("progress");
    const timeLabel = document.querySelector(".time");
    const volume = document.getElementById("volume");
    const fsBtn = document.getElementById("fsBtn");
    const search = document.getElementById("videoSearch");
    const playlistItems = Array.from(document.querySelectorAll(".playlist-item"));

    let current = 0;

    function formatTime(sec) {
        if (isNaN(sec)) return "0:00";
        let m = Math.floor(sec / 60);
        let s = Math.floor(sec % 60).toString().padStart(2, "0");
        return `${m}:${s}`;
    }

    function loadVideo(index) {
        if (index < 0) index = playlistItems.length - 1;
        if (index >= playlistItems.length) index = 0;
        current = index;

        const item = playlistItems[current];
        playlistItems.forEach(i => i.classList.remove("active"));
        item.classList.add("active");

        player.src = item.dataset.src;
        player.setAttribute("poster", item.dataset.poster || "");
        player.play().catch(()=>{});
        updateButton();
    }

    playPauseBtn.addEventListener("click", () => {
        if (player.paused) player.play();
        else player.pause();
        updateButton();
    });

    prevBtn.addEventListener("click", () => loadVideo(current - 1));
    nextBtn.addEventListener("click", () => loadVideo(current + 1));

    playlistItems.forEach((item, index) => {
        item.addEventListener("click", () => loadVideo(index));
    });

    function updateButton() {
        playPauseBtn.textContent = player.paused ? "▶️" : "⏸";
    }

    player.addEventListener("timeupdate", () => {
        if (!player.duration) return;
        progress.value = (player.currentTime / player.duration) * 100;
        timeLabel.textContent = `${formatTime(player.currentTime)} / ${formatTime(player.duration)}`;
    });

    progress.addEventListener("input", (e) => {
        if (!player.duration) return;
        player.currentTime = (e.target.value / 100) * player.duration;
    });

    player.addEventListener("ended", () => loadVideo(current + 1));

    volume.addEventListener("input", () => {
        player.volume = volume.value;
    });

    fsBtn.addEventListener("click", () => {
        if (!document.fullscreenElement) player.requestFullscreen();
        else document.exitFullscreen();
    });

    search.addEventListener("input", () => {
        const q = search.value.toLowerCase();
        playlistItems.forEach(item => {
            const title = item.querySelector(".title").textContent.toLowerCase();
            item.style.display = title.includes(q) ? "" : "none";
        });
    });

    // Load video pertama saat halaman dibuka
    if (playlistItems.length > 0) loadVideo(0);

})();