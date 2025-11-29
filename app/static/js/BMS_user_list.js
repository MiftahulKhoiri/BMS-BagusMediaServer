async function loadUsers() {
    const res = await fetch("/admin/users/list");
    const data = await res.json();

    const tbody = document.getElementById("userBody");
    tbody.innerHTML = "";

    data.users.forEach(u => {
        tbody.innerHTML += `
            <tr>
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td>
                    <select class="role-select" onchange="updateRole(${u.id}, this.value)">
                        <option value="root" ${u.role === "root" ? "selected" : ""}>Root</option>
                        <option value="admin" ${u.role === "admin" ? "selected" : ""}>Admin</option>
                        <option value="user" ${u.role === "user" ? "selected" : ""}>User</option>
                    </select>
                </td>
                <td>
                    <button class="btn-delete" onclick="deleteUser(${u.id})">Hapus</button>
                </td>
            </tr>
        `;
    });
}

async function updateRole(id, role) {
    const res = await fetch("/admin/users/update-role", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ id, role })
    });

    const data = await res.json();
    notif(data.message, data.status);
}

async function deleteUser(id) {
    if (!confirm("Yakin hapus user beserta semua datanya?")) return;

    const res = await fetch("/admin/users/delete", {
        method: "DELETE",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ id })
    });

    const data = await res.json();
    notif(data.message, data.status);

    loadUsers();
}

function notif(msg, status) {
    const box = document.getElementById("notif");
    box.style.display = "block";
    box.innerHTML = msg;
    box.style.background = status === "success" ? "#2ea043" : "#d33";
}

loadUsers();