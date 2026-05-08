"""
Initialize the SQLite database schema in data/app.db.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import init_db

if __name__ == "__main__":
    init_db()
    print("Database schema initialized in data/app.db.")
