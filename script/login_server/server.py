from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import os
import logging
import datetime
import psutil
import jwt
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import json
from typing import Tuple
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Comment out the missing module import
# from new_user_management_website_with_python.app import app as new_flask_app
# Create a placeholder Flask app instead
from flask import Flask

new_flask_app = Flask('new_app')


def get_user_data_dir():
    """Get the user data directory"""
    # For Replit environment
    if os.getenv('REPL_ID'):
        base_dir = os.path.join(os.getcwd(), 'data')
        logs_dir = os.path.join(base_dir, 'logs')
    else:
        # Original local environment logic
        app_data = os.getenv('LOCALAPPDATA')
        if not app_data:
            app_data = os.path.expanduser('~/.local/share')
        base_dir = os.path.join(app_data, 'AI Agency')
        logs_dir = os.path.join(base_dir, 'AI_saves_logs')

    # Create directories if they don't exist
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    return logs_dir


def setup_logging():
    """Setup logging configuration"""
    logs_dir = get_user_data_dir()

    # Create log file with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'login_server_{timestamp}.log')

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file),
                  logging.StreamHandler()])


# Setup logging when module is imported
setup_logging()
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
            static_folder='user_handling_website/static',
            template_folder='user_handling_website')
app.config[
    'SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
CORS(app)  # Enable CORS for all routes
app.wsgi_app = ProxyFix(app.wsgi_app)

# Mount the new Flask app at /new
# Use a simplified configuration to avoid issues with missing modules
application = DispatcherMiddleware(
    app,
    {
        '/new': new_flask_app  # Using our placeholder Flask app
    })


# Initialize database before starting the server
def init_db():
    """Initialize database schema"""
    try:
        logger.debug("Initializing database...")
        db = get_db()
        cursor = db.cursor()

        # Create roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY,
                role_name TEXT UNIQUE NOT NULL,
                permissions TEXT NOT NULL
            )
        ''')

        # Create users table with all required fields including role
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL DEFAULT 4,
                bio TEXT,
                profile_picture TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                FOREIGN KEY (role_id) REFERENCES roles(role_id)
            )
        ''')

        # Create user activity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                prompt TEXT,
                payload TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')

        # Insert default roles if they don't exist
        cursor.execute('''
            INSERT OR IGNORE INTO roles (role_id, role_name, permissions)
            VALUES 
                (1, 'admin', '{"all": true, "manage_users": true, "manage_content": true, "social_media": true, "prompting": true}'),
                (2, 'medium_admin', '{"view_users": true, "manage_content": true, "social_media": true, "prompting": true}'),
                (3, 'social_media_handler', '{"social_media": true, "prompting": true}'),
                (4, 'basic_user', '{"prompting": true}')
        ''')
        db.commit()
        logger.info('Database initialized successfully')
        cursor.close()
        db.close()
    except Exception as e:
        logger.error(f'Failed to initialize database: {str(e)}')
        raise


def get_db():
    """Get a database connection"""
    # Import the adapter (try to import locally first)
    try:
        from db_adapter import get_db_adapter
    except ImportError:
        from script.login_server.db_adapter import get_db_adapter

    # Get connection through the adapter
    db = get_db_adapter().get_connection()

    # Only set row_factory for SQLite connections
    if isinstance(db, sqlite3.Connection):
        db.row_factory = sqlite3.Row

    return db


init_db()


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"


def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]

        if not token:
            logger.warning('Token is missing')
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token,
                              app.config['SECRET_KEY'],
                              algorithms=['HS256'])
            with get_db() as db:
                user = db.execute('SELECT * FROM users WHERE username = ?',
                                  (data['username'], )).fetchone()

            if not user:
                logger.warning(f'User not found: {data["username"]}')
                return jsonify({'error': 'User not found'}), 401

        except jwt.ExpiredSignatureError:
            logger.warning('Token has expired')
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            logger.warning('Invalid token')
            return jsonify({'error': 'Invalid token'}), 401

        return f(user, *args, **kwargs)

    return decorated


