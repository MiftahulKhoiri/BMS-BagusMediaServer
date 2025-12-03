#!/bin/bash
#
# ==============================================
#  BMS - BagusMediaServer Raspberry Pi Launcher
#  FINAL VERSION — AUTO STATIC NGINX + AUTO INSTALL
# ==============================================


echo "=== BMS - BagusMediaServer Launcher ==="
echo ""

# ----------------------------------------------------------
# 0. DETEKSI FOLDER PROJECT OTOMATIS
# ----------------------------------------------------------
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STATIC_DIR="$PROJECT_DIR/app/static"

echo "[i] Project Directory: $PROJECT_DIR"
echo "[i] Static Directory : $STATIC_DIR"
echo ""


# ----------------------------------------------------------
# 1. CEGAH JALAN SEBAGAI ROOT
# ----------------------------------------------------------
if [[ $EUID -eq 0 ]]; then
    echo "[!] Jangan jalankan script ini sebagai root!"
    exit 1
fi


# ----------------------------------------------------------
# 2. AUTO INSTALL NGINX & SUPERVISOR
# ----------------------------------------------------------
echo "=== Mengecek kebutuhan sistem ==="
sudo apt update -y

# Install Nginx
if ! command -v nginx &> /dev/null; then
    echo "[+] Menginstall NGINX..."
    sudo apt install -y nginx
else
    echo "[✓] NGINX sudah ada."
fi

# Install Supervisor
if ! command -v supervisorctl &> /dev/null; then
    echo "[+] Menginstall Supervisor..."
    sudo apt install -y supervisor
else
    echo "[✓] Supervisor sudah ada."
fi

echo ""


# ----------------------------------------------------------
# 3. CEK & BUAT VENV
# ----------------------------------------------------------
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Membuat Virtual Environment..."
    python3 -m venv $VENV_DIR
else
    echo "[✓] Virtual Environment ditemukan."
fi


# ----------------------------------------------------------
# 4. AKTIVASI VENV
# ----------------------------------------------------------
echo "[+] Mengaktifkan venv..."
source "$VENV_DIR/bin/activate"


# ----------------------------------------------------------
# 5. INSTALL REQUIREMENTS
# ----------------------------------------------------------
echo "[+] Update pip..."
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    echo "[+] Install dependencies..."
    pip install -r requirements.txt
else
    echo "[!] File requirements.txt tidak ditemukan."
fi


# ----------------------------------------------------------
# 6. INFO SISTEM
# ----------------------------------------------------------
IP_ADDR=$(hostname -I | awk '{print $1}')
if command -v vcgencmd &>/dev/null; then
    CPU_TEMP=$(vcgencmd measure_temp | cut -d= -f2)
else
    CPU_TEMP="N/A"
fi

echo ""
echo "=========== INFO RASPBERRY PI ==========="
echo "[i] IP Address : $IP_ADDR"
echo "[i] CPU Temp   : $CPU_TEMP"
echo "========================================="
echo ""


# ----------------------------------------------------------
# 7. MENU MODE JALAN
# ----------------------------------------------------------
echo "Pilih Mode:"
echo "1) Development"
echo "2) Production (NGINX + Gunicorn)"
echo "3) Supervisord"
echo "4) Test"
echo ""

read -p "Pilihan [1-4]: " MODE
echo ""


case $MODE in

# ==========================================================
# MODE 1 — DEVELOPMENT
# ==========================================================
1)
    echo "=== MODE DEVELOPMENT ==="
    echo "Akses: http://$IP_ADDR:5000"
    gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 "app:create_app()"
    ;;


# ==========================================================
# MODE 2 — PRODUCTION
# ==========================================================
2)
    echo "=== MODE PRODUCTION (NGINX + GUNICORN) ==="

    NGINX_CONF="bms_server"

    # Buat konfigurasi nginx dengan placeholder STATIC_PATH_FIX
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
        alias STATIC_PATH_FIX;
        try_files \$uri \$uri/ =404;
        expires 30d;
    }
}
EOF

    # Ganti placeholder STATIC_PATH_FIX dengan path static asli
    sudo sed -i "s|STATIC_PATH_FIX|$STATIC_DIR|g" /etc/nginx/sites-available/$NGINX_CONF

    # Enable config
    sudo ln -sf /etc/nginx/sites-available/$NGINX_CONF /etc/nginx/sites-enabled/

    # Reload nginx
    sudo nginx -t
    sudo systemctl restart nginx

    echo "[+] Menjalankan Gunicorn..."
    gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 \
        --daemon --pid /tmp/gunicorn.pid \
        --access-logfile /tmp/gunicorn_access.log \
        --error-logfile /tmp/gunicorn_error.log \
        "app:create_app()"

    echo "Akses sekarang: http://$IP_ADDR"
    ;;


# ==========================================================
# MODE 3 — SUPERVISORD
# ==========================================================
3)
    echo "=== MODE SUPERVISORD ==="

    mkdir -p logs/

    cat > bms_supervisor.conf << EOF
[program:bms_gunicorn]
directory=$PROJECT_DIR
command=$PROJECT_DIR/$VENV_DIR/bin/gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 "app:create_app()"
user=$USER
autostart=true
autorestart=true
stderr_logfile=$PROJECT_DIR/logs/gunicorn_err.log
stdout_logfile=$PROJECT_DIR/logs/gunicorn_out.log
environment=PATH="$PROJECT_DIR/$VENV_DIR/bin"
EOF

    echo "[✓] File supervisor dibuat: bms_supervisor.conf"
    echo "Install:"
    echo " sudo cp bms_supervisor.conf /etc/supervisor/conf.d/bms.conf"
    echo " sudo supervisorctl reread"
    echo " sudo supervisorctl update"
    echo " sudo supervisorctl start bms_gunicorn"
    ;;


# ==========================================================
# MODE 4 — TEST
# ==========================================================
4)
    echo "=== TEST MODE ==="
    echo "Gunicorn manual:"
    echo "gunicorn -w 2 -b 0.0.0.0:5000 app:create_app"
    ;;

*)
    echo "Pilihan tidak valid."
    ;;
esac


# ----------------------------------------------------------
# DEACTIVATE VENV
# ----------------------------------------------------------
deactivate 2>/dev/null
echo ""
echo "=== BMS Launcher Selesai ==="