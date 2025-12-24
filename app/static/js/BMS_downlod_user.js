let timer = null;

function startDownload(type) {
  const url = document.getElementById("url").value;
  if (!url) {
    alert("URL wajib diisi");
    return;
  }

  fetch(`/bms/downlod/${type}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({url})
  })
  .then(res => res.json())
  .then(data => {
    if (!data.task_id) {
      updateProgress("Gagal memulai download");
      return;
    }
    pollProgress(data.task_id);
  });
}

function pollProgress(taskId) {
  clearInterval(timer);
  timer = setInterval(() => {
    fetch(`/bms/downlod/progress/${taskId}`)
      .then(res => res.json())
      .then(data => {
        updateProgress(`Status: ${data.status} ${data.progress || ""}`);
        if (data.status === "finished") {
          clearInterval(timer);
        }
      });
  }, 1000);
}

function updateProgress(text) {
  document.getElementById("progress").innerText = text;
}