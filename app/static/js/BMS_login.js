// JavaScript untuk validasi dan interaksi form login
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const alertContainer = document.getElementById('alertContainer');
    
    // Validasi form
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset error state
        resetErrors();
        
        // Validasi input
        let isValid = true;
        
        if (!usernameInput.value.trim()) {
            showError(usernameInput, 'usernameError', 'Username harus diisi');
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
        const formData = new FormData(loginForm);
        
        // Kirim data menggunakan fetch API
        fetch(loginForm.action, {
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
            btnText.textContent = 'Masuk';
            
            if (data.success) {
                // Login berhasil
                showAlert('Login berhasil! Mengalihkan...', 'success');
                
                // Redirect ke halaman dashboard setelah 2 detik
                setTimeout(() => {
                    window.location.href = data.redirect || '/dashboard';
                }, 2000);
            } else {
                // Login gagal
                showAlert(data.message || 'Login gagal. Periksa username dan password Anda.', 'error');
                
                // Tampilkan error spesifik jika ada
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
            // Reset button state
            submitBtn.disabled = false;
            btnText.textContent = 'Masuk';
            
            // Tampilkan pesan error
            showAlert('Terjadi kesalahan. Silakan coba lagi.', 'error');
            console.error('Error:', error);
        });
    }
    
    // Fungsi untuk menampilkan error
    function showError(input, errorId, message) {
        input.classList.add('error');
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
    
    // Fungsi untuk mereset error
    function resetErrors() {
        const errorInputs = document.querySelectorAll('.input-text.error');
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
        } else {
            resetError(this, 'passwordError');
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
    });
});