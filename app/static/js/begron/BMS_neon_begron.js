/**
 * neon.js
 * Soft random-moving neon blobs on a fullscreen canvas.
 * - Circles are medium size (not too big / not too small)
 * - Move smoothly with gentle velocity and easing
 * - Color palette rotates every 30 seconds
 *
 * Usage: include <canvas id="neonBackground"></canvas> in HTML,
 * and load this file after the canvas.
 */

(() => {
  const canvas = document.getElementById('neonBackground');
  if (!canvas) return;
  const ctx = canvas.getContext('2d', { alpha: true });

  let DPR = Math.max(1, window.devicePixelRatio || 1);

  function resize() {
    DPR = Math.max(1, window.devicePixelRatio || 1);
    canvas.width = Math.floor(canvas.clientWidth * DPR);
    canvas.height = Math.floor(canvas.clientHeight * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener('resize', resize, { passive: true });
  resize();

  // --- CONFIG ---
  const NUM_BLOBS = Math.max(6, Math.floor(Math.min(window.innerWidth, 900) / 130));
  const MIN_RADIUS = 20;
  const MAX_RADIUS = 48;
  const MAX_SPEED = 0.50; // px per ms (small for smoothness)
  const COLOR_SETS = [
    ['#33fff6', '#00ff99', '#88ffdd'],
    ['#ff6bcb', '#ffb86b', '#ffd36b'],
    ['#8bff6b', '#4dffb4', '#6fffd4'],
    ['#6b8bff', '#6bdcff', '#a3b6ff'],
    ['#ff6b6b', '#ff8bdb', '#ffd6a6']
  ];
  let paletteIndex = 0;
  let currentPalette = COLOR_SETS[paletteIndex];

  // change palette every 30 seconds
  const PALETTE_INTERVAL = 30_000;
  setInterval(() => {
    paletteIndex = (paletteIndex + 1) % COLOR_SETS.length;
    currentPalette = COLOR_SETS[paletteIndex];
  }, PALETTE_INTERVAL);

  // Utility: random helpers
  const rand = (a, b) => a + Math.random() * (b - a);
  const choose = (arr) => arr[Math.floor(Math.random() * arr.length)];

  // Blob object
  class Blob {
    constructor(i) {
      this.reset(i);
    }

    reset(i) {
      // Place blobs across the canvas with padding
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      this.r = rand(MIN_RADIUS, MAX_RADIUS);
      this.x = rand(this.r, w - this.r);
      this.y = rand(this.r, h - this.r);
      // give small random velocities
      const angle = Math.random() * Math.PI * 2;
      const speed = rand(0.03, MAX_SPEED); // px per ms
      this.vx = Math.cos(angle) * speed;
      this.vy = Math.sin(angle) * speed;
      // color
      this.color = choose(currentPalette);
      // soft target movement to produce gentle wandering
      this.targetTime = Date.now() + rand(2000, 7000);
      this.targetX = this.x + rand(-60, 60);
      this.targetY = this.y + rand(-60, 60);
      // subtle phase for pulsation
      this.phase = Math.random() * Math.PI * 2;
    }

    update(dt) {
      // Occasionally pick a new small target
      if (Date.now() > this.targetTime) {
        this.targetTime = Date.now() + rand(2000, 8000);
        this.targetX = Math.min(Math.max(this.r, this.x + rand(-120, 120)), canvas.clientWidth - this.r);
        this.targetY = Math.min(Math.max(this.r, this.y + rand(-120, 120)), canvas.clientHeight - this.r);
      }

      // Steer towards target gently
      const steerX = (this.targetX - this.x) * 0.0006 * dt;
      const steerY = (this.targetY - this.y) * 0.0006 * dt;
      this.vx += steerX;
      this.vy += steerY;

      // apply velocity
      this.x += this.vx * dt;
      this.y += this.vy * dt;

      // slight damping
      this.vx *= 0.995;
      this.vy *= 0.995;

      // keep inside with soft rebound
      if (this.x < this.r) { this.x = this.r; this.vx = Math.abs(this.vx) * 0.3; }
      if (this.x > canvas.clientWidth - this.r) { this.x = canvas.clientWidth - this.r; this.vx = -Math.abs(this.vx) * 0.3; }
      if (this.y < this.r) { this.y = this.r; this.vy = Math.abs(this.vy) * 0.3; }
      if (this.y > canvas.clientHeight - this.r) { this.y = canvas.clientHeight - this.r; this.vy = -Math.abs(this.vy) * 0.3; }

      // pulsation phase
      this.phase += dt * 0.002;
    }

    draw(ctx) {
      // gentle pulsation in size
      const pulse = 1 + Math.sin(this.phase) * 0.06;
      const radius = this.r * pulse;

      // glow
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';

      // outer blur
      ctx.beginPath();
      ctx.fillStyle = this.color;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = Math.max(20, Math.min(80, radius * 0.8));
      ctx.globalAlpha = 0.18;
      ctx.arc(this.x, this.y, radius * 1.9, 0, Math.PI * 2);
      ctx.fill();

      // mid glow
      ctx.beginPath();
      ctx.globalAlpha = 0.28;
      ctx.arc(this.x, this.y, radius * 1.2, 0, Math.PI * 2);
      ctx.fill();

      // core
      ctx.beginPath();
      ctx.globalAlpha = 0.95;
      ctx.shadowBlur = 10;
      ctx.arc(this.x, this.y, radius * 0.6, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      ctx.restore();
    }
  }

  // create blobs
  let blobs = [];
  function rebuildBlobs() {
    blobs = [];
    for (let i = 0; i < NUM_BLOBS; i++) {
      blobs.push(new Blob(i));
    }
  }
  rebuildBlobs();

  // update colors gradually when palette changes
  function refreshPalette() {
    for (let b of blobs) {
      b.color = choose(currentPalette);
    }
  }
  // watch color change by timing (same as setInterval earlier)
  let lastPaletteChange = Date.now();
  setInterval(() => {
    refreshPalette();
    lastPaletteChange = Date.now();
  }, PALETTE_INTERVAL);

  // animation loop
  let last = performance.now();
  function loop(now) {
    const dt = Math.min(40, now - last); // cap dt for stability (ms)
    last = now;

    // clear with slight alpha to create trailing
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(0,0,0,0.12)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // draw blobs
    for (let b of blobs) {
      b.update(dt);
      b.draw(ctx);
    }

    // subtle moving vignette gradient
    const g = ctx.createRadialGradient(
      canvas.clientWidth * 0.5, canvas.clientHeight * 0.4, canvas.clientWidth * 0.05,
      canvas.clientWidth * 0.5, canvas.clientHeight * 0.5, Math.max(canvas.clientWidth, canvas.clientHeight) * 0.9
    );
    g.addColorStop(0, 'rgba(0,0,0,0.00)');
    g.addColorStop(1, 'rgba(0,0,0,0.35)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);

    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // handle window focus/blur to pause updates when not visible (save battery)
  let visible = true;
  document.addEventListener('visibilitychange', () => {
    visible = !document.hidden;
    if (!visible) {
      // reduce work by stopping animation frame loops - we keep RAF running but minimal drawing handled by loop using dt cap
    }
  });

  // react to resize and rebuild blobs for density
  window.addEventListener('resize', () => {
    resize();
    rebuildBlobs();
  });

})();