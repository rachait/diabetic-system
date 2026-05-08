"""
Alias route for user orders to match frontend expectation
"""
from flask import Blueprint, jsonify, session
from database import get_db_connection

user_orders_bp = Blueprint('user_orders', __name__, url_prefix='/user')

@user_orders_bp.route('/orders', methods=['GET'])
def user_orders():
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
    for order in orders:
        cursor.execute('''
            SELECT p.name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'orders': orders, 'count': len(orders)})
