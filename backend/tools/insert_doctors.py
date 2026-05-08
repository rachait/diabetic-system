import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'app.db'))

doctors = [
    ("Rachait Talwar", "Endocrinology", "Monday,Wednesday,Friday", 500, "available", None, 0),
    ("Vinit Pandey", "Internal Medicine", "Tuesday,Thursday", 400, "available", None, 0),
    ("Aarti Sharma", "Diabetology", "Monday,Tuesday,Thursday", 600, "available", None, 0),
    ("Suresh Kumar", "General Medicine", "Friday,Saturday", 350, "available", None, 0),
    ("Priya Singh", "Nutrition", "Wednesday,Friday", 450, "available", None, 0),
    ("Anil Mehra", "Cardiology", "Monday,Thursday", 700, "available", None, 0),
]

def insert_doctors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for d in doctors:
        cursor.execute('''
            INSERT INTO doctors (name, specialization, available_days, consultation_fee, status, avatar_url, slot_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', d)
    conn.commit()
    conn.close()
    print(f"Inserted {len(doctors)} doctors.")

if __name__ == "__main__":
    insert_doctors()
