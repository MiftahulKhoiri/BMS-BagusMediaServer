// MATRIX BACKGROUND
const canvas = document.getElementById("matrixCanvas");
const ctx = canvas.getContext("2d");

canvas.height = window.innerHeight;
canvas.width = window.innerWidth;

const letters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const fontSize = 16;
const columns = canvas.width / fontSize;

let drops = [];
for (let i = 0; i < columns; i++) {
    drops[i] = 1;
}

function draw() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#00ff99";
    ctx.font = fontSize + "px monospace";

    for (let i = 0; i < drops.length; i++) {
        let text = letters[Math.floor(Math.random() * letters.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.95) {
            drops[i] = 0;
        }

        drops[i]++;
    }
}

setInterval(draw, 40);

// Resize support
window.onresize = () => {
    canvas.height = window.innerHeight;
    canvas.width = window.innerWidth;
};