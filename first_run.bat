@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo       SETUP ^& PROVISIONING LOGISTIK APP
echo ===================================================
echo.
echo [INFO] Pastikan layanan XAMPP (Apache ^& MySQL) sudah AKTIF sebelum melanjutkan.
pause
echo.

echo [1/5] Memeriksa Virtual Environment (venv)...
IF NOT EXIST venv (
    echo [INFO] Direktori 'venv' tidak ditemukan. Membuat virtual environment baru...
    python -m venv venv
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Gagal membuat virtual environment. Pastikan Python terinstall dan terdaftar di PATH.
        pause
        exit /b 1
    )
) ELSE (
    echo [INFO] Direktori 'venv' sudah ada.
)

echo.
echo [2/5] Mengaktifkan venv ^& menginstall dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
IF !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Gagal menginstall packages dari requirements.txt.
    pause
    exit /b 1
)

echo.
echo [3/5] Membangun skema database...
python -c "from app import app, db; ctx=app.app_context(); ctx.push(); db.create_all()"
IF !ERRORLEVEL! NEQ 0 (
    echo [WARN] Pembuatan skema database via inline python gagal. Melakukan fallback ke Flask-Migrate...
    flask db init
    flask db migrate -m "Initial schema"
    flask db upgrade
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Flask-Migrate gagal. Pastikan database MySQL 'logistik_db' sudah dibuat.
        pause
        exit /b 1
    )
)

echo.
echo [4/5] Mengimpor data tarif (import_tarif.py)...
IF EXIST import_tarif.py (
    python import_tarif.py
) ELSE (
    echo [WARN] File import_tarif.py tidak ditemukan. Proses dilewati.
)

echo.
echo [5/5] Melakukan seeding pesanan dummy...
flask seed
IF !ERRORLEVEL! NEQ 0 (
    echo [WARN] Perintah 'flask seed' gagal. Melakukan fallback ke eksekusi file script langsung...
    IF EXIST seed.py (
        python seed.py
    ) ELSE (
        echo [WARN] File seed.py tidak ditemukan. Proses seeding dilewati.
    )
)

echo.
echo ===================================================
echo       PROVISIONING SELESAI ^& BERHASIL
echo ===================================================
pause