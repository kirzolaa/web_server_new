import sqlite3
import json
import os
import uuid
import hashlib
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
import logging
import threading
import time

# Thread-local storage for database connections
_thread_local = threading.local()

class Database:
    def __init__(self, db_path="database.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.schema_path = "database_tables_form.json"
        self.secret_key = self._get_or_create_secret_key()
        self.fernet = self._initialize_encryption()
        self.connect()
        self._initialize_database()
    
    def _get_or_create_secret_key(self, key_file="secret.key"):
        """Get or create a secret key for encryption"""
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate a secure random key
            key = secrets.token_bytes(32)
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def _initialize_encryption(self):
        """Initialize Fernet encryption with the secret key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'static_salt_for_key_derivation',  # In production, use a unique salt per application
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        return Fernet(key)
    
    def connect(self):
        """Create a new database connection for the current thread"""
        if not hasattr(_thread_local, 'conn') or _thread_local.conn is None:
            _thread_local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            _thread_local.cursor = _thread_local.conn.cursor()
        
        self.conn = _thread_local.conn
        self.cursor = _thread_local.cursor
    
    def _hash_password(self, password, salt=None):
        """Hash a password with a salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(16)
        # Use a strong key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        hashed_password = kdf.derive(password.encode())
        return base64.b64encode(hashed_password).decode('utf-8'), base64.b64encode(salt).decode('utf-8')
    
    def _verify_password(self, stored_password, provided_password, salt):
        """Verify a password against its hash"""
        salt = base64.b64decode(salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        provided_hash = kdf.derive(provided_password.encode())
        stored_hash = base64.b64decode(stored_password)
        return provided_hash == stored_hash
    
    def _encrypt_sensitive_data(self, data):
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def _initialize_database(self):
        """Initialize the database with tables based on the JSON schema"""
        try:
            # Load schema from JSON file
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            
            # Create users table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                full_name TEXT,
                email TEXT UNIQUE NOT NULL,
                bio TEXT,
                profile_pic TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            # Create user_roles table for the roles array
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Create roles table with permissions as JSON
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY,
                role_name TEXT UNIQUE NOT NULL,
                permissions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            # Insert default roles if they don't exist
            now = datetime.now().isoformat()
            self.cursor.execute('''
            INSERT OR IGNORE INTO roles (role_id, role_name, permissions, created_at, updated_at)
            VALUES 
                (?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()), 'admin', json.dumps({"all": True, "manage_users": True, "manage_roles": True, "manage_content": True, "social_media": True, "prompting": True}), now, now,
                str(uuid.uuid4()), 'medium_admin', json.dumps({"view_users": True, "manage_content": True, "social_media": True, "prompting": True}), now, now,
                str(uuid.uuid4()), 'social_media_handler', json.dumps({"social_media": True, "prompting": True}), now, now,
                str(uuid.uuid4()), 'basic_user', json.dumps({"prompting": True}), now, now
            ))
            
            # Create api_keys table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                api_secret TEXT NOT NULL,
                api_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            ''')
            
            # Create api_role_permissions table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_role_permissions (
                api_key_id TEXT NOT NULL,
                permission_name TEXT NOT NULL,
                FOREIGN KEY(api_key_id) REFERENCES api_keys(id)
            )
            ''')
            
            # Create user_activity table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                activity_timestamp TEXT NOT NULL,
                activity_id TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Create activity_details table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_details (
                id TEXT PRIMARY KEY,
                activity_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                prompt_timestamp TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                FOREIGN KEY (activity_id) REFERENCES user_activity(id)
            )
            ''')
            
            # Create activity_responses table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_responses (
                id TEXT PRIMARY KEY,
                activity_detail_id TEXT NOT NULL,
                response TEXT NOT NULL,
                FOREIGN KEY (activity_detail_id) REFERENCES activity_details(id)
            )
            ''')
            
            # Create user_sessions table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL,
                expiration_time REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Create role_permissions table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                id TEXT PRIMARY KEY,
                role_id TEXT NOT NULL,
                permission TEXT NOT NULL,
                FOREIGN KEY (role_id) REFERENCES roles(role_id)
            )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error initializing database: {str(e)}")
    
    def close(self):
        """Close the database connection"""
        if hasattr(_thread_local, 'conn'):
            _thread_local.conn.close()
            del _thread_local.conn
            del _thread_local.cursor
    
    def create_user(self, username, password, email, full_name=None, bio=None, profile_pic=None, roles=None):
        """Create a new user with secure password hashing"""
        user_id = str(uuid.uuid4())
        hashed_password, salt = self._hash_password(password)
        now = datetime.now().isoformat()
        
        try:
            self.cursor.execute('''
            INSERT INTO users (id, username, password, password_salt, full_name, email, bio, profile_pic, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, hashed_password, salt, full_name, email, bio, profile_pic, now, now))
            
            # Add user roles if provided
            if roles:
                for role_data in roles:
                    role_id = str(uuid.uuid4())
                    self.cursor.execute('''
                    INSERT INTO user_roles (id, user_id, role)
                    VALUES (?, ?, ?)
                    ''', (role_id, user_id, role_data['role']))
                    
                    # Add permissions for this role
                    if 'permissions' in role_data:
                        for permission in role_data['permissions']:
                            perm_id = str(uuid.uuid4())
                            self.cursor.execute('''
                            INSERT INTO role_permissions (id, role_id, permission)
                            VALUES (?, ?, ?)
                            ''', (perm_id, role_id, permission))
            
            self.conn.commit()
            return user_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e
    
    def authenticate_user(self, username, password):
        """Authenticate a user by username and password"""
        self.cursor.execute('''
        SELECT id, password, password_salt FROM users WHERE username = ?
        ''', (username,))
        
        result = self.cursor.fetchone()
        if not result:
            return None
        
        user_id, stored_password, salt = result
        if self._verify_password(stored_password, password, salt):
            return user_id
        return None
    
    def get_user(self, user_id):
        """Get user data by ID"""
        self.cursor.execute('''
        SELECT id, username, full_name, email, bio, profile_pic, created_at, updated_at
        FROM users WHERE id = ?
        ''', (user_id,))
        
        user = self.cursor.fetchone()
        if not user:
            return None
        
        # Convert to dictionary
        user_dict = {
            'id': user[0],
            'username': user[1],
            'full_name': user[2],
            'email': user[3],
            'bio': user[4],
            'profile_pic': user[5],
            'created_at': user[6],
            'updated_at': user[7],
            'roles': []
        }
        
        # Get user roles
        self.cursor.execute('''
        SELECT id, role FROM user_roles WHERE user_id = ?
        ''', (user_id,))
        
        roles = self.cursor.fetchall()
        for role_id, role_name in roles:
            # Get permissions for this role
            self.cursor.execute('''
            SELECT permission FROM role_permissions WHERE role_id = ?
            ''', (role_id,))
            
            permissions = [perm[0] for perm in self.cursor.fetchall()]
            user_dict['roles'].append({
                'role': role_name,
                'permissions': permissions
            })
        
        return user_dict
    
    def get_user_by_email(self, email):
        """Get user by email address"""
        try:
            self.cursor.execute('''
            SELECT id, username, email, full_name, bio, profile_pic, created_at, updated_at 
            FROM users WHERE email = ?
            ''', (email,))
            
            result = self.cursor.fetchone()
            if not result:
                return None
                
            user_data = {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'full_name': result[3],
                'bio': result[4],
                'profile_pic': result[5],
                'created_at': result[6],
                'updated_at': result[7]
            }
            
            # Get user roles
            self.cursor.execute('''
            SELECT role FROM user_roles WHERE user_id = ?
            ''', (user_data['id'],))
            
            roles = [row[0] for row in self.cursor.fetchall()]
            user_data['roles'] = roles
            
            return user_data
        except sqlite3.Error as e:
            logging.error(f"Error getting user by email: {str(e)}")
            return None
            
    def update_user_password(self, user_id, new_password):
        """Update a user's password"""
        try:
            # Hash the new password
            hashed_password, salt = self._hash_password(new_password)
            now = datetime.now().isoformat()
            
            self.cursor.execute('''
            UPDATE users 
            SET password = ?, password_salt = ?, updated_at = ? 
            WHERE id = ?
            ''', (hashed_password, salt, now, user_id))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error updating user password: {str(e)}")
            return False
    
    def create_api_key(self, user_id):
        """Create a new API key for a user
        
        Args:
            user_id (str): The ID of the user to create a key for
            
        Returns:
            dict: API key data including key, secret, and additional information
        """
        api_key_id = str(uuid.uuid4())
        api_key = secrets.token_urlsafe(32)
        api_secret = secrets.token_urlsafe(64)
        api_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        # Encrypt the API secret before storing
        encrypted_secret = self._encrypt_sensitive_data(api_secret)
        
        try:
            self.cursor.execute('''
            INSERT INTO api_keys (id, user_id, api_key, api_secret, api_id, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (api_key_id, user_id, api_key, encrypted_secret, api_id, now, 'Active'))
            
            # Add default permission for the API key
            self.cursor.execute('''
            INSERT INTO api_role_permissions (api_key_id, permission_name)
            VALUES (?, ?)
            ''', (api_key_id, 'Standard API access'))
            
            self.conn.commit()
            return {
                'id': api_key_id,
                'api_key': api_key,
                'api_secret': api_secret,  # Return the unencrypted secret to the user once
                'api_id': api_id,
                'created_at': now,
                'status': 'Active',
                'permissions': ['Standard API access']
            }
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error creating API key: {str(e)}")
            return None
    
    def verify_api_key(self, api_key, api_secret):
        """Verify an API key and secret"""
        self.cursor.execute('''
        SELECT id, user_id, api_secret FROM api_keys WHERE api_key = ?
        ''', (api_key,))
        
        result = self.cursor.fetchone()
        if not result:
            return None
        
        key_id, user_id, encrypted_secret = result
        decrypted_secret = self._decrypt_sensitive_data(encrypted_secret)
        
        if decrypted_secret == api_secret:
            return user_id
        return None
    
    def log_user_activity(self, user_id, activity_type, prompt, response=None):
        """Log user activity including prompts and responses"""
        activity_id = str(uuid.uuid4())
        prompt_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        try:
            # Create activity entry
            self.cursor.execute('''
            INSERT INTO user_activity (id, user_id, activity_type, activity_timestamp, activity_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (activity_id, user_id, activity_type, now, activity_id))
            
            # Create activity detail entry
            detail_id = str(uuid.uuid4())
            self.cursor.execute('''
            INSERT INTO activity_details (id, activity_id, prompt, prompt_timestamp, prompt_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (detail_id, activity_id, prompt, now, prompt_id))
            
            # Add response if provided
            if response:
                if isinstance(response, list):
                    for resp in response:
                        resp_id = str(uuid.uuid4())
                        self.cursor.execute('''
                        INSERT INTO activity_responses (id, activity_detail_id, response)
                        VALUES (?, ?, ?)
                        ''', (resp_id, detail_id, resp))
                else:
                    resp_id = str(uuid.uuid4())
                    self.cursor.execute('''
                    INSERT INTO activity_responses (id, activity_detail_id, response)
                    VALUES (?, ?, ?)
                    ''', (resp_id, detail_id, response))
            
            self.conn.commit()
            return activity_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e
    
    def get_all_users(self):
        """Get a list of all users with basic information"""
        self.cursor.execute('''
        SELECT id, username, full_name, email, profile_pic FROM users
        ''')
        
        users = []
        for user in self.cursor.fetchall():
            user_id = user[0]
            
            # Get the first role for each user (simplified)
            self.cursor.execute('''
            SELECT role FROM user_roles WHERE user_id = ? LIMIT 1
            ''', (user_id,))
            
            role_result = self.cursor.fetchone()
            role = role_result[0] if role_result else "Basic User"
            
            users.append({
                'id': user_id,
                'username': user[1],
                'full_name': user[2],
                'email': user[3],
                'profile_pic': user[4],
                'role': role
            })
        
        return users
    
    def check_user_exists(self, username=None, email=None):
        """Check if a user with the given username or email already exists"""
        if username and email:
            self.cursor.execute('''
            SELECT id, username, email FROM users WHERE username = ? OR email = ?
            ''', (username, email))
        elif username:
            self.cursor.execute('''
            SELECT id, username, email FROM users WHERE username = ?
            ''', (username,))
        elif email:
            self.cursor.execute('''
            SELECT id, username, email FROM users WHERE email = ?
            ''', (email,))
        else:
            return None
            
        result = self.cursor.fetchone()
        if not result:
            return None
            
        # Return information about the existing user
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'exists': True,
            'duplicate_username': username and result[1].lower() == username.lower(),
            'duplicate_email': email and result[2].lower() == email.lower()
        }
    
    def store_session_token(self, user_id, session_token, expiration_time):
        """Store a session token with its expiration time"""
        try:
            token_id = str(uuid.uuid4())
            self.cursor.execute('''
            INSERT INTO user_sessions (id, user_id, token, expiration_time)
            VALUES (?, ?, ?, ?)
            ''', (token_id, user_id, session_token, expiration_time))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error storing session token: {str(e)}")
            return False
    
    def validate_session_token(self, session_token):
        """Validate a session token and return user_id if valid"""
        try:
            current_time = time.time()
            self.cursor.execute('''
            SELECT user_id, expiration_time FROM user_sessions 
            WHERE token = ? AND expiration_time > ?
            ''', (session_token, current_time))
            
            result = self.cursor.fetchone()
            if not result:
                return None
                
            return result[0]  # Return user_id
        except sqlite3.Error as e:
            logging.error(f"Error validating session token: {str(e)}")
            return None
    
    def update_user(self, user_id, updates):
        """Update user information
        
        Args:
            user_id (int): The ID of the user to update
            updates (dict): Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build the SET clause dynamically based on the updates dictionary
            set_clause = []
            values = []
            
            for field, value in updates.items():
                set_clause.append(f"{field} = ?")
                values.append(value)
            
            # Add updated_at timestamp
            set_clause.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            
            # Add user_id to values
            values.append(user_id)
            
            # Execute the update query
            query = f"UPDATE users SET {', '.join(set_clause)} WHERE id = ?"
            self.cursor.execute(query, values)
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error updating user: {str(e)}")
            return False
    
    def get_user_by_username(self, username):
        """Get user by username
        
        Args:
            username (str): The username to look up
            
        Returns:
            dict: User data if found, None otherwise
        """
        try:
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = self.cursor.fetchone()
            
            if not user:
                return None
                
            # Convert row to dictionary
            columns = [col[0] for col in self.cursor.description]
            user_data = {columns[i]: user[i] for i in range(len(columns))}
            
            return user_data
        except sqlite3.Error as e:
            logging.error(f"Error getting user by username: {str(e)}")
            return None
    
    def get_user_api_keys(self, user_id):
        """Get all API keys for a user
        
        Args:
            user_id (str): The ID of the user to get keys for
            
        Returns:
            list: List of API keys for the user with detailed information
        """
        try:
            self.cursor.execute("""
            SELECT id, api_key, created_at, status 
            FROM api_keys 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            """, (user_id,))
            
            keys = self.cursor.fetchall()
            
            # Convert rows to dictionaries
            result = []
            for key in keys:
                # Get permissions for this key (default to standard API access if none found)
                self.cursor.execute("""
                SELECT permission_name FROM api_role_permissions 
                WHERE api_key_id = ?
                """, (key[0],))
                
                permissions = self.cursor.fetchall()
                permission_list = [p[0] for p in permissions] if permissions else ["Standard API access"]
                
                result.append({
                    'id': key[0],
                    'api_key': key[1],
                    'created_at': key[2],
                    'status': key[3] if key[3] else 'Active',  # Default to Active if status is NULL
                    'permissions': permission_list
                })
            
            return result
        except sqlite3.Error as e:
            logging.error(f"Error getting user API keys: {str(e)}")
            return []
    
    def delete_api_key(self, api_key_id, user_id):
        """Delete an API key
        
        Args:
            api_key_id (str): The ID of the API key to delete
            user_id (str): The ID of the user who owns the key (for security)
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        try:
            # First check if the key belongs to the user
            self.cursor.execute("""
            SELECT id FROM api_keys 
            WHERE id = ? AND user_id = ?
            """, (api_key_id, user_id))
            
            key = self.cursor.fetchone()
            if not key:
                return False
            
            # Delete the key
            self.cursor.execute("DELETE FROM api_keys WHERE id = ?", (api_key_id,))
            
            # Delete associated permissions if they exist
            self.cursor.execute("DELETE FROM api_role_permissions WHERE api_key_id = ?", (api_key_id,))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error deleting API key: {str(e)}")
            return False
    
    # Role management methods
    def get_all_roles(self):
        """Get all roles
        
        Returns:
            list: List of all roles with their permissions
        """
        try:
            self.cursor.execute("SELECT role_id, role_name, permissions, created_at, updated_at FROM roles ORDER BY role_name")
            roles = self.cursor.fetchall()
            
            result = []
            for role in roles:
                # Handle NULL permissions by providing an empty dict
                permissions = {}
                if role[2] is not None:
                    try:
                        permissions = json.loads(role[2])
                    except json.JSONDecodeError:
                        permissions = {}
                
                result.append({
                    'role_id': role[0],
                    'role_name': role[1],
                    'permissions': permissions,
                    'created_at': role[3],
                    'updated_at': role[4]
                })
            
            return result
        except sqlite3.Error as e:
            logging.error(f"Error getting all roles: {str(e)}")
            return []
    
    def get_role(self, role_id=None, role_name=None):
        """Get a role by ID or name
        
        Args:
            role_id (str, optional): The ID of the role to get
            role_name (str, optional): The name of the role to get
            
        Returns:
            dict: Role data if found, None otherwise
        """
        try:
            if role_id:
                self.cursor.execute("SELECT role_id, role_name, permissions, created_at, updated_at FROM roles WHERE role_id = ?", (role_id,))
            elif role_name:
                self.cursor.execute("SELECT role_id, role_name, permissions, created_at, updated_at FROM roles WHERE role_name = ?", (role_name,))
            else:
                return None
                
            role = self.cursor.fetchone()
            if not role:
                return None
                
            # Handle NULL permissions by providing an empty dict
            permissions = {}
            if role[2] is not None:
                try:
                    permissions = json.loads(role[2])
                except json.JSONDecodeError:
                    permissions = {}
            
            return {
                'role_id': role[0],
                'role_name': role[1],
                'permissions': permissions,
                'created_at': role[3],
                'updated_at': role[4]
            }
        except sqlite3.Error as e:
            logging.error(f"Error getting role: {str(e)}")
            return None
    
    def create_role(self, role_name, permissions):
        """Create a new role
        
        Args:
            role_name (str): The name of the role
            permissions (dict): Dictionary of permissions
            
        Returns:
            dict: Role data if created, None otherwise
        """
        try:
            # Check if role already exists
            if self.get_role(role_name=role_name):
                return None
                
            role_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            self.cursor.execute("""
            INSERT INTO roles (role_id, role_name, permissions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """, (role_id, role_name, json.dumps(permissions), now, now))
            
            self.conn.commit()
            
            return {
                'role_id': role_id,
                'role_name': role_name,
                'permissions': permissions,
                'created_at': now,
                'updated_at': now
            }
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error creating role: {str(e)}")
            return None
    
    def update_role(self, role_id, updates):
        """Update a role
        
        Args:
            role_id (str): The ID of the role to update
            updates (dict): Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if role exists
            role = self.get_role(role_id=role_id)
            if not role:
                return False
                
            set_clause = []
            values = []
            
            if 'role_name' in updates:
                set_clause.append("role_name = ?")
                values.append(updates['role_name'])
                
            if 'permissions' in updates:
                set_clause.append("permissions = ?")
                values.append(json.dumps(updates['permissions']))
                
            # Add updated_at timestamp
            set_clause.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            
            # Add role_id to values
            values.append(role_id)
            
            # Execute the update query
            query = f"UPDATE roles SET {', '.join(set_clause)} WHERE role_id = ?"
            self.cursor.execute(query, values)
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error updating role: {str(e)}")
            return False
    
    def delete_role(self, role_id):
        """Delete a role
        
        Args:
            role_id (str): The ID of the role to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if role exists
            role = self.get_role(role_id=role_id)
            if not role:
                return False
                
            # Don't allow deleting default roles
            if role['role_name'] in ['admin', 'medium_admin', 'social_media_handler', 'basic_user']:
                return False
                
            # Delete the role
            self.cursor.execute("DELETE FROM roles WHERE role_id = ?", (role_id,))
            
            # Update users with this role to basic_user
            basic_role = self.get_role(role_name='basic_user')
            if basic_role:
                self.cursor.execute("UPDATE user_roles SET role = ? WHERE role = ?", (basic_role['role_name'], role['role_name']))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error deleting role: {str(e)}")
            return False
    
    def get_user_roles(self, user_id):
        """Get all roles for a user
        
        Args:
            user_id (str): The ID of the user to get roles for
            
        Returns:
            list: List of role names for the user
        """
        try:
            self.cursor.execute("""
            SELECT role FROM user_roles 
            WHERE user_id = ?
            """, (user_id,))
            
            roles = self.cursor.fetchall()
            return [role[0] for role in roles]
        except sqlite3.Error as e:
            logging.error(f"Error getting user roles: {str(e)}")
            return []
    
    def get_user_permissions(self, user_id):
        """Get all permissions for a user based on their roles
        
        Args:
            user_id (str): The ID of the user to get permissions for
            
        Returns:
            dict: Combined permissions from all user roles
        """
        try:
            # Get user roles
            user_roles = self.get_user_roles(user_id)
            
            # Get permissions for each role
            permissions = {}
            for role_name in user_roles:
                # Ensure role_name is lowercase to match database entries
                role = self.get_role(role_name=role_name.lower())
                if role and 'permissions' in role:
                    for perm, value in role['permissions'].items():
                        if value:
                            permissions[perm] = True
            
            return permissions
        except Exception as e:
            logging.error(f"Error getting user permissions: {str(e)}")
            return {}
    
    def has_permission(self, user_id, permission):
        """Check if a user has a specific permission
        
        Args:
            user_id (str): The ID of the user to check
            permission (str): The permission to check for
            
        Returns:
            bool: True if the user has the permission, False otherwise
        """
        try:
            permissions = self.get_user_permissions(user_id)
            return permissions.get('all', False) or permissions.get(permission, False)
        except Exception as e:
            logging.error(f"Error checking permission: {str(e)}")
            return False
    
    def assign_role_to_user(self, user_id, role_name):
        """Assign a role to a user
        
        Args:
            user_id (str): The ID of the user
            role_name (str): The name of the role to assign
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if role exists
            role = self.get_role(role_name=role_name)
            if not role:
                return False
                
            # Check if user already has this role
            user_roles = self.get_user_roles(user_id)
            if role_name in user_roles:
                return True
                
            # Add role to user
            role_id = str(uuid.uuid4())
            self.cursor.execute("""
            INSERT INTO user_roles (id, user_id, role)
            VALUES (?, ?, ?)
            """, (role_id, user_id, role_name))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error assigning role to user: {str(e)}")
            return False
    
    def remove_role_from_user(self, user_id, role_name):
        """Remove a role from a user
        
        Args:
            user_id (str): The ID of the user
            role_name (str): The name of the role to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete the role assignment
            self.cursor.execute("""
            DELETE FROM user_roles 
            WHERE user_id = ? AND role = ?
            """, (user_id, role_name))
            
            # Ensure user has at least one role (basic_user)
            user_roles = self.get_user_roles(user_id)
            if not user_roles:
                self.assign_role_to_user(user_id, 'basic_user')
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error removing role from user: {str(e)}")
            return False
    
    def update_user(self, user_id, update_data):
        """Update user details
        
        Args:
            user_id (int): The ID of the user to update
            update_data (dict): Dictionary containing the fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build the SQL query dynamically based on the fields to update
            fields = []
            values = []
            
            for field, value in update_data.items():
                fields.append(f"{field} = ?")
                values.append(value)
            
            # Add the user_id to the values list
            values.append(user_id)
            
            # Construct the SQL query
            sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
            
            # Execute the query
            self.cursor.execute(sql, values)
            self.conn.commit()
            
            return True
        except sqlite3.Error as e:
            logging.error(f"Error updating user: {str(e)}")
            return False
    
    def delete_user(self, user_id):
        """Delete a user
        
        Args:
            user_id (int): The ID of the user to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Start a transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Delete user roles
            self.cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
            
            # Delete user API keys
            self.cursor.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
            
            # Delete the user
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            # Commit the transaction
            self.conn.commit()
            
            return True
        except sqlite3.Error as e:
            # Rollback the transaction in case of error
            self.conn.rollback()
            logging.error(f"Error deleting user: {str(e)}")
            return False
    
    def update_user_roles(self, user_id, roles):
        """Update a user's roles
        
        Args:
            user_id (int): The ID of the user to update roles for
            roles (list): List of role names to assign to the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Start a transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Delete existing roles
            self.cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
            
            # Add new roles
            for role_name in roles:
                self.cursor.execute(
                    "INSERT INTO user_roles (user_id, role) VALUES (?, ?)",
                    (user_id, role_name)
                )
            
            # Commit the transaction
            self.conn.commit()
            
            return True
        except sqlite3.Error as e:
            # Rollback the transaction in case of error
            self.conn.rollback()
            logging.error(f"Error updating user roles: {str(e)}")
            return False

# Initialize the database when the module is imported
db = Database()