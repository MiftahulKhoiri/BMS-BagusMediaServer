/**
 * BMS JELLYFISH BACKGROUND ANIMATION
 * Enhanced version - Ukuran diperkecil, pergerakan halus
 */

class Jellyfish {
    constructor(canvas, ctx) {
        this.canvas = canvas;
        this.ctx = ctx;
        
        // ⭐⭐ UKURAN DIPERKECIL: dari 25-60 menjadi 12-30 pixels ⭐⭐
        this.size = 5 + Math.random() * 10; // 12-30 pixels
        
        // POSISI: Random di dalam canvas
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        
        // KECEPATAN: Diperlambat secara signifikan untuk pergerakan lebih halus
        this.speedX = (Math.random() - 0.6) * 0.4;
        this.speedY = (Math.random() - 0.6) * 0.3;
        
        // VARIABEL UNTUK PERGERAKAN YANG LEBIH HALUS
        this.waveOffset = Math.random() * Math.PI * 2;
        this.waveSpeed = 0.002 + Math.random() * 0.002;
        this.waveAmplitude = 0.5 + Math.random() * 1;
        
        // ACCELERATION: Untuk perubahan kecepatan yang gradual
        this.accelerationX = 0;
        this.accelerationY = 0;
        this.maxAcceleration = 0.02;
        this.friction = 0.99;
        
        // OPACITY: Ditingkatkan untuk visibilitas lebih baik
        this.opacity = 0.8 + Math.random() * 0.2;
        
        // WARNA: Lebih terang dan jelas
        this.colors = [
            { r: 0, g: 255, b: 255 },    // Cyan terang
            { r: 255, g: 105, b: 255 },  // Pink neon 
            { r: 100, g: 255, b: 255 },  // Cyan muda
            { r: 255, g: 50, b: 255 },   // Magenta terang
            { r: 0, g: 200, b: 255 }     // Biru terang
        ];
        this.color = this.colors[Math.floor(Math.random() * this.colors.length)];
        
        // PULSE ANIMATION: Efek berdenyut yang lebih halus
        this.pulseSpeed = 0.005 + Math.random() * 0.005;
        this.pulseOffset = Math.random() * Math.PI * 2;
        this.pulseSize = 0.15;
        
        // TARGET MOVEMENT: Untuk pergerakan yang lebih terarah dan halus
        this.targetX = this.x;
        this.targetY = this.y;
        this.changeTargetTimer = 0;
        this.targetChangeInterval = 2000 + Math.random() * 3000;
    }

    update() {
        // UPDATE TARGET POSITION secara berkala
        this.changeTargetTimer += 16;
        if (this.changeTargetTimer > this.targetChangeInterval) {
            this.changeTargetTimer = 0;
            this.setNewTarget();
        }
        
        // GERAKAN MENUJU TARGET dengan easing yang halus
        const dx = this.targetX - this.x;
        const dy = this.targetY - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 5) {
            const easeFactor = 0.005 + (0.01 * (this.size / 30)); // Disesuaikan dengan ukuran baru
            this.speedX += dx * easeFactor;
            this.speedY += dy * easeFactor;
        }
        
        // TERAPKAN GELOMBANG HALUS pada pergerakan
        this.waveOffset += this.waveSpeed;
        const waveInfluence = 0.3;
        this.speedX += Math.sin(this.waveOffset) * waveInfluence * 0.02;
        this.speedY += Math.cos(this.waveOffset * 0.7) * waveInfluence * 0.02;
        
        // LIMIT KECEPATAN MAKSIMUM
        const maxSpeed = 0.8;
        const currentSpeed = Math.sqrt(this.speedX * this.speedX + this.speedY * this.speedY);
        if (currentSpeed > maxSpeed) {
            this.speedX = (this.speedX / currentSpeed) * maxSpeed;
            this.speedY = (this.speedY / currentSpeed) * maxSpeed;
        }
        
        // APLIKASIKAN GESEKAN untuk pergerakan yang lebih natural
        this.speedX *= this.friction;
        this.speedY *= this.friction;
        
        // UPDATE POSISI dengan kecepatan yang sudah disesuaikan
        this.x += this.speedX;
        this.y += this.speedY;
        
