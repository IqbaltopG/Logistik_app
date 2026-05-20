CREATE DATABASE IF NOT EXISTS logistik_db;
USE logistik_db;

DROP TABLE IF EXISTS pengiriman;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS tarif;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    role ENUM('admin', 'customer') NOT NULL
);

INSERT INTO users (username, password, role) VALUES 
('admin', 'admin', 'admin'),
('cust1', 'cust1', 'customer');

CREATE TABLE tarif (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kota_asal VARCHAR(100) NOT NULL,
    kota_tujuan VARCHAR(100) NOT NULL,
    harga INT NOT NULL
);

INSERT INTO tarif (kota_asal, kota_tujuan, harga) VALUES
('Jakarta', 'Bandung', 500000),
('Jakarta', 'Surabaya', 1500000),
('Surabaya', 'Malang', 300000),
('Bandung', 'Semarang', 800000);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    detail_barang TEXT NOT NULL,
    kota_asal VARCHAR(100) NOT NULL,
    kota_tujuan VARCHAR(100) NOT NULL,
    status_order ENUM('Pending', 'Valid', 'Tidak Valid') DEFAULT 'Pending', 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE pengiriman (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    driver_nama VARCHAR(255) NOT NULL,
    armada_plat VARCHAR(50) NOT NULL,
    status_pengiriman ENUM('Penjadwalan', 'Di Perjalanan', 'Terkirim') DEFAULT 'Penjadwalan',
    epod_ref VARCHAR(255),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
