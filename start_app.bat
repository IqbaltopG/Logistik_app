@echo off
setlocal enabledelayedexpansion
title Aplikasi Logistik (Server)

echo ===================================================
echo           MULAI APLIKASI LOGISTIK (DEV)
echo ===================================================
echo.

:: Auto-Setup jika client baru pertama kali membuka
IF NOT EXIST venv (
    echo [INFO] Setup awal terdeteksi. Melakukan konfigurasi otomatis...
    call first_run.bat
)

echo [INFO] Mengaktifkan Virtual Environment...
call venv\Scripts\activate.bat

echo [INFO] Menyiapkan environment variables...
set FLASK_DEBUG=1
set FLASK_APP=app.py

echo [INFO] Menjalankan instance Flask server...
echo [INFO] Akses aplikasi di: http://127.0.0.1:5000
echo ===================================================
python app.py

echo.
echo [WARN] Server dihentikan oleh user atau terjadi crash.
pause