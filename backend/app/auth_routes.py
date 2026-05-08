"""
Authentication and User Management Routes
"""
from flask import Blueprint, request, jsonify, session
import hashlib
import secrets
from database import get_db_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _log_auth_event(event_type, status, user_id=None, username=None):
    """Persist authentication activity for admin auditing."""
    try:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO auth_activity_logs (user_id, username, event_type, status, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (user_id, username, event_type, status, ip_address, user_agent)
        )
        conn.commit()
        conn.close()
    except Exception:
        # Logging must not break auth flow.
        pass

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

def verify_password(stored_hash, password):
    """Verify password against hash"""
    try:
        salt, pwd_hash = stored_hash.split('$')
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return computed_hash.hex() == pwd_hash
    except:
        return False

def get_user_by_id(user_id):
    """Get user from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not all([username, email, password]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        if len(password) < 6:
            return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': 'Username or email already exists'}), 409
        
        # First registered account becomes admin to bootstrap dashboard access.
        cursor.execute('SELECT COUNT(*) AS admin_count FROM users WHERE is_admin = 1')
        admin_count = int(cursor.fetchone()['admin_count'])
        is_admin = 1 if admin_count == 0 else 0

        # Create user
        pwd_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, pwd_hash, full_name, is_admin))
        conn.commit()
        
        user_id = cursor.lastrowid
        conn.close()
        
        session['user_id'] = user_id
        _log_auth_event('register', 'success', user_id=user_id, username=username)
        
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'user_id': user_id,
            'username': username,
            'is_admin': bool(is_admin)
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Missing username or password'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(user['password_hash'], password):
            _log_auth_event('login', 'failed', username=username or None)
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        session['user_id'] = user['id']
        session['is_admin'] = bool(user['is_admin'])
        _log_auth_event('login', 'success', user_id=user['id'], username=user['username'])
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'is_admin': bool(user['is_admin'])
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    current_user_id = session.get('user_id')
    current_username = None
    if current_user_id:
        user = get_user_by_id(current_user_id)
        current_username = user.get('username') if user else None
    _log_auth_event('logout', 'success', user_id=current_user_id, username=current_username)
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out'}), 200

@auth_bp.route('/profile', methods=['GET', 'PUT'])
def profile():
    """Get or update user profile"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        if request.method == 'GET':
            user = get_user_by_id(user_id)
            if not user:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
            # Remove password hash from response
            user.pop('password_hash', None)
            return jsonify({'status': 'success', 'user': user}), 200
        
        elif request.method == 'PUT':
            data = request.get_json() or {}
            full_name = data.get('full_name')
            age = data.get('age')
            medical_history = data.get('medical_history')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if full_name is not None:
                updates.append('full_name = ?')
                params.append(full_name)
            if age is not None:
                updates.append('age = ?')
                params.append(age)
            if medical_history is not None:
                updates.append('medical_history = ?')
                params.append(medical_history)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(user_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
            
            conn.close()
            
            user = get_user_by_id(user_id)
            user.pop('password_hash', None)
            
            return jsonify({'status': 'success', 'message': 'Profile updated', 'user': user}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_bp.route('/check', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    user_id = session.get('user_id')
    
    if user_id:
        user = get_user_by_id(user_id)
        if user:
            user.pop('password_hash', None)
            return jsonify({'status': 'success', 'authenticated': True, 'user': user}), 200
    
    return jsonify({'status': 'success', 'authenticated': False}), 200
