from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
from qfluentwidgets import ScrollArea, InfoBar, PrimaryPushButton, TransparentPushButton
from login_server.login_client import LoginClient
import json

class ListingUsersInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.login_client = None
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        """Set up the user interface"""
        self.container = QWidget()
        self.vbox_layout = QVBoxLayout(self.container)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Username', 'Name', 'Email', 'Role', 'Created At', 'Actions'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.vbox_layout.addWidget(self.table)
        self.setWidget(self.container)
        self.setWidgetResizable(True)

    def load_users(self):
        """Load users from the server"""
        if not self.login_client:
            return
            
        try:
            response = self.login_client.get_users()
            if response.status_code == 200:
                users = response.json()
                self.populate_table(users)
            elif response.status_code == 403:
                self.show_no_permission()
            else:
                self.show_error("Failed to load users")
        except Exception as e:
            self.show_error(f"Error loading users: {str(e)}")

    def populate_table(self, users):
        """Populate the table with user data"""
        self.table.setRowCount(len(users))
        
        # Get user permissions
        token = self.login_client.token
        try:
            payload = json.loads(self.login_client.decode_token(token))
            role_id = payload.get('role_id')
            response = self.login_client.get_role_permissions(role_id)
            permissions = response.json() if response.status_code == 200 else {}
            can_manage = permissions.get('all', False) or permissions.get('manage_users', False)
        except:
            can_manage = False

        for row, user in enumerate(users):
            # Add user data
            self.table.setItem(row, 0, QTableWidgetItem(user.get('username', '')))
            self.table.setItem(row, 1, QTableWidgetItem(user.get('name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
            self.table.setItem(row, 3, QTableWidgetItem(user.get('role_name', '')))
            self.table.setItem(row, 4, QTableWidgetItem(user.get('created_at', '')))
            
            if can_manage:
                # Create action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = TransparentPushButton('Edit')
                delete_btn = TransparentPushButton('Delete')
                
                edit_btn.clicked.connect(lambda checked, u=user: self.edit_user(u))
                delete_btn.clicked.connect(lambda checked, u=user: self.delete_user(u))
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                action_layout.addStretch()
                
                self.table.setCellWidget(row, 5, action_widget)

    def show_no_permission(self):
        """Show no permission message"""
        self.table.setRowCount(0)
        InfoBar.error(
            title='Access Denied',
            content="You don't have permission to view users",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def show_error(self, message):
        """Show error message"""
        InfoBar.error(
            title='Error',
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def edit_user(self, user):
        """Edit user dialog"""
        # TODO: Implement edit user dialog
        QMessageBox.information(self, "Edit User", f"Edit user {user['username']}")

    def delete_user(self, user):
        """Delete user confirmation"""
        reply = QMessageBox.question(
            self, 
            'Delete User',
            f"Are you sure you want to delete user {user['username']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                response = self.login_client.delete_user(user['username'])
                if response.status_code == 200:
                    InfoBar.success(
                        title='Success',
                        content=f"User {user['username']} deleted successfully",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    self.load_users()  # Reload the table
                else:
                    self.show_error(f"Failed to delete user: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                self.show_error(f"Error deleting user: {str(e)}")
