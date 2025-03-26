import sys
import os
import json
import requests
import darkdetect
import traceback
import logging
import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QDate, QDateTime, QEvent, QPoint
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QFileDialog, QTextEdit, QFormLayout, QComboBox, QDateEdit, QLineEdit,
                           QGroupBox, QSpinBox, QGridLayout, QDockWidget as DockWidget, QDateTimeEdit, QCalendarWidget, QDialog, QSplashScreen)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont
from qfluentwidgets import (FluentIcon, PushButton, ToolButton, TransparentToolButton,
                         LineEdit, PrimaryPushButton, SpinBox, ProgressBar, PushSettingCard,
                         OptionsSettingCard, TitleLabel, CaptionLabel, SubtitleLabel,
                         TextEdit, DateTimeEdit, setTheme, Theme, setThemeColor, NavigationPushButton,
                         FluentWindow, NavigationItemPosition, MessageBox, ScrollArea, CardWidget, IconWidget, FlowLayout, BodyLabel,
                         ComboBoxSettingCard, OptionsConfigItem, CalendarPicker, PillPushButton,
                         DropDownPushButton, RoundMenu, Action, TransparentPushButton,
                         PrimarySplitPushButton, InfoBar)
from ma import (
    ScrollableToolsInterface, ScrollableAnalyticsInterface, ScrollableGenerationInterface,
    ToolsInterface, AnalyticsInterface, GenerationInterface
)
from login_server.login_client import LoginClient
from setting_interface import SettingInterface
from profile_interface import ProfileInterface
from listing_users_interface import ListingUsersInterface
import re
import logging
import datetime

def get_user_data_dir():
    """Get the user data directory in AppData/Local"""
    import os
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
    # Get the correct logs directory from AppData/Local
    logs_dir = get_user_data_dir()
    
    # Create log file with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'modern_analytics_{timestamp}.log')
    
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

class CustomSplashScreen(QSplashScreen):
    def __init__(self):
        # Get splash image path
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        splash_path = os.path.join(resources_dir, 'ai.png')
        
        # Create pixmap from splash image and scale it
        pixmap = QPixmap(splash_path)
        # Scale to desired size (e.g., 400x400 pixels while keeping aspect ratio)
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(scaled_pixmap)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())

class LoadingSplashScreen(QSplashScreen):
    def __init__(self):
        # Get splash image path
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        splash_path = os.path.join(resources_dir, 'ai.png')
        
        # Create pixmap from splash image and scale it
        pixmap = QPixmap(splash_path)
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(scaled_pixmap)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())
        
        # Set message style
        self.setStyleSheet("""
            QSplashScreen {
                color: #2196F3;
                font-size: 14px;
                font-weight: bold;
            }
        """)
    
    def showLoading(self):
        self.show()
        self.showMessage("Loading your workspace...\nThis might take a while, please be patient!", 
                        Qt.AlignBottom | Qt.AlignCenter, Qt.black)

class RoleSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Role Selection")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Password field
        self.password_label = QLabel("Enter admin password:", self)
        self.password_input = LineEdit(self)
        self.password_input.setEchoMode(LineEdit.Password)
        self.password_input.setPlaceholderText("Required for Admin roles")
        
        # Buttons
        button_box = QHBoxLayout()
        self.ok_button = PrimaryPushButton("Confirm")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = PushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)
        
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addLayout(button_box)
        
    def validate_and_accept(self):
        password = self.password_input.text()
        if password == "113742M$@&":
            self.accept()
        else:
            InfoBar.error(
                title='Error',
                content='Invalid admin password',
                parent=self
            )

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        # Username field
        self.username_input = LineEdit(self)
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumWidth(300)
        layout.addRow("Username:", self.username_input)

        # Name field
        self.name_input = LineEdit(self)
        self.name_input.setPlaceholderText("Name")
        self.name_input.setMinimumWidth(300)
        layout.addRow("Name:", self.name_input)

        # Email field
        self.email_input = LineEdit(self)
        self.email_input.setPlaceholderText("Email")
        self.email_input.hide()
        self.email_label = QLabel("Email (optional):", self)
        self.email_label.hide()
        layout.addRow(self.email_label, self.email_input)

        # Password field
        self.password_container = QWidget(self)
        password_layout = QHBoxLayout(self.password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        
        self.password_input = LineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.show_password_btn = TransparentToolButton(self)
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        eye_icon_path = os.path.join(resources_dir, 'eye.png')
        self.eye_icon = QIcon(eye_icon_path) if os.path.exists(eye_icon_path) else FluentIcon.VIEW
        self.show_password_btn.setIcon(self.eye_icon)
        self.show_password_btn.setFixedSize(24, 24)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.show_password_btn)
        
        self.form_layout.addRow("Password:", self.password_container)
        
        # Bio
        self.bio_edit = TextEdit(self)
        self.bio_edit.setPlaceholderText("Tell us about yourself")
        self.bio_edit.setMaximumHeight(100)
        self.bio_edit.hide()
        self.bio_label = QLabel("Bio (optional):", self)
        self.bio_label.hide()
        self.form_layout.addRow(self.bio_label, self.bio_edit)
        
        # Profile Picture
        self.picture_layout = QHBoxLayout()
        self.picture_path = LineEdit(self)
        self.picture_path.setPlaceholderText("Select a profile picture")
        self.picture_path.setReadOnly(True)
        self.browse_button = PushButton("Browse")
        self.browse_button.clicked.connect(self.browse_picture)
        self.picture_layout.addWidget(self.picture_path)
        self.picture_layout.addWidget(self.browse_button)
        self.picture_container = QWidget()
        self.picture_container.setLayout(self.picture_layout)
        self.picture_container.hide()
        self.picture_label = QLabel("Profile Picture (optional):", self)
        self.picture_label.hide()
        self.form_layout.addRow(self.picture_label, self.picture_container)
        
        # Password requirements
        self.password_req_label = QLabel("""
Password Requirements:
• At least 8 characters long
• At least one uppercase letter
• At least one lowercase letter
• At least one number
• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
        """)
        self.password_req_label.setStyleSheet("color: #666; font-size: 10pt;")
        self.password_req_label.hide()
        self.form_layout.addRow("", self.password_req_label)
        
        # Role selection with button
        role_layout = QHBoxLayout()
        self.role_combo = QComboBox(self)
        self.role_combo.setFixedHeight(32)
        self.role_combo.setMinimumWidth(200)
        self.role_combo.addItems(["Basic User", "Social Media Handler", "Medium Admin", "Admin"])
        self.role_combo.setCurrentIndex(0)  # Default to Basic User
        self.role_combo.currentIndexChanged.connect(self.handle_role_change)
        
        role_layout.addWidget(self.role_combo)
        layout.addRow("Role:", role_layout)

        # Buttons
        button_box = QHBoxLayout()
        self.register_button = PrimaryPushButton("Register")
        self.register_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = PushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_box.addWidget(self.register_button)
        button_box.addWidget(self.cancel_button)
        layout.addRow("", button_box)

    def handle_role_change(self, index):
        """Handle role selection change"""
        # Check if selected role requires admin password
        if index in [2, 3]:  # Medium Admin or Admin
            dialog = RoleSelectionDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                # If password validation failed, revert to Basic User
                self.role_combo.setCurrentIndex(0)

    def browse_picture(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "",
            "Image Files (*.png *.jpg *.jpeg *.gif);;All Files (*)"
        )
        if file_name:
            self.picture_path.setText(file_name)

    def validate_and_accept(self):
        username = self.username_input.text().strip()
        name = self.name_input.text().strip()
        password = self.password_input.text()
        email = self.email_input.text().strip()
        bio = self.bio_edit.toPlainText().strip()
        role_id = 4 - self.role_combo.currentIndex()  # Convert combo index to role_id

        if not username or not password or not name:
            MessageBox(
                "Error",
                "Username, password, and name are required",
                self
            ).exec_()
            return

        if email and '@' not in email:
            MessageBox(
                "Error",
                "Invalid email format",
                self
            ).exec_()
            return

        # Password validation
        if len(password) < 8:
            MessageBox(
                "Error",
                "Password must be at least 8 characters long",
                self
            ).exec_()
            return

        if not any(c.isupper() for c in password):
            MessageBox(
                "Error",
                "Password must contain at least one uppercase letter",
                self
            ).exec_()
            return

        if not any(c.islower() for c in password):
            MessageBox(
                "Error",
                "Password must contain at least one lowercase letter",
                self
            ).exec_()
            return

        if not any(c.isdigit() for c in password):
            MessageBox(
                "Error",
                "Password must contain at least one number",
                self
            ).exec_()
            return

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            MessageBox(
                "Error",
                "Password must contain at least one special character",
                self
            ).exec_()
            return

        self.registration_data = {
            'username': username,
            'name': name,
            'password': password,
            'role_id': role_id,
            'email': email,
            'bio': bio,
            'profile_picture': self.picture_path.text()
        }
        self.accept()

