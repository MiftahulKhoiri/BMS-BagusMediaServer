// jellyfish_neon.js
(function () {
  const canvas = document.getElementById("jellyCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d", { alpha: true });

  let DPR = Math.max(1, window.devicePixelRatio || 1);

  function resize() {
    DPR = Math.max(1, window.devicePixelRatio || 1);
    canvas.width = canvas.clientWidth * DPR;
    canvas.height = canvas.clientHeight * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }

  resize();
  window.addEventListener("resize", resize);

  // ====== CONFIG ======
  const MAX_JELLY = 6;
  const COLORS = ["#6be6ff", "#8b8bff", "#ff7bd1", "#6bffb0", "#ffd36b"];

  const BASE_SPEED = 0.018;
  const STEER = 0.000045;
  const DAMP = 0.9997;

  const rand = (a, b) => a + Math.random() * (b - a);
  const choose = (arr) => arr[Math.floor(Math.random() * arr.length)];

  // ====== JELLYFISH CLASS ======
  class Jelly {
    constructor() {
      this.reset();
    }

    reset() {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;

      this.r = rand(35, 85);
      this.x = rand(this.r, w - this.r);
      this.y = rand(this.r, h - this.r);
      this.vx = rand(-0.02, 0.02);
      this.vy = rand(-0.02, 0.02);

      this.color = choose(COLORS);
      this.targetTime = Date.now() + rand(2500, 7000);
      this.targetX = this.x + rand(-120, 120);
      this.targetY = this.y + rand(-120, 120);

      this.phase = Math.random() * Math.PI * 2;
      this.pulseSpeed = rand(0.0009, 0.0020);
      this.tentacles = Math.floor(rand(4, 8));
    }

    update(dt) {
      if (Date.now() > this.targetTime) {
        this.targetTime = Date.now() + rand(3000, 9000);
        this.targetX = this.x + rand(-150, 150);
        this.targetY = this.y + rand(-150, 150);
      }

      // steering (super lembut)
      let sx = (this.targetX - this.x) * STEER * dt;
      let sy = (this.targetY - this.y) * STEER * dt;
      this.vx += sx;
      this.vy += sy;

      // random kecil biar natural
      this.vx += rand(-0.00002, 0.00002) * dt;
      this.vy += rand(-0.00002, 0.00002) * dt;

      // limit speed
      const speed = Math.hypot(this.vx, this.vy);
      const max = BASE_SPEED * (this.r / 60);
      if (speed > max) {
        this.vx *= max / speed;
        this.vy *= max / speed;
      }

      // apply velocity
      this.x += this.vx * dt;
      this.y += this.vy * dt;

      this.vx *= DAMP;
      this.vy *= DAMP;

      // borders
      if (this.x < this.r) this.x = this.r;
      if (this.x > canvas.clientWidth - this.r)
        this.x = canvas.clientWidth - this.r;
      if (this.y < this.r) this.y = this.r;
      if (this.y > canvas.clientHeight - this.r)
        this.y = canvas.clientHeight - this.r;

      this.phase += dt * this.pulseSpeed;
    }

    draw(ctx) {
      const pulse = 1 + Math.sin(this.phase) * 0.07;
      const R = this.r * pulse;

      ctx.save();
      ctx.globalCompositeOperation = "lighter";

      // glow outer
      ctx.globalAlpha = 0.18;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = 40;
      ctx.beginPath();
      ctx.ellipse(this.x, this.y, R * 1.7, R, 0, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();

      // bell inner
      ctx.globalAlpha = 0.32;
      const g = ctx.createRadialGradient(
        this.x,
        this.y - R * 0.15,
        R * 0.2,
        this.x,
        this.y,
        R
      );
      g.addColorStop(0, this.color);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.ellipse(this.x, this.y, R * 1.05, R * 0.75, 0, 0, Math.PI * 2);
      ctx.fill();

      // core bright
      ctx.globalAlpha = 0.95;
      ctx.shadowBlur = 10;
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.arc(this.x, this.y - R * 0.15, R * 0.35, 0, Math.PI * 2);
      ctx.fill();

      // tentacles
      for (let i = 0; i < this.tentacles; i++) {
        const ang =
          -Math.PI / 2 +
          (i - this.tentacles / 2) * 0.3 +
          Math.sin(this.phase * 0.6) * 0.15;
        const len = R * rand(0.8, 1.6);

        const x1 = this.x + Math.cos(ang) * (R * 0.4);
        const y1 = this.y + Math.sin(ang) * (R * 0.4);

        const x2 = x1 + Math.cos(ang + 0.3) * len * 0.4;
        const y2 = y1 + Math.sin(ang + 0.3) * len * 0.4;

        const x3 = x1 + Math.cos(ang + 0.5) * len;
        const y3 = y1 + Math.sin(ang + 0.5) * len;

        ctx.globalAlpha = 0.25;
        ctx.strokeStyle = this.color;
        ctx.lineWidth = Math.max(1, R * 0.04);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.bezierCurveTo(x2, y2, x2, y2, x3, y3);
        ctx.stroke();
      }

      ctx.restore();
    }
  }

  // build jellies
  let j = [];
  for (let i = 0; i < MAX_JELLY; i++) j.push(new Jelly());

  let last = performance.now();
  function loop(now) {
    const dt = Math.min(40, now - last);
    last = now;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(0,0,0,0.12)";
    ctx.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);

    for (let jelly of j) {
      jelly.update(dt);
      jelly.draw(ctx);
    }

    requestAnimationFrame(loop);
  }

  requestAnimationFrame(loop);
})();