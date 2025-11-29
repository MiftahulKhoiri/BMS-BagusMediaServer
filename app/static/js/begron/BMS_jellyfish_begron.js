/* ==========================================================
   BMS Jellyfish Background — Neon Aqua Motion
========================================================== */

const canvas = document.getElementById("jellyCanvas");
const ctx = canvas.getContext("2d");

let W, H;

/* Resize otomatis */
function resize(){
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
}
resize();
window.onresize = resize;

/* ==========================================================
   Ubur-ubur object (soft blob)
========================================================== */
class Jellyfish {
    constructor(){
        this.x = Math.random() * W;
        this.y = Math.random() * H;
        this.r = 40 + Math.random() * 80;

        this.dx = (Math.random() * 0.8 - 0.4);
        this.dy = (Math.random() * 0.8 - 0.4);

        this.color = this.randomColor();
    }

    randomColor(){
        const colors = [
            "rgba(0,255,200,0.35)",
            "rgba(100,100,255,0.35)",
            "rgba(255,0,200,0.35)",
            "rgba(0,120,255,0.35)"
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    move(){
        this.x += this.dx;
        this.y += this.dy;

        // Mantul lembut
        if(this.x < 0 || this.x > W) this.dx *= -1;
        if(this.y < 0 || this.y > H) this.dy *= -1;

        // Perlahan berubah warna
        if(Math.random() < 0.002){
            this.color = this.randomColor();
        }
    }

    draw(){
        ctx.beginPath();
        ctx.fillStyle = this.color;
        ctx.shadowBlur = 55;
        ctx.shadowColor = this.color;
        ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
        ctx.fill();
    }
}

/* ==========================================================
   Generate banyak ubur-ubur neon
========================================================== */
let jellyfishList = [];
let TOTAL = 16; // Aman untuk Android

for(let i = 0; i < TOTAL; i++){
    jellyfishList.push(new Jellyfish());
}

/* ==========================================================
   Animation Loop
========================================================== */
function animate(){
    ctx.clearRect(0,0,W,H);

    for(let j of jellyfishList){
        j.move();
        j.draw();
    }

    requestAnimationFrame(animate);
}

animate();