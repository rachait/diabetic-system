# --- Doctor seeding ---
def seed_doctors():
    """Seed initial doctor data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if doctors already exist
    cursor.execute('SELECT COUNT(*) as count FROM doctors')
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return
    doctors = [
        ("Rachait Talwar", "Endocrinology", "Monday,Wednesday,Friday", 500, "available", None, 0),
        ("Vinit Pandey", "Internal Medicine", "Tuesday,Thursday", 400, "available", None, 0),
    ]
    for name, specialization, days, fee, status, avatar, slots in doctors:
        cursor.execute('''
            INSERT INTO doctors (name, specialization, available_days, consultation_fee, status, avatar_url, slot_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, specialization, days, fee, status, avatar, slots))
    conn.commit()
    conn.close()
    print("[DB] Doctors seeded successfully")
"""
Database initialization and models for User, Store, Cart, and Booking management
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            time_slot TEXT,
            appointment_type TEXT DEFAULT 'in-person',
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            full_name TEXT,
            age INTEGER,
            medical_history TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Lightweight migration for existing databases created before is_admin existed.
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    if 'is_admin' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            available_days TEXT NOT NULL, -- Comma-separated days (e.g., 'Monday,Wednesday,Friday')
            consultation_fee REAL NOT NULL,
            status TEXT DEFAULT 'available', -- available, busy, inactive
            avatar_url TEXT,
            average_rating REAL DEFAULT 0,
            slot_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Risk assessments (diabetes predictions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pregnancies INTEGER, glucose INTEGER, blood_pressure INTEGER,
            skin_thickness INTEGER, insulin INTEGER, bmi REAL,
            diabetes_pedigree REAL, age INTEGER,
            prediction TEXT, confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Nutrients/Products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            price REAL NOT NULL,
            quantity_available INTEGER,
            image_url TEXT,
            benefits TEXT,
            recommended_for TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Shopping cart items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Orders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_id TEXT,
            shipping_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Order items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Nutritionist bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nutritionist_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nutritionist_name TEXT,
            booking_date TIMESTAMP,
            duration_minutes INTEGER DEFAULT 30,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Meal plans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            duration_days INTEGER,
            target_audience TEXT,
            calories_per_day INTEGER,
            meals_per_day INTEGER,
            price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Authentication activity logs (admin audit trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            event_type TEXT NOT NULL,
            status TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully")

def seed_products():
    """Seed initial product data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if products already exist
    cursor.execute('SELECT COUNT(*) as count FROM products')
    if cursor.fetchone()['count'] > 0:
        return
    
    products = [
        # Vitamins & Supplements
        ("Metformin Support Supplement", "Supplements", "Helps support healthy blood sugar levels", 29.99, 100, "https://via.placeholder.com/200?text=Metformin", "Supports glucose metabolism", "Pre-diabetic, Diabetic"),
        ("Omega-3 Fish Oil", "Supplements", "Supports cardiovascular and metabolic health", 24.99, 80, "https://via.placeholder.com/200?text=Omega3", "Heart health, Anti-inflammatory", "All risk levels"),
        ("Vitamin D3 1000IU", "Vitamins", "Essential for bone health and immune support", 14.99, 150, "https://via.placeholder.com/200?text=VitaminD", "Immune support, Bone health", "All risk levels"),
        ("Chromium Picolinate", "Supplements", "Helps regulate blood sugar and reduce cravings", 19.99, 120, "https://via.placeholder.com/200?text=Chromium", "Blood sugar control", "Pre-diabetic, Diabetic"),
        ("Berberine 500mg", "Supplements", "Natural way to support healthy glucose levels", 34.99, 60, "https://via.placeholder.com/200?text=Berberine", "Glucose metabolism", "Diabetic"),
        
        # Meal Plans
        ("7-Day Diabetes-Friendly Meal Plan", "Meal Plans", "Complete meal plan with recipes and grocery list", 49.99, 999, "https://via.placeholder.com/200?text=MealPlan", "Balanced nutrition, Low glycemic", "All risk levels"),
        ("30-Day Weight Management Program", "Meal Plans", "Comprehensive plan for healthy weight loss", 99.99, 999, "https://via.placeholder.com/200?text=WeightPlan", "Weight loss, Metabolism support", "Pre-diabetic, Diabetic"),
        ("Low-Carb Keto Meal Guide", "Meal Plans", "Detailed keto meal planning for blood sugar control", 39.99, 999, "https://via.placeholder.com/200?text=KetoPlan", "Low carbs, High fat", "Diabetic"),
        
        # Wellness Products
        ("Blood Glucose Monitor Bundle", "Devices", "Includes meter, strips, and lancets", 79.99, 50, "https://via.placeholder.com/200?text=BGMonitor", "Monitoring, Accuracy", "Diabetic"),
        ("Smart Fitness Tracker", "Wearables", "Track activity, sleep, and heart rate", 129.99, 40, "https://via.placeholder.com/200?text=Tracker", "Activity tracking", "All risk levels"),
            ("Doctors", "Services", "Consultation with certified doctors", 0.0, 10, None, "Medical consultation", "All patients"),
    ]
    
    for name, category, desc, price, qty, img, benefits, audience in products:
        cursor.execute('''
            INSERT INTO products (name, category, description, price, quantity_available, image_url, benefits, recommended_for)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, desc, price, qty, img, benefits, audience))
    
    conn.commit()
    conn.close()
    print("[DB] Products seeded successfully")

# Initialize on import
if not os.path.exists(DB_PATH):
    init_db()
    seed_products()
    seed_doctors()
