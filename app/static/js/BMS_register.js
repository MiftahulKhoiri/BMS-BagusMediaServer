// JavaScript untuk validasi dan interaksi form register
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const alertContainer = document.getElementById('alertContainer');

    // Validasi form
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();

        resetErrors();

        let isValid = true;

        // Validasi username
        if (!usernameInput.value.trim()) {
            showError(usernameInput, 'usernameError', 'Username harus diisi');
            isValid = false;
        } else if (usernameInput.value.trim().length < 3) {
            showError(usernameInput, 'usernameError', 'Username minimal 3 karakter');
            isValid = false;
        } else if (!/^[a-zA-Z0-9_]+$/.test(usernameInput.value)) {
            showError(usernameInput, 'usernameError', 'Username hanya boleh huruf, angka, underscore');
            isValid = false;
        }

        // Validasi password
        if (!passwordInput.value.trim()) {
            showError(passwordInput, 'passwordError', 'Password harus diisi');
            isValid = false;
        } else if (passwordInput.value.length < 6) {
            showError(passwordInput, 'passwordError', 'Password minimal 6 karakter');
            isValid = false;
        } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(passwordInput.value)) {
            showError(passwordInput, 'passwordError', 'Password harus ada huruf besar, kecil, dan angka');
            isValid = false;
        }

        // Validasi konfirmasi password
        if (!confirmPasswordInput.value.trim()) {
            showError(confirmPasswordInput, 'confirmPasswordError', 'Konfirmasi password harus diisi');
            isValid = false;
        } else if (passwordInput.value !== confirmPasswordInput.value) {
            showError(confirmPasswordInput, 'confirmPasswordError', 'Konfirmasi password tidak sama');
            isValid = false;
        }

        // Jika valid → kirim form
        if (isValid) {
            submitBtn.disabled = true;
            btnText.innerHTML = '<span class="loading"></span> Memproses...';
            submitFormData();
        }
    });

    // Kirim data form via AJAX
    function submitFormData() {
        const formData = new FormData(registerForm);

        fetch(registerForm.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.disabled = false;
            btnText.textContent = 'Daftar';

            if (data.success) {
                showAlert('Registrasi berhasil! Mengalihkan ke halaman login...', 'success');
                setTimeout(() => window.location.href = '/auth/login', 2000);
            } else {
                showAlert(data.message || 'Registrasi gagal.', 'error');

                if (data.errors) {
                    if (data.errors.username) {
                        showError(usernameInput, 'usernameError', data.errors.username);
                    }
                    if (data.errors.password) {
                        showError(passwordInput, 'passwordError', data.errors.password);
                    }
                }
            }
        })
        .catch(() => {
            submitBtn.disabled = false;
            btnText.textContent = 'Daftar';
            showAlert('Terjadi kesalahan jaringan.', 'error');
        });
    }

    // Password strength check
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        let indicator = document.getElementById('passwordStrength');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'passwordStrength';
            indicator.className = 'password-strength';
            this.parentNode.appendChild(indicator);
        }

        if (!password) {
            indicator.style.display = 'none';
            return;
        }

        let score = 0;
        const tests = [
            /[A-Z]/, /[a-z]/, /\d/, /[!@#$%^&*(),.?":{}|<>]/
        ];
        tests.forEach(test => { if (test.test(password)) score++; });

        let strength = 'weak', message = 'Password lemah';

        if (score >= 3 && password.length >= 8) {
            strength = 'medium';
            message = 'Password cukup';
        }
        if (score >= 3 && password.length >= 10) {
            strength = 'strong';
            message = 'Password kuat';
        }

        indicator.textContent = message;
        indicator.className = `password-strength strength-${strength}`;
        indicator.style.display = 'block';
    });

    confirmPasswordInput.addEventListener('input', function() {
        if (this.value !== passwordInput.value) {
            showError(this, 'confirmPasswordError', 'Konfirmasi password tidak sama');
        } else {
            resetError(this, 'confirmPasswordError');
        }
    });

    // Utility Functions
    function showError(input, errorId, message) {
        input.classList.add('error');
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    function resetError(input, errorId) {
        input.classList.remove('error');
        const errorElement = document.getElementById(errorId);
        errorElement.style.display = 'none';
    }

    function resetErrors() {
        document.querySelectorAll('.error-message').forEach(e => e.style.display = 'none');
        document.querySelectorAll('.error').forEach(e => e.classList.remove('error'));
    }

    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        alert.style.display = 'block';

        setTimeout(() => alert.style.display = 'none', 5000);
    }
});