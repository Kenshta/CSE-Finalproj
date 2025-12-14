CREATE DATABASE IF NOT EXISTS shoes_db;
USE shoes_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE shoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    size DECIMAL(3,1) NOT NULL,  -- e.g., 9.0, 10.5
    color VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL
);

-- Insert 21 realistic shoe records
INSERT INTO shoes (brand, model, size, color, price, stock) VALUES
('Nike', 'Air Max 270', 9.0, 'Black/White', 150.00, 25),
('Adidas', 'Ultraboost 22', 10.5, 'Core Black', 180.00, 18),
('Puma', 'RS-X', 8.0, 'White/Red', 110.00, 30),
('New Balance', '574', 11.0, 'Navy', 85.00, 22),
('Reebok', 'Classic Leather', 9.5, 'White', 75.00, 40),
('Converse', 'Chuck Taylor All Star', 8.5, 'Red', 60.00, 50),
('Vans', 'Old Skool', 10.0, 'Black', 70.00, 35),
('Nike', 'Air Force 1', 12.0, 'White', 110.00, 20),
('Adidas', 'Stan Smith', 9.0, 'Green/White', 90.00, 28),
('Puma', 'Suede Classic', 8.0, 'Blue', 80.00, 33),
('Asics', 'Gel-Kayano 29', 10.0, 'Black/Orange', 160.00, 15),
('Brooks', 'Ghost 15', 9.5, 'Blue/Silver', 140.00, 12),
('Skechers', 'D''Lites', 7.0, 'White/Pink', 65.00, 45),
('Under Armour', 'HOVR Phantom', 11.0, 'Gray', 130.00, 17),
('New Balance', '990v5', 10.5, 'Gray', 185.00, 10),
('Nike', 'ZoomX Invincible Run', 9.0, 'Volt', 180.00, 8),
('Adidas', 'NMD_R1', 8.5, 'White/Blue', 140.00, 24),
('Puma', 'Future Rider', 9.0, 'Yellow/Black', 90.00, 30),
('Reebok', 'Nano X2', 10.0, 'Black/Green', 140.00, 14),
('Converse', 'One Star', 8.0, 'Black', 70.00, 38),
('Vans', 'Sk8-Hi', 9.5, 'Red/White', 75.00, 27);