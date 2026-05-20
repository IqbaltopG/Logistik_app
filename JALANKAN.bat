@echo off
title Logistik Admin App
echo Memulai Sistem...
echo Pastikan XAMPP (Apache & MySQL) sudah menyala!

if not exist "venv\" (
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo Server berjalan! Buka http://localhost:5000
start http://localhost:5000
python app.py
pause