document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const alertContainer = document.getElementById("alertContainer");

    // ============================================================
    //  HANDLE SUBMIT (VALIDASI + AJAX LOGIN)
    // ============================================================
    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault(); // Stop submit normal

        let isValid = true;
        resetErrors();

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        // --- VALIDASI USERNAME ---
        if (username.length < 3) {
            showError(usernameInput, "usernameError", "Username minimal 3 karakter");
            isValid = false;
        }

        // --- VALIDASI PASSWORD ---
        if (password.length < 8) {
            showError(passwordInput, "passwordError", "Password minimal 8 karakter");
            isValid = false;
        }

        if (!isValid) return;

        // Tombol loading
        submitBtn.disabled = true;
        btnText.innerHTML = '<span class="loading"></span> Memproses...';

        // --- AJAX SEND TO BACKEND ---
        const formData = new FormData(loginForm);

        try {
            const res = await fetch("/auth/login", {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                // Redirect sesuai role
                window.location.href = data.redirect;
            } else {
                showAlert("Login gagal. Periksa username / password.", "error");
            }

        } catch (err) {
            showAlert("Koneksi gagal. Coba lagi.", "error");
        }

        // Reset tombol
        submitBtn.disabled = false;
        btnText.textContent = "Masuk";
    });

    // ============================================================
    //  ERROR HANDLER
    // ============================================================
    function showError(input, errorId, message) {
        input.classList.add("error");
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = message;
        errorElement.style.display = "block";
    }

    function resetErrors() {
        document.querySelectorAll(".input-text.error").forEach((i) => i.classList.remove("error"));
        document.querySelectorAll(".error-message").forEach((m) => {
            m.style.display = "none";
            m.textContent = "";
        });
    }

    function resetError(input, errorId) {
        input.classList.remove("error");
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = "";
        errorElement.style.display = "none";
    }

    // ============================================================
    //  ALERT NOTIFICATION (FLASH FRONTEND)
    // ============================================================
    function showAlert(message, type) {
        if (!alertContainer) return;

        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${escapeHTML(message)}
            </div>
        `;

        setTimeout(() => {
            alertContainer.innerHTML = "";
        }, 4000);
    }

    // Escaping HTML untuk keamanan
    function escapeHTML(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // ============================================================
    //  REAL-TIME INPUT CHECK
    // ============================================================
    usernameInput.addEventListener("input", function () {
        if (this.value.length >= 3) resetError(this, "usernameError");
    });

    passwordInput.addEventListener("input", function () {
        if (this.value.length >= 8) resetError(this, "passwordError");
    });
});