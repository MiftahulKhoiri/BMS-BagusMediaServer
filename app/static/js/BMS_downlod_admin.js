function loadHistory() {
  fetch("/bms/downlod/history")
    .then(res => res.json())
    .then(data => {
      const tbody = document.querySelector("#table tbody");
      tbody.innerHTML = "";

      data.data.forEach(item => {
        tbody.innerHTML += `
          <tr>
            <td>${item.id}</td>
            <td>${item.tipe}</td>
            <td>${item.title}</td>
            <td>${item.file_path}</td>
            <td>
              <button onclick="hapus(${item.id})">Hapus</button>
            </td>
          </tr>
        `;
      });
    });
}

function hapus(id) {
  if (!confirm("Yakin hapus data ini?")) return;

  fetch(`/bms/downlod/delete/${id}`, {method: "DELETE"})
    .then(() => loadHistory());
}

loadHistory();