from flask import Flask, render_template, send_from_directory, request, jsonify, session, redirect, url_for, flash
import os
import base64
import string
import random
import sys
from database_handler import auth_handler, login_required
from werkzeug.utils import secure_filename
# Import the EmailHandler for password recovery
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agency-server', 'script'))
from email_handler.email_handler import EmailHandler
# Import the API key generation module
from api_key_generation import get_user_api_keys, delete_api_key, get_api_secret

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)  # For secure session management

# Configure allowed file extensions for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the EmailHandler
email_handler = EmailHandler()

@app.route('/')
def index():
    """Render the index page or redirect to dashboard if logged in"""
    # Check if user is logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'danger')
            return redirect(url_for('login'))
        
        # Use login_user method instead of authenticate_user
        result = auth_handler.login_user(username, password)
        
        if result['success']:
            # Set session variables
            session['user_id'] = result['user_id']
            session['username'] = username
            
            # Get user permissions and store in session
            permissions = auth_handler.db.get_user_permissions(result['user_id'])
            session['permissions'] = permissions
            
            flash('Login successful!', 'success')
            next_page = request.args.get('next') or url_for('dashboard')
            return redirect(next_page)
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('login'))
    else:
        # Check if user is already logged in
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('login_register.html', next=request.args.get('next'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        full_name = data.get('full_name')
        bio = data.get('bio')
        role = data.get('role', 'Basic User')  # Default to Basic User if not specified
        admin_password = data.get('admin_password', '')
        
        # Check admin password for Admin and Medium Admin roles
        if role in ['Admin', 'Medium Admin']:
            if admin_password != '1137M$@&#':
                flash('Invalid admin password. Access denied.', 'error')
                return render_template('login_register.html')
        
        # Handle profile picture upload
        profile_pic_data = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                # Read the file data and convert to base64
                file_data = file.read()
                encoded_image = base64.b64encode(file_data).decode('utf-8')
                # Create a data URL with the appropriate MIME type
                mime_type = file.content_type or 'image/jpeg'  # Default to jpeg if type not available
                profile_pic_data = f"data:{mime_type};base64,{encoded_image}"
        
        # Add role and profile picture to user data
        result = auth_handler.register_user(
            username, 
            password, 
            email, 
            full_name, 
            bio, 
            roles=[role],
            profile_pic=profile_pic_data
        )
        
        if result['success']:
            # Set session variables to log the user in automatically
            session['user_id'] = result['user_id']
            session['username'] = username
            
            # Store permissions in session
            if 'permissions' in result:
                session['permissions'] = result['permissions']
            
            flash('Registration successful! You have been automatically logged in.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result['message'], 'error')
    
    return render_template('login_register.html')

@app.route('/logout')
def logout():
    """Log out the user"""
    # Clear the session
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    """Render the profile page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data
    user_id = session['user_id']
    user = auth_handler.db.get_user(user_id)
    
    # Get user permissions from session or fetch them if not available
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    return render_template('profile.html', user=user, permissions=permissions)

@app.route('/users')
@login_required
def users():
    # Get all users from database
    users_list = auth_handler.db.get_all_users()
    
    # Get user permissions from session or fetch them if not available
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    # Check if user has permission to manage users
    if not permissions.get('manage_users') and not permissions.get('all'):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('users.html', users=users_list, permissions=permissions)

@app.route('/api/generate_api_key', methods=['POST'])
@login_required
def generate_api_key():
    user_id = session.get('user_id')
    
    # Generate new API key
    api_key_data = auth_handler.db.create_api_key(user_id)
    
    return jsonify({
        'success': True,
        'api_key': api_key_data
    })

@app.route('/api_keys')
def api_keys():
    """Render the API keys page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.url))
    
    # Get user data
    user_id = session['user_id']
    user = auth_handler.db.get_user(user_id)
    
    # Get user permissions from session or fetch them if not available
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    # Get user's API keys
    keys = auth_handler.db.get_user_api_keys(user_id)
    
    return render_template('api_keys.html', user=user, keys=keys, permissions=permissions)

@app.route('/api/keys', methods=['GET'])
def get_keys():
    """Get API keys for the current user"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user's API keys
    user_id = session['user_id']
    keys = auth_handler.db.get_user_api_keys(user_id)
    
    return jsonify({'success': True, 'keys': keys})

@app.route('/api/keys', methods=['POST'])
def create_key():
    """Create a new API key for the current user"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Create a new API key
    user_id = session['user_id']
    key = auth_handler.db.create_api_key(user_id)
    
    return jsonify({'success': True, 'key': key})

@app.route('/api/keys/<key_id>', methods=['DELETE'])
def delete_key(key_id):
    """Delete an API key"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Delete the API key
    user_id = session['user_id']
    result = auth_handler.db.delete_api_key(key_id, user_id)
    
    if result:
        return jsonify({'success': True, 'message': 'API key deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to delete API key'}), 400

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})

@app.route('/api/profile', methods=['POST'])
def update_profile():
    """Update user profile information"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        data = request.json
        
        # Update user data
        updates = {}
        if 'full_name' in data:
            updates['full_name'] = data['full_name']
        if 'bio' in data:
            updates['bio'] = data['bio']
        
        # Update user in database
        if updates:
            auth_handler.db.update_user(user_id, updates)
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'No data to update'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profile/picture', methods=['POST'])
def update_profile_picture():
    """Update user profile picture"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        data = request.json
        
        if 'profile_pic' in data:
            # Update profile picture in database
            auth_handler.db.update_user(user_id, {'profile_pic': data['profile_pic']})
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'No profile picture data provided'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profile/username', methods=['POST'])
def update_username():
    """Update username"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        data = request.json
        
        if 'new_username' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Verify password
        user = auth_handler.db.get_user(user_id)
        if not auth_handler.verify_password(data['password'], user['password_hash']):
            return jsonify({'success': False, 'message': 'Invalid password'})
        
        # Check if username is already taken
        if auth_handler.db.get_user_by_username(data['new_username']) and data['new_username'] != user['username']:
            return jsonify({'success': False, 'message': 'Username already taken'})
        
        # Update username
        auth_handler.db.update_user(user_id, {'username': data['new_username']})
        session['username'] = data['new_username']
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profile/password', methods=['POST'])
def update_password():
    """Update password"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        data = request.json
        
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Verify current password
        user = auth_handler.db.get_user(user_id)
        if not auth_handler.verify_password(data['current_password'], user['password_hash']):
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        # Update password
        password_hash = auth_handler.hash_password(data['new_password'])
        auth_handler.db.update_user(user_id, {'password_hash': password_hash})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/password-recovery', methods=['GET'])
def password_recovery_form():
    """Render the password recovery form"""
    return render_template('password_recovery.html')

@app.route('/recover-password', methods=['POST'])
def recover_password():
    """Process password recovery request"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Check if email exists in the database
        user = auth_handler.db.get_user_by_email(email)
        
        if not user:
            flash('No account found with that email address.', 'error')
            return redirect(url_for('password_recovery_form'))
        
        # Generate a new random password
        new_password = generate_secure_password()
        
        # Update the user's password in the database
        auth_handler.reset_user_password(user['id'], new_password)
        
        # Send recovery email with the new password
        email_sent = email_handler.send_password_recovery_email(
            recipient_email=email,
            username=user['username'],
            password=new_password
        )
        
        if email_sent:
            flash('Password recovery email has been sent. Please check your inbox.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Failed to send recovery email. Please try again later.', 'error')
            return redirect(url_for('password_recovery_form'))

def generate_secure_password(length=12):
    """Generate a secure random password"""
    # Define character sets
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    special_chars = '!@#$%^&*()_-+=<>?'
    
    # Ensure at least one of each type
    password = [
        random.choice(uppercase_letters),
        random.choice(lowercase_letters),
        random.choice(digits),
        random.choice(special_chars)
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = uppercase_letters + lowercase_letters + digits + special_chars
    password.extend(random.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password characters
    random.shuffle(password)
    
    # Convert list to string
    return ''.join(password)

@app.route('/style/<path:filename>')
def serve_static(filename):
    return send_from_directory('style', filename)

@app.route('/static/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static', filename)

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Get user data
    user_id = session['user_id']
    user = auth_handler.db.get_user(user_id)
    
    # Get user permissions from session or fetch them if not available
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    return render_template('dashboard.html', user=user, permissions=permissions)

@app.route('/roles')
def roles_page():
    """Render the roles management page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data
    user_id = session['user_id']
    user = auth_handler.db.get_user(user_id)
    
    # Get user permissions from session or fetch them if not available
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all roles
    roles = auth_handler.db.get_all_roles()
    
    return render_template('roles.html', user=user, roles=roles, permissions=permissions)

# API endpoints for role management
@app.route('/api/roles', methods=['GET'])
@login_required
def get_roles():
    """Get all available roles"""
    try:
        # Get all available roles directly from database
        all_roles = auth_handler.db.get_all_roles()
        
        # Log the roles for debugging
        print(f"Found {len(all_roles)} roles")
        
        # Return the complete role objects
        return jsonify({'success': True, 'roles': all_roles})
    except Exception as e:
        print(f"Error in get_roles: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/roles/all', methods=['GET'])
def get_all_roles_api():
    """Get all available roles as a simple JSON array"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
        # Get all available roles directly from database
        all_roles = auth_handler.db.get_all_roles()
        
        # Extract just the role names
        role_names = []
        for role in all_roles:
            if 'role_name' in role and role['role_name']:
                role_names.append(role['role_name'])
        
        # Log the roles for debugging
        print(f"API: Found {len(role_names)} roles: {role_names}")
        
        return jsonify({'success': True, 'roles': role_names})
    except Exception as e:
        print(f"Error in get_all_roles_api: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/roles/<int:role_id>', methods=['GET'])
def get_role(role_id):
    """Get a specific role"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(user_id)
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get the role
    role = auth_handler.db.get_role(role_id=role_id)
    
    if not role:
        return jsonify({'success': False, 'message': 'Role not found'}), 404
    
    return jsonify({'success': True, 'role': role})

@app.route('/api/roles', methods=['POST'])
def create_role():
    """Create a new role"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(user_id)
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get role data from request
    data = request.json
    
    if not data or not data.get('name') or not data.get('permissions'):
        return jsonify({'success': False, 'message': 'Invalid role data'}), 400
    
    # Create the role
    role_id = auth_handler.db.create_role(data['name'], data['permissions'], data.get('description', ''))
    
    if not role_id:
        return jsonify({'success': False, 'message': 'Failed to create role'}), 500
    
    return jsonify({'success': True, 'role_id': role_id}), 201

@app.route('/api/roles/<int:role_id>', methods=['PUT'])
def update_role(role_id):
    """Update a role"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(user_id)
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get role data from request
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'Invalid role data'}), 400
    
    # Check if role exists
    role = auth_handler.db.get_role(role_id=role_id)
    
    if not role:
        return jsonify({'success': False, 'message': 'Role not found'}), 404
    
    # Prepare updates dictionary
    updates = {}
    if 'name' in data:
        updates['role_name'] = data['name']
    if 'permissions' in data:
        updates['permissions'] = data['permissions']
    if 'description' in data:
        updates['description'] = data['description']
    
    # Update the role
    success = auth_handler.db.update_role(role_id, updates)
    
    if not success:
        return jsonify({'success': False, 'message': 'Failed to update role'}), 500
    
    return jsonify({'success': True, 'message': 'Role updated successfully'})

@app.route('/api/roles/<int:role_id>', methods=['DELETE'])
def delete_role(role_id):
    """Delete a role"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(user_id)
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Check if role exists
    role = auth_handler.db.get_role(role_id)
    
    if not role:
        return jsonify({'success': False, 'message': 'Role not found'}), 404
    
    # Delete the role
    success = auth_handler.db.delete_role(role_id)
    
    if not success:
        return jsonify({'success': False, 'message': 'Failed to delete role. Default roles cannot be deleted.'}), 400
    
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/roles', methods=['GET'])
def get_user_roles(user_id):
    """Get roles for a specific user"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    current_user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(current_user_id)
    
    # Check if user has permission to manage roles or is requesting their own roles
    if current_user_id != user_id and not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Check if user exists
    user = auth_handler.db.get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get user roles
    roles = auth_handler.db.get_user_roles(user_id)
    
    return jsonify({'success': True, 'roles': roles})

@app.route('/api/users/<int:user_id>/roles/<role_name>', methods=['POST'])
def assign_role_to_user(user_id, role_name):
    """Assign a role to a user"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    current_user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(current_user_id)
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Check if user exists
    user = auth_handler.db.get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Check if role exists
    role = auth_handler.db.get_role(role_name=role_name)
    
    if not role:
        return jsonify({'success': False, 'message': 'Role not found'}), 404
    
    # Assign role to user
    success = auth_handler.db.assign_role_to_user(user_id, role_name)
    
    if not success:
        return jsonify({'success': False, 'message': 'Failed to assign role to user'}), 500
    
    # Update session permissions if this is the current user
    update_session_permissions(user_id)
    
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/roles/<role_name>', methods=['DELETE'])
def remove_role_from_user(user_id, role_name):
    """Remove a role from a user"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get user permissions
    current_user_id = session['user_id']
    permissions = auth_handler.db.get_user_permissions(current_user_id)
    
    # Check if user has permission to manage roles
    if not permissions.get('manage_roles') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Check if user exists
    user = auth_handler.db.get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Check if role exists
    role = auth_handler.db.get_role(role_name=role_name)
    
    if not role:
        return jsonify({'success': False, 'message': 'Role not found'}), 404
    
    # Remove role from user
    success = auth_handler.db.remove_role_from_user(user_id, role_name)
    
    if not success:
        return jsonify({'success': False, 'message': 'Failed to remove role from user'}), 500
    
    # Update session permissions if this is the current user
    update_session_permissions(user_id)
    
    return jsonify({'success': True})

# Add a utility function to update user permissions in session
def update_session_permissions(user_id):
    """Update the user permissions in the session"""
    if 'user_id' in session and session['user_id'] == user_id:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
        return permissions
    return None

# API routes for user management
@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    """Create a new user"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'You do not have permission to create users'}), 403
    
    # Get data from request
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role_name = data.get('role')
    
    # Validate required fields
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email, and password are required'}), 400
    
    # Create role data
    role = {'name': role_name}
    
    # Register the user
    result = auth_handler.register_user(
        username, 
        password, 
        email, 
        full_name, 
        bio=None, 
        roles=[role],
        profile_pic=None
    )
    
    if result['success']:
        return jsonify({'success': True, 'user_id': result['user_id']})
    else:
        return jsonify({'success': False, 'message': result['message']}), 400

@app.route('/api/users/<username>', methods=['GET'])
@login_required
def get_user(username):
    """Get user details"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'You do not have permission to view user details'}), 403
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Remove sensitive data
    if 'password' in user:
        del user['password']
    
    return jsonify({'success': True, 'user': user})

@app.route('/api/users/<username>', methods=['PUT'])
@login_required
def update_user(username):
    """Update user details"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'You do not have permission to update users'}), 403
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get data from request
    data = request.json
    
    # Update user details
    update_data = {}
    if 'email' in data:
        update_data['email'] = data['email']
    if 'full_name' in data:
        update_data['full_name'] = data['full_name']
    if 'bio' in data:
        update_data['bio'] = data['bio']
    
    # Update password if provided
    if 'password' in data and data['password']:
        # Hash the password
        hashed_password = auth_handler.hash_password(data['password'])
        update_data['password'] = hashed_password
    
    # Update the user
    success = auth_handler.db.update_user(user['id'], update_data)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to update user'}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def delete_user(username):
    """Delete a user"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'You do not have permission to delete users'}), 403
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Cannot delete yourself
    if user['id'] == user_id:
        return jsonify({'success': False, 'message': 'You cannot delete your own account'}), 400
    
    # Delete the user
    success = auth_handler.db.delete_user(user['id'])
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to delete user'}), 500

@app.route('/users/<username>', methods=['GET'])
@login_required
def view_user(username):
    """View a specific user's profile"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        flash('You do not have permission to view user profiles', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('users'))
    
    # Get user roles
    user_role_names = auth_handler.db.get_user_roles(user['id'])
    user_roles = []
    for role_name in user_role_names:
        role = auth_handler.db.get_role(role_name=role_name.lower())
        if role:
            user_roles.append(role)
    
    # Get user permissions
    user_permissions = auth_handler.db.get_user_permissions(user['id'])
    
    return render_template('user_profile.html', user=user, user_roles=user_roles, user_permissions=user_permissions, permissions=permissions)

@app.route('/users/<username>/edit', methods=['GET'])
@login_required
def edit_user(username):
    """Edit a specific user's profile"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        flash('You do not have permission to edit user profiles', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('users'))
    
    # Get all available roles
    all_roles = auth_handler.db.get_all_roles()
    
    # Get user roles
    user_role_names = auth_handler.db.get_user_roles(user['id'])
    user_roles = []
    for role_name in user_role_names:
        role = auth_handler.db.get_role(role_name=role_name.lower())
        if role:
            user_roles.append(role)
    
    return render_template('edit_user.html', user=user, all_roles=all_roles, user_roles=user_roles, permissions=permissions)

@app.route('/api/users/<username>/roles', methods=['PATCH'])
@login_required
def update_user_roles(username):
    """Update a user's roles"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get data from request
    data = request.json
    if not data or 'roles' not in data:
        return jsonify({'success': False, 'message': 'No roles provided'}), 400
    
    # Update user roles
    success = auth_handler.db.update_user_roles(user['id'], data['roles'])
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to update user roles'}), 500

@app.route('/api/users/<username>', methods=['GET'])
@login_required
def get_user_api(username):
    """Get user details"""
    # Check if user has permission to manage users
    user_id = session['user_id']
    permissions = session.get('permissions')
    if not permissions:
        permissions = auth_handler.db.get_user_permissions(user_id)
        session['permissions'] = permissions
    
    if not permissions.get('manage_users') and not permissions.get('all'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get user details
    user = auth_handler.db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get user roles
    user_roles = auth_handler.db.get_user_roles(user['id'])
    
    # Add roles to user object
    user_data = dict(user)
    user_data['user_roles'] = user_roles
    
    return jsonify({'success': True, 'user': user_data})

@app.route('/api/verify-password', methods=['POST'])
def verify_password():
    """Verify user password and retrieve API secret"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Get request data
    data = request.form
    password = data.get('password')
    key_id = data.get('key_id')
    
    if not password or not key_id:
        return jsonify({'success': False, 'message': 'Password and key ID are required'}), 400
    
    # Get user data
    user_id = session['user_id']
    user = auth_handler.db.get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Verify password
    if not auth_handler.db._verify_password(user['password'], password, user['password_salt']):
        return jsonify({'success': False, 'message': 'Incorrect password'}), 401
    
    # Get API secret
    api_secret = get_api_secret(auth_handler.db.conn, key_id, user_id)
    
    if not api_secret:
        return jsonify({'success': False, 'message': 'API key not found or does not belong to you'}), 404
    
    return jsonify({
        'success': True,
        'api_secret': api_secret
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
