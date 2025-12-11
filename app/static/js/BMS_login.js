document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const alertContainer = document.getElementById("alertContainer");

    // ============================================================
    //  FRONT-END VALIDATION
    // ============================================================
    loginForm.addEventListener("submit", function (e) {
        // Jangan auto-submit, biarkan browser submit normal
        // tapi tetap validasi dulu
        let isValid = true;
        resetErrors();

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (username.length < 3) {
            showError(usernameInput, "usernameError", "Username minimal 3 karakter");
            isValid = false;
        }

        if (password.length < 8) {
            showError(passwordInput, "passwordError", "Password minimal 8 karakter");
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
            return;
        }

        // Disable tombol agar tidak double-submit
        submitBtn.disabled = true;
        btnText.innerHTML = '<span class="loading"></span> Memproses...';
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

    function showAlert(message, type) {
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
    //  REAL-TIME CHECK
    // ============================================================
    usernameInput.addEventListener("input", function () {
        if (this.value.length >= 3) resetError(this, "usernameError");
    });

    passwordInput.addEventListener("input", function () {
        if (this.value.length >= 8) resetError(this, "passwordError");
    });
});