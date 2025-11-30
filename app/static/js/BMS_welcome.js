/* ==========================================
   BMS WELCOME PAGE — LIGHT JS
   (Fade-in animasi & smooth UI)
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    const box = document.querySelector(".welcome-container");

    // Animasi fade-in halus
    box.style.opacity = "0";
    box.style.transform = "translateY(20px)";
    setTimeout(() => {
        box.style.transition = "0.9s ease";
        box.style.opacity = "1";
        box.style.transform = "translateY(0)";
    }, 150);

});