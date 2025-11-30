// JavaScript untuk validasi dan interaksi form login
document.addEventListener('DOMContentLoaded', function() {
    console.log('Login script loaded');
    
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const alertContainer = document.getElementById('alertContainer');
    const debugInfo = document.getElementById('debugInfo');
    const debugStatus = document.getElementById('debugStatus');
    const debugData = document.getElementById('debugData');
    
    // Tampilkan debug info di development
    debugInfo.style.display = 'block';
    
    // Validasi form
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted');
        
        // Reset error state
        resetErrors();
        
        // Validasi input
        let isValid = true;
        let validationErrors = [];
        
        // Validasi username
        if (!usernameInput.value.trim()) {
            showError(usernameInput, 'usernameError', 'Username harus diisi');
            isValid = false;
            validationErrors.push('Username kosong');
        } else if (usernameInput.value.trim().length < 3) {
            showError(usernameInput, 'usernameError', 'Username minimal 3 karakter');
            isValid = false;
            validationErrors.push('Username terlalu pendek');
        }
        
        // Validasi password
        if (!passwordInput.value.trim()) {
            showError(passwordInput, 'passwordError', 'Password harus diisi');
            isValid = false;
            validationErrors.push('Password kosong');
        } else if (passwordInput.value.length < 6) {
            showError(passwordInput, 'passwordError', 'Password minimal 6 karakter');
            isValid = false;
            validationErrors.push('Password terlalu pendek');
        }
        
        // Update debug info
        updateDebugInfo(`Validating: ${isValid ? 'PASS' : 'FAIL'}`, validationErrors.join(', '));
        
        if (isValid) {
            // Tampilkan loading state
            submitBtn.disabled = true;
            btnText.innerHTML = '<span class="loading"></span> Memproses...';
            
            console.log('Form validation passed, submitting...');
            
            // Kirim data ke server
            submitFormData();
        } else {
            showAlert('Harap perbaiki error di atas', 'error');
        }
    });
    
    // Fungsi untuk mengirim data form
    function submitFormData() {
        // Buat objek FormData dari form
        const formData = new FormData(loginForm);
        const formDataObj = {};
        
        // Convert FormData ke object untuk debug
        for (let [key, value] of formData.entries()) {
            formDataObj[key] = value;
        }
        
        console.log('Submitting form data:', formDataObj);
        updateDebugInfo('Submitting...', JSON.stringify(formDataObj));
        
        // Kirim data menggunakan fetch API
        fetch(loginForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json',
            }
        })
        .then(response => {
            console.log('Response status:', response.status);
            updateDebugInfo(`Response: ${response.status}`, 'Processing...');
            
            if (!response.ok) {
                // Jika response bukan 2xx, lempar error
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            
            // Reset button state
            submitBtn.disabled = false;
            btnText.textContent = 'Masuk';
            
            if (data.success) {
                // Login berhasil
                updateDebugInfo('SUCCESS', 'Login berhasil, redirecting...');
                showAlert('Login berhasil! Mengalihkan...', 'success');
                
                // Redirect ke halaman dashboard setelah 2 detik
                setTimeout(() => {
                    window.location.href = data.redirect || '/dashboard';
                }, 2000);
            } else {
                // Login gagal
                updateDebugInfo('FAILED', data.message || 'Login gagal');
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
            console.error('Error:', error);
            
            // Reset button state
            submitBtn.disabled = false;
            btnText.textContent = 'Masuk';
            
            // Tampilkan pesan error
            updateDebugInfo('ERROR', error.message);
            showAlert('Terjadi kesalahan. Silakan coba lagi.', 'error');
            
            // Untuk debugging lebih lanjut
            if (error.message.includes('Failed to fetch')) {
                showAlert('Tidak dapat terhubung ke server. Periksa koneksi internet Anda.', 'error');
            }
        });
    }
    
    // Fungsi untuk update debug info
    function updateDebugInfo(status, data) {
        debugStatus.textContent = `Status: ${status}`;
        debugData.textContent = `Data: ${data}`;
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
        } else if (this.value.trim().length < 3) {
            showError(this, 'usernameError', 'Username minimal 3 karakter');
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
    
    // Test koneksi saat halaman dimuat
    console.log('Testing server connection...');
    updateDebugInfo('Testing connection', 'Checking server...');
});