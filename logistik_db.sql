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
    rute VARCHAR(255) NOT NULL,
    harga_cdd INT NOT NULL,
    harga_fuso INT NOT NULL,
    harga_tronton INT NOT NULL,
    harga_trailer INT NOT NULL
);


CREATE TABLE armada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plat_nomor VARCHAR(50) NOT NULL UNIQUE,
    tipe_armada ENUM('CDD', 'Fuso', 'Tronton', 'Trailer', 'Trailer 20 Feet', 'Trailer 40 Feet', 'Dolly') NOT NULL,
    status ENUM('Tersedia', 'Beroperasi') DEFAULT 'Tersedia'
);

INSERT INTO armada (plat_nomor, tipe_armada, status) VALUES
('KT 8001 AA', 'CDD', 'Tersedia'),
('KT 8002 BB', 'Fuso', 'Tersedia'),
('KT 8003 CC', 'Tronton', 'Tersedia'),
('KT 8004 DD', 'Trailer 20 Feet', 'Beroperasi'),
('KT 8005 EE', 'Trailer 40 Feet', 'Tersedia');

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    detail_barang TEXT NOT NULL,
    jenis_layanan VARCHAR(50) NOT NULL,
    rute VARCHAR(255) NOT NULL,
    jenis_armada VARCHAR(50) NOT NULL,
    jumlah_unit INT DEFAULT 1,
    total_harga INT NOT NULL,
    status_order ENUM('Pending', 'Valid', 'Tidak Valid') DEFAULT 'Pending', 
    status_pembayaran VARCHAR(50) DEFAULT 'Belum Bayar',
    no_resi VARCHAR(100) UNIQUE NULL,
    alasan_pembatalan TEXT NULL,
    cancelled_by ENUM('Customer', 'Admin') NULL,
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
