# Login Server Documentation

## Overview
This login server provides a comprehensive user management system with secure authentication, profile management, role-based access control, and email verification features.

## Server Endpoints

### Authentication Endpoints

#### 1. Registration
- **Endpoint**: `/register`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "username": "string",
    "name": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Responses**:
  - `201`: User registered successfully
  - `409`: Username or email already exists
  - `400`: Invalid password or missing fields

#### 2. Login
- **Endpoint**: `/login`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Responses**:
  - `200`: Login successful (returns JWT token)
  - `401`: Invalid credentials

#### 3. Logout
- **Endpoint**: `/logout`
- **Method**: POST
- **Headers**: `Authorization: Bearer <token>`
- **Responses**:
  - `200`: Logout successful
  - `401`: Unauthorized

### Profile Management

#### 4. Get Profile
- **Endpoint**: `/profile`
- **Method**: GET
- **Headers**: `Authorization: Bearer <token>`
- **Responses**:
  - `200`: Returns user profile
  - `401`: Unauthorized
  - `404`: Profile not found

#### 5. Update Profile
- **Endpoint**: `/profile`
- **Method**: PUT
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "name": "string",
    "bio": "string",
    "profile_picture": "string"
  }
  ```
- **Responses**:
  - `200`: Profile updated successfully
  - `401`: Unauthorized

#### 6. Update Password
- **Endpoint**: `/update_password`
- **Method**: PUT
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "current_password": "string",
    "new_password": "string"
  }
  ```
- **Responses**:
  - `200`: Password updated successfully
  - `401`: Invalid current password
  - `400`: Invalid new password

#### 7. Update Username
- **Endpoint**: `/update_username`
- **Method**: PUT
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "new_username": "string",
    "password": "string"
  }
  ```
- **Responses**:
  - `200`: Username updated successfully
  - `401`: Invalid password
  - `409`: Username already exists

### Account Recovery

#### 8. Verify Email
- **Endpoint**: `/verify_email`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "string",
    "username": "string"
  }
  ```
- **Responses**:
  - `200`: Email verified successfully
  - `404`: Email/username combination not found

#### 9. Get Credentials
- **Endpoint**: `/get_credentials`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "string",
    "username": "string",
    "verification_code": "string"
  }
  ```
- **Responses**:
  - `200`: Credentials recovery initiated
  - `404`: User not found
  - `400`: Invalid verification code

### User Management (Admin Only)

#### 10. Get Users List
- **Endpoint**: `/users`
- **Method**: GET
- **Headers**: `Authorization: Bearer <token>`
- **Required Permission**: admin or medium_admin
- **Responses**:
  - `200`: Returns list of users
  - `401`: Unauthorized
  - `403`: Insufficient permissions

#### 11. Get Roles
- **Endpoint**: `/roles`
- **Method**: GET
- **Headers**: `Authorization: Bearer <token>`
- **Required Permission**: admin
- **Responses**:
  - `200`: Returns available roles
  - `401`: Unauthorized
  - `403`: Insufficient permissions

#### 12. Manage Roles
- **Endpoint**: `/roles`
- **Method**: POST/PUT/DELETE
- **Headers**: `Authorization: Bearer <token>`
- **Required Permission**: admin
- **Request Body**:
  ```json
  {
    "action": "create|update|delete",
    "role_name": "string",
    "permissions": "json_string",
    "role_id": "integer"
  }
  ```
- **Responses**:
  - `200`: Role managed successfully
  - `401`: Unauthorized
  - `403`: Insufficient permissions
  - `400`: Invalid request

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Role-Based Access Control
Four default roles with different permission levels:
1. **admin**: Full system access
2. **medium_admin**: Content management and social media access
3. **social_media_handler**: Social media and prompting access
4. **basic_user**: Basic prompting access only

## Technical Details

### Database Schema
- **Users Table**:
  - username (PRIMARY KEY)
  - name
  - email (UNIQUE)
  - password_hash
  - role_id
  - bio
  - profile_picture
  - created_at
  - last_login

- **Roles Table**:
  - role_id (PRIMARY KEY)
  - role_name (UNIQUE)
  - permissions

### Dependencies
- Flask
- Flask-CORS
- JWT
- SQLite3
- Werkzeug
- Waitress
- psutil

## Server Configuration
The server uses:
- CORS enabled for all routes
- ProxyFix middleware for reverse proxy support
- Waitress as the production WSGI server
- Comprehensive logging system with file and console output

## Running the Server
```bash
# Development mode
python server.py

# Production mode (default)
# Runs on 0.0.0.0:5000 with Waitress
python server.py
```

## Security Considerations
1. Uses JWT for authentication
2. Password hashing with Werkzeug
3. Role-based access control
4. Email verification for account recovery
5. Secure password requirements
6. Logging of security-related events

## Error Handling
- Comprehensive error logging
- Detailed error messages
- Database connection error handling
- Token validation error handling
- Permission validation

## File Storage
- Logs stored in AppData/Local/AI Agency/AI_saves_logs (Windows)
- Falls back to ~/.local/share/AI Agency (non-Windows)
- SQLite database in the same directory as server.py

## Connecting to the Server

### Python Example
```python
import requests

# Server URL (default)
SERVER_URL = 'http://localhost:5000'

# Registration
def register_user(username, name, email, password):
    response = requests.post(f'{SERVER_URL}/register', json={
        'username': username,
        'name': name,
        'email': email,
        'password': password
    })
    return response.json(), response.status_code

# Login
def login_user(username, password):
    response = requests.post(f'{SERVER_URL}/login', json={
        'username': username,
        'password': password
    })
    return response.json(), response.status_code

# Token Validation
def validate_token(token):
    response = requests.post(f'{SERVER_URL}/validate_token', json={
        'token': token
    })
    return response.json(), response.status_code

# Get User Info
def get_user_info(token):
    response = requests.get(f'{SERVER_URL}/user_info', 
                            headers={'Authorization': token})
    return response.json(), response.status_code
```

## Troubleshooting
- Ensure all dependencies are installed
- Check firewall settings
- Verify network connectivity
- Review server logs for detailed error information

## Dependencies
- Flask
- Flask-CORS
- JWT
- SQLite3
- Werkzeug
- Waitress
- psutil

## Configuration
Modify `server.py` to change:
- Database path
- Server host/port
- Logging configuration
