🍔 Canteen Management System

A robust, full-stack web application designed to streamline canteen operations. This system manages the entire flow from a customer placing an order to the kitchen staff marking it as ready, utilizing Python Flask for the backend and MySQL for data persistence.

🚀 Project Overview

This project solves the problem of chaos during peak lunch hours. It features a user-friendly interface for students/employees to order food and a powerful admin dashboard for staff to manage inventory and orders in real-time.

Key Engineering Highlights:

RESTful API Architecture: Decoupled client-server communication using JSON.

ACID Transactions: Implemented complex SQL transaction blocks with commit and rollback to ensure zero data loss during orders.

Server-Side Validation: Enforces strict business logic (e.g., 10-second order cancellation window).

✨ Key Features

Digital Menu: Interactive menu with images and descriptions.

Instant Ordering: Seamless "Add to Cart" and checkout experience.

Live Status Tracking: Real-time order status updates for customers.

Smart Time Estimation: Automatically calculates prep time based on cart items.

Admin Dashboard: comprehensive view for kitchen staff to manage incoming orders.

Sales History: Archival system for completed orders and sales analytics.

🛠️ Tech Stack

Backend: Python (Flask)

Database: MySQL (using flask_mysqldb)

Frontend: HTML5, CSS3, JavaScript (AJAX/Fetch API)

Architecture: MVC (Model-View-Controller)

⚙️ Installation & Setup

Clone the repository

git clone [https://github.com/soham-exe/canteen_management.git](https://github.com/soham-exe/canteen_management.git)
cd canteen_management


Install Dependencies

pip install flask flask-mysqldb


Database Configuration

Open your MySQL Client (Workbench or Command Line).

Create the database and tables (Schema provided below).

Update app.py with your credentials:

app.config['MYSQL_USER'] = 'your_username'
app.config['MYSQL_PASSWORD'] = 'your_password'


Run the Application

python app.py


Access the app at http://localhost:5000.

🗄️ Database Schema (Quick Start)

Execute this SQL to get started:

CREATE DATABASE canteen_db;
USE canteen_db;

CREATE TABLE menu_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    price DECIMAL(10,2),
    preparation_time INT,
    image_url VARCHAR(255)
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    total_price DECIMAL(10,2),
    order_status VARCHAR(50) DEFAULT 'Pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_completion_time DATETIME
);

CREATE TABLE order_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    item_id INT,
    quantity INT,
    price_per_item DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
-- (Add archive tables as seen in app.py)


🧪 Test Scenarios & System Behavior

Sr. No.

Input Action / Code Logic

Expected Output / Behavior

1

User Action: Place Order 



 POST /place_order with valid Cart JSON

Success: Returns order_id, saves to DB, and status becomes 'Pending'.

2

System Logic: Error during DB write 



 (Simulated SQL Failure inside try block)

Rollback: mysql.connection.rollback() triggers. Order is NOT saved. Database stays consistent.

3

User Action: Cancel Order 



 POST /cancel_order/<id> (Time < 10s)

Success: Order status updates to 'Cancelled'.

4

User Action: Cancel Order 



 POST /cancel_order/<id> (Time > 10s)

Forbidden (403): Returns "Cancellation window expired."

5

Admin Action: Mark Ready 



 `POST /admin

