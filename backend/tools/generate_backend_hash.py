"""
Generate a password hash using the backend's PBKDF2-HMAC-SHA256 method.
"""
import hashlib
import secrets

password = "admin123"

salt = secrets.token_hex(16)
pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
hash_str = f"{salt}${pwd_hash.hex()}"
print("Password hash for admin123:", hash_str)
