"""
Migration script to add 'gender' column to risk_assessments table if it does not exist.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'app.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if 'gender' column exists
cursor.execute("PRAGMA table_info(risk_assessments)")
columns = [row[1] for row in cursor.fetchall()]

if 'gender' not in columns:
    cursor.execute("ALTER TABLE risk_assessments ADD COLUMN gender TEXT")
    conn.commit()
    print("Added 'gender' column to risk_assessments table.")
else:
    print("'gender' column already exists in risk_assessments table.")

conn.close()
