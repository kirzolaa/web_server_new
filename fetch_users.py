import sqlite3
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
from database import Database
import bcrypt

def get_secret_key():
    """Get the secret key for encryption"""
    key_file = "secret.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    return None

def initialize_encryption(secret_key):
    """Initialize Fernet encryption with the secret key"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'static_salt_for_key_derivation',  # In production, use a unique salt per application
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key))
    return Fernet(key)

def verify_password(stored_password, provided_password):
    """Verify a password against its bcrypt hash"""
    try:
        # Convert both inputs to bytes
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        return False

# Initialize the database
db = Database()

# Connect to the database
db_path = "database.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the secret key for encryption
secret_key = get_secret_key()
if secret_key:
    fernet = initialize_encryption(secret_key)
else:
    print("Warning: Secret key not found. Some encrypted fields may not be decodable.")
    fernet = None

# Fetch all users
cursor.execute("""
    SELECT id, username, password, full_name, email, bio, profile_pic, created_at, updated_at
    FROM users
""")

users = cursor.fetchall()

print("\n=== All Users in Database ===\n")
for user in users:
    user_id, username, password, full_name, email, bio, profile_pic, created_at, updated_at = user
    
    # Example: Verify a test password
    test_password = "_OQ7k2MqiDd+"
    is_valid = verify_password(password, test_password)
    
    print(f"\nUser ID: {user_id}")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Full Name: {full_name}")
    print(f"Bio: {bio}")
    print(f"Profile Pic: {profile_pic}")
    print(f"Created At: {created_at}")
    print(f"Updated At: {updated_at}")
    print(f"Stored Password: {password}")
    
    print(f"Password Match: {is_valid}")
    print("-" * 50)

conn.close()
