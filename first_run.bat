@echo off
setlocal enabledelayedexpansion
title Setup Logistik App

echo ===================================================
echo       SETUP ^& PROVISIONING LOGISTIK APP
echo ===================================================
echo.
echo [INFO] Pastikan layanan XAMPP (Apache ^& MySQL) sudah AKTIF.
echo.

:: 0. Auto-Reset Database (Jika menggunakan XAMPP Windows Default)
IF EXIST "c:\xampp\mysql\bin\mysql.exe" (
    echo [0/5] Mereset Database 'logistik_db' via XAMPP...
    "c:\xampp\mysql\bin\mysql.exe" -u root -e "DROP DATABASE IF EXISTS logistik_db; CREATE DATABASE logistik_db;" >nul 2>&1
    IF EXIST "logistik_db.sql" (
        "c:\xampp\mysql\bin\mysql.exe" -u root logistik_db < logistik_db.sql
    )
) ELSE (
    echo [WARN] XAMPP tidak ditemukan di path default. Pastikan database 'logistik_db' sudah dibuat.
)

:: 1. Cek Python
python --version >nul 2>&1
IF !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Python tidak terdeteksi. Silakan install Python dan pastikan "Add Python to PATH" dicentang.
    pause
    exit /b 1
)

echo.
echo [1/5] Menyiapkan Virtual Environment (venv)...
IF NOT EXIST venv (
    python -m venv venv
)

echo [2/5] Mengaktifkan venv ^& menginstall dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/5] Membangun skema database...
python -c "from app import app, db; ctx=app.app_context(); ctx.push(); db.create_all()"

echo [4/5] Mengimpor data tarif (import_tarif.py)...
IF EXIST import_tarif.py (
    python import_tarif.py
)

echo [5/5] Melakukan seeding pesanan dummy...
python seed.py

echo.
echo ===================================================
echo       PROVISIONING SELESAI ^& BERHASIL
echo ===================================================
pause