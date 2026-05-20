#!/bin/bash

echo "🔄 Mereset dan sinkronisasi database dari file SQL..."
sudo /opt/lampp/bin/mysql -u root -e "DROP DATABASE IF EXISTS logistik_db; CREATE DATABASE logistik_db;"
sudo /opt/lampp/bin/mysql -u root logistik_db < logistik_db.sql

echo "📦 Mempersiapkan Virtual Environment Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Menyandera server... Aplikasi berjalan di http://localhost:5000"
export FLASK_DEBUG=1
python3 app.py