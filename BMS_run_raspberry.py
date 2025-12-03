#!/bin/bash

echo "=== BMS - BagusMediaServer Launcher ==="
echo "Sistem: Raspberry Pi"
echo ""

# Nama folder virtual environment
VENV_DIR="venv"

# ----------------------------------------
# 1. CEK APAKAH SCRIPT DIJALANKAN DENGAN SUDO
# ----------------------------------------
if [[ $EUID -eq 0 ]]; then
    echo "[!] PERINGATAN: Script sedang dijalankan sebagai root/sudo!"
    echo "    Lebih baik jalankan sebagai user biasa (pi)."
    echo "    Keluar dari script..."
    exit 1
fi

# ----------------------------------------------------------
# AUTO INSTALASI NGINX & SUPERVISOR
# ----------------------------------------------------------
echo ""
echo "=== Mengecek kebutuhan sistem ==="

# Update package list
echo "[+] Update package list..."
sudo apt update -y

# Cek dan install Nginx
if ! command -v nginx &> /dev/null; then
    echo "[+] Menginstall Nginx..."
    sudo apt install -y nginx
    echo "[✓] Nginx terinstall."
else
    echo "[✓] Nginx sudah terpasang."
fi

# Cek dan install Supervisor
if ! command -v supervisorctl &> /dev/null; then
    echo "[+] Menginstall Supervisor..."
    sudo apt install -y supervisor
    echo "[✓] Supervisor terinstall."
else
    echo "[✓] Supervisor sudah terpasang."
fi

echo "=== Sistem siap digunakan ==="
echo ""

# ----------------------------------------
# 2. CEK APAKAH DI RASPBERRY PI
# ----------------------------------------
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null && ! grep -q "raspberrypi" /etc/os-release 2>/dev/null; then
    echo "[!] PERINGATAN: Sistem ini tidak terdeteksi sebagai Raspberry Pi!"
    read -p "    Lanjutkan tetap? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ----------------------------------------
# 3. CEK DAN BUAT VIRTUAL ENVIRONMENT
# ----------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Virtual environment belum ada. Membuat venv baru..."
    python3 -m venv $VENV_DIR
    
    if [ $? -ne 0 ]; then
        echo "[!] Gagal membuat virtual environment!"
        echo "    Pastikan python3-venv terinstal:"
        echo "    sudo apt install python3-venv"
        exit 1
    fi
else
    echo "[✓] Virtual environment sudah ada."
fi

# ----------------------------------------
# 4. AKTIVASI VIRTUAL ENV
# ----------------------------------------
echo "[+] Mengaktifkan virtual environment..."
source $VENV_DIR/bin/activate

if [ $? -ne 0 ]; then
    echo "[!] Gagal mengaktifkan virtual environment!"
    exit 1
fi

# ----------------------------------------
# 5. UPDATE PIP DAN SETUP
# ----------------------------------------
echo "[+] Update pip dan setup tools..."
pip install --upgrade pip setuptools wheel

# ----------------------------------------
# 6. INSTALL REQUIREMENTS
# ----------------------------------------
if [ -f "requirements.txt" ]; then
    echo "[+] Menginstall dependencies dari requirements.txt..."
    
    # Cek jika ada dependency khusus Raspberry Pi
    if grep -q "RPi.GPIO\|picamera\|gpiozero" requirements.txt; then
        echo "[!] Deteksi library hardware Raspberry Pi"
        echo "    Pastikan SPI/I2C sudah dienable jika diperlukan"
    fi
    
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "[!] Ada masalah saat install dependencies"
        echo "    Mungkin perlu package system tambahan"
    fi
else
    echo "[!] requirements.txt tidak ditemukan!"
    echo "    Melanjutkan tanpa install dependencies..."
fi

# ----------------------------------------
# 7. KONFIGURASI UNTUK RASPBERRY PI
# ----------------------------------------
echo ""
echo "======================================"
echo " KONFIGURASI RASPBERRY PI"
echo "======================================"

# Cek CPU temperature
CPU_TEMP=$(vcgencmd measure_temp | cut -d= -f2)
echo "[i] CPU Temperature: $CPU_TEMP"

# Cek free memory
FREE_MEM=$(free -h | awk '/^Mem:/ {print $4}')
echo "[i] Available Memory: $FREE_MEM"

# Tampilkan IP address
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "[i] IP Address: $IP_ADDR"

# ----------------------------------------
# 8. PILIH MODE JALAN
# ----------------------------------------
echo ""
echo "PILIH MODE JALAN SERVER:"
echo "1) Development (Gunicorn saja, port 5000)"
echo "2) Production (Dengan Nginx reverse proxy)"
echo "3) Supervisord (Background service)"
echo "4) Test saja (Tidak start server)"
echo ""
read -p "Pilihan [1-4]: " MODE

case $MODE in
    1)
        # MODE DEVELOPMENT
        echo ""
        echo "======================================"
        echo " MODE DEVELOPMENT"
        echo "======================================"
        echo "Server akan berjalan di: http://$IP_ADDR:5000"
        echo "Atau http://localhost:5000"
        echo ""
        echo "Tekan CTRL+C untuk menghentikan"
        echo ""
        
        # Optimasi untuk Raspberry Pi (kurang worker karena RAM terbatas)
        gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 --timeout 120 "app:create_app()"
        ;;
    
    2)
        # MODE PRODUCTION DENGAN NGINX
        echo ""
        echo "======================================"
        echo " MODE PRODUCTION (NGINX + GUNICORN)"
        echo "======================================"
        
        # Cek apakah nginx terinstal
        if ! command -v nginx &> /dev/null; then
            echo "[!] Nginx tidak ditemukan!"
            echo "    Install dengan: sudo apt install nginx"
            echo "    Jalankan mode lain atau install nginx terlebih dahulu"
            exit 1
        fi
        
        # Buat konfigurasi nginx untuk BMS
        echo "[+] Membuat konfigurasi Nginx..."
        
        NGINX_CONF="bms_server"
        sudo tee /etc/nginx/sites-available/$NGINX_CONF > /dev/null << EOF
