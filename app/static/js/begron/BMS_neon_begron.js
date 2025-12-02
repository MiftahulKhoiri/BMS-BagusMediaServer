// Membuat canvas untuk efek neon
const canvas = document.createElement("canvas");
canvas.id = "neonCanvas";
document.body.appendChild(canvas);

const ctx = canvas.getContext("2d");

// Resize canvas agar full layar
function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resize();
window.addEventListener("resize", resize);

// Daftar warna neon cerah
const neonColors = [
    "#ff00ff", "#ff33cc", "#ff0099",
    "#00ffff", "#33ccff", "#0099ff",
    "#39FF14", "#66ff66", "#00ff99",
    "#ffaa00", "#ff4444", "#ff0066"
];

// Pilih warna neon acak yang halus
function randomColor() {
    return neonColors[Math.floor(Math.random() * neonColors.length)];
}

// Membuat titik-titik neon
const particles = [];

for (let i = 0; i < 80; i++) {
    particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,

        // TITIK LEBIH BESAR di sini
        size: Math.random() * 4 + 2, // ukuran 2px - 6px

        color: randomColor(),
        alpha: Math.random(),

        // gerakan lembut
        speedX: (Math.random() - 0.5) * 0.6,
        speedY: (Math.random() - 0.5) * 0.6,

        // kedip lembut
        blinkSpeed: Math.random() * 0.02 + 0.005,

        // warna berganti otomatis
        colorTimer: Math.random() * 200 + 100
    });
}

// Animasi utama
function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {

        // Ubah warna otomatis
        p.colorTimer--;
        if (p.colorTimer <= 0) {
            p.color = randomColor();
            p.colorTimer = Math.random() * 200 + 100;
        }

        // Gerakan lembut acak
        p.x += p.speedX;
        p.y += p.speedY;

        if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
        if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;

        // Kedipan halus
        p.alpha += p.blinkSpeed;
        if (p.alpha <= 0.3 || p.alpha >= 1) {
            p.blinkSpeed *= -1;
        }

        // Gambar titik neon besar
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 25;   // glow sedikit ditambah biar sesuai ukuran

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
    });

    requestAnimationFrame(animate);
}

animate();