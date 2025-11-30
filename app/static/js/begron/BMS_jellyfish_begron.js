/**
 * BMS JELLYFISH BACKGROUND ANIMATION
 * Enhanced version - Warna lebih terang, jumlah dikurangi
 */

class Jellyfish {
    constructor(canvas, ctx) {
        this.canvas = canvas;
        this.ctx = ctx;
        
        // UKURAN: Diperkecil dari versi sebelumnya
        this.size = 25 + Math.random() * 35; // 25-60 pixels (sebelumnya 30-70)
        
        // POSISI: Random di dalam canvas
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        
        // KECEPATAN: Gerakan lebih lambat dan natural
        this.speedX = (Math.random() - 0.5) * 0.8;
        this.speedY = (Math.random() - 0.5) * 0.6;
        
        // OPACITY: Ditingkatkan untuk visibilitas lebih baik
        this.opacity = 0.8 + Math.random() * 0.2; // 0.8-1.0 (sebelumnya 0.7-1.0)
        
        // WARNA: Lebih terang dan jelas
        this.colors = [
            { r: 0, g: 255, b: 255 },    // Cyan terang
            { r: 255, g: 105, b: 255 },  // Pink neon 
            { r: 100, g: 255, b: 255 },  // Cyan muda
            { r: 255, g: 50, b: 255 },   // Magenta terang
            { r: 0, g: 200, b: 255 }     // Biru terang
        ];
        this.color = this.colors[Math.floor(Math.random() * this.colors.length)];
        
        // PULSE ANIMATION: Efek berdenyut
        this.pulseSpeed = 0.01 + Math.random() * 0.02;
        this.pulseOffset = Math.random() * Math.PI * 2;
        this.pulseSize = 0.2; // 20% variation in size
    }

    update() {
        // Update position dengan gerakan natural
        this.x += this.speedX;
        this.y += this.speedY;
        
        // Boundary check - muncul di sisi lain jika keluar canvas
        if (this.x < -this.size) this.x = this.canvas.width + this.size;
        if (this.x > this.canvas.width + this.size) this.x = -this.size;
        if (this.y < -this.size) this.y = this.canvas.height + this.size;
        if (this.y > this.canvas.height + this.size) this.y = -this.size;
        
        // Subtle floating movement
        this.speedX += (Math.random() - 0.5) * 0.05;
        this.speedY += (Math.random() - 0.5) * 0.03;
        
        // Limit speed
        this.speedX = Math.max(Math.min(this.speedX, 1), -1);
        this.speedY = Math.max(Math.min(this.speedY, 1), -1);
    }

    draw() {
        const ctx = this.ctx;
        const pulse = Math.sin(Date.now() * this.pulseSpeed + this.pulseOffset) * this.pulseSize;
        const currentSize = this.size * (1 + pulse);
        
        // GLOW EFFECT - Diperkuat
        ctx.save();
        ctx.globalAlpha = this.opacity * 0.7;
        ctx.filter = `blur(15px) brightness(1.3)`;
        ctx.fillStyle = `rgb(${this.color.r}, ${this.color.g}, ${this.color.b})`;
        
        // Draw glow (larger, blurred circle)
        ctx.beginPath();
        ctx.arc(this.x, this.y, currentSize * 1.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
        
        // MAIN JELLYFISH BODY
        ctx.save();
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.9)`;
        
        // Draw main body
        ctx.beginPath();
        ctx.arc(this.x, this.y, currentSize, 0, Math.PI * 2);
        ctx.fill();
        
        // TENTACLES - Simple representation
        ctx.strokeStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.7)`;
        ctx.lineWidth = 2;
        
        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            const tentacleLength = currentSize * (1.2 + Math.random() * 0.5);
            const endX = this.x + Math.cos(angle) * tentacleLength;
            const endY = this.y + Math.sin(angle) * tentacleLength;
            
            ctx.beginPath();
            ctx.moveTo(this.x, this.y);
            ctx.lineTo(endX, endY);
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
        
        // JUMLAH JELLYFISH: Dikurangi dari versi asli
        this.jellyfishCount = 6; // Hanya 6 jellyfish (biasanya 8-12)
        
        this.init();
    }

    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        // Create jellyfishes
        for (let i = 0; i < this.jellyfishCount; i++) {
            // Stagger creation for performance
            setTimeout(() => {
                this.jellyfishes.push(new Jellyfish(this.canvas, this.ctx));
            }, i * 300);
        }
        
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    animate() {
        // Clear canvas dengan background semi-transparent untuk trail effect
        this.ctx.fillStyle = 'rgba(10, 10, 42, 0.1)'; // Dark blue dengan sedikit transparency
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw all jellyfishes
        this.jellyfishes.forEach(jellyfish => {
            jellyfish.update();
            jellyfish.draw();
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new JellyfishBackground();
});

// Handle page visibility changes untuk optimasi performance
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Reduce animation speed when tab is not visible
        // Implementation can be added if needed
    }
});