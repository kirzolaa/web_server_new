import instaloader
from datetime import datetime
from itertools import dropwhile, takewhile, islice
import pandas as pd
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QLineEdit, QDateEdit, QWidget, QFormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class PostFetchThread(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, username, method, params=None, login_username=None, login_password=None):
        super().__init__()
        self.username = username
        self.method = method
        self.params = params or {}
        self.login_username = login_username
        self.login_password = login_password
        self.loader = instaloader.Instaloader()

    def run(self):
        try:
            # Login if credentials are provided
            if self.login_username and self.login_password:
                try:
                    self.progress_update.emit("Logging in to Instagram...")
                    self.loader.login(self.login_username, self.login_password)
                    self.progress_update.emit("Login successful!")
                    time.sleep(2)  # Wait a bit after login
                except Exception as e:
                    self.error_signal.emit(f"Login failed: {str(e)}")
                    return
            else:
                self.progress_update.emit("Warning: Running without authentication. Rate limits may apply.")
                time.sleep(2)

            profile = instaloader.Profile.from_username(self.loader.context, self.username)
            
            if self.method == "date_range":
                self._get_posts_by_date_range(profile)
            elif self.method == "top_posts":
                self._get_top_posts(profile)
            elif self.method == "recent_posts":
                self._get_recent_posts(profile)
            elif self.method == "all_posts":
                self._get_all_posts(profile)
                
            self.finished.emit()
            
        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}")

    def _get_posts_by_date_range(self, profile):
        since_date = self.params.get('since_date')
        until_date = self.params.get('until_date')
        posts = profile.get_posts()
        
        self.progress_update.emit(f"Fetching posts between {since_date.strftime('%Y-%m-%d')} and {until_date.strftime('%Y-%m-%d')}")
        
        post_data = []
        for post in takewhile(lambda p: p.date > until_date, 
                            dropwhile(lambda p: p.date > since_date, posts)):
            post_info = self._extract_post_info(post)
            post_data.append(post_info)
            self.progress_update.emit(f"Found post from {post.date}")
            time.sleep(2)  # Prevent rate limiting
            
        if post_data:
            df = pd.DataFrame(post_data)
            filename = f"{self.username}_posts_{since_date.strftime('%Y%m%d')}_{until_date.strftime('%Y%m%d')}.xlsx"
            df.to_excel(filename, index=False)
            self.progress_update.emit(f"Saved {len(post_data)} posts to {filename}")

    def _get_top_posts(self, profile):
        percentage = self.params.get('percentage', 10)
        posts = profile.get_posts()
        
        self.progress_update.emit(f"Fetching top {percentage}% of posts")
        
        # Sort posts by engagement (likes + comments)
        posts_sorted = sorted(posts, key=lambda p: p.likes + p.comments, reverse=True)
        top_count = int(profile.mediacount * percentage / 100)
        
        post_data = []
        for post in islice(posts_sorted, top_count):
            post_info = self._extract_post_info(post)
            post_data.append(post_info)
            self.progress_update.emit(f"Found post with {post.likes} likes and {post.comments} comments")
            time.sleep(2)  # Prevent rate limiting
            
        if post_data:
            df = pd.DataFrame(post_data)
            filename = f"{self.username}_top_{percentage}percent_posts.xlsx"
            df.to_excel(filename, index=False)
            self.progress_update.emit(f"Saved {len(post_data)} top posts to {filename}")

    def _get_recent_posts(self, profile):
        count = self.params.get('count', 10)
        posts = profile.get_posts()
        
        self.progress_update.emit(f"Fetching {count} most recent posts")
        
        post_data = []
        for post in islice(posts, count):
            post_info = self._extract_post_info(post)
            post_data.append(post_info)
            self.progress_update.emit(f"Found post from {post.date}")
            time.sleep(2)  # Prevent rate limiting
            
        if post_data:
            df = pd.DataFrame(post_data)
            filename = f"{self.username}_recent_{count}_posts.xlsx"
            df.to_excel(filename, index=False)
            self.progress_update.emit(f"Saved {len(post_data)} recent posts to {filename}")

    def _get_all_posts(self, profile):
        self.progress_update.emit("Fetching all posts")
        
        post_data = []
        for post in profile.get_posts():
            post_info = self._extract_post_info(post)
            post_data.append(post_info)
            self.progress_update.emit(f"Found post from {post.date}")
            time.sleep(2)  # Prevent rate limiting
            
        if post_data:
            df = pd.DataFrame(post_data)
            filename = f"{self.username}_all_posts.xlsx"
            df.to_excel(filename, index=False)
            self.progress_update.emit(f"Saved {len(post_data)} posts to {filename}")

    def _extract_post_info(self, post):
        return {
            'Date': post.date,
            'Caption': post.caption,
            'Likes': post.likes,
            'Comments': post.comments,
            'Is Video': post.is_video,
            'Video Duration': post.video_duration if post.is_video else None,
            'URL': post.url,
            'Location': post.location if post.location else None,
            'Hashtags': ', '.join(post.caption_hashtags) if post.caption else '',
            'Mentions': ', '.join(post.caption_mentions) if post.caption else '',
        }

class PostTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instagram Post Tester")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        form_layout = QFormLayout()
        
        # Login credentials
        self.login_username = QLineEdit()
        form_layout.addRow("Login Username:", self.login_username)
        
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Login Password:", self.login_password)
        
        # Target username input
        self.username_input = QLineEdit()
        form_layout.addRow("Target Username:", self.username_input)
        
        # Method selector
        self.method_selector = QComboBox()
        self.method_selector.addItems([
            "Date Range Posts",
            "Top Posts",
            "Recent Posts",
            "All Posts"
        ])
        self.method_selector.currentTextChanged.connect(self.on_method_changed)
        form_layout.addRow("Method:", self.method_selector)
        
        # Date range inputs
        self.since_date = QDateEdit()
        self.since_date.setCalendarPopup(True)
        self.since_date.setDate(datetime.now().date())
        form_layout.addRow("Since Date:", self.since_date)
        
        self.until_date = QDateEdit()
        self.until_date.setCalendarPopup(True)
        self.until_date.setDate(datetime.now().date())
        form_layout.addRow("Until Date:", self.until_date)
        
        # Top posts percentage
        self.percentage_input = QLineEdit()
        self.percentage_input.setText("10")
        form_layout.addRow("Top Posts %:", self.percentage_input)
        
        # Recent posts count
        self.count_input = QLineEdit()
        self.count_input.setText("10")
        form_layout.addRow("Recent Posts Count:", self.count_input)
        
        layout.addLayout(form_layout)
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_fetch)
        layout.addWidget(self.start_button)
        
        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)
        
        self.on_method_changed(self.method_selector.currentText())

    def on_method_changed(self, method):
        # Show/hide relevant inputs based on selected method
        is_date_range = method == "Date Range Posts"
        is_top_posts = method == "Top Posts"
        is_recent_posts = method == "Recent Posts"
        
        self.since_date.setVisible(is_date_range)
        self.until_date.setVisible(is_date_range)
        self.percentage_input.setVisible(is_top_posts)
        self.count_input.setVisible(is_recent_posts)

    def start_fetch(self):
        username = self.username_input.text().strip()
        if not username:
            self.output_area.append("Please enter a target username")
            return
            
        method = self.method_selector.currentText()
        
        # Get login credentials
        login_username = self.login_username.text().strip()
        login_password = self.login_password.text().strip()
        
        # Prepare parameters based on selected method
        params = {}
        if method == "Date Range Posts":
            params = {
                'since_date': self.since_date.dateTime().toPyDateTime(),
                'until_date': self.until_date.dateTime().toPyDateTime(),
            }
            method_key = "date_range"
        elif method == "Top Posts":
            try:
                percentage = int(self.percentage_input.text())
                params = {'percentage': percentage}
            except ValueError:
                self.output_area.append("Please enter a valid percentage")
                return
            method_key = "top_posts"
        elif method == "Recent Posts":
            try:
                count = int(self.count_input.text())
                params = {'count': count}
            except ValueError:
                self.output_area.append("Please enter a valid count")
                return
            method_key = "recent_posts"
        else:
            method_key = "all_posts"
        
        # Clear output area
        self.output_area.clear()
        
        # Disable inputs during fetch
        self.start_button.setEnabled(False)
        self.username_input.setEnabled(False)
        self.method_selector.setEnabled(False)
        self.login_username.setEnabled(False)
        self.login_password.setEnabled(False)
        
        # Start fetch thread
        self.thread = PostFetchThread(username, method_key, params, login_username, login_password)
        self.thread.progress_update.connect(self.update_output)
        self.thread.error_signal.connect(self.show_error)
        self.thread.finished.connect(self.on_fetch_complete)
        self.thread.start()

    def update_output(self, message):
        self.output_area.append(message)

    def show_error(self, error):
        self.output_area.append(f"\nERROR: {error}")
        self.enable_inputs()

    def on_fetch_complete(self):
        self.output_area.append("\nFetch completed!")
        self.enable_inputs()

    def enable_inputs(self):
        self.start_button.setEnabled(True)
        self.username_input.setEnabled(True)
        self.method_selector.setEnabled(True)
        self.login_username.setEnabled(True)
        self.login_password.setEnabled(True)

if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    window = PostTestWindow()
    window.show()
    sys.exit(app.exec_())
