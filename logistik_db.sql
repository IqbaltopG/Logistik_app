CREATE DATABASE IF NOT EXISTS logistik_db;
USE logistik_db;

DROP TABLE IF EXISTS pengiriman;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS armada;
DROP TABLE IF EXISTS tarif;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'customer') NOT NULL
);

CREATE TABLE tarif (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kota_asal VARCHAR(100) NOT NULL,
    kota_tujuan VARCHAR(100) NOT NULL,
    harga_dasar FLOAT NOT NULL,
    harga_per_kg FLOAT NOT NULL,
    harga_per_m3 FLOAT NOT NULL
);

INSERT INTO tarif (kota_asal, kota_tujuan, harga_dasar, harga_per_kg, harga_per_m3) VALUES
('Balikpapan', 'Samarinda', 500000, 2000, 50000),
('Samarinda', 'Bontang', 600000, 2500, 60000),
('Balikpapan', 'Kutai Kartanegara', 700000, 3000, 70000),
('Kutai Kartanegara', 'Kutai Timur', 800000, 3500, 80000);

CREATE TABLE armada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plat_nomor VARCHAR(50) NOT NULL UNIQUE,
    tipe_armada ENUM('Tronton', 'Trailer', 'Dolly') NOT NULL,
    status ENUM('Tersedia', 'Beroperasi') DEFAULT 'Tersedia'
);

INSERT INTO armada (plat_nomor, tipe_armada, status) VALUES
('KT 8001 AA', 'Tronton', 'Tersedia'),
('KT 8002 BB', 'Trailer', 'Tersedia'),
('KT 8003 CC', 'Dolly', 'Beroperasi');

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    detail_barang TEXT NOT NULL,
    tipe_barang ENUM('Container', 'Cargo') NOT NULL,
    kota_asal VARCHAR(100) NOT NULL,
    kota_tujuan VARCHAR(100) NOT NULL,
    berat_kg FLOAT NOT NULL,
    dimensi_p FLOAT DEFAULT NULL,
    dimensi_l FLOAT DEFAULT NULL,
    dimensi_t FLOAT DEFAULT NULL,
    estimasi_harga FLOAT NOT NULL,
    status_order ENUM('Pending', 'Valid', 'Tidak Valid') DEFAULT 'Pending', 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE pengiriman (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    driver_nama VARCHAR(255) NOT NULL,
    armada_id INT NOT NULL,
    status_pengiriman ENUM('Penjadwalan', 'Di Perjalanan', 'Terkirim') DEFAULT 'Penjadwalan',
    epod_ref VARCHAR(255),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (armada_id) REFERENCES armada(id) ON DELETE CASCADE
);
