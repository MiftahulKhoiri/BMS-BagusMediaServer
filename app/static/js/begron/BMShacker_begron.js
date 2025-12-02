/* BMS Hacker Background Shards Generator
   Membuat serpihan teks acak (binary/hex) yang melayang
   di background hacker.
*/

document.addEventListener("DOMContentLoaded", () => {

    const bg = document.querySelector(".bms-hacker-bg");
    if (!bg) return;

    const HEX = ["A", "B", "C", "D", "E", "F"];
    const BIN = ["0", "1"];
    const SHARDS_COUNT = 35;  // jumlah serpihan hacker
    const speeds = ["slow", "mid", "fast"];
    const sizes = ["s1", "s2", "s3"];

    function randomText() {
        let mode = Math.random() > 0.5 ? "hex" : "bin";
        let out = "";

        for (let i = 0; i < 4; i++) {
            if (mode === "hex") {
                out += Math.random() > 0.5
                    ? HEX[Math.floor(Math.random()*HEX.length)]
                    : Math.floor(Math.random()*10);
            } else {
                out += BIN[Math.floor(Math.random()*2)];
            }
            out += Math.random() > 0.5 ? " " : "";
        }
        return out.trim();
    }

    function createShard() {
        const div = document.createElement("div");
        div.classList.add("hacker-shard");

        // ukuran
        div.classList.add(sizes[Math.floor(Math.random()*sizes.length)]);
        // kecepatan
        div.classList.add(speeds[Math.floor(Math.random()*speeds.length)]);

        // posisi acak
        div.style.left = Math.floor(Math.random() * 100) + "%";
        div.style.top = (70 + Math.random()*30) + "%";

        div.textContent = randomText();

        bg.appendChild(div);
    }

    // buat serpihan sebanyak SHARDS_COUNT
    for (let i = 0; i < SHARDS_COUNT; i++) {
        createShard();
    }

});