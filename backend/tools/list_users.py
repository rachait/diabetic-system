"""
List all users in the data/app.db database.
"""
import sqlite3

DB_PATH = 'data/app.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, username, email, is_admin, full_name FROM users;")
users = cursor.fetchall()

if users:
    print("Users in database:")
    for u in users:
        print(f"ID: {u[0]}, Username: {u[1]}, Email: {u[2]}, Admin: {u[3]}, Name: {u[4]}")
else:
    print("No users found in database.")

conn.close()
