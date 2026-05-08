import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'app.db'))

products = [
    # High risk
    {"name": "Continuous Glucose Monitor (CGM)", "category": "Monitoring", "description": "Real-time blood sugar tracking every 5 min", "price": 4999, "quantity_available": 12},
    {"name": "Glucometer Pro X2 + Strips", "category": "Monitoring", "description": "Clinical-grade glucose testing kit", "price": 1999, "quantity_available": 0},
    {"name": "Insulin Pen Needles (32G)", "category": "Medication", "description": "For insulin injection — prescribed use only", "price": 299, "quantity_available": 6},
    {"name": "Metformin 1000mg", "category": "Medication", "description": "High-dose oral diabetes medication", "price": 149, "quantity_available": 180},
    {"name": "Diabetic Ketoacidosis (DKA) Kit", "category": "Emergency", "description": "Emergency testing strips for ketones", "price": 799, "quantity_available": 22},
    {"name": "HbA1c Home Test Kit", "category": "Diagnostic", "description": "3-month average blood sugar level test", "price": 799, "quantity_available": 9},
    # Moderate risk
    {"name": "Glucometer Standard + 50 Strips", "category": "Monitoring", "description": "Daily home blood sugar monitoring", "price": 999, "quantity_available": 45},
    {"name": "Blood Pressure Monitor (digital)", "category": "Monitoring", "description": "Hypertension linked to moderate diabetics", "price": 1899, "quantity_available": 18},
    {"name": "Metformin 500mg", "category": "Medication", "description": "Standard-dose oral medication", "price": 89, "quantity_available": 220},
    {"name": "Omega-3 Fatty Acids 1000mg", "category": "Supplements", "description": "Reduces cardiovascular risk in diabetics", "price": 599, "quantity_available": 14},
    {"name": "Chromium Picolinate 400mcg", "category": "Supplements", "description": "Improves insulin sensitivity", "price": 399, "quantity_available": 62},
    {"name": "Diabetic Care Compression Socks", "category": "Wellness", "description": "Improves circulation, prevents neuropathy", "price": 449, "quantity_available": 38},
    {"name": "Low-GI Meal Plan Kit", "category": "Diet", "description": "Portion-controlled weekly meal planning box", "price": 1499, "quantity_available": 7},
]

def insert_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for p in products:
        cursor.execute('''
            INSERT INTO products (name, category, description, price, quantity_available)
            VALUES (?, ?, ?, ?, ?)
        ''', (p["name"], p["category"], p["description"], p["price"], p["quantity_available"]))
    conn.commit()
    conn.close()
    print(f"Inserted {len(products)} products.")

if __name__ == "__main__":
    insert_products()
