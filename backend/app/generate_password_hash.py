"""
Utility to generate bcrypt password hashes for user restoration.
Run this script and copy the hash for use in restore_users.py.
"""
import bcrypt

password = input("Enter password to hash: ").encode()
hash = bcrypt.hashpw(password, bcrypt.gensalt())
print("Hashed password:", hash.decode())
