document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const alertContainer = document.getElementById('alertContainer');

    // VALIDASI SAAT SUBMIT
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        resetErrors();

        let isValid = true;

        if (!usernameInput.value.trim()) {
            showError(usernameInput, 'usernameError', 'Username harus diisi');
            isValid = false;
        } else if (usernameInput.value.trim().length < 3) {
            showError(usernameInput, 'usernameError', 'Username minimal 3 karakter');
            isValid = false;
        }

        if (!passwordInput.value.trim()) {
            showError(passwordInput, 'passwordError', 'Password harus diisi');
            isValid = false;
        } else if (passwordInput.value.length < 6) {
            showError(passwordInput, 'passwordError', 'Password minimal 6 karakter');
            isValid = false;
        }

        if (isValid) {
            submitBtn.disabled = true;
            btnText.innerHTML = '<span class="loading"></span> Memproses...';
            submitFormData();
        }
    });

    // KIRIM DATA KE SERVER VIA FETCH
    function submitFormData() {
        const formData = new FormData(loginForm);

        fetch(loginForm.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.disabled = false;
            btnText.textContent = 'Masuk';

            if (data.success) {
                showAlert('Login berhasil! Mengalihkan...', 'success');

                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1500);
            } else {
                showAlert(data.message || 'Login gagal.', 'error');

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
        .catch(error => {
            submitBtn.disabled = false;
            btnText.textContent = 'Masuk';

            showAlert('Terjadi kesalahan. Silakan coba lagi.', 'error');
            console.error('Error:', error);
        });
    }

    // ERROR HANDLER
    function showError(input, errorId, message) {
        input.classList.add('error');
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    function resetErrors() {
        document.querySelectorAll('.input-text.error').forEach(i => i.classList.remove('error'));
        document.querySelectorAll('.error-message').forEach(m => m.style.display = 'none');
    }

    function resetError(input, errorId) {
        input.classList.remove('error');
        document.getElementById(errorId).style.display = 'none';
    }

    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);

        setTimeout(() => alert.style.display = 'none', 4000);
    }

    // REAL-TIME VALIDATION
    usernameInput.addEventListener('blur', function() {
        if (!this.value.trim()) {
            showError(this, 'usernameError', 'Username harus diisi');
        } else if (this.value.trim().length < 3) {
            showError(this, 'usernameError', 'Username minimal 3 karakter');
        } else {
            resetError(this, 'usernameError');
        }
    });

    passwordInput.addEventListener('blur', function() {
        if (!this.value.trim()) {
            showError(this, 'passwordError', 'Password harus diisi');
        } else if (this.value.length < 6) {
            showError(this, 'passwordError', 'Password minimal 6 karakter');
        } else {
            resetError(this, 'passwordError');
        }
    });

    usernameInput.addEventListener('input', function() {
        if (this.classList.contains('error')) resetError(this, 'usernameError');
    });

    passwordInput.addEventListener('input', function() {
        if (this.classList.contains('error')) resetError(this, 'passwordError');
    });
});