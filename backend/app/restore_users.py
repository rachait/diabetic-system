"""
Restore users utility: Add users in bulk and set admin flag if needed.
Run this script inside your backend container or with your Python environment.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

def restore_users(users):
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    for user in users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, is_admin, full_name, age, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['username'], user['email'], user['password_hash'], user.get('is_admin', 0), user.get('full_name'), user.get('age'), user.get('medical_history')
        ))
    conn.commit()
    conn.close()
    print(f"Restored {len(users)} users.")

if __name__ == "__main__":
    # Example users to restore (replace with your actual data)
    users = [
        # ...existing users...
        {'username': 'adminai', 'email': 'adminai@system.com', 'password_hash': '2d90718bbb1fd9163548f8589321a4e2$6d46e57fd8cd29ac8b188b71f53d3e5bcbbb8a2f3d6cbe5f7948849c2e4944e2', 'is_admin': 1, 'full_name': 'Admin AI', 'age': None, 'medical_history': ''},
    ]
    restore_users(users)
