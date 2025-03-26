import logging
import requests
import json
import os
from typing import Dict, Tuple, Optional
import sys
import os
import json
import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QRectF, QDate, QDateTime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QFileDialog, QTextEdit, QFormLayout, QComboBox, QDateEdit, QLineEdit,
                           QGroupBox, QSpinBox, QGridLayout, QDockWidget as DockWidget, QDateTimeEdit, QCalendarWidget)
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QColor, QBrush
from qfluentwidgets import (FluentIcon, PushButton, ToolButton, TransparentToolButton,
                         LineEdit, PrimaryPushButton, SpinBox, ProgressBar, PushSettingCard,
                         OptionsSettingCard, TitleLabel, CaptionLabel, SubtitleLabel,
                         TextEdit, DateTimeEdit, setTheme, Theme, setThemeColor, NavigationPushButton,
                         FluentWindow, NavigationItemPosition, MessageBox, SplashScreen,
                         ScrollArea, CardWidget, IconWidget, FlowLayout, BodyLabel,
                         ComboBoxSettingCard, OptionsConfigItem, CalendarPicker, PillPushButton,
                         DropDownPushButton, RoundMenu, Action, TransparentPushButton,
                         PrimarySplitPushButton, InfoBar)
import pandas as pd
import time
import sys
from datetime import datetime
from itertools import takewhile, dropwhile, islice
from setting_interface import SettingInterface
from user_data_handler import UserDataHandler
from config_setting import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from post_fetcher import InstagramFetcher, PostData
from typing import List, Dict
import csv
import logging


def get_user_data_dir():
    """Get the user data directory in AppData/Local"""
    app_data = os.getenv('LOCALAPPDATA')
    if not app_data:
        app_data = os.path.expanduser('~/.local/share')  # Fallback for non-Windows
    
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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'login_client_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )

# Setup logging when module is imported
setup_logging()
logger = logging.getLogger(__name__)