        // BOUNDARY CHECK dengan rebound yang halus
        const margin = this.size * 3; // Margin diperbesar karena ukuran jellyfish lebih kecil
        if (this.x < -margin) {
            this.x = this.canvas.width + margin;
            this.setNewTarget();
        }
        if (this.x > this.canvas.width + margin) {
            this.x = -margin;
            this.setNewTarget();
        }
        if (this.y < -margin) {
            this.y = this.canvas.height + margin;
            this.setNewTarget();
        }
        if (this.y > this.canvas.height + margin) {
            this.y = -margin;
            this.setNewTarget();
        }
    }
    
    setNewTarget() {
        const padding = 80; // Padding dikurangi karena jellyfish lebih kecil
        this.targetX = padding + Math.random() * (this.canvas.width - padding * 2);
        this.targetY = padding + Math.random() * (this.canvas.height - padding * 2);
    }

    draw() {
        const ctx = this.ctx;
        const pulse = Math.sin(Date.now() * this.pulseSpeed + this.pulseOffset) * this.pulseSize;
        const currentSize = this.size * (1 + pulse);
        
        // GLOW EFFECT - Diperkuat tapi proporsional dengan ukuran baru
        ctx.save();
        ctx.globalAlpha = this.opacity * 0.7;
        ctx.filter = `blur(12px) brightness(1.3)`; // Blur dikurangi karena ukuran lebih kecil
        ctx.fillStyle = `rgb(${this.color.r}, ${this.color.g}, ${this.color.b})`;
        
        // Draw glow (larger, blurred circle)
        ctx.beginPath();
        ctx.arc(this.x, this.y, currentSize * 1.3, 0, Math.PI * 2); // Glow size dikurangi
        ctx.fill();
        ctx.restore();
        
        // MAIN JELLYFISH BODY
        ctx.save();
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.9)`;
        
        // Draw main body dengan bentuk yang lebih organik
        ctx.beginPath();
        
        const horizontalStretch = 1 + Math.sin(this.waveOffset * 1.3) * 0.1;
        const verticalStretch = 1 + Math.cos(this.waveOffset * 0.9) * 0.1;
        
        ctx.ellipse(
            this.x, 
            this.y, 
            currentSize * horizontalStretch, 
            currentSize * verticalStretch, 
            0, 0, Math.PI * 2
        );
        ctx.fill();
        
        // TENTACLES - Lebih halus dan proporsional dengan ukuran baru
        ctx.strokeStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.7)`;
        ctx.lineWidth = 1.2; // Line width dikurangi
        ctx.lineCap = 'round';
        
        const tentacleCount = 6;
        for (let i = 0; i < tentacleCount; i++) {
            const angle = (i / tentacleCount) * Math.PI * 2;
            const baseLength = currentSize * 0.8;
            const waveLength = currentSize * (0.8 + Math.random() * 0.4);
            
            ctx.beginPath();
            ctx.moveTo(this.x, this.y);
            
            const segments = 3;
            for (let seg = 1; seg <= segments; seg++) {
                const segmentProgress = seg / segments;
                const segX = this.x + Math.cos(angle) * baseLength * segmentProgress;
                const segY = this.y + Math.sin(angle) * baseLength * segmentProgress;
                
                const wave = Math.sin(this.waveOffset * 2 + angle * 2 + seg) * 4 * segmentProgress; // Wave amplitude dikurangi
                const waveX = segX + Math.cos(angle + Math.PI/2) * wave;
                const waveY = segY + Math.sin(angle + Math.PI/2) * wave;
                
                ctx.lineTo(waveX, waveY);
            }
            
            ctx.stroke();
        }
        
        ctx.restore();
    }
}

class JellyfishBackground {
    constructor() {
        this.canvas = document.getElementById('jellyCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.jellyfishes = [];
        
        // ⭐⭐ JUMLAH JELLYFISH: Bisa ditambah karena ukuran lebih kecil ⭐⭐
        this.jellyfishCount = 16; // Ditambah dari 6 menjadi 8
        
        this.lastTime = 0;
        this.deltaTime = 0;
        
        this.init();
    }

    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        for (let i = 0; i < this.jellyfishCount; i++) {
            setTimeout(() => {
                this.jellyfishes.push(new Jellyfish(this.canvas, this.ctx));
            }, i * 500);
        }
        
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        this.jellyfishes.forEach(jellyfish => {
            jellyfish.setNewTarget();
        });
    }

    animate(currentTime = 0) {
        this.deltaTime = currentTime - this.lastTime;
        this.lastTime = currentTime;
        
        this.ctx.fillStyle = 'rgba(10, 10, 42, 0.08)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.jellyfishes.forEach(jellyfish => {
            jellyfish.update();
            jellyfish.draw();
        });
        
        requestAnimationFrame((time) => this.animate(time));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new JellyfishBackground();
});