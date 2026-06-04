@echo off
title RESET DATABASE DARURAT
echo PERINGATAN: Ini akan menghapus SELURUH data logistik Anda!
setlocal enabledelayedexpansion
title Reset Database Logistik App

echo ===================================================
echo       RESET DATABASE KE KONDISI BERSIH (TANPA SEED)
echo ===================================================
echo.
echo [PERINGATAN] Tindakan ini akan MENGHAPUS SEMUA DATA TRANSAKSI (Orders, Pengiriman).
echo Data yang tersisa hanya: Akun Admin, Armada (Default), dan Tarif (dari CSV).
echo.
pause

:: Menggunakan path default XAMPP Windows
c:\xampp\mysql\bin\mysql.exe -u root -e "DROP DATABASE IF EXISTS logistik_db; CREATE DATABASE logistik_db;"
c:\xampp\mysql\bin\mysql.exe -u root logistik_db < logistik_db.sql
:: 1. Reset Database via XAMPP
IF EXIST "c:\xampp\mysql\bin\mysql.exe" (
    echo.
    echo [1/3] Mereset Database 'logistik_db' via XAMPP...
    "c:\xampp\mysql\bin\mysql.exe" -u root -e "DROP DATABASE IF EXISTS logistik_db; CREATE DATABASE logistik_db;" >nul 2>&1
    IF EXIST "logistik_db.sql" (
        "c:\xampp\mysql\bin\mysql.exe" -u root logistik_db < logistik_db.sql
    )
) ELSE (
    echo [ERROR] XAMPP tidak ditemukan di path default. Proses dibatalkan.
    pause
    exit /b 1
)

echo Database berhasil di-reset ke pengaturan pabrik!
:: 2. Aktivasi Venv
echo [2/3] Mengaktifkan Virtual Environment...
IF NOT EXIST venv (
    echo [ERROR] Virtual environment tidak ditemukan. Silakan jalankan first_run.bat terlebih dahulu.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

:: 3. Import Tarif (Armada sudah otomatis masuk lewat logistik_db.sql)
echo [3/3] Mengimpor data tarif dasar (import_tarif.py)...
IF EXIST import_tarif.py (
    python import_tarif.py
)

echo.
echo [BERHASIL] Database telah dibersihkan. Silakan jalankan start_app.bat untuk memulai aplikasi.
pause