@echo off
title RESET DATABASE DARURAT
echo PERINGATAN: Ini akan menghapus SELURUH data logistik Anda!
pause

:: Menggunakan path default XAMPP Windows
c:\xampp\mysql\bin\mysql.exe -u root -e "DROP DATABASE IF EXISTS logistik_db; CREATE DATABASE logistik_db;"
c:\xampp\mysql\bin\mysql.exe -u root logistik_db < logistik_db.sql

echo Database berhasil di-reset ke pengaturan pabrik!
pause