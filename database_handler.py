import re
import secrets
import time
from functools import wraps
from flask import request, jsonify, session, redirect, url_for, flash
from database import db

class AuthHandler:
    def __init__(self):
        self.db = db
        self.token_blacklist = set()  # For logout functionality
        self.failed_attempts = {}     # For rate limiting
        self.attempt_window = 15 * 60  # 15 minutes window for rate limiting
        self.max_attempts = 5         # Max failed attempts before rate limiting
    
    def _is_rate_limited(self, username):
        """Check if a username is rate limited due to too many failed attempts"""
        current_time = time.time()
        if username in self.failed_attempts:
            attempts, timestamp = self.failed_attempts[username]
            # If within the time window and exceeded max attempts
            if current_time - timestamp < self.attempt_window and attempts >= self.max_attempts:
                return True
            # Reset if outside time window
            elif current_time - timestamp >= self.attempt_window:
                self.failed_attempts[username] = (0, current_time)
        return False
    
    def _record_failed_attempt(self, username):
        """Record a failed login attempt"""
        current_time = time.time()
        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            self.failed_attempts[username] = (attempts + 1, current_time)
        else:
            self.failed_attempts[username] = (1, current_time)
    
    def _validate_password_strength(self, password):
        """Validate password meets security requirements"""
        # At least 8 characters, containing uppercase, lowercase, number, and special char
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def _validate_email(self, email):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return True
        return False
    
    def _generate_session_token(self):
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password):
        """Hash a password for storage
        
        Args:
            password (str): The password to hash
            
        Returns:
            str: The hashed password
        """
        import bcrypt
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, stored_password, provided_password):
        """Verify a password against its hash
        
        Args:
            stored_password (str): The stored hashed password
            provided_password (str): The password to verify
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        import bcrypt
        try:
            return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception as e:
            print(f"Error verifying password: {str(e)}")
            return False
    
    def register_user(self, username, password, email, full_name=None, bio=None, roles=None, profile_pic=None):
        """Register a new user
        
        Args:
            username (str): The username for the new user
            password (str): The password for the new user
            email (str): The email for the new user
            full_name (str, optional): The full name for the new user. Defaults to None.
            bio (str, optional): The bio for the new user. Defaults to None.
            roles (list, optional): The roles for the new user. Defaults to None.
            profile_pic (str, optional): The profile picture for the new user. Defaults to None.
            
        Returns:
            dict: The result of the registration
        """
        # Validate inputs
        if not username or not password or not email:
            return {
                'success': False,
                'message': 'All required fields must be provided'
            }
        
        # Validate email format
        if not self._validate_email(email):
            return {
                'success': False,
                'message': 'Invalid email format'
            }
        
        # Validate password strength
        is_valid, message = self._validate_password_strength(password)
        if not is_valid:
            return {
                'success': False,
                'message': message
            }
        
        # Check if user already exists
        try:
            existing_user = self.db.check_user_exists(username, email)
            if existing_user:
                # Provide a more specific error message based on what's duplicated
                if existing_user['duplicate_username'] and existing_user['duplicate_email']:
                    return {
                        'success': False,
                        'message': 'Both username and email already exist'
                    }
                elif existing_user['duplicate_username']:
                    return {
                        'success': False,
                        'message': 'Username already exists'
                    }
                elif existing_user['duplicate_email']:
                    return {
                        'success': False,
                        'message': 'Email already exists'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Username or email already exists'
                    }
            
            # Prepare user roles
            user_roles = []
            if roles:
                for role_name in roles:
                    # Map UI role names to database role names
                    if role_name == 'Admin':
                        user_roles.append({
                            'role': 'admin',
                            'permissions': ['read', 'write', 'delete', 'admin']
                        })
                    elif role_name == 'Medium Admin':
                        user_roles.append({
                            'role': 'medium_admin',
                            'permissions': ['read', 'write', 'delete']
                        })
                    elif role_name == 'Social Media Handler':
                        user_roles.append({
                            'role': 'social_media_handler',
                            'permissions': ['read', 'write']
                        })
                    else:  # Default to Basic User
                        user_roles.append({
                            'role': 'basic_user',
                            'permissions': ['read']
                        })
            else:
                # Default role
                user_roles.append({
                    'role': 'basic_user',
                    'permissions': ['read']
                })
            
            # Hash the password
            hashed_password = self.hash_password(password)
            
            # Create user
            user_id = self.db.create_user(
                username=username,
                password=hashed_password,
                email=email,
                full_name=full_name,
                bio=bio,
                profile_pic=profile_pic,
                roles=user_roles
            )
            
            if user_id:
                # Get the user's permissions to include in the response
                permissions = self.db.get_user_permissions(user_id)
                
                return {
                    'success': True,
                    'message': 'User registered successfully',
                    'user_id': user_id,
                    'permissions': permissions
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create user'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Registration failed: {str(e)}'
            }
    
    def login_user(self, username, password):
        """Authenticate a user and create a session"""
        # Check rate limiting
        if self._is_rate_limited(username):
            return {
                'success': False,
                'message': 'Too many failed attempts. Please try again later.'
            }
        
        # Authenticate user
        user_id = self.db.authenticate_user(username, password)
        
        if not user_id:
            # Record failed attempt
            self._record_failed_attempt(username)
            return {
                'success': False,
                'message': 'Invalid username or password'
            }
        
        # Generate session token
        session_token = self._generate_session_token()
        
        # Store session token in database with expiration time
        expiration_time = time.time() + 3600  # 1 hour
        self.db.store_session_token(user_id, session_token, expiration_time)
        
        # Get user data
        user_data = self.db.get_user(user_id)
        
        return {
            'success': True,
            'message': 'Login successful',
            'user_id': user_id,
            'session_token': session_token,
            'user_data': user_data
        }
    
    def logout_user(self, session_token):
        """Logout a user by invalidating their session token"""
        # Add token to blacklist
        self.token_blacklist.add(session_token)
        
        return {
            'success': True,
            'message': 'Logout successful'
        }
    
    def is_authenticated(self, session_token):
        """Check if a session token is valid"""
        # Check if token is in blacklist
        if session_token in self.token_blacklist:
            return False
        
        # Check if token exists in database and hasn't expired
        user_id = self.db.validate_session_token(session_token)
        if not user_id:
            return False
        return True
    
    def reset_user_password(self, user_id, new_password):
        """
        Reset a user's password
        
        Args:
            user_id (str): The ID of the user whose password needs to be reset
            new_password (str): The new password to set
            
        Returns:
            dict: Result with success status and message
        """
        try:
            # Validate the new password
            is_valid, message = self._validate_password_strength(new_password)
            if not is_valid:
                return {
                    'success': False,
                    'message': message
                }
            
            # Hash the new password
            hashed_password = self.hash_password(new_password)
            
            # Update the password in the database
            result = self.db.update_user_password(user_id, hashed_password)
            
            if result:
                return {
                    'success': True,
                    'message': 'Password has been reset successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to reset password'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error resetting password: {str(e)}'
            }

# Create a decorator for requiring authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in by checking for user_id in session
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

# Initialize the auth handler
auth_handler = AuthHandler()