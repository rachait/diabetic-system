"""
Promote a user to admin in the users table.
Usage: Run this script and enter the username or email of the user to promote.
"""
import sqlite3

import os
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'app.db')

username = input('Enter username or email to promote to admin: ').strip()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('UPDATE users SET is_admin = 1 WHERE username = ? OR email = ?', (username, username))
conn.commit()

if cursor.rowcount:
    print(f"User '{username}' promoted to admin.")
else:
    print(f"No user found with username or email '{username}'.")

conn.close()
