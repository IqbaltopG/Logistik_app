#!/bin/bash

echo "Menyiapkan Virtual Environment..."
python3 -m venv venv

echo "Mengaktifkan Virtual Environment..."
source venv/bin/activate

echo "Menginstal Dependensi..."
pip install -r requirements.txt

echo "Mengekspor Environment Variables..."
export FLASK_DEBUG=1
export FLASK_APP=app.py

echo "Menjalankan Aplikasi Flask..."
python app.py
