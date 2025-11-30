// JavaScript untuk validasi dan interaksi form register
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const roleSelect = document.getElementById('role');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const alertContainer = document.getElementById('alertContainer');
    
    // Validasi form
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset error state
        resetErrors();
        
        // Validasi input
        let isValid = true;
        
        // Validasi username
        if (!usernameInput.value.trim()) {
            showError(usernameInput, 'usernameError', 'Username harus diisi');
            isValid = false;
        } else if (usernameInput.value.trim().length < 3) {
            showError(usernameInput, 'usernameError', 'Username minimal 3 karakter');
            isValid = false;
        } else if (!/^[a-zA-Z0-9_]+$/.test(usernameInput.value)) {
            showError(usernameInput, 'usernameError', 'Username hanya boleh mengandung huruf, angka, dan underscore');
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
            showError(passwordInput, 'passwordError', 'Password harus mengandung huruf besar, huruf kecil, dan angka');
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
        
        // Validasi role
        if (!roleSelect.value) {
            showError(roleSelect, 'roleError', 'Pilih role untuk akun Anda');
            isValid = false;
        }
        
        if (isValid) {
            // Tampilkan loading state
            submitBtn.disabled = true;
            btnText.innerHTML = '<span class="loading"></span> Memproses...';
            
            // Kirim data ke server
            submitFormData();
        }
    });
    
    // Fungsi untuk mengirim data form
    function submitFormData() {
        // Buat objek FormData
        const formData = new FormData(registerForm);
        
        // Kirim data menggunakan fetch API
        fetch(registerForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Reset button state
            submitBtn.disabled = false;
            btnText.textContent = 'Daftar';
            
            if (data.success) {
                // Registrasi berhasil
                showAlert('Registrasi berhasil! Mengalihkan ke halaman login...', 'success');
                
                // Redirect ke halaman login setelah 3 detik
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 3000);
            } else {
                // Registrasi gagal
                showAlert(data.message || 'Registrasi gagal. Silakan coba lagi.', 'error');
                
                // Tampilkan error spesifik jika ada
                if (data.errors) {
                    if (data.errors.username) {
                        showError(usernameInput, 'usernameError', data.errors.username);
                    }
                    if (data.errors.password) {
                        showError(passwordInput, 'passwordError', data.errors.password);
                    }
                    if (data.errors.role) {
                        showError(roleSelect, 'roleError', data.errors.role);
                    }
                }
            }
        })
        .catch(error => {
            // Reset button state
            submitBtn.disabled = false;
            btnText.textContent = 'Daftar';
            
            // Tampilkan pesan error
            showAlert('Terjadi kesalahan. Silakan coba lagi.', 'error');
            console.error('Error:', error);
        });
    }
    
    // Validasi real-time untuk password strength
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const strengthIndicator = document.getElementById('passwordStrength');
        
        if (!strengthIndicator) {
            // Buat indicator jika belum ada
            const indicator = document.createElement('div');
            indicator.id = 'passwordStrength';
            indicator.className = 'password-strength';
            this.parentNode.appendChild(indicator);
        }
        
        if (password.length === 0) {
            strengthIndicator.style.display = 'none';
            return;
        }
        
        let strength = 'weak';
        let message = 'Password lemah';
        
        if (password.length >= 8) {
            const hasUpper = /[A-Z]/.test(password);
            const hasLower = /[a-z]/.test(password);
            const hasNumbers = /\d/.test(password);
            const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
            
            const score = [hasUpper, hasLower, hasNumbers, hasSpecial].filter(Boolean).length;
            
            if (score >= 3 && password.length >= 10) {
                strength = 'strong';
                message = 'Password kuat';
            } else if (score >= 2) {
                strength = 'medium';
                message = 'Password cukup';
            }
        }
        
        strengthIndicator.textContent = message;
        strengthIndicator.className = `password-strength strength-${strength}`;
        strengthIndicator.style.display = 'block';
    });
    
    // Validasi real-time untuk konfirmasi password
    confirmPasswordInput.addEventListener('input', function() {
        if (this.value !== passwordInput.value) {
            showError(this, 'confirmPasswordError', 'Konfirmasi password tidak sama');
        } else {
            resetError(this, 'confirmPasswordError');
        }
    });
    
    // Fungsi untuk menampilkan error
    function showError(input, errorId, message) {
        input.classList.add('error');
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
    
    // Fungsi untuk mereset error
    function resetErrors() {
        const errorInputs = document.querySelectorAll('.input-text.error, .input-select.error');
        errorInputs.forEach(input => {
            input.classList.remove('error');
        });
        
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(message => {
            message.style.display = 'none';
        });
    }
    
    // Fungsi untuk menampilkan alert
    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        alert.style.display = 'block';
        
        // Hapus alert setelah 5 detik
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    }
    
    // Validasi real-time untuk username
    usernameInput.addEventListener('blur', function() {
        if (!this.value.trim()) {
            showError(this, 'usernameError', 'Username harus diisi');
        } else if (this.value.trim().length < 3) {
            showError(this, 'usernameError', 'Username minimal 3 karakter');
        } else if (!/^[a-zA-Z0-9_]+$/.test(this.value)) {
            showError(this, 'usernameError', 'Username hanya boleh mengandung huruf, angka, dan underscore');
        } else {
            resetError(this, 'usernameError');
        }
    });
    
    // Validasi real-time untuk password
    passwordInput.addEventListener('blur', function() {
        if (!this.value.trim()) {
            showError(this, 'passwordError', 'Password harus diisi');
        } else if (this.value.length < 6) {
            showError(this, 'passwordError', 'Password minimal 6 karakter');
        } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(this.value)) {
            showError(this, 'passwordError', 'Password harus mengandung huruf besar, huruf kecil, dan angka');
        } else {
            resetError(this, 'passwordError');
        }
    });
    
    // Validasi real-time untuk role
    roleSelect.addEventListener('change', function() {
        if (!this.value) {
            showError(this, 'roleError', 'Pilih role untuk akun Anda');
        } else {
            resetError(this, 'roleError');
        }
    });
    
    // Fungsi untuk mereset error spesifik
    function resetError(input, errorId) {
        input.classList.remove('error');
        const errorElement = document.getElementById(errorId);
        errorElement.style.display = 'none';
    }
    
    // Tambahkan event listener untuk menghilangkan error saat user mulai mengetik
    usernameInput.addEventListener('input', function() {
        if (this.classList.contains('error')) {
            resetError(this, 'usernameError');
        }
    });
    
    passwordInput.addEventListener('input', function() {
        if (this.classList.contains('error')) {
            resetError(this, 'passwordError');
        }
        
        // Update konfirmasi password validation
        if (confirmPasswordInput.value && confirmPasswordInput.value !== this.value) {
            showError(confirmPasswordInput, 'confirmPasswordError', 'Konfirmasi password tidak sama');
        } else if (confirmPasswordInput.value) {
            resetError(confirmPasswordInput, 'confirmPasswordError');
        }
    });
});