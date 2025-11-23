#!/bin/bash

echo "=== BMS - BagusMediaServer Launcher ==="

# Nama folder virtual environment
VENV_DIR="venv"

# ----------------------------------------
# 1. CEK APAKAH VIRTUAL ENV SUDAH ADA
# ----------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Virtual environment belum ada. Membuat venv baru..."
    python3 -m venv $VENV_DIR

    if [ $? -ne 0 ]; then
        echo "[!] Gagal membuat virtual environment!"
        exit 1
    fi
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
# 3. UPDATE pip
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
# 5. MENJALANKAN FLASK SERVER
# ----------------------------------------
echo ""
echo "======================================"
echo " Menjalankan BMS Server (run.py)..."
echo "======================================"
echo ""

python3 run.py

# ----------------------------------------
# Setelah selesai
# ----------------------------------------
echo ""
echo "[✓] BMS Server selesai dijalankan."