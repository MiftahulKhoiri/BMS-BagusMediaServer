function shutdownServer() {
    if (!confirm("Yakin mau MEMATIKAN server Flask?")) return;

    fetch("/api/shutdown", { method: "POST" })
        .then(() => alert("Server dimatikan!"))
        .catch(() => alert("Gagal shutdown"));
}

function restartServer() {
    if (!confirm("Restart server Flask sekarang?")) return;

    fetch("/api/restart", { method: "POST" })
        .then(() => location.reload())
        .catch(() => alert("Gagal restart"));
}

function changeRole(id, role) {
    fetch(`/admin/user/role/${id}/${role}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            alert(data.message || "Role diubah!");
            location.reload();
        });
}

function deleteUser(id) {
    if (!confirm("Hapus user ini?")) return;

    fetch(`/admin/user/delete/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            alert(data.message || "User dihapus!");
            location.reload();
        });
}

function deleteUser(id) {
    if (confirm("Hapus user ini?")) {
        window.location.href = "/admin/delete/" + id;
    }
}


function shutdownServer() {
    fetch('/server/shutdown', {method: 'POST'})
    .then(r => r.json())
    .then(d => alert(d.message));
}

function restartServer() {
    fetch('/server/restart', {method: 'POST'})
    .then(r => r.json())
    .then(d => alert(d.message));
}