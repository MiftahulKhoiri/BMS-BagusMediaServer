const $ = id => document.getElementById(id)

const statusText = $('statusText')
const statusIcon = $('statusIcon')
const progressBar = $('progressBar')
const progressLabel = $('progressLabel')
const currentVersion = $('currentVersion')
const onlineVersion = $('onlineVersion')
const logbox = $('logbox')

function setBusy(on, msg){
  statusIcon.style.display = on ? "inline-block" : "none"
  statusText.textContent = "Status: " + (msg || "Siap")
}

function setProgress(val, txt){
  progressBar.style.width = val + "%"
  progressLabel.textContent = txt || ""
}

async function checkUpdate(){
  setBusy(true, "Memeriksa update...")
  setProgress(30, "Menghubungi server...")

  try{
    const res = await fetch("/update/check")
    const j = await res.json()

    currentVersion.textContent = j.current
    onlineVersion.textContent = j.online

    setProgress(100, j.update_available ? "Update tersedia!" : "Sudah terbaru")
    setBusy(false, j.update_available ? "Update tersedia" : "Sudah terbaru")
  }
  catch(err){
    setBusy(false, "Gagal cek update")
    log("[Error] " + err)
  }
}

async function doUpdate(){
  if(!confirm("Yakin menjalankan update? Backup otomatis dibuat.")) return

  setBusy(true, "Menjalankan update...")
  setProgress(10, "Membuat backup...")

  try{
    const res = await fetch("/update/do")
    const j = await res.json()

    log("[Sukses] " + j.msg)
    setProgress(100, "Update selesai")
    setBusy(false, "Update selesai")

    fetchLogs()
  }
  catch(err){
    log("[Error] "+err)
    setBusy(false, "Gagal update")
  }
}

async function fetchLogs(){
  setBusy(true, "Memuat log...")

  try{
    const res = await fetch("/update/logs")
    const j = await res.json()

    logbox.textContent = j.log || "(Log kosong)"
    setBusy(false, "Log dimuat")
  }
  catch(err){
    log("[Error] " + err)
    setBusy(false, "Gagal memuat log")
  }
}

function log(text){
  const now = new Date().toLocaleString()
  logbox.textContent = `${now} — ${text}\n` + logbox.textContent
}

// Events
$('btnCheck').onclick = checkUpdate
$('btnDo').onclick = doUpdate
$('btnLogs').onclick = fetchLogs
$('btnClearLog').onclick = () => logbox.textContent = ""

// Auto load
checkUpdate()