def check_permission(required_permission):
    """Decorator to check if user has required permission"""

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No token provided'}), 401

            try:
                data = jwt.decode(token,
                                  app.config['SECRET_KEY'],
                                  algorithms=['HS256'])
                with get_db() as db:
                    role = db.execute(
                        'SELECT permissions FROM roles WHERE role_id = ?',
                        (data.get('role_id'), )).fetchone()

                    if not role:
                        return jsonify({'error': 'Invalid role'}), 403

                    permissions = json.loads(role['permissions'])
                    if permissions.get('all') or permissions.get(
                            required_permission):
                        return f(*args, **kwargs)

                    return jsonify({'error': 'Insufficient permissions'}), 403

            except Exception as e:
                return jsonify({'error': 'Invalid token'}), 401

        return decorated_function

    return decorator


@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        logger.debug(f"Received registration request with data: {data}")

        if not data or not data.get('username') or not data.get('password'):
            logger.warning("Missing required fields in registration request")
            return jsonify({'error': 'Missing required fields'}), 400

        username = data['username']
        password = data['password']
        email = data.get('email')
        bio = data.get('bio', '')
        profile_picture = data.get('profile_picture')
        role_id = data.get('role_id', 4)  # Default to basic user
        name = data.get('name')

        logger.debug(
            f"Processing registration for username: {username}, email: {email}"
        )

        # Validate password
        is_valid, msg = validate_password(password)
        if not is_valid:
            logger.warning(f"Password validation failed: {msg}")
            return jsonify({'error': msg}), 400

        with get_db() as db:
            # Verify role exists
            role = db.execute('SELECT role_id FROM roles WHERE role_id = ?',
                              (role_id, )).fetchone()
            if not role:
                return jsonify({'error': 'Invalid role ID'}), 400

            # Check if username exists
            if db.execute('SELECT 1 FROM users WHERE username = ?',
                          (username, )).fetchone():
                logger.warning(f"Username already exists: {username}")
                return jsonify({'error': 'Username already exists'}), 409

            # Check if email exists (if provided)
            if email and db.execute('SELECT 1 FROM users WHERE email = ?',
                                    (email, )).fetchone():
                logger.warning(f"Email already exists: {email}")
                return jsonify({'error': 'Email already exists'}), 409

            # Hash password
            password_hash = generate_password_hash(password)

            # Insert new user with role
            db.execute(
                '''
                INSERT INTO users (username, name, email, password_hash, bio, profile_picture, role_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, name, email, password_hash, bio, profile_picture,
                  role_id))
            db.commit()

            # Generate token with role information
            token = jwt.encode(
                {
                    'username':
                    username,
                    'role_id':
                    role_id,
                    'exp':
                    datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, app.config['SECRET_KEY'])

            logger.info(f'User registered successfully: {username}')
            return jsonify({
                'message': 'User registered successfully',
                'token': token,
                'username': username,
                'role_id': role_id
            }), 201

    except sqlite3.IntegrityError as e:
        logger.error(f'Database integrity error during registration: {str(e)}')
        return jsonify({'error': 'Username or email already exists'}), 409
    except Exception as e:
        logger.error(f'Error during registration: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    try:
        with get_db() as db:
            user = db.execute(
                '''
                SELECT u.*, r.permissions 
                FROM users u 
                JOIN roles r ON u.role_id = r.role_id 
                WHERE u.username = ?
            ''', (data['username'], )).fetchone()

            if user and check_password_hash(user['password_hash'],
                                            data['password']):
                # Update last login
                db.execute(
                    'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?',
                    (data['username'], ))
                db.commit()

                # Generate token with role information
                token = jwt.encode(
                    {
                        'username':
                        user['username'],
                        'role_id':
                        user['role_id'],
                        'exp':
                        datetime.datetime.utcnow() +
                        datetime.timedelta(hours=24)
                    }, app.config['SECRET_KEY'])

                logger.info(f'User logged in successfully: {user["username"]}')
                return jsonify({
                    'token': token,
                    'username': user['username'],
                    'role_id': user['role_id'],
                    'permissions': json.loads(user['permissions'])
                }), 200
            else:
                logger.warning(
                    f'Invalid login attempt for user: {data["username"]}')
                return jsonify({'error': 'Invalid username or password'}), 401

    except Exception as e:
        logger.error(f'Error during login: {str(e)}')
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/profile/picture', methods=['POST'])
@token_required
def update_profile_picture(user):
    try:
        if 'profile_picture' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({'error': 'Invalid file type'}), 400

        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file with unique name
        filename = f"{user['username']}_{int(datetime.datetime.now().timestamp())}.png"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Update user profile in database with new picture URL
        picture_url = f'/static/uploads/{filename}'
        with get_db() as db:
            db.execute(
                'UPDATE users SET profile_picture = ? WHERE username = ?',
                (picture_url, user['username']))
            db.commit()

        return jsonify({'picture_url': picture_url}), 200

    except Exception as e:
        logger.error(f'Failed to update profile picture: {str(e)}')
        return jsonify({'error': 'Failed to update profile picture'}), 500


@app.route('/api/activity', methods=['GET'])
@token_required
def get_user_activity(user):
    try:
        with get_db() as db:
            # Get last 10 activities for the user
            activities = db.execute(
                '''
                SELECT type, description, created_at 
                FROM user_activity 
                WHERE username = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            ''', (user['username'], )).fetchall()

            return jsonify([{
                'type': activity['type'],
                'description': activity['description'],
                'timestamp': activity['created_at']
            } for activity in activities]), 200

    except Exception as e:
        logger.error(f'Failed to get user activity: {str(e)}')
        return jsonify({'error': 'Failed to load activity data'}), 500


@app.route('/api/stats', methods=['GET'])
@token_required
def get_user_stats(user):
    try:
        with get_db() as db:
            # Get login count
            login_count = db.execute(
                '''
                SELECT COUNT(*) as count 
                FROM user_activity 
                WHERE username = ? AND type = 'login'
            ''', (user['username'], )).fetchone()['count']

            # Get total actions count
            total_actions = db.execute(
                '''
                SELECT COUNT(*) as count 
                FROM user_activity 
                WHERE username = ?
            ''', (user['username'], )).fetchone()['count']

            # Get activity by type
            activity_by_type = db.execute(
                '''
                SELECT type, COUNT(*) as count 
                FROM user_activity 
                WHERE username = ? 
                GROUP BY type
            ''', (user['username'], )).fetchall()

            return jsonify({
                'login_count':
                login_count,
                'total_actions':
                total_actions,
                'activity_by_type': [{
                    'type': act['type'],
                    'count': act['count']
                } for act in activity_by_type]
            }), 200

    except Exception as e:
        logger.error(f'Failed to get user stats: {str(e)}')
        return jsonify({'error': 'Failed to load statistics'}), 500


@app.route('/profile', methods=['GET'])
@token_required
def get_profile(user):
    """Get user profile"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?',
                           (user['username'], ))
            user_data = cursor.fetchone()

            if user_data:
                return jsonify({
                    'username': user_data['username'],
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'bio': user_data['bio'],
                    'profile_picture': user_data['profile_picture']
                }), 200
            else:
                logger.error(f"User not found: {user['username']}")
                return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        return jsonify({'error': 'Failed to load profile data'}), 500


@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(user):
    """Update user profile"""
    data = request.get_json()

    try:
        with get_db() as db:
            update_fields = []
            params = []

            if 'email' in data:
                update_fields.append('email = ?')
                params.append(data['email'])

            if 'bio' in data:
                update_fields.append('bio = ?')
                params.append(data['bio'])

            if 'profile_picture' in data:
                update_fields.append('profile_picture = ?')
                params.append(data['profile_picture'])

            if 'name' in data:
                update_fields.append('name = ?')
                params.append(data['name'])

            if update_fields:
                query = f'''UPDATE users SET {', '.join(update_fields)}
                           WHERE username = ?'''
                params.append(user['username'])

                db.execute(query, params)
                db.commit()

                logger.info(f'Profile updated for user: {user["username"]}')
                return jsonify({'message':
                                'Profile updated successfully'}), 200
            else:
                return jsonify({'message': 'No fields to update'}), 200

    except sqlite3.IntegrityError:
        logger.error(f'Email already exists: {data.get("email")}')
        return jsonify({'error': 'Email already exists'}), 409
    except Exception as e:
        logger.error(f'Error updating profile: {str(e)}')
        return jsonify({'error': 'Failed to update profile'}), 500


@app.route('/users', methods=['GET'])
@token_required
@check_permission(['admin', 'medium_admin'])
def get_users():
    """Get list of users (requires admin or medium_admin permission)"""
    try:
        with get_db() as db:
            users = db.execute('''
                SELECT u.username, u.name, u.email, u.role_id, r.role_name, u.created_at, u.last_login
                FROM users u
                JOIN roles r ON u.role_id = r.role_id
            ''').fetchall()

            user_list = [dict(user) for user in users]
            return jsonify(user_list), 200

    except Exception as e:
        logger.error(f'Error getting users: {str(e)}')
        return jsonify({'error': 'Failed to get users'}), 500


@app.route('/users/<username>', methods=['PUT', 'DELETE'])
@token_required
@check_permission(['admin'])
def manage_user(username):
    """Manage user (requires admin permission)"""
    try:
        if request.method == 'DELETE':
            with get_db() as db:
                db.execute('DELETE FROM users WHERE username = ?',
                           (username, ))
                db.commit()
                return jsonify(
                    {'message': f'User {username} deleted successfully'}), 200
        elif request.method == 'PUT':
            data = request.get_json()
            with get_db() as db:
                updates = []
                values = []
                for key in ['name', 'email', 'role_id']:
                    if key in data:
                        updates.append(f'{key} = ?')
                        values.append(data[key])
                if updates:
                    values.append(username)
                    query = f'UPDATE users SET {", ".join(updates)} WHERE username = ?'
                    db.execute(query, values)
                    db.commit()
                    return jsonify(
                        {'message':
                         f'User {username} updated successfully'}), 200
                return jsonify({'message': 'No updates provided'}), 400
    except Exception as e:
        logger.error(f'Error managing user: {str(e)}')
        return jsonify({'error': 'Failed to manage user'}), 500


@app.route('/roles', methods=['GET'])
@token_required
def get_roles():
    """Get available roles"""
    try:
        with get_db() as db:
            roles = db.execute(
                'SELECT role_id, role_name FROM roles').fetchall()
            return jsonify([dict(role) for role in roles]), 200
    except Exception as e:
        logger.error(f'Error getting roles: {str(e)}')
        return jsonify({'error': 'Failed to get roles'}), 500


@app.route('/role', methods=['POST', 'PUT', 'DELETE'])
@token_required
@check_permission(['admin'])  # Only admins can manage roles
def manage_role():
    """Endpoint to manage roles (create, update, delete)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        db = get_db()
        cursor = db.cursor()

        if request.method == 'POST':
            # Create new role
            if not all(k in data for k in ['role_name', 'permissions']):
                return jsonify({'error': 'Missing required fields'}), 400

            try:
                cursor.execute(
                    '''
                    INSERT INTO roles (role_name, permissions)
                    VALUES (?, ?)
                ''', (data['role_name'], json.dumps(data['permissions'])))
                db.commit()
                return jsonify({'message': 'Role created successfully'}), 201
            except sqlite3.IntegrityError:
                return jsonify({'error': 'Role name already exists'}), 409

        elif request.method == 'PUT':
            # Update existing role
            if not all(k in data
                       for k in ['role_id', 'role_name', 'permissions']):
                return jsonify({'error': 'Missing required fields'}), 400

            cursor.execute(
                '''
                UPDATE roles
                SET role_name = ?, permissions = ?
                WHERE role_id = ?
            ''', (data['role_name'], json.dumps(
                    data['permissions']), data['role_id']))

            if cursor.rowcount == 0:
                return jsonify({'error': 'Role not found'}), 404

            db.commit()
            return jsonify({'message': 'Role updated successfully'}), 200

        elif request.method == 'DELETE':
            # Delete role
            if 'role_id' not in data:
                return jsonify({'error': 'Role ID required'}), 400

            # Check if role is assigned to any users
            cursor.execute('SELECT COUNT(*) FROM users WHERE role_id = ?',
                           (data['role_id'], ))
            if cursor.fetchone()[0] > 0:
                return jsonify(
                    {'error':
                     'Cannot delete role that is assigned to users'}), 400

            cursor.execute('DELETE FROM roles WHERE role_id = ?',
                           (data['role_id'], ))

            if cursor.rowcount == 0:
                return jsonify({'error': 'Role not found'}), 404

            db.commit()
            return jsonify({'message': 'Role deleted successfully'}), 200

    except Exception as e:
        logger.error(f'Error in role management: {str(e)}')
        if 'db' in locals():
            db.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if 'db' in locals():
            db.close()


@app.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify if email matches username in database"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')

        if not username or not email:
            return jsonify({'error': 'Username and email are required'}), 400

        # Get user from database
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT email FROM users WHERE username = ?',
                       (username, ))
        result = cursor.fetchone()

        if result:
            stored_email = result[0]
            return jsonify({'valid': stored_email == email}), 200

        return jsonify({'valid': False}), 200

    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/get-credentials', methods=['POST'])
def get_credentials():
    """Get user credentials for password recovery"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')

        if not username or not email:
            return jsonify({'error': 'Username and email are required'}), 400

        # Generate a temporary password
        import random
        import string

        def generate_temp_password():
            # Generate a password with:
            # 2 uppercase letters + 2 lowercase letters + 2 digits + 2 special chars
            chars = []
            chars.extend(random.choices(string.ascii_uppercase, k=2))
            chars.extend(random.choices(string.ascii_lowercase, k=2))
            chars.extend(random.choices(string.digits, k=2))
            chars.extend(random.choices("!@#$%^&*", k=2))
            # Shuffle the characters
            random.shuffle(chars)
            return ''.join(chars)

        temp_password = generate_temp_password()

        # Update user's password in database
        db = get_db()
        cursor = db.cursor()

        # First verify the user exists with given email
        cursor.execute(
            'SELECT username FROM users WHERE username = ? AND email = ?',
            (username, email))
        user = cursor.fetchone()

        if user:
            # Hash the new temporary password
            password_hash = generate_password_hash(temp_password)

            # Update the password using username since we don't have an id column
            cursor.execute(
                'UPDATE users SET password_hash = ? WHERE username = ?',
                (password_hash, username))
            db.commit()

            return jsonify({'password': temp_password}), 200

        return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/update_password', methods=['PUT'])
@token_required
def update_password(user):
    """Update user password"""
    data = request.get_json()

    if not data or not data.get('old_password') or not data.get(
            'new_password'):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        if check_password_hash(user['password_hash'], data['old_password']):
            with get_db() as db:
                new_password_hash = generate_password_hash(
                    data['new_password'])
                db.execute(
                    'UPDATE users SET password_hash = ? WHERE username = ?',
                    (new_password_hash, user['username']))
                db.commit()

            logger.info(f'Password updated for user: {user["username"]}')
            return jsonify({'message': 'Password updated successfully'}), 200
        else:
            return jsonify({'error': 'Invalid old password'}), 401

    except Exception as e:
        logger.error(f'Error updating password: {str(e)}')
        return jsonify({'error': 'Failed to update password'}), 500


@app.route('/update_username', methods=['PUT'])
@token_required
def update_username(user):
    """Update username"""
    data = request.get_json()

    if not data or not data.get('new_username') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        if check_password_hash(user['password_hash'], data['password']):
            with get_db() as db:
                # Check if new username exists
                if db.execute('SELECT 1 FROM users WHERE username = ?',
                              (data['new_username'], )).fetchone():
                    return jsonify({'error': 'Username already exists'}), 409

                db.execute('UPDATE users SET username = ? WHERE username = ?',
                           (data['new_username'], user['username']))
                db.commit()

            logger.info(
                f'Username updated from {user["username"]} to {data["new_username"]}'
            )
            return jsonify({
                'message': 'Username updated successfully',
                'username': data['new_username']
            }), 200
        else:
            return jsonify({'error': 'Invalid password'}), 401

    except Exception as e:
        logger.error(f'Error updating username: {str(e)}')
        return jsonify({'error': 'Failed to update username'}), 500


@app.route('/logout', methods=['POST'])
@token_required
def logout(user):
    """Handle user logout"""
    logger.info(f'User logged out: {user["username"]}')
    return jsonify({'message': 'Logged out successfully'}), 200


def track_user_activity(username: str, activity_type: str, description: str):
    """Track user activity in the database"""
    try:
        with get_db() as db:
            db.execute(
                '''
                INSERT INTO user_activity (username, type, description, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (username, activity_type, description))
            db.commit()
    except Exception as e:
        logger.error(f'Failed to track user activity: {str(e)}')


if __name__ == '__main__':
    # Check if running on Replit
    if os.getenv('REPL_ID'):
        port = int(os.getenv('PORT', 8080))
    else:
        port = 8080

    # Run the server
    logger.info(f"Starting server on port {port}")
    serve(application, host='0.0.0.0',
          port=port)  # Use application instead of app to include both apps