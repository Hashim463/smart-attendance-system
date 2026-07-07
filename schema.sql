-- ==========================================================
-- Smart Attendance System - Database Schema
-- Run this once in MySQL before starting the app:
--   mysql -u root -p < schema.sql
-- ==========================================================

CREATE DATABASE IF NOT EXISTS smart_attendance;
USE smart_attendance;

-- Admin users (created manually / via seed script)
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    class_section VARCHAR(50),
    face_registered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance records
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    time_in TIME NOT NULL,
    status ENUM('Present', 'Late') DEFAULT 'Present',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance_per_day (student_id, date)
);

-- Seed an initial admin (username: admin / password: admin123)
-- Password hash generated with werkzeug.security.generate_password_hash("admin123")
-- Run seed_admin.py instead if you want a fresh hash matching your Werkzeug version.
