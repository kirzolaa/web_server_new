import uuid
import base64
import hashlib
import secrets
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
from flask import Flask, jsonify, session

app = Flask(__name__)

"""
Database schema for reference:
# Create api_keys table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            api_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Create api_role_permissions table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_role_permissions (
            id TEXT PRIMARY KEY,
            api_key_id TEXT NOT NULL,
            role TEXT NOT NULL,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        )
        ''')
        
        # Create api_permission table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_permissions (
            id TEXT PRIMARY KEY,
            api_role_id TEXT NOT NULL,
            permission TEXT NOT NULL,
            FOREIGN KEY (api_role_id) REFERENCES api_role_permissions(id)
        )
        ''')
"""

# Encryption key (in production, this should be stored securely, not hardcoded)
ENCRYPTION_KEY = b'your-encryption-key-here'


def _derive_key(password, salt, iterations=100000):
    """Derive a key from a password and salt"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return base64.urlsafe_b64encode(kdf.derive(password))


def _encrypt_sensitive_data(data, key=ENCRYPTION_KEY):
    """Encrypt sensitive data"""
    try:
        if isinstance(data, str):
            data = data.encode()
        
        # Generate a random salt
        salt = secrets.token_bytes(16)
        
        # Derive a key from the password and salt
        derived_key = _derive_key(key, salt)
        
        # Create a Fernet cipher with the derived key
        cipher = Fernet(derived_key)
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(data)
        
        # Combine salt and encrypted data for storage
        return base64.urlsafe_b64encode(salt + encrypted_data).decode()
    except Exception as e:
        print(f"Encryption error: {str(e)}")
        raise e


def _decrypt_sensitive_data(encrypted_data, key=ENCRYPTION_KEY):
    """Decrypt sensitive data"""
    try:
        # Decode the combined salt and encrypted data
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        
        # Extract salt (first 16 bytes) and encrypted data
        salt, encrypted_data = decoded_data[:16], decoded_data[16:]
        
        # Derive the key from the password and salt
        derived_key = _derive_key(key, salt)
        
        # Create a Fernet cipher with the derived key
        cipher = Fernet(derived_key)
        
        # Decrypt the data
        decrypted_data = cipher.decrypt(encrypted_data)
        
        return decrypted_data.decode()
    except Exception as e:
        print(f"Decryption error: {str(e)}")
        raise e


def generate_api_key(db_connection, user_id):
    """Generate a new API key for a user"""
    import bcrypt

    # Generate API key components
    try:
        with open('api_key_id.json', 'r') as f:
            api_key_id = json.load(f)['api_key_id']
    except FileNotFoundError:
        api_key_id = '00001'
    
    api_key_id = str(int(api_key_id) + 1).zfill(5)
    
    with open('api_key_id.json', 'w') as f:
        json.dump({'api_key_id': api_key_id}, f)
    api_key = secrets.token_urlsafe(32)
    api_secret = secrets.token_urlsafe(64)

    # Hash the API secret
    hashed_secret = bcrypt.hashpw(api_secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Store in database
    cursor = db_connection.cursor()
    cursor.execute('''
        INSERT INTO api_keys (id, user_id, api_key, api_secret, api_id, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (api_key_id, user_id, api_key, hashed_secret, api_key_id, datetime.now().isoformat(), 'Active'))

    db_connection.commit()

    return {
        'api_key': api_key,
        'api_secret': api_secret,
        'api_id': api_key_id
    }


def get_user_api_keys(db_connection, user_id):
    """Get all API keys for a user"""
    cursor = db_connection.cursor()
    
    try:
        cursor.execute('''
        SELECT id, api_key, api_id, created_at 
        FROM api_keys 
        WHERE user_id = ?
        ''', (user_id,))
        
        keys = []
        for row in cursor.fetchall():
            keys.append({
                'id': row[0],
                'api_key': row[1],
                'api_id': row[2],
                'created_at': row[3]
            })
        
        return keys
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        raise e


def get_api_secret(db_connection, api_key_id, user_id):
    """Get the API secret for a specific API key"""
    cursor = db_connection.cursor()
    
    try:
        # First check if the key belongs to the user
        cursor.execute("""
        SELECT api_secret FROM api_keys 
        WHERE id = ? AND user_id = ?
        """, (api_key_id, user_id))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        # Decrypt the API secret
        encrypted_secret = result[0]
        decrypted_secret = _decrypt_sensitive_data(encrypted_secret)
        
        return decrypted_secret
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return None


def delete_api_key(db_connection, api_key_id, user_id):
    """Delete an API key"""
    cursor = db_connection.cursor()
    
    try:
        # First verify the key belongs to the user
        cursor.execute('''
        SELECT id FROM api_keys 
        WHERE id = ? AND user_id = ?
        ''', (api_key_id, user_id))
        
        if not cursor.fetchone():
            return False  # Key doesn't exist or doesn't belong to user
        
        # Delete any permissions associated with this key
        cursor.execute('''
        DELETE FROM api_permissions 
        WHERE api_role_id IN (
            SELECT id FROM api_role_permissions WHERE api_key_id = ?
        )
        ''', (api_key_id,))
        
        # Delete role permissions
        cursor.execute('''
        DELETE FROM api_role_permissions 
        WHERE api_key_id = ?
        ''', (api_key_id,))
        
        # Delete the key itself
        cursor.execute('''
        DELETE FROM api_keys 
        WHERE id = ?
        ''', (api_key_id,))
        
        db_connection.commit()
        return True
    except sqlite3.Error as e:
        db_connection.rollback()
        print(f"Database error: {str(e)}")
        return False


@app.route('/api/generate-key', methods=['POST'])
def generate_key():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    api_key = generate_api_key(auth_handler.db.conn, user_id)
    
    if api_key:
        return jsonify({'success': True, 'api_key': api_key})
    return jsonify({'success': False, 'message': 'Failed to generate API key'}), 500


if __name__ == "__main__":
    # This is just for testing purposes
    conn = sqlite3.connect('test_database.db')
    test_user_id = str(uuid.uuid4())
    
    try:
        # Create test tables
        conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            api_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
        ''')
        
        # Generate a test API key
        api_key = generate_api_key(conn, test_user_id)
        print("Generated API Key:", api_key)
        
        # Get user's API keys
        keys = get_user_api_keys(conn, test_user_id)
        print("User API Keys:", keys)
        
        # Get API secret
        api_secret = get_api_secret(conn, api_key['api_id'], test_user_id)
        print("API Secret:", api_secret)
    finally:
        conn.close()
