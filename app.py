from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_mysqldb import MySQL
from datetime import datetime, timedelta

app = Flask(__name__)

# --- MySQL Configuration ---
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password' # Ensure this is your correct password
app.config['MYSQL_DB'] = 'canteen_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # Returns results as dictionaries

# Secret key for Flask session messages (e.g., flash messages)
app.secret_key = 'supersecretkey' # Change this in a production environment

mysql = MySQL(app)

# --- Admin Credentials ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123" # Use a more secure method in production

# ===================================================
# <<< CUSTOMER-FACING ROUTES >>>
# ===================================================

@app.route('/')
def index():
    """Renders the customer homepage with the menu and canteen status."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM menu_items ORDER BY item_id")
        menu_items = cur.fetchall()

        # Fetch canteen status (defaults to CLOSED if not found)
        cur.execute("SELECT setting_value FROM canteen_status WHERE setting_key = 'canteen_open_status'")
        status_result = cur.fetchone()
        canteen_status = status_result['setting_value'] if status_result else 'CLOSED'
    finally:
        cur.close()

    return render_template('index.html', menu_items=menu_items, canteen_status=canteen_status)

@app.route('/place_order', methods=['POST'])
def place_order():
    """Handles order submission from customer, calculates completion time, and saves to DB."""
    try:
        data = request.get_json()
        customer_name = data.get('customer_name')
        cart = data.get('cart')
        total_price = data.get('total_price')

        if not customer_name or not cart:
            return jsonify({'success': False, 'message': 'Name and cart cannot be empty.'}), 400

        cur = mysql.connection.cursor()
        
        # Calculate maximum preparation time from cart items
        item_ids = [item['id'] for item in cart]
        if not item_ids: # Prevent SQL error if cart somehow empty
             return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

        placeholders = ','.join(['%s'] * len(item_ids))
        cur.execute(f"SELECT MAX(preparation_time) as max_time FROM menu_items WHERE item_id IN ({placeholders})", tuple(item_ids))
        result = cur.fetchone()
        max_prep_time = result['max_time'] if result and result['max_time'] is not None else 5 # Default 5 mins

        completion_time = datetime.now() + timedelta(minutes=max_prep_time)

        # Insert into 'orders' table
        cur.execute(
            "INSERT INTO orders (customer_name, total_price, estimated_completion_time) VALUES (%s, %s, %s)",
            (customer_name, total_price, completion_time)
        )
        order_id = cur.lastrowid

        # Insert into 'order_details' table
        for item in cart:
            cur.execute(
                "INSERT INTO order_details (order_id, item_id, quantity, price_per_item) VALUES (%s, %s, %s, %s)",
                (order_id, item['id'], item['quantity'], item['price'])
            )
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True, 'order_id': order_id})

    except Exception as e:
        mysql.connection.rollback()
        print(f"Error placing order: {e}")
        # Close cursor if it's still open after an error during commit
        if 'cur' in locals() and cur: cur.close() 
        return jsonify({'success': False, 'message': 'An error occurred while placing the order.'}), 500

@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    """Displays the order receipt page after successful placement."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM orders WHERE order_id = %s", [order_id])
        order = cur.fetchone()

        if not order:
            return "Order not found.", 404

        cur.execute("""
            SELECT mi.name, od.quantity, od.price_per_item 
            FROM order_details od
            JOIN menu_items mi ON od.item_id = mi.item_id
            WHERE od.order_id = %s
        """, [order_id])
        order_items = cur.fetchall()
    finally:
        cur.close()

    return render_template('order_success.html', order=order, order_items=order_items)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    """API endpoint for customers to cancel their order within 10 seconds."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT order_date, order_status FROM orders WHERE order_id = %s", [order_id])
        order_data = cur.fetchone()

        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found.'}), 404
        
        if order_data['order_status'] != 'Pending':
            return jsonify({'success': False, 'message': 'This order can no longer be cancelled.'}), 400

        # Server-side validation of the 10-second window
        time_difference = datetime.now() - order_data['order_date']
        if time_difference.total_seconds() > 10:
            return jsonify({'success': False, 'message': 'The 10-second cancellation window has expired.'}), 403

        # Update status if validation passes
        cur.execute("UPDATE orders SET order_status = 'Cancelled' WHERE order_id = %s", [order_id])
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Your order has been cancelled.'})

    except Exception as e:
        mysql.connection.rollback()
        print(f"Cancellation Error: {e}")
        return jsonify({'success': False, 'message': 'A server error occurred during cancellation.'}), 500
    finally:
        cur.close()

@app.route('/track')
def track_order_page():
    """Renders the customer-facing order tracking page."""
    return render_template('track_order.html')

@app.route('/get_order_status/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    """API endpoint to fetch full order details for the tracking page."""
    cur = mysql.connection.cursor()
    try:
        # Check active orders first
        cur.execute("""
            SELECT customer_name, total_price, order_status, estimated_completion_time 
            FROM orders WHERE order_id = %s
        """, [order_id])
        order_summary = cur.fetchone()
        item_details = []

        if order_summary:
            # Fetch details from active order_details table
            cur.execute("""
                SELECT mi.name, od.quantity FROM order_details od
                JOIN menu_items mi ON od.item_id = mi.item_id
                WHERE od.order_id = %s
            """, [order_id])
            item_details = cur.fetchall()
        else:
            # If not active, check the archive summary
            cur.execute("""
                SELECT customer_name, total_price, 'Completed' as order_status, 
                       completion_time as estimated_completion_time
                FROM completed_orders_archive WHERE order_id = %s
            """, [order_id])
            order_summary = cur.fetchone()

            if order_summary:
                # Fetch details from the details archive table
                cur.execute("""
                    SELECT item_name as name, quantity FROM completed_order_details_archive
                    WHERE order_id = %s
                """, [order_id])
                item_details = cur.fetchall()

        if not order_summary:
            return jsonify({'success': False, 'message': 'Order not found.'}), 404
        
        # Prepare JSON response with proper serialization
        return jsonify({
            'success': True, 
            'status': order_summary['order_status'],
            'completion_time': order_summary['estimated_completion_time'].isoformat() if order_summary.get('estimated_completion_time') else None,
            'customer_name': order_summary['customer_name'],
            'total_price': float(order_summary['total_price']),
            'items': item_details # Assumes DictCursor returns list of dicts
        })

    except Exception as e:
        print(f"Error fetching order status: {e}")
        return jsonify({'success': False, 'message': 'A server error occurred while fetching status.'}), 500
    finally:
         if cur: cur.close()

# ===================================================
# <<< ADMIN ROUTES >>>
# ===================================================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Handles admin login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # NOTE: Use flask-login or similar for secure session management in production
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Renders the admin dashboard for live orders."""
    cur = mysql.connection.cursor()
    try:
        # Auto-complete orders that have passed their estimated completion time
        cur.execute("""
            UPDATE orders
            SET order_status = 'Completed'
            WHERE order_status = 'Pending'
            AND estimated_completion_time IS NOT NULL 
            AND estimated_completion_time <= NOW()
        """)
        mysql.connection.commit()

        # Fetch remaining active orders
        cur.execute("SELECT * FROM orders ORDER BY order_id ASC")
        orders = cur.fetchall()
    finally:
        cur.close()
    
    return render_template('admin_dashboard_ajax.html', orders=orders)

