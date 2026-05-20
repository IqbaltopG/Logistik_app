@echo off

echo Menyiapkan Virtual Environment...
if not exist venv (
    python -m venv venv
)

echo Mengaktifkan Virtual Environment...
call venv\Scripts\activate

echo Menginstal Dependensi...
pip install -r requirements.txt

echo Mengekspor Environment Variables...
set FLASK_DEBUG=1
set FLASK_APP=app.py

echo Menjalankan Aplikasi Flask...
python app.py

pause
