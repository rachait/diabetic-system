"""
Store, Product, Cart, and Order Management Routes
"""
from flask import Blueprint, request, jsonify, session
from database import get_db_connection
try:
    import stripe
except ImportError:  # Optional dependency for payment integrations.
    stripe = None

store_bp = Blueprint('store', __name__, url_prefix='/api/store')

# Initialize Stripe (you'll set this in env)
if stripe is not None:
    stripe.api_key = "sk_test_placeholder"  # Set from environment

@store_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    try:
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM products WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if search:
            query += ' AND (name LIKE ? OR description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'products': products,
            'count': len(products)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        conn.close()
        
        if not product:
            return jsonify({'status': 'error', 'message': 'Product not found'}), 404
        
        return jsonify({'status': 'success', 'product': dict(product)}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/cart', methods=['GET'])
def get_cart():
    """Get user's shopping cart"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ci.id, ci.product_id, ci.quantity, p.name, p.price, 
                   (ci.quantity * p.price) as item_total
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = ?
        ''', (user_id,))
        
        items = [dict(row) for row in cursor.fetchall()]
        
        total = sum(item['item_total'] for item in items)
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'items': items,
            'total': total,
            'item_count': len(items)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id or quantity < 1:
            return jsonify({'status': 'error', 'message': 'Invalid product or quantity'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT id FROM products WHERE id = ?', (product_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': 'Product not found'}), 404
        
        # Check if already in cart
        cursor.execute('SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?', 
                      (user_id, product_id))
        existing = cursor.fetchone()
        
        if existing:
            # Update quantity
            cursor.execute('UPDATE cart_items SET quantity = quantity + ? WHERE id = ?',
                         (quantity, existing['id']))
        else:
            # Insert new item
            cursor.execute('INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)',
                         (user_id, product_id, quantity))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Added to cart'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/cart/remove/<int:cart_item_id>', methods=['DELETE'])
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cart_items WHERE id = ? AND user_id = ?', 
                      (cart_item_id, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Removed from cart'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    """Clear entire cart"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Cart cleared'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/checkout', methods=['POST'])
def checkout():
    """Create order from cart"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        shipping_address = data.get('shipping_address', '')
        
        if not shipping_address:
            return jsonify({'status': 'error', 'message': 'Shipping address required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get cart items
        cursor.execute('''
            SELECT ci.product_id, ci.quantity, p.price
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = ?
        ''', (user_id,))
        
        items = cursor.fetchall()
        
        if not items:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400
        
        # Calculate total
        total = sum(item['quantity'] * item['price'] for item in items)
        
        # Create order
        cursor.execute('''
            INSERT INTO orders (user_id, total_amount, shipping_address, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, total, shipping_address))
        
        order_id = cursor.lastrowid
        
        # Add order items
        for item in items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['quantity'], item['price']))
        
        # Clear cart
        cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Order created',
            'order_id': order_id,
            'total_amount': total
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@store_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get user's orders"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, total_amount, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        orders = [dict(row) for row in cursor.fetchall()]
        
        # Get items for each order
        for order in orders:
            cursor.execute('''
                SELECT p.name, oi.quantity, oi.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order['id'],))
            order['items'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'orders': orders,
            'count': len(orders)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