@app.route('/admin/menu')
def admin_menu():
    """Renders the menu management page."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT item_id, name, description, price, preparation_time, image_url FROM menu_items ORDER BY item_id")
        menu_items = cur.fetchall()
    finally:
        cur.close()
    return render_template('admin_menu.html', menu_items=menu_items)

# --- Admin CRUD Operations for Menu Items ---

@app.route('/admin/menu/add', methods=['POST'])
def add_menu_item():
    """Handles adding a new menu item."""
    try:
        name = request.form['name']
        price = request.form['price']
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', '')
        preparation_time = request.form['preparation_time']
        
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO menu_items (name, description, price, preparation_time, image_url) VALUES (%s, %s, %s, %s, %s)",
            (name, description, price, preparation_time, image_url)
        )
        mysql.connection.commit()
        cur.close()
        flash(f'"{name}" added to the menu.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error adding menu item: {e}")
        flash('Error adding item. Please check input.', 'danger')
        if 'cur' in locals() and cur: cur.close()
    return redirect(url_for('admin_menu'))
    
@app.route('/admin/menu/edit/<int:item_id>', methods=['POST'])
def edit_menu_item(item_id):
    """Handles updating an existing menu item."""
    try:
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        preparation_time = request.form['preparation_time']
        image_url = request.form['image_url']
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE menu_items 
            SET name=%s, description=%s, price=%s, preparation_time=%s, image_url=%s 
            WHERE item_id=%s
        """, (name, description, price, preparation_time, image_url, item_id))
        mysql.connection.commit()
        cur.close()
        flash(f'"{name}" updated successfully.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error editing menu item: {e}")
        flash('Error updating item.', 'danger')
        if 'cur' in locals() and cur: cur.close()
    return redirect(url_for('admin_menu'))

@app.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    """Handles deleting a menu item."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM menu_items WHERE item_id = %s", [item_id])
        mysql.connection.commit()
        cur.close()
        flash('Item deleted successfully.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error deleting menu item: {e}")
        flash('Error deleting item. It might be referenced in past orders.', 'danger')
        if 'cur' in locals() and cur: cur.close()
    return redirect(url_for('admin_menu'))

# --- Admin API Routes ---

@app.route('/admin/update_order_status_api', methods=['POST'])
def update_order_status_api():
    """API endpoint for 'Mark Ready' button; archives order and details."""
    data = request.get_json()
    order_id = data.get('order_id')
    
    if not order_id:
        return jsonify({'success': False, 'message': 'Missing order ID.'}), 400

    cur = mysql.connection.cursor()
    mysql.connection.begin() 
    try:
        # Clean up potential duplicates in archives first
        cur.execute("DELETE FROM completed_orders_archive WHERE order_id = %s", [order_id])
        cur.execute("DELETE FROM completed_order_details_archive WHERE order_id = %s", [order_id])
        
        # Fetch summary data
        cur.execute("SELECT customer_name, total_price, order_date, estimated_completion_time FROM orders WHERE order_id = %s", [order_id])
        order_summary = cur.fetchone()
        
        if not order_summary:
            mysql.connection.rollback()
            return jsonify({'success': False, 'message': 'Order not found in active queue.'}), 404

        # Calculate late status
        was_late = 0
        estimated_time = order_summary.get('estimated_completion_time')
        if estimated_time and estimated_time < datetime.now():
            was_late = 1

        # Archive summary
        cur.execute("""
            INSERT INTO completed_orders_archive 
            (order_id, customer_name, total_price, order_date, completion_time, was_late)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            order_id, order_summary['customer_name'], order_summary['total_price'], 
            order_summary['order_date'], estimated_time, was_late
        ))
        
        # Fetch and Archive item details
        cur.execute("""
            SELECT mi.name, od.quantity, od.price_per_item
            FROM order_details od JOIN menu_items mi ON od.item_id = mi.item_id
            WHERE od.order_id = %s
        """, [order_id])
        item_details = cur.fetchall()

        for item in item_details:
            cur.execute("""
                INSERT INTO completed_order_details_archive 
                (order_id, item_name, quantity, price_per_item) VALUES (%s, %s, %s, %s)
            """, (order_id, str(item['name']), item['quantity'], item['price_per_item']))

        # Delete from active queue (CASCADE handles order_details)
        cur.execute("DELETE FROM orders WHERE order_id = %s", [order_id])

        mysql.connection.commit()
        return jsonify({'success': True, 'message': f'Order #{order_id} archived.'})

    except Exception as e:
        mysql.connection.rollback() 
        print(f"Final Archive Error: {e}")
        return jsonify({'success': False, 'message': f'Archive failed: {str(e)}'}), 500
    finally:
        if cur: cur.close()

