function BMSnotify(message, type="info", timeout=3000){

    const box = document.getElementById("bms-notify-box");

    box.className = "";
    box.classList.add(type);
    box.innerText = message;

    box.style.display = "block";
    setTimeout(() => { box.style.opacity = 1; }, 20);

    // Hilang otomatis
    setTimeout(() => {
        box.style.opacity = 0;
        setTimeout(() => { box.style.display = "none"; }, 400);
    }, timeout);
}