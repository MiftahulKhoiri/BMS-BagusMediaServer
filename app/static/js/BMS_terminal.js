const outputBox = document.getElementById("terminalOutput");
const inputBox = document.getElementById("terminalInput");

function appendOutput(text) {
    outputBox.textContent += "\n" + text;
    outputBox.scrollTop = outputBox.scrollHeight;
}

inputBox.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        let cmd = inputBox.value.trim();
        if (!cmd) return;

        appendOutput("> " + cmd);
        inputBox.value = "";

        let form = new FormData();
        form.append("cmd", cmd);

        fetch("/terminal/run", { method: "POST", body: form })
            .then(r => r.json())
            .then(data => {
                appendOutput(data.output);
            })
            .catch(() => {
                appendOutput("❌ Error koneksi ke server!");
            });
    }
});