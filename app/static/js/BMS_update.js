document.addEventListener("DOMContentLoaded", () => {

    const checkBtn = document.getElementById("checkBtn");
    const updateBtn = document.getElementById("updateBtn");
    const commitList = document.getElementById("commitList");
    const checkResult = document.getElementById("checkResult");
    const updateStatus = document.getElementById("updateStatus");

    loadCommitList(); // tampilkan commit terbaru saat UI dibuka


    // ================================
    //  LOAD COMMIT TERBARU
    // ================================
    function loadCommitList() {
        fetch("/update/latest-commits")
            .then(res => res.json())
            .then(data => {
                commitList.innerHTML = "";

                if (!data.commits) {
                    commitList.innerHTML = "<p>Gagal memuat commit.</p>";
                    return;
                }

                data.commits.forEach(c => {
                    commitList.innerHTML += `
                        <div class="commit-item">
                            <div class="commit-hash">🔗 ${c.hash}</div>
                            <div class="commit-msg">${c.message}</div>
                            <div class="commit-time">${c.time}</div>
                        </div>
                    `;
                });
            });
    }


    // ================================
    //  CEK UPDATE
    // ================================
    checkBtn.addEventListener("click", () => {
        checkResult.innerHTML = "<p>⏳ Memeriksa pembaruan...</p>";

        fetch("/update/check-api")
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    checkResult.innerHTML = `<p style="color:red;">Gagal: ${data.error}</p>`;
                    return;
                }

                if (data.update_available) {
                    checkResult.innerHTML = `
                        <p style="color:#00ff9d;">
                            ✔ Update tersedia!<br>
                            Commit baru: ${data.remote_commit}<br>
                            Pesan: ${data.remote_message}
                        </p>
                    `;
                    updateBtn.disabled = false;
                } else {
                    checkResult.innerHTML = `
                        <p style="color:#fff;">
                            ✔ Perangkat lunak sudah versi terbaru.
                        </p>`;
                    updateBtn.disabled = true;
                }
            });
    });


    // ================================
    //  UPDATE SYSTEM (download → apply)
    // ================================
    updateBtn.addEventListener("click", () => {
        if (!confirm("Yakin download dan menerapkan update?")) return;

        updateStatus.innerHTML = "⏳ Mendownload update...\n";

        fetch("/update/start-download")
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    updateStatus.innerHTML += "❌ Gagal download ZIP\n";
                    return;
                }

                updateStatus.innerHTML += "✔ Download selesai!\n";
                updateStatus.innerHTML += "⏳ Menerapkan update...\n";

                return fetch("/update/apply-update");
            })
            .then(res => res.json())
            .then(result => {
                if (!result.success) {
                    updateStatus.innerHTML += `❌ Gagal pada tahap ${result.step}\nError: ${result.error}`;
                    return;
                }

                updateStatus.innerHTML += `✔ Update selesai!\nCommit baru: ${result.new_commit}\n`;
                updateStatus.innerHTML += "\n🔄 Silakan restart server jika tidak otomatis.";
            });
    });

});