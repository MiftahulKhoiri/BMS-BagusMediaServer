document.addEventListener("DOMContentLoaded", function () {

    const loginForm = document.getElementById("loginForm");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");

    // Elemen error inline pada HTML
    const usernameError = document.getElementById("usernameError");
    const passwordError = document.getElementById("passwordError");

    // === RESET ERROR ===
    function resetAllErrors() {
        usernameInput.classList.remove("error");
        passwordInput.classList.remove("error");

        usernameError.textContent = "";
        passwordError.textContent = "";
    }

    function showError(input, errorElement, message) {
        input.classList.add("error");
        errorElement.textContent = message;
    }

    // ============================================================
    //  FORM SUBMIT HANDLER (AJAX LOGIN)
    // ============================================================
    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        resetAllErrors();
        let valid = true;

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        // Validasi username
        if (username.length < 3) {
            showError(usernameInput, usernameError, "Username minimal 3 karakter");
            valid = false;
        }

        // Validasi password
        if (password.length < 8) {
            showError(passwordInput, passwordError, "Password minimal 8 karakter");
            valid = false;
        }

        if (!valid) return;

        // === Tombol loading ===
        submitBtn.disabled = true;
        btnText.innerHTML = '<span class="loading"></span> Memproses...';

        const formData = new FormData(loginForm);

        try {
            const res = await fetch("/auth/login", {
                method: "POST",
                body: formData
            });

            // Cek apakah response JSON atau HTML
            let data;
            try {
                data = await res.json();
            } catch (jsonErr) {
                showError(passwordInput, passwordError, "Server mengirim format tidak valid.");
                throw new Error("Invalid JSON");
            }

            // Jika login sukses → redirect
            if (data.success) {
                window.location.href = data.redirect;
                return;
            }

            // Jika backend kirim error spesifik
            if (data.error_field === "username") {
                showError(usernameInput, usernameError, data.message);
            }
            else if (data.error_field === "password") {
                showError(passwordInput, passwordError, data.message);
            }
            else {
                showError(passwordInput, passwordError, data.message || "Login gagal.");
            }

        } catch (err) {
            showError(passwordInput, passwordError, "Koneksi gagal. Coba lagi.");
        }

        // Reset tombol
        submitBtn.disabled = false;
        btnText.textContent = "Masuk";
    });

    // ============================================================
    //  REAL-TIME INPUT VALIDATION
    // ============================================================
    usernameInput.addEventListener("input", function () {
        if (this.value.length >= 3) {
            usernameInput.classList.remove("error");
            usernameError.textContent = "";
        }
    });

    passwordInput.addEventListener("input", function () {
        if (this.value.length >= 8) {
            passwordInput.classList.remove("error");
            passwordError.textContent = "";
        }
    });

});

// ============================================================
//  SHOW / HIDE PASSWORD
// ============================================================
const togglePassword = document.getElementById("togglePassword");

togglePassword.addEventListener("click", function () {
    const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
    passwordInput.setAttribute("type", type);

    // Ganti icon
    togglePassword.textContent = type === "password" ? "👁️" : "🙈";
});