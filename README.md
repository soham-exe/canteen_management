# 🍔 Canteen Management System

A robust, full-stack web application designed to streamline canteen operations. This system manages the entire flow — from customers placing orders to kitchen staff marking them as ready. Built using **Python Flask** (backend) and **MySQL** for persistent, ACID-safe storage.

---

## 🚀 Project Overview

This project aims to eliminate chaos during peak lunch hours by offering:

- A smooth ordering experience for students/employees.
- A powerful admin panel for staff to track live orders.
- A reliable backend with transactional safety and strict business logic.

### 🔧 Key Engineering Highlights

- **RESTful API Architecture** — Clean separation using JSON-based communication  
- **ACID Transactions** — Ensures zero data loss; commits only on success  
- **Server-Side Validations** — Rules like “10-second cancellation window” enforced in backend  
- **Real-Time Processing** — Quick updates for both customers and kitchen staff  

---

## ✨ Features

### 👤 User Side
- **Digital Menu** — Items with images, descriptions, and prices  
- **Add to Cart & Checkout** — Fast, intuitive UX  
- **Live Order Tracking** — Know when your order is getting prepared  
- **Smart ETA** — Prep time computed based on all items in the cart  

### 👨‍🍳 Admin / Staff Side
- **Order Dashboard** — View new, ongoing, and ready orders  
- **Inventory-Friendly Flow** — Items fetched directly from DB  
- **Sales History** — Archive and analyze completed orders  

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|------------|
| **Backend** | Python (Flask) |
| **Database** | MySQL (`flask_mysqldb`) |
| **Frontend** | HTML5, CSS3, JavaScript (AJAX / Fetch API) |
| **Architecture** | MVC (Model–View–Controller) |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/soham-exe/canteen_management.git
cd canteen_management
```

### 2️⃣ Install Dependencies

```bash
pip install flask flask-mysqldb
```


### 3️⃣ Database Configuration

- **Open MySQL Workbench or CLI**
- **Run the schema below**
- **Update your credentials in app.py:**

```bash
app.config['MYSQL_USER'] = 'your_username'
app.config['MYSQL_PASSWORD'] = 'your_password'
```

### 4️⃣ Run the Application
```bash
python app.py
```

### ➡️ Visit http://localhost:5000

### 🗄️ Database Schema (Quick Start)
```bash
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

/* (Optional archive tables defined inside app.py) */
```

### 🧪 Test Scenarios & Expected Behavior

|Sr. No.|	Input / Action|	Expected Output|
|-------|------------------|---------------|
|1|	User places order (POST /place_order) with valid cart JSON|	Returns order_id; order saved with status Pending|
|2|	Simulated DB failure inside try-block|	Rollback triggered; no partial order saved|
|3|	User cancels order within 10 seconds|	Status becomes Cancelled|
|4|	User cancels order after 10 seconds	|403 Forbidden — “Cancellation window expired”|
|5|	Admin updates status via /admin/update_order_status_api	|Status updated (e.g., Pending → Preparing → Ready)|

**👨‍💻 Developed By Soham**