class LoginWindow(QWidget):
    loginSuccessful = pyqtSignal(str, str)
    def __init__(self):
        super().__init__()
        self.login_client = LoginClient()
        self.is_login_mode = True
        
        # Set window properties
        self.setWindowTitle("Login")
        self.setFixedSize(500, 600)  # Increased size for better visibility
        
        # Set window icon
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        profile_icon_path = os.path.join(resources_dir, 'profile.png')
        if os.path.exists(profile_icon_path):
            self.setWindowIcon(QIcon(profile_icon_path))
        
        # Initialize email handler
        from email_handler.email_handler import EmailHandler
        self.email_handler = EmailHandler()
        
        self.setup_ui()
        
        # Connect initial button handler
        self.login_button.clicked.connect(self.handle_login)

    def setup_ui(self):
        """Setup the login window UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Add margins
        main_layout.setSpacing(15)  # Increase spacing between widgets
        
        # Title
        title_label = SubtitleLabel("AI Agency Login", self)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Add some spacing
        main_layout.addSpacing(10)
        
        # Form layout for input fields
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self.form_layout.setSpacing(10)  # Increase spacing between form rows
        
        # Username
        self.username_edit = LineEdit(self)
        self.username_edit.setPlaceholderText("Username")
        self.username_edit.setMinimumWidth(300)
        self.form_layout.addRow("Username:", self.username_edit)
        
        # Name
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("Name")
        self.name_edit.setMinimumWidth(300)
        self.name_edit.hide()
        self.name_label = QLabel("Name:", self)
        self.name_label.hide()
        self.form_layout.addRow(self.name_label, self.name_edit)
        
        # Email
        self.email_edit = LineEdit(self)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.hide()
        self.email_label = QLabel("Email (optional):", self)
        self.email_label.hide()
        self.form_layout.addRow(self.email_label, self.email_edit)
        
        # Password
        self.password_container = QWidget(self)
        password_layout = QHBoxLayout(self.password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        
        self.password_edit = LineEdit(self)
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        self.show_password_btn = TransparentToolButton(self)
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        eye_icon_path = os.path.join(resources_dir, 'eye.png')
        self.eye_icon = QIcon(eye_icon_path) if os.path.exists(eye_icon_path) else FluentIcon.VIEW
        self.show_password_btn.setIcon(self.eye_icon)
        self.show_password_btn.setFixedSize(24, 24)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(self.show_password_btn)
        
        self.form_layout.addRow("Password:", self.password_container)
        
        # Bio
        self.bio_edit = TextEdit(self)
        self.bio_edit.setPlaceholderText("Tell us about yourself")
        self.bio_edit.setMaximumHeight(100)
        self.bio_edit.hide()
        self.bio_label = QLabel("Bio (optional):", self)
        self.bio_label.hide()
        self.form_layout.addRow(self.bio_label, self.bio_edit)
        
        # Profile Picture
        self.picture_layout = QHBoxLayout()
        self.picture_path = LineEdit(self)
        self.picture_path.setPlaceholderText("Select a profile picture")
        self.picture_path.setReadOnly(True)
        self.browse_button = PushButton("Browse")
        self.browse_button.clicked.connect(self.browse_picture)
        self.picture_layout.addWidget(self.picture_path)
        self.picture_layout.addWidget(self.browse_button)
        self.picture_container = QWidget()
        self.picture_container.setLayout(self.picture_layout)
        self.picture_container.hide()
        self.picture_label = QLabel("Profile Picture (optional):", self)
        self.picture_label.hide()
        self.form_layout.addRow(self.picture_label, self.picture_container)
        
        # Password requirements
        self.password_req_label = QLabel("""
