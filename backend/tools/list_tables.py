"""
List all tables in the specified SQLite database.
"""
import sqlite3

DB_PATH = 'backend/healthcare.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if tables:
    print("Tables in database:")
    for t in tables:
        print("-", t[0])
else:
    print("No tables found in database.")

conn.close()
