import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QFormLayout, QDialog, QLineEdit, QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from qfluentwidgets import (FluentIcon, PushButton, LineEdit, ScrollArea,
                          TitleLabel, CaptionLabel, CardWidget, IconWidget,
                          FlowLayout, BodyLabel, PrimaryPushButton, TransparentPushButton,
                          InfoBar)

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Password Requirements Label
        requirements = """
        Password Requirements:
        • At least 8 characters long
        • At least one uppercase letter
        • At least one lowercase letter
        • At least one number
        • At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
        """
        req_label = QLabel(requirements, self)
        req_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(req_label)
        
        # Old Password
        self.old_password = LineEdit(self)
        self.old_password.setEchoMode(QLineEdit.Password)
        self.old_password.setPlaceholderText("Current Password")
        layout.addWidget(self.old_password)
        
        # New Password
        self.new_password = LineEdit(self)
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("New Password")
        layout.addWidget(self.new_password)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = PrimaryPushButton("Change", self)
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = PushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def validate_and_accept(self):
        """Validate password before accepting"""
        new_password = self.new_password.text()
        
        # Check length
        if len(new_password) < 8:
            InfoBar.error(
                title='Invalid Password',
                content='Password must be at least 8 characters long',
                parent=self
            )
            return
            
        # Check uppercase
        if not any(c.isupper() for c in new_password):
            InfoBar.error(
                title='Invalid Password',
                content='Password must contain at least one uppercase letter',
                parent=self
            )
            return
            
        # Check lowercase
        if not any(c.islower() for c in new_password):
            InfoBar.error(
                title='Invalid Password',
                content='Password must contain at least one lowercase letter',
                parent=self
            )
            return
            
        # Check numbers
        if not any(c.isdigit() for c in new_password):
            InfoBar.error(
                title='Invalid Password',
                content='Password must contain at least one number',
                parent=self
            )
            return
            
        # Check special characters
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password):
            InfoBar.error(
                title='Invalid Password',
                content='Password must contain at least one special character',
                parent=self
            )
            return
            
        self.accept()

class ChangeUsernameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Username")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # New Username
        self.new_username = LineEdit(self)
        self.new_username.setPlaceholderText("New Username")
        layout.addWidget(self.new_username)
        
        # Password for verification
        self.password = LineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Current Password")
        layout.addWidget(self.password)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = PrimaryPushButton("Change", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = PushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

class ChangeEmailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Email")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Email field
        self.email_edit = LineEdit(self)
        self.email_edit.setPlaceholderText("New Email")
        layout.addWidget(self.email_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = PrimaryPushButton("Change", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = PushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

class ChangeBioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Bio")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Bio field
        self.bio_edit = LineEdit(self)
        self.bio_edit.setPlaceholderText("Tell us about yourself")
        layout.addWidget(self.bio_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = PrimaryPushButton("Change", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = PushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

class ProfileInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.default_profile_pic = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'profile.png')
        self.login_client = None
        self.setup_ui()
        
    def setup_ui(self):
        self.profile_widget = QWidget(self)
        self.setWidget(self.profile_widget)
        self.setWidgetResizable(True)
        
        layout = QVBoxLayout(self.profile_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 30, 50, 30)
        
        # Profile Card
        self.profile_card = CardWidget(self.profile_widget)
        card_layout = QVBoxLayout(self.profile_card)
        
        # Profile Picture Section
        pic_layout = QHBoxLayout()
        
        # Profile Picture
        self.profile_pic = QLabel(self.profile_card)
        self.profile_pic.setFixedSize(100, 100)
        self.profile_pic.setScaledContents(True)
        default_pixmap = QPixmap(self.default_profile_pic)
        if not default_pixmap.isNull():
            self.profile_pic.setPixmap(default_pixmap)
        pic_layout.addWidget(self.profile_pic)
        
        # Picture Buttons Layout
        pic_buttons = QVBoxLayout()
        
        # Change Picture Button
        self.change_pic_btn = PushButton('Change Picture', self.profile_card)
        self.change_pic_btn.clicked.connect(self.change_profile_picture)
        pic_buttons.addWidget(self.change_pic_btn)
        
        # Remove Picture Button
        self.remove_pic_btn = PushButton('Remove Picture', self.profile_card)
        self.remove_pic_btn.clicked.connect(self.remove_profile_picture)
        pic_buttons.addWidget(self.remove_pic_btn)
        
        pic_layout.addLayout(pic_buttons)
        pic_layout.addStretch()
        
        card_layout.addLayout(pic_layout)
        
        # Form Layout for user details
        form_layout = QFormLayout()
        
        # Username
        self.username_edit = LineEdit(self.profile_card)
        self.username_edit.setPlaceholderText('Enter your username')
        self.change_username_btn = TransparentPushButton('Change', self.profile_card)
        self.change_username_btn.clicked.connect(self.change_username)
        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_edit)
        username_layout.addWidget(self.change_username_btn)
        username_layout.addStretch()
        form_layout.addRow('Username:', username_layout)
        
        # Role
        self.role_label = QLabel("Unknown")
        form_layout.addRow('Role:', self.role_label)
        
        # Permissions
        self.permissions_list = QTextEdit(self.profile_card)
        self.permissions_list.setReadOnly(True)
        self.permissions_list.setMaximumHeight(100)
        self.permissions_list.setPlaceholderText("No permissions available")
        form_layout.addRow('Permissions:', self.permissions_list)
        
        # Email
        self.email_edit = LineEdit(self.profile_card)
        self.email_edit.setPlaceholderText('Enter your email')
        self.change_email_btn = TransparentPushButton('Change', self.profile_card)
        self.change_email_btn.clicked.connect(self.change_email)
        email_layout = QHBoxLayout()
        email_layout.addWidget(self.email_edit)
        email_layout.addWidget(self.change_email_btn)
        email_layout.addStretch()
        form_layout.addRow('Email:', email_layout)
        
        # Bio
        self.bio_edit = LineEdit(self.profile_card)
        self.bio_edit.setPlaceholderText('Tell us about yourself')
        self.change_bio_btn = TransparentPushButton('Change', self.profile_card)
        self.change_bio_btn.clicked.connect(self.change_bio)
        bio_layout = QHBoxLayout()
        bio_layout.addWidget(self.bio_edit)
        bio_layout.addWidget(self.change_bio_btn)
        bio_layout.addStretch()
        form_layout.addRow('Bio:', bio_layout)
        
        card_layout.addLayout(form_layout)
        
        # Buttons Layout
        buttons_layout = QHBoxLayout()
        
        # Change Password Button
        self.change_password_btn = PushButton('Change Password', self.profile_card)
        self.change_password_btn.clicked.connect(self.change_password)
        buttons_layout.addWidget(self.change_password_btn)
        
        # Logout Button
        self.logout_btn = TransparentPushButton('Logout', self.profile_card)
        self.logout_btn.clicked.connect(self.logout)
        buttons_layout.addWidget(self.logout_btn)
        
        card_layout.addLayout(buttons_layout)
        
        layout.addWidget(self.profile_card)
        layout.addStretch()

    def update_field(self, field: str, value: str):
        """Update a single field in the profile"""
        if not self.login_client:
            return
            
        try:
            profile_data = {field: value}
            response, status_code = self.login_client.update_user_profile(profile_data)
            
            if status_code != 200:
                error_msg = response.get('error', f'Failed to update {field}')
                InfoBar.error(
                    title='Error',
                    content=error_msg,
                    parent=self
                )
                # Revert the field to its previous value
                self.load_profile()
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to update {field}: {str(e)}',
                parent=self
            )
            # Revert the field to its previous value
            self.load_profile()

    def load_profile(self):
        """Load profile data from server"""
        if not self.login_client:
            return
            
        try:
            response, status_code = self.login_client.get_user_profile()
            
            if status_code == 200:
                # Response data is directly the user data
                self.username_edit.setText(response.get('username', ''))
                self.email_edit.setText(response.get('email', ''))
                self.bio_edit.setText(response.get('bio', ''))
                
                # Update role and permissions
                role_names = {
                    1: 'Admin',
                    2: 'Medium Admin',
                    3: 'Social Media Handler',
                    4: 'Basic User'
                }
                role_id = self.login_client.role_id
                self.role_label.setText(role_names.get(role_id, 'Unknown'))
                
                # Format permissions
                if self.login_client.permissions:
                    permissions_text = "Your permissions:\n"
                    for perm, enabled in self.login_client.permissions.items():
                        if enabled:
                            permissions_text += f"✓ {perm.replace('_', ' ').title()}\n"
                    self.permissions_list.setText(permissions_text)
                else:
                    self.permissions_list.setText("No permissions available")
                
                # Load profile picture if exists
                pic_path = response.get('profile_picture')
                if pic_path and os.path.exists(pic_path):
                    self.set_profile_picture(pic_path)
                else:
                    # Reset to default if no custom picture
                    default_pixmap = QPixmap(self.default_profile_pic)
                    if not default_pixmap.isNull():
                        self.profile_pic.setPixmap(default_pixmap)
                        
                # Show success message
                InfoBar.success(
                    title='Success',
                    content='Profile loaded successfully',
                    parent=self
                )
            else:
                error_msg = response.get('error', 'Failed to load profile data')
                InfoBar.error(
                    title='Error',
                    content=error_msg,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to load profile: {str(e)}',
                parent=self
            )
            
    def save_profile(self):
        """Save profile data to server"""
        if not self.login_client:
            InfoBar.error(
                title='Error',
                content='Not logged in',
                parent=self
            )
            return
            
        try:
            profile_data = {
                'email': self.email_edit.text(),
                'bio': self.bio_edit.text(),
                'profile_picture': getattr(self, '_current_pic_path', None)
            }
            
            response, status_code = self.login_client.update_user_profile(profile_data)
            
            if status_code == 200:
                InfoBar.success(
                    title='Success',
                    content='Profile updated successfully',
                    parent=self
                )
            else:
                error_msg = response.get('error', 'Failed to update profile')
                InfoBar.error(
                    title='Error',
                    content=error_msg,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to save profile: {str(e)}',
                parent=self
            )
            
    def change_password(self):
        """Show change password dialog"""
        dialog = ChangePasswordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            old_password = dialog.old_password.text()
            new_password = dialog.new_password.text()
            
            try:
                import sqlite3
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute("SELECT password FROM users WHERE username=?", (self.login_client.username,))
                user_data = c.fetchone()
                conn.close()
                
                if user_data and user_data[0] == old_password:
                    import sqlite3
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute("UPDATE users SET password=? WHERE username=?", (new_password, self.login_client.username))
                    conn.commit()
                    conn.close()
                    
                    InfoBar.success(
                        title='Success',
                        content='Password changed successfully',
                        parent=self
                    )
                else:
                    error_msg = 'Failed to change password'
                    InfoBar.error(
                        title='Error',
                        content=error_msg,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='Error',
                    content=f'Failed to change password: {str(e)}',
                    parent=self
                )
                
    def change_username(self):
        """Show change username dialog"""
        dialog = ChangeUsernameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_username = dialog.new_username.text()
            password = dialog.password.text()
            
            try:
                import sqlite3
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute("SELECT password FROM users WHERE username=?", (self.login_client.username,))
                user_data = c.fetchone()
                conn.close()
                
                if user_data and user_data[0] == password:
                    import sqlite3
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute("UPDATE users SET username=? WHERE username=?", (new_username, self.login_client.username))
                    conn.commit()
                    conn.close()
                    
                    self.username_edit.setText(new_username)
                    InfoBar.success(
                        title='Success',
                        content='Username changed successfully',
                        parent=self
                    )
                else:
                    error_msg = 'Failed to change username'
                    InfoBar.error(
                        title='Error',
                        content=error_msg,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='Error',
                    content=f'Failed to change username: {str(e)}',
                    parent=self
                )
            
    def change_email(self):
        """Change email with confirmation"""
        if not self.login_client:
            return
            
        new_email = self.email_edit.text()
        if not new_email:
            InfoBar.error(
                title='Error',
                content='Please enter a new email',
                parent=self
            )
            return
            
        try:
            profile_data = {'email': new_email}
            response, status_code = self.login_client.update_user_profile(profile_data)
            
            if status_code == 200:
                InfoBar.success(
                    title='Success',
                    content='Email changed successfully',
                    parent=self
                )
            else:
                error_msg = response.get('error', 'Failed to change email')
                InfoBar.error(
                    title='Error',
                    content=error_msg,
                    parent=self
                )
                # Revert to previous value
                self.load_profile()
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to change email: {str(e)}',
                parent=self
            )
            # Revert to previous value
            self.load_profile()

    def change_bio(self):
        """Change bio with confirmation"""
        if not self.login_client:
            return
            
        new_bio = self.bio_edit.text()
        if not new_bio:
            InfoBar.error(
                title='Error',
                content='Please enter a new bio',
                parent=self
            )
            return
            
        try:
            profile_data = {'bio': new_bio}
            response, status_code = self.login_client.update_user_profile(profile_data)
            
            if status_code == 200:
                InfoBar.success(
                    title='Success',
                    content='Bio changed successfully',
                    parent=self
                )
            else:
                error_msg = response.get('error', 'Failed to change bio')
                InfoBar.error(
                    title='Error',
                    content=error_msg,
                    parent=self
                )
                # Revert to previous value
                self.load_profile()
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to change bio: {str(e)}',
                parent=self
            )
            # Revert to previous value
            self.load_profile()
            
    def change_profile_picture(self):
        """Open file dialog to select new profile picture"""
        if not self.login_client:
            InfoBar.error(
                title='Error',
                content='Not logged in',
                parent=self
            )
            return
            
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_name:
            try:
                # Copy image to data directory
                data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'profile_pics')
                os.makedirs(data_dir, exist_ok=True)
                
                # Generate unique filename using username
                ext = os.path.splitext(file_name)[1]
                new_path = os.path.join(data_dir, f'{self.login_client.username}_profile{ext}')
                
                # Copy file
                import shutil
                shutil.copy2(file_name, new_path)
                
                # Set new profile picture
                self.set_profile_picture(new_path)
                
                # Update profile on server with new picture
                self.save_profile()
                
            except Exception as e:
                InfoBar.error(
                    title='Error',
                    content=f'Failed to update profile picture: {str(e)}',
                    parent=self
                )
                
    def set_profile_picture(self, picture_path):
        """Set profile picture from path"""
        try:
            pixmap = QPixmap(picture_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    100, 100,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.profile_pic.setPixmap(scaled_pixmap)
                self._current_pic_path = picture_path
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to set profile picture: {str(e)}',
                parent=self
            )
            
    def remove_profile_picture(self):
        """Remove current profile picture and reset to default"""
        try:
            default_pixmap = QPixmap(self.default_profile_pic)
            if not default_pixmap.isNull():
                self.profile_pic.setPixmap(default_pixmap)
            self._current_pic_path = None
            
            # Update server
            if self.login_client:
                profile_data = {'profile_picture': None}
                response, status_code = self.login_client.update_user_profile(profile_data)
                
                if status_code == 200:
                    InfoBar.success(
                        title='Success',
                        content='Profile picture removed',
                        parent=self
                    )
                else:
                    error_msg = response.get('error', 'Failed to remove profile picture')
                    InfoBar.error(
                        title='Error',
                        content=error_msg,
                        parent=self
                    )
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to remove profile picture: {str(e)}',
                parent=self
            )
            
    def logout(self):
        """Handle logout button click"""
        if not self.login_client:
            return
            
        try:
            if self.parent:
                self.parent.show_login()  # Show login window
            InfoBar.success(
                title='Success',
                content='Logged out successfully',
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to logout: {str(e)}',
                parent=self
            )
            
    def set_username(self, username):
        """Set the username and load profile data"""
        if not username:
            return
            
        self.username_edit.setText(username)
        
        # Load profile data if we have a login client
        if self.login_client:
            self.load_profile()
