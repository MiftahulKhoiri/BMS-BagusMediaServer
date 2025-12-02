// ===============
//  BMS Home UI FX
// ===============

// Efek klik halus
document.querySelectorAll(".home-item").forEach(item => {
    item.addEventListener("mousedown", () => {
        item.style.transform = "scale(0.94)";
    });
    item.addEventListener("mouseup", () => {
        item.style.transform = "scale(1)";
    });
    item.addEventListener("mouseleave", () => {
        item.style.transform = "scale(1)";
    });
});

// Fade-in keseluruhan home-box
window.addEventListener("DOMContentLoaded", () => {
    const box = document.querySelector(".home-box");
    box.style.opacity = "0";
    box.style.transform = "translateY(20px)";

    setTimeout(() => {
        box.style.transition = "0.8s ease";
        box.style.opacity = "1";
        box.style.transform = "translateY(0)";
    }, 100);
});