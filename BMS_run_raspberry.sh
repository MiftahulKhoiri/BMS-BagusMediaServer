#!/bin/bash
#
# ==============================================
#  BMS - BagusMediaServer Raspberry Pi Launcher
#  Versi Stabil — Full Fix NGINX Static Alias
# ==============================================

echo "=== BMS - BagusMediaServer Launcher ==="
echo "Sistem: Raspberry Pi"
echo ""

# Nama folder untuk Virtual Environment
VENV_DIR="venv"

# ----------------------------------------------------------
# 1. CEGAH ROOT
# ----------------------------------------------------------
if [[ $EUID -eq 0 ]]; then
    echo "[!] Script dijalankan sebagai root!"
    echo "    Jalankan sebagai user biasa (pi)."
    exit 1
fi

# ----------------------------------------------------------
# 2. AUTO INSTALL NGINX & SUPERVISOR
# ----------------------------------------------------------
echo ""
echo "=== Mengecek kebutuhan sistem ==="

echo "[+] Update package list..."
sudo apt update -y

# Install Nginx
if ! command -v nginx &> /dev/null; then
    echo "[+] Menginstall Nginx..."
    sudo apt install -y nginx
    echo "[✓] Nginx terinstall."
else
    echo "[✓] Nginx sudah terpasang."
fi

# Install Supervisor
if ! command -v supervisorctl &> /dev/null; then
    echo "[+] Menginstall Supervisor..."
    sudo apt install -y supervisor
    echo "[✓] Supervisor terinstall."
else
    echo "[✓] Supervisor sudah terpasang."
fi

echo "=== Sistem siap digunakan ==="
echo ""

# ----------------------------------------------------------
# 3. CEK RASPBERRY PI
# ----------------------------------------------------------
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "[!] Sistem bukan Raspberry Pi!"
    read -p "Lanjutkan? (y/N): " ans
    [[ $ans =~ ^[Yy]$ ]] || exit 1
fi

# ----------------------------------------------------------
# 4. BUAT VENV
# ----------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Membuat virtual environment..."
    python3 -m venv $VENV_DIR || {
        echo "[!] Gagal membuat virtual environment!"
        exit 1
    }
else
    echo "[✓] Virtual environment ditemukan."
fi

# ----------------------------------------------------------
# 5. AKTIVASI VENV
# ----------------------------------------------------------
echo "[+] Mengaktifkan virtual environment..."
source $VENV_DIR/bin/activate || {
    echo "[!] Gagal mengaktifkan venv!"
    exit 1
}

# ----------------------------------------------------------
# 6. INSTALL REQUIREMENTS
# ----------------------------------------------------------
echo "[+] Update pip..."
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    echo "[+] Menginstall requirements..."
    pip install -r requirements.txt || echo "[!] Ada error saat install dependencies."
else
    echo "[!] requirements.txt tidak ditemukan."
fi

# ----------------------------------------------------------
# 7. INFO HARDWARE
# ----------------------------------------------------------
echo ""
echo "========= INFO RASPBERRY PI ========="

if command -v vcgencmd &> /dev/null; then
    CPU_TEMP=$(vcgencmd measure_temp | cut -d= -f2)
else
    CPU_TEMP="N/A"
fi
echo "[i] CPU Temp    : $CPU_TEMP"

MEM_FREE=$(free -h | awk '/^Mem:/ {print $4}')
echo "[i] RAM Bebas   : $MEM_FREE"

IP_ADDR=$(hostname -I | awk '{print $1}')
echo "[i] IP Address  : $IP_ADDR"

echo "====================================="
echo ""

# ----------------------------------------------------------
# 8. PILIH MODE
# ----------------------------------------------------------
echo "Mode:"
echo "1) Development"
echo "2) Production (NGINX + Gunicorn)"
echo "3) Supervisord"
echo "4) Test"
echo ""
read -p "Pilihan [1-4]: " MODE
echo ""

case $MODE in

# ----------------------------------------------------------
# MODE 1 - DEVELOPMENT
# ----------------------------------------------------------
1)
    echo "=== MODE DEVELOPMENT ==="
    echo "Server di: http://$IP_ADDR:5000"
    echo "CTRL + C untuk menghentikan"
    gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 --timeout 120 "app:create_app()"
    ;;

# ----------------------------------------------------------
# MODE 2 - PRODUCTION (NGINX + GUNICORN)
# ----------------------------------------------------------
2)
    echo "=== MODE PRODUCTION ==="

    NGINX_CONF="bms_server"

    echo "[+] Membuat konfigurasi NGINX..."

    sudo tee /etc/nginx/sites-available/$NGINX_CONF > /dev/null << EOF
server {
    listen 80;
    server_name $IP_ADDR;

    access_log /var/log/nginx/bms_access.log;
    error_log /var/log/nginx/bms_error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $(pwd)/app/static;
        try_files \$uri \$uri/ =404;
        expires 30d;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/$NGINX_CONF /etc/nginx/sites-enabled/

    echo "[+] Testing config..."
    sudo nginx -t || exit 1

    echo "[+] Restarting NGINX..."
    sudo systemctl restart nginx

    echo "[+] Menjalankan Gunicorn (daemon)..."
    gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 \
        --daemon --pid /tmp/gunicorn.pid \
        --access-logfile /tmp/gunicorn_access.log \
        --error-logfile /tmp/gunicorn_error.log \
        "app:create_app()"

    echo "[✓] Gunicorn berjalan (PID: \$(cat /tmp/gunicorn.pid))"
    echo "Akses: http://$IP_ADDR"

    read -p "Tekan Enter untuk menghentikan server..."

    echo "[+] Shutdown server..."
    kill $(cat /tmp/gunicorn.pid 2>/dev/null)
    sudo systemctl stop nginx
    echo "[✓] Server dimatikan."
    ;;

# ----------------------------------------------------------
# MODE 3 - SUPERVISORD
# ----------------------------------------------------------
3)
    echo "=== MODE SUPERVISORD ==="

    mkdir -p logs/

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

    echo "[✓] File dibuat: bms_supervisor.conf"
    echo "Install di supervisor:"
    echo "  sudo cp bms_supervisor.conf /etc/supervisor/conf.d/bms.conf"
    echo "  sudo supervisorctl reread"
    echo "  sudo supervisorctl update"
    echo "  sudo supervisorctl start bms_gunicorn"
    ;;

# ----------------------------------------------------------
# MODE 4 - TEST
# ----------------------------------------------------------
4)
    echo "=== MODE TEST ==="
    echo "Gunicorn manual:"
    echo "gunicorn -w 2 -b 0.0.0.0:5000 app:create_app"
    ;;

*)
    echo "[!] Pilihan salah, mode development aktif."
    gunicorn -w 2 -b 0.0.0.0:5000 "app:create_app()"
    ;;
esac

deactivate 2>/dev/null

echo ""
echo "======================================"
echo " BMS Launcher selesai"
echo "======================================"