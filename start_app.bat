@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo           MULAI APLIKASI LOGISTIK (DEV)
echo ===================================================
echo.

echo [INFO] Memeriksa kesiapan environtment...
IF NOT EXIST venv (
    echo [ERROR] Direktori 'venv' tidak ditemukan!
    echo [INFO] Harap jalankan 'first_run.bat' terlebih dahulu untuk melakukan inisialisasi awal.
    pause
    exit /b 1
)

echo [INFO] Mengaktifkan Virtual Environment...
call venv\Scripts\activate.bat

echo [INFO] Menyiapkan environment variables...
set FLASK_DEBUG=1

echo [INFO] Menjalankan instance Flask server...
echo ===================================================
python app.py

echo.
echo [INFO] Server dihentikan oleh user atau terjadi crash.
pause