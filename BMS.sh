#!/bin/bash

echo "=== BMS - BagusMediaServer Launcher ==="

# Nama folder virtual environment
VENV_DIR="venv"

# ----------------------------------------
# 1. CEK VIRTUAL ENVIRONMENT
# ----------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Virtual environment belum ada. Membuat venv baru..."
    python3 -m venv $VENV_DIR
else
    echo "[✓] Virtual environment sudah ada."
fi

# ----------------------------------------
# 2. AKTIVASI VIRTUAL ENV
# ----------------------------------------
echo "[+] Mengaktifkan virtual environment..."
source $VENV_DIR/bin/activate

if [ $? -ne 0 ]; then
    echo "[!] Gagal mengaktifkan virtual environment!"
    exit 1
fi

# ----------------------------------------
# 3. UPDATE PIP
# ----------------------------------------
echo "[+] Update pip..."
pip install --upgrade pip

# ----------------------------------------
# 4. INSTALL REQUIREMENTS
# ----------------------------------------
if [ -f "requirements.txt" ]; then
    echo "[+] Menginstall dependencies dari requirements.txt..."
    pip install -r requirements.txt
else
    echo "[!] requirements.txt tidak ditemukan!"
fi

# ----------------------------------------
# 5. MENJALANKAN BMS DENGAN GUNICORN
# ----------------------------------------
echo ""
echo "======================================"
echo " Menjalankan BMS via Gunicorn..."
echo "======================================"
echo ""

# Sesuaikan jika create_app kamu ada di file app.py
gunicorn -w 3 -b 127.0.0.1:5000 "app:create_app()"

# Setelah Gunicorn mati (CTRL+C)
echo ""
echo "[✓] BMS Server dihentikan."