class LoginClient:
    """
    A client for interacting with the login server
    
    Provides methods for user authentication and token management
    """
    
    def __init__(self, server_url: str = None):
        """
        Initialize the login client
        
        :param server_url: Optional URL of the login server. If not provided, will read from config file.
        """
        if server_url:
            self.server_url = server_url
        else:
            # Try to read server URL from config file
            try:
                config_path = os.path.join(os.path.dirname(__file__), 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.server_url = config.get('server_url', 'http://localhost:5000')
                else:
                    self.server_url = 'http://localhost:5000'
                logger.debug(f"Using server URL from config: {self.server_url}")
            except Exception as e:
                logger.error(f"Failed to read config file, using default URL: {e}")
                self.server_url = 'http://localhost:5000'
        
        self.token = None
        self.username = None
        self.role_id = None
        self.permissions = None
        logger.debug(f"LoginClient initialized with server URL: {self.server_url}")
        self.load_session()

    def load_session(self):
        """Load saved session data if exists"""
        try:
            session_file = os.path.join(get_user_data_dir(), 'session.json')
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.username = data.get('username')
                    self.role_id = data.get('role_id')
                    self.permissions = data.get('permissions')
                logger.debug(f"Loaded session for user: {self.username}")
        except Exception as e:
            logger.error(f"Failed to load session: {e}")

    def save_session(self):
        """Save session data"""
        try:
            session_file = os.path.join(get_user_data_dir(), 'session.json')
            with open(session_file, 'w') as f:
                json.dump({
                    'token': self.token,
                    'username': self.username,
                    'role_id': self.role_id,
                    'permissions': self.permissions
                }, f)
            logger.debug(f"Saved session for user: {self.username}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def clear_session(self):
        """Clear session data"""
        self.token = None
        self.username = None
        self.role_id = None
        self.permissions = None
        try:
            session_file = os.path.join(get_user_data_dir(), 'session.json')
            if os.path.exists(session_file):
                os.remove(session_file)
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[Dict, int]:
        """Make a request to the server with fallback to localhost"""
        try:
            # Try with configured URL first
            response = requests.request(method, f"{self.server_url}{endpoint}", **kwargs)
            return response.json(), response.status_code
        except requests.ConnectionError:
            # If connection fails and we're not already using localhost, try localhost
            if not self.server_url.startswith('http://localhost'):
                logger.debug(f"Connection failed, trying localhost...")
                fallback_url = 'http://localhost:5000'
                try:
                    response = requests.request(method, f"{fallback_url}{endpoint}", **kwargs)
                    if response.ok:
                        # If localhost works, update the config
                        self.server_url = fallback_url
                        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
                        try:
                            with open(config_path, 'w') as f:
                                json.dump({'server_url': fallback_url}, f, indent=4)
                            logger.debug(f"Updated config to use localhost")
                        except Exception as e:
                            logger.error(f"Failed to update config: {e}")
                    return response.json(), response.status_code
                except requests.ConnectionError as e:
                    logger.error(f"Failed to connect to fallback URL: {e}")
                    raise
            else:
                raise

    def register(self, username: str, password: str, name: str, email: Optional[str] = None, 
                bio: Optional[str] = None, profile_picture: Optional[str] = None, 
                role_id: Optional[int] = 4):
        """Register a new user"""
        data = {
            'username': username,
            'password': password,
            'name': name,
            'email': email,
            'bio': bio,
            'profile_picture': profile_picture,
            'role_id': role_id
        }
        
        # Remove None values from data
        data = {k: v for k, v in data.items() if v is not None}
        
        response, status_code = self._make_request('POST', '/register', json=data)
        return response, status_code

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Login user"""
        response_data, status_code = self._make_request('POST', '/login', json={
            'username': username,
            'password': password
        })
        
        if status_code == 200:
            self.token = response_data.get('token')
            self.username = response_data.get('username')
            self.role_id = response_data.get('role_id')
            self.permissions = response_data.get('permissions')
            self.save_session()
            return True, "Login successful"
        return False, response_data.get('error', 'Login failed')

    def logout(self) -> Tuple[Dict, int]:
        """Logout user"""
        if not self.token:
            return {"error": "Not logged in"}, 401

        try:
            logger.debug(f"Sending logout request to {self.server_url}/logout")
            
            response = requests.post(
                f"{self.server_url}/logout",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            logger.debug(f"Logout response status: {response.status_code}")
            logger.debug(f"Logout response content: {response.text}")
            
            self.clear_session()
            return response.json(), response.status_code
        except requests.RequestException as e:
            logger.error(f"Logout request failed: {str(e)}")
            return {"error": str(e)}, 500

    def get_user_profile(self) -> Tuple[Dict, int]:
        """Get user profile data"""
        if not self.token:
            return {"error": "Not logged in"}, 401

        try:
            logger.debug(f"Sending get user profile request to {self.server_url}/profile")
            
            response = requests.get(
                f"{self.server_url}/profile",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            logger.debug(f"Get user profile response status: {response.status_code}")
            logger.debug(f"Get user profile response content: {response.text}")
            
            return response.json(), response.status_code
        except requests.RequestException as e:
            logger.error(f"Get user profile request failed: {str(e)}")
            return {"error": str(e)}, 500

    def get_profile(self) -> Tuple[Dict, int]:
        """Get user profile"""
        try:
            if not self.token:
                logger.error("No token available")
                return {"error": "Not logged in"}, 401
                
            headers = {"Authorization": f"Bearer {self.token}"}
            logger.debug(f"Sending get profile request to {self.server_url}/profile")
            return self._make_request('GET', '/profile', headers=headers)
        except Exception as e:
            logger.error(f"Failed to get profile: {str(e)}")
            return {"error": str(e)}, 500

    def update_user_profile(self, profile_data: Dict) -> Tuple[Dict, int]:
        """Update user profile"""
        try:
            if not self.token:
                logger.error("No token available")
                return {"error": "Not logged in"}, 401
                
            headers = {"Authorization": f"Bearer {self.token}"}
            logger.debug(f"Sending update profile request to {self.server_url}/profile")
            return self._make_request('PUT', '/profile', json=profile_data, headers=headers)
        except Exception as e:
            logger.error(f"Failed to update profile: {str(e)}")
            return {"error": str(e)}, 500

    def update_password(self, old_password: str, new_password: str) -> Tuple[Dict, int]:
        """Update user password"""
        if not self.token:
            return {"error": "Not logged in"}, 401

        try:
            logger.debug(f"Sending update password request to {self.server_url}/update_password")
            
            response = requests.put(
                f"{self.server_url}/update_password",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "old_password": old_password,
                    "new_password": new_password
                }
            )
            
            logger.debug(f"Update password response status: {response.status_code}")
            logger.debug(f"Update password response content: {response.text}")
            
            return response.json(), response.status_code
        except requests.RequestException as e:
            logger.error(f"Update password request failed: {str(e)}")
            return {"error": str(e)}, 500

    def update_username(self, new_username: str, password: str) -> Tuple[Dict, int]:
        """Update username"""
        if not self.token:
            return {"error": "Not logged in"}, 401

        try:
            logger.debug(f"Sending update username request to {self.server_url}/update_username")
            
            response = requests.put(
                f"{self.server_url}/update_username",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "new_username": new_username,
                    "password": password
                }
            )
            
            logger.debug(f"Update username response status: {response.status_code}")
            logger.debug(f"Update username response content: {response.text}")
            
            if response.status_code == 200:
                self.username = new_username
                self.save_session()
            return response.json(), response.status_code
        except requests.RequestException as e:
            logger.error(f"Update username request failed: {str(e)}")
            return {"error": str(e)}, 500

    def has_permission(self, permission: str) -> bool:
        """Check if the current user has a specific permission"""
        if not self.permissions:
            return False
        return self.permissions.get('all', False) or self.permissions.get(permission, False)

    def get_roles(self) -> Tuple[bool, List[Dict]]:
        """Get available roles"""
        response = self._make_request('GET', '/roles')
        if response.status_code == 200:
            return True, response.json()
        return False, []

    def get_users(self) -> Tuple[Dict, int]:
        """Get list of users"""
        return self._make_request('GET', '/users')
    
    def get_role_permissions(self, role_id):
        """Get role permissions"""
        return self._make_request('GET', f'/roles/{role_id}/permissions')
    
    def delete_user(self, username):
        """Delete a user"""
        return self._make_request('DELETE', f'/users/{username}')
    
    def update_user(self, username, data):
        """Update a user"""
        return self._make_request('PUT', f'/users/{username}', json=data)

    def decode_token(self, token):
        """Decode JWT token"""
        import jwt
        return jwt.decode(token, options={"verify_signature": False})

# Example usage
def main():
    # Create a login client
    client = LoginClient()
    
    # Register a user
    reg_result, reg_status = client.register('testuser', 'password123', 'John Doe', 'test@example.com', 'This is a test bio', 'path/to/profile/picture.jpg')
    print("Registration:", reg_result, reg_status)
    
    # Login
    login_result, login_status = client.login('testuser', 'password123')
    print("Login:", login_result, login_status)
    
    # Get user info
    if client.token:
        user_info, user_status = client.get_user_profile()
        print("User Info:", user_info, user_status)
    
    # Update user profile
    if client.token:
        profile_data = {'email': 'newemail@example.com'}
        update_result, update_status = client.update_user_profile(profile_data)
        print("Update Profile:", update_result, update_status)
    
    # Update password
    if client.token:
        update_result, update_status = client.update_password('password123', 'newpassword123')
        print("Update Password:", update_result, update_status)
    
    # Update username
    if client.token:
        update_result, update_status = client.update_username('newtestuser', 'newpassword123')
        print("Update Username:", update_result, update_status)
    
    # Logout (clear token and username)
    client.logout()

if __name__ == '__main__':
    main()
