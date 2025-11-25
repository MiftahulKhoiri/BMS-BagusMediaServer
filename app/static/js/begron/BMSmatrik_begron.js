const canvas = document.getElementById("matrixCanvas");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const chars = "0101010011101010101010010101010101BAGUSCHOIRI";
const matrix = [];

const fontSize = 14;
const columns = canvas.width / fontSize;

for (let i = 0; i < columns; i++) {
    matrix[i] = 1;
}

function draw() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.06)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#00ff88";
    ctx.font = fontSize + "px monospace";

    for (let i = 0; i < matrix.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(text, i * fontSize, matrix[i] * fontSize);

        if (matrix[i] * fontSize > canvas.height && Math.random() > 0.975) {
            matrix[i] = 0;
        }
        
        matrix[i]++;
    }
}

setInterval(draw, 40);