Password Requirements:
• At least 8 characters long
• At least one uppercase letter
• At least one lowercase letter
• At least one number
• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
        """)
        self.password_req_label.setStyleSheet("color: #666; font-size: 10pt;")
        self.password_req_label.hide()
        self.form_layout.addRow("", self.password_req_label)
        
        # Role selection
        self.role_layout = QHBoxLayout()
        self.role_combo = QComboBox(self)
        self.role_combo.setFixedHeight(32)
        self.role_combo.setMinimumWidth(200)
        self.role_combo.addItems(["Basic User", "Social Media Handler", "Medium Admin", "Admin"])
        self.role_combo.setCurrentIndex(0)  # Default to Basic User
        self.role_combo.currentIndexChanged.connect(self.handle_role_change)
        self.role_layout.addWidget(self.role_combo)
        self.role_combo.hide()
        self.role_label = QLabel("Role:", self)
        self.role_label.hide()
        self.form_layout.addRow(self.role_label, self.role_combo)
        
        main_layout.addWidget(form_widget)
        
        # Error label
        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.error_label)
        
        # Add some spacing
        main_layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Increase spacing between buttons
        
        self.login_button = PrimaryPushButton("Login")
        self.login_button.setMinimumWidth(120)
        
        self.register_toggle = PushButton("Switch to Register")
        self.register_toggle.clicked.connect(self.switch_mode)
        self.register_toggle.setMinimumWidth(120)
        
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_toggle)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        # Create caps lock warning
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        warning_icon_path = os.path.join(resources_dir, 'warning.png')
        self.caps_warning = QLabel(self)
        self.caps_warning.setPixmap(QIcon(warning_icon_path).pixmap(16, 16))
        self.caps_warning.setStyleSheet("""
            QLabel {
                color: #FF9800;
                padding: 5px;
                border: 1px solid #FF9800;
                border-radius: 4px;
                background: #FFF3E0;
            }
        """)
        self.caps_warning.setText("  Caps Lock is ON")
        self.caps_warning.hide()
        
        # Install event filter for caps lock detection
        self.password_edit.installEventFilter(self)
        
        # Add forgot password button
        self.forgot_password_button = TransparentPushButton("Forgot Password?", self)
        self.forgot_password_button.clicked.connect(self.handle_forgot_password)
        main_layout.addWidget(self.forgot_password_button)
    
    def toggle_password_visibility(self):
        """Toggle password field between visible and hidden"""
        if self.password_edit.echoMode() == QLineEdit.Password:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
    
    def eventFilter(self, obj, event):
        """Handle key events for caps lock detection"""
        if obj == self.password_edit:
            if event.type() == QEvent.KeyPress:
                # Check if the key is a letter
                key = event.key()
                if Qt.Key_A <= key <= Qt.Key_Z:
                    # Get the actual text that would be inserted
                    text = event.text()
                    # Get keyboard state
                    keyboard = QApplication.keyboardModifiers()
                    shift_pressed = bool(keyboard & Qt.ShiftModifier)
                    
                    # If shift is not pressed but we get uppercase, or
                    # if shift is pressed but we get lowercase, Caps Lock is on
                    caps_on = (not shift_pressed and text.isupper()) or (shift_pressed and text.islower())
                    
                    # Show or hide the warning
                    self.caps_warning.setVisible(caps_on)
            
            elif event.type() == QEvent.FocusOut:
                # Hide warning when field loses focus
                self.caps_warning.hide()
        
        return super().eventFilter(obj, event)
    
    def show_error(self, message: str):
        """Show error message"""
        self.error_label.setText(message)

    def browse_picture(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "",
            "Image Files (*.png *.jpg *.jpeg *.gif);;All Files (*)"
        )
        if file_name:
            self.picture_path.setText(file_name)

    def switch_mode(self):
        """Switch between login and register modes"""
        if self.is_login_mode:
            # Switching to register mode
            self.is_login_mode = False
            self.login_button.setText("Register")
            self.login_button.clicked.disconnect()  # Disconnect old handler
            self.login_button.clicked.connect(self.handle_register)  # Connect new handler
            self.register_toggle.setText("Switch to Login")
            self.email_edit.show()
            self.email_label.show()
            self.bio_edit.show()
            self.bio_label.show()
            self.picture_container.show()
            self.picture_label.show()
            self.password_req_label.show()
            self.role_combo.show()  # Show role selection
            self.role_label.show()  # Show role label
            self.name_edit.show()
            self.name_label.show()
            self.email_edit.setPlaceholderText("Email (optional)")
            self.bio_edit.setPlaceholderText("Tell us about yourself (optional)")
        else:
            # Switching to login mode
            self.is_login_mode = True
            self.login_button.setText("Login")
            self.login_button.clicked.disconnect()  # Disconnect old handler
            self.login_button.clicked.connect(self.handle_login)  # Connect new handler
            self.register_toggle.setText("Switch to Register")
            self.email_edit.hide()
            self.email_label.hide()
            self.bio_edit.hide()
            self.bio_label.hide()
            self.picture_container.hide()
            self.picture_label.hide()
            self.password_req_label.hide()
            self.role_combo.hide()  # Hide role selection
            self.role_label.hide()  # Hide role label
            self.name_edit.hide()
            self.name_label.hide()
        # Clear all fields
        self.username_edit.clear()
        self.password_edit.clear()
        self.email_edit.clear()
        self.bio_edit.clear()
        self.picture_path.clear()
        self.name_edit.clear()

    def validate_input(self, username: str, password: str, email: str = None) -> bool:
        """Validate user input and show appropriate error messages"""
        if not username:
            self.show_error('Username is required')
            return False
            
        if len(username) < 3:
            self.show_error('Username must be at least 3 characters long')
            return False
            
        if not password:
            self.show_error('Password is required')
            return False
            
        if len(password) < 6:
            self.show_error('Password must be at least 6 characters long')
            return False
            
        if not self.is_login_mode and email:
            # Simple email validation
            if '@' not in email or '.' not in email:
                self.show_error('Please enter a valid email address')
                return False
                
        return True
        
    def handle_login(self):
        """Handle login button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            self.show_error('Username and password are required')
            return
            
        success, message = self.login_client.login(username, password)
        
        if success:
            self.show_error('Login successful!')
            self.loginSuccessful.emit(username, password)
            self.close()
        else:
            self.show_error(message)
            
    def handle_register(self):
        """Handle register button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        bio = self.bio_edit.toPlainText().strip()
        profile_picture = self.picture_path.text().strip()
        role_id = 4 - self.role_combo.currentIndex()  # Convert combo index to role_id
        
        # Validate input
        if not username or not password or not name:
            self.show_error('Username, password, and name are required')
            return
            
        # Validate email format if provided
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.show_error('Invalid email format')
            return
            
        # Password validation
        if len(password) < 8:
            self.show_error('Password must be at least 8 characters long')
            return
            
        if not any(c.isupper() for c in password):
            self.show_error('Password must contain at least one uppercase letter')
            return
            
        if not any(c.islower() for c in password):
            self.show_error('Password must contain at least one lowercase letter')
            return
            
        if not any(c.isdigit() for c in password):
            self.show_error('Password must contain at least one number')
            return
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            self.show_error('Password must contain at least one special character')
            return
            
        try:
            # Only send non-empty values
            data = {
                'username': username,
                'name': name,
                'password': password,
                'role_id': role_id
            }
            if email:
                data['email'] = email
            if bio:
                data['bio'] = bio
            if profile_picture:
                data['profile_picture'] = profile_picture
                
            response, status_code = self.login_client.register(**data)
            
            if status_code == 201:
                self.show_error('Registration successful! You can now log in.')
                # Switch back to login mode
                self.is_login_mode = True
                self.switch_mode()
                # Pre-fill username for convenience
                self.username_edit.setText(username)
            else:
                error_msg = response.get('error', 'Registration failed')
                self.show_error(error_msg)
        except Exception as e:
            self.show_error(f'Failed to register: {str(e)}')

    def handle_forgot_password(self):
        """Handle forgot password request"""
        # Create a dialog for email input
        dialog = QDialog(self)
        dialog.setWindowTitle("Password Recovery")
        dialog.setFixedWidth(300)
        
        layout = QVBoxLayout()
        
        # Email input
        email_label = QLabel("Enter your email:")
        email_input = LineEdit()
        email_input.setPlaceholderText("your.email@example.com")
        
        # Username input
        username_label = QLabel("Enter your username:")
        username_input = LineEdit()
        username_input.setPlaceholderText("username")
        
        # Submit button
        submit_button = PrimaryPushButton("Send Recovery Email")
        
        def handle_submit():
            email = email_input.text().strip()
            username = username_input.text().strip()
            
            if not email or not username:
                self.show_error("Please enter both email and username")
                return
            
            # Verify email exists and matches username using email handler
            if not self.email_handler.verify_email_exists(email, username):
                self.show_error("Email does not match username in our records")
                return
            
            # Get user credentials from server
            response, status_code = self.login_client._make_request('POST', '/get-credentials',
                                                                json={"username": username, "email": email})
            
            if status_code != 200:
                self.show_error("Failed to retrieve account credentials. Please try again later.")
                return
                
            password = response.get('password')
            if not password:
                self.show_error("Failed to retrieve account credentials. Please try again later.")
                return
            
            # Send recovery email with credentials
            if self.email_handler.send_password_recovery_email(email, username, password):
                dialog.accept()  # Close the dialog first
                MessageBox(
                    "Success",
                    "A temporary password has been sent to your email.\n\n"
                    "Please check your inbox and use it to log in.\n\n"
                    "For security reasons, we recommend changing your password after logging in.",
                    self
                ).exec()
            else:
                dialog.accept()  # Close the dialog first
                self.show_error("Failed to send recovery email. Please try again later.")
        
        submit_button.clicked.connect(handle_submit)
        
        # Add widgets to layout
        layout.addWidget(email_label)
        layout.addWidget(email_input)
        layout.addWidget(username_label)
        layout.addWidget(username_input)
        layout.addWidget(submit_button)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def handle_role_change(self, index):
        """Handle role selection change"""
        # Check if selected role requires admin password
        if index in [2, 3]:  # Medium Admin or Admin
            dialog = RoleSelectionDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                # If password validation failed, revert to Basic User
                self.role_combo.setCurrentIndex(0)

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agency")
        
        # Set custom application icon
        app_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'ai.png')
        self.setWindowIcon(QIcon(app_icon_path))
        self.resize(1000, 750)
        
        self.login_window = None
        self.login_client = LoginClient()  # Create a single LoginClient instance
        
        # Create sub interfaces
        self.tools_interface = ScrollableToolsInterface(self)
        self.analytics_interface = ScrollableAnalyticsInterface(self)
        self.generation_interface = ScrollableGenerationInterface(self)
        self.settings_interface = SettingInterface(self)
        self.profile_interface = ProfileInterface(self)
        self.users_interface = ListingUsersInterface(self)
        
        # Assign unique object names
        self.tools_interface.setObjectName("toolsInterface")
        self.analytics_interface.setObjectName("analyticsInterface")
        self.generation_interface.setObjectName("generationInterface")
        self.settings_interface.setObjectName("settingsInterface")
        self.profile_interface.setObjectName("profileInterface")
        self.users_interface.setObjectName("usersInterface")
        
        # Pass login client to interfaces that need it
        self.profile_interface.login_client = self.login_client
        self.users_interface.login_client = self.login_client
        
        # Set up navigation
        self.setup_window()
        
    def setup_window(self):
        """Set up window navigation"""
        # Get icon paths
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        tools_icon_path = os.path.join(resources_dir, 'tools.png')
        analytics_icon_path = os.path.join(resources_dir, 'analytics.png')
        generation_icon_path = os.path.join(resources_dir, 'ai.png')  # Using AI icon for generation
        settings_icon_path = os.path.join(resources_dir, 'settings.png')
        profile_icon_path = os.path.join(resources_dir, 'profile.png')
        
        # Add navigation items
        self.addSubInterface(
            self.tools_interface,
            QIcon(tools_icon_path),
            "Tools",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.analytics_interface,
            QIcon(analytics_icon_path),
            "Analytics",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.generation_interface,
            QIcon(generation_icon_path),
            "Generation",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.users_interface,
            QIcon(profile_icon_path),  # Using profile icon for users list
            "Users",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.profile_interface,
            QIcon(profile_icon_path),
            "Profile",
            NavigationItemPosition.BOTTOM
        )
        
        self.addSubInterface(
            self.settings_interface,
            QIcon(settings_icon_path),
            "Settings",
            NavigationItemPosition.BOTTOM
        )
        
        # Set theme
        setTheme(Theme.AUTO)
        
    def show_login(self):
        """Show login window and hide main window"""
        self.hide()  # Hide main window
        self.login_window = LoginWindow()
        self.login_window.login_client = self.login_client
        self.login_window.loginSuccessful.connect(self.on_login_successful)
        self.login_window.show()
        
    def on_login_successful(self, username, password):
        """Handle successful login"""
        try:
            # Show loading splash
            loading_splash = LoadingSplashScreen()
            loading_splash.showLoading()
            QApplication.processEvents()
            
            # Don't recreate the interfaces, just update them
            self.resize(1000, 650)
            self.setWindowTitle('AI Analytics')
            
            # Close login window
            if self.login_window:
                self.login_window.close()
                self.login_window = None
            
            # Set up profile interface with user credentials
            self.profile_interface.login_client = self.login_client
            self.profile_interface.set_username(username)
            
            # Show main window and close splash
            self.show()
            loading_splash.finish(self)
            
        except Exception as e:
            logger.error(f"Error setting up main window: {str(e)}")
            MessageBox(
                'Error',
                'Failed to initialize main window',
                self
            ).exec()
        
def init_app():
    """Initialize and run the application"""
    try:
        # Enable High DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        
        # Set high DPI scaling
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
        
        # Create application with high DPI support
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Show initial splash screen
        splash = CustomSplashScreen()
        splash.show()
        app.processEvents()
        
        # Create main window
        w = MainWindow()
        w.show_login()
        
        # Set theme
        setTheme(Theme.LIGHT)
        setThemeColor('#0066FF')
        
        # Finish initial splash screen
        splash.finish(w)
        
        # Run application
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    init_app()