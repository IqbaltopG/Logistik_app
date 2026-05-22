@echo off
title Menjalankan Aplikasi Logistik

echo 🔄 Mereset dan sinkronisasi database dari file SQL...
c:\xampp\mysql\bin\mysql.exe -u root -e "DROP DATABASE IF EXISTS logistik_db; CREATE DATABASE logistik_db;"
c:\xampp\mysql\bin\mysql.exe -u root logistik_db < logistik_db.sql

echo 📦 Mempersiapkan Virtual Environment Python...
if not exist "venv" (
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo 📥 Mengimpor data tarif asli dari file CSV...
python import_tarif.py

echo 🌱 Melakukan seeding data pesanan...
flask seed

echo 🚀 Menyandera server... Aplikasi berjalan di http://localhost:5000
set FLASK_DEBUG=1
python app.py
pause