server {
    listen 80;
    server_name $IP_ADDR;
    
    # Log files
    access_log /var/log/nginx/bms_access.log;
    error_log /var/log/nginx/bms_error.log;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Static files (jika ada)
    location /static {
        alias /path/to/your/static/files;
        expires 30d;
    }
}
EOF
        
        # Enable site
        if [ ! -f "/etc/nginx/sites-enabled/$NGINX_CONF" ]; then
            sudo ln -s /etc/nginx/sites-available/$NGINX_CONF /etc/nginx/sites-enabled/
        fi
        
        # Test nginx configuration
        echo "[+] Testing Nginx configuration..."
        sudo nginx -t
        
        if [ $? -eq 0 ]; then
            echo "[✓] Konfigurasi Nginx valid"
            echo "[+] Restarting Nginx..."
            sudo systemctl restart nginx
            
            echo ""
            echo "======================================"
            echo " SERVER PRODUCTION SIAP"
            echo "======================================"
            echo "Nginx berjalan di port 80"
            echo "Akses server di: http://$IP_ADDR"
            echo ""
            echo "Starting Gunicorn (background)..."
            
            # Jalankan gunicorn di background
            gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 --daemon --pid /tmp/gunicorn.pid --access-logfile /tmp/gunicorn_access.log --error-logfile /tmp/gunicorn_error.log "app:create_app()"
            
            echo "[✓] Gunicorn berjalan di background (PID: \$(cat /tmp/gunicorn.pid))"
            echo ""
            echo "Perintah untuk menghentikan:"
            echo "  kill \$(cat /tmp/gunicorn.pid)"
            echo "  sudo systemctl stop nginx"
            echo ""
            echo "Untuk melihat log:"
            echo "  tail -f /tmp/gunicorn_error.log"
            echo "  tail -f /var/log/nginx/bms_error.log"
            
            # Tunggu user menekan enter
            read -p "Press Enter to stop server and cleanup..."
            
            # Stop server
            echo "[+] Stopping servers..."
            kill $(cat /tmp/gunicorn.pid 2>/dev/null) 2>/dev/null
            sudo systemctl stop nginx
            echo "[✓] Servers stopped"
        else
            echo "[!] Konfigurasi Nginx tidak valid!"
            exit 1
        fi
        ;;
    
    3)
        # MODE SUPERVISORD (RECOMMENDED)
        echo ""
        echo "======================================"
        echo " MODE SUPERVISORD (RECOMMENDED)"
        echo "======================================"
        
        if ! command -v supervisorctl &> /dev/null; then
            echo "[!] Supervisord tidak terinstal"
            echo "    Install dengan: sudo apt install supervisor"
            exit 1
        fi
        
        echo "[+] Membuat konfigurasi Supervisord..."
        
        # Buat direktori untuk log jika belum ada
        mkdir -p logs
        
        # Buat konfigurasi supervisor
        SUPERVISOR_CONF="bms_gunicorn"
        
        cat > bms_supervisor.conf << EOF
[program:bms_gunicorn]
directory=$(pwd)
command=$(pwd)/$VENV_DIR/bin/gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 --timeout 120 "app:create_app()"
user=$USER
autostart=true
autorestart=true
stderr_logfile=$(pwd)/logs/gunicorn_err.log
stdout_logfile=$(pwd)/logs/gunicorn_out.log
environment=PATH="$(pwd)/$VENV_DIR/bin"
EOF
        
        echo "[i] Konfigurasi Supervisord dibuat: bms_supervisor.conf"
        echo ""
        echo "Untuk setup Supervisord:"
        echo "1. Copy ke /etc/supervisor/conf.d/:"
        echo "   sudo cp bms_supervisor.conf /etc/supervisor/conf.d/bms.conf"
        echo "2. Update supervisor:"
        echo "   sudo supervisorctl reread"
        echo "   sudo supervisorctl update"
        echo "3. Start service:"
        echo "   sudo supervisorctl start bms_gunicorn"
        echo ""
        echo "Status: sudo supervisorctl status"
        echo "Stop:   sudo supervisorctl stop bms_gunicorn"
        echo "Logs:   tail -f logs/gunicorn_err.log"
        ;;
    
    4)
        # MODE TEST
        echo ""
        echo "======================================"
        echo " MODE TEST"
        echo "======================================"
        echo "[✓] Virtual environment aktif"
        echo "[✓] Dependencies terinstall"
        echo ""
        echo "Untuk menjalankan server:"
        echo "1. Manual dengan gunicorn:"
        echo "   gunicorn -w 2 -b 0.0.0.0:5000 app:create_app"
        echo "2. Manual dengan flask dev server (tidak untuk production):"
        echo "   export FLASK_APP=app.py"
        echo "   flask run --host=0.0.0.0 --port=5000"
        echo ""
        echo "Testing selesai."
        ;;
    
    *)
        echo "Pilihan tidak valid. Menggunakan mode default (Development)"
        echo ""
        echo "Starting development server..."
        gunicorn -w 2 -b 0.0.0.0:5000 "app:create_app()"
        ;;
esac

# Deactivate virtual environment jika masih aktif
deactivate 2>/dev/null

echo ""
echo "======================================"
echo " BMS Launcher selesai"
echo "======================================"