@app.route('/admin/reset_daily_data', methods=['POST'])
def reset_daily_data():
    """API endpoint for 'End-of-Day Reset'; clears all transactional data."""
    cur = mysql.connection.cursor()
    mysql.connection.begin()
    try:
        # Clear child tables first
        cur.execute("DELETE FROM order_details;")
        cur.execute("DELETE FROM completed_order_details_archive;")
        
        # Clear parent tables
        cur.execute("DELETE FROM orders;")
        cur.execute("DELETE FROM completed_orders_archive;")
        
        # Reset AUTO_INCREMENT counters
        cur.execute("ALTER TABLE orders AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE order_details AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE completed_order_details_archive AUTO_INCREMENT = 1;")
        
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'All orders cleared. Counters reset.'})

    except Exception as e:
        mysql.connection.rollback()
        print(f"Reset Error: {e}")
        return jsonify({'success': False, 'message': f'Reset failed: {str(e)}'}), 500
    finally:
         if cur: cur.close()

@app.route('/admin/api/order_details/<int:order_id>', methods=['GET'])
def get_order_details_api(order_id):
    """API endpoint to fetch item details for a specific order (active or archived)."""
    cur = mysql.connection.cursor()
    try:
        # Check archive details first (most likely scenario for this modal)
        cur.execute("""
            SELECT item_name AS name, quantity, price_per_item
            FROM completed_order_details_archive WHERE order_id = %s
        """, [order_id])
        details = cur.fetchall()

        # If not in archive, check active details (for modal on live dashboard)
        if not details:
            cur.execute("""
                SELECT mi.name, od.quantity, od.price_per_item
                FROM order_details od JOIN menu_items mi ON od.item_id = mi.item_id
                WHERE od.order_id = %s
            """, [order_id])
            details = cur.fetchall()
        
        if details:
            items_list = []
            for item in details:
                items_list.append({
                    'name': str(item['name']),
                    'quantity': int(item['quantity']),
                    'price_per_item': float(item['price_per_item']) 
                })
            return jsonify({'success': True, 'items': items_list})
        else:
            return jsonify({'success': False, 'message': 'No item details found for this order.'}), 404

    except Exception as e:
        print(f"Error fetching order details API: {e}") 
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500
    finally:
        if cur: cur.close()

@app.route('/admin/completed_orders')
def admin_completed_orders():
    """Renders the sales history dashboard."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM completed_orders_archive ORDER BY order_id ASC")
        orders = cur.fetchall()
        
        cur.execute("SELECT SUM(total_price) AS total_sales FROM completed_orders_archive")
        total_sales_result = cur.fetchone()
        total_sales = total_sales_result['total_sales'] if total_sales_result['total_sales'] else 0
    finally:    
        cur.close()

    return render_template('admin_completed_orders.html', orders=orders, total_sales=total_sales) 

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True) # debug=True helps see errors in browser during development
