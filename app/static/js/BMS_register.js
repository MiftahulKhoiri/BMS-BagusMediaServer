// JavaScript untuk validasi dan interaksi form register
document.addEventListener("DOMContentLoaded", function () {

    const registerForm = document.getElementById("registerForm");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm_password");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");

    // ============================================================
    //  FRONT-END VALIDATION BEFORE FORM SUBMIT
    // ============================================================
    registerForm.addEventListener("submit", function (e) {

        resetErrors();

        let isValid = true;
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const confirm = confirmInput.value.trim();

        // Username validation
        if (username.length < 3) {
            showError(usernameInput, "usernameError", "Username minimal 3 karakter");
            isValid = false;
        } else if (!/^[A-Za-z0-9_]{3,32}$/.test(username)) {
            showError(usernameInput, "usernameError", "Gunakan huruf/angka/underscore saja");
            isValid = false;
        }

        // Password validation
        if (password.length < 8) {
            showError(passwordInput, "passwordError", "Password minimal 8 karakter");
            isValid = false;
        }

        // Confirm password validation
        if (password !== confirm) {
            showError(confirmInput, "confirmPasswordError", "Konfirmasi password tidak cocok");
            isValid = false;
        }

        // If validation fails → prevent form submit
        if (!isValid) {
            e.preventDefault();
            return;
        }

        // ===============================
        //   SAFE SUBMIT (No AJAX)
        // ===============================
        submitBtn.disabled = true;
        btnText.innerHTML = '<span class="loading"></span> Memproses...';

        // Browser will submit normally
    });

    // ============================================================
    //  PASSWORD STRENGTH INDICATOR
    // ============================================================
    passwordInput.addEventListener("input", function () {
        const pwd = this.value;

        let indicator = document.getElementById("passwordStrength");
        if (!indicator) {
            indicator = document.createElement("div");
            indicator.id = "passwordStrength";
            indicator.className = "password-strength";
            this.parentNode.appendChild(indicator);
        }

        if (!pwd) {
            indicator.style.display = "none";
            return;
        }

        let score = 0;
        const tests = [
            /[A-Z]/, /[a-z]/, /\d/, /[!@#$%^&*(),.?":{}|<>]/
        ];
        tests.forEach(test => { if (test.test(pwd)) score++; });

        let strength = "weak", msg = "Password lemah";

        if (score >= 3 && pwd.length >= 8) {
            strength = "medium";
            msg = "Password cukup";
        }
        if (score >= 3 && pwd.length >= 10) {
            strength = "strong";
            msg = "Password kuat";
        }

        indicator.textContent = msg;
        indicator.className = `password-strength strength-${strength}`;
        indicator.style.display = "block";
    });

    // ============================================================
    //  REAL-TIME CONFIRM PASSWORD CHECK
    // ============================================================
    confirmInput.addEventListener("input", function () {
        if (this.value !== passwordInput.value) {
            showError(this, "confirmPasswordError", "Konfirmasi password tidak cocok");
        } else {
            resetError(this, "confirmPasswordError");
        }
    });

    // ============================================================
    //  UTILITY FUNCTIONS
    // ============================================================
    function showError(input, errorId, message) {
        input.classList.add("error");
        const el = document.getElementById(errorId);
        el.textContent = message;
        el.style.display = "block";
    }

    function resetError(input, errorId) {
        input.classList.remove("error");
        const el = document.getElementById(errorId);
        el.style.display = "none";
    }

    function resetErrors() {
        document.querySelectorAll(".error-message").forEach(e => {
            e.style.display = "none";
            e.textContent = "";
        });
        document.querySelectorAll(".error").forEach(e => e.classList.remove("error"));
    }
});