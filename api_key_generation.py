import uuid
import base64
import hashlib
import secrets
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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
    """Generate a new API key for a user
    
    Args:
        db_connection: SQLite database connection
        user_id: ID of the user to generate the key for
        
    Returns:
        dict: Dictionary containing the API key, secret, and ID
    """
    api_key_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)
    api_secret = secrets.token_urlsafe(64)
    api_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Create a cursor from the connection
    cursor = db_connection.cursor()
    
    try:
        # Encrypt the API secret before storing
        encrypted_secret = _encrypt_sensitive_data(api_secret)
        
        # Insert the new API key into the database
        cursor.execute('''
        INSERT INTO api_keys (id, user_id, api_key, api_secret, api_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (api_key_id, user_id, api_key, encrypted_secret, api_id, now))
        
        # Commit the transaction
        db_connection.commit()
        
        return {
            'api_key': api_key,
            'api_secret': api_secret,  # Return the unencrypted secret to the user once
            'api_id': api_id
        }
    except sqlite3.Error as e:
        # Rollback in case of error
        db_connection.rollback()
        print(f"Database error: {str(e)}")
        raise e


def get_user_api_keys(db_connection, user_id):
    """Get all API keys for a user
    
    Args:
        db_connection: SQLite database connection
        user_id: ID of the user to get keys for
        
    Returns:
        list: List of API keys for the user
    """
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
    """Get the API secret for a specific API key
    
    Args:
        db_connection: SQLite database connection
        api_key_id: ID of the API key to get the secret for
        user_id: ID of the user who owns the key (for security)
        
    Returns:
        str: Decrypted API secret if found, None otherwise
    """
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
    """Delete an API key
    
    Args:
        db_connection: SQLite database connection
        api_key_id: ID of the API key to delete
        user_id: ID of the user who owns the key (for security)
        
    Returns:
        bool: True if the key was deleted, False otherwise
    """
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
            created_at TEXT NOT NULL
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
