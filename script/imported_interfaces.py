from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QObject
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QFileDialog, QComboBox, QLineEdit, QDateEdit)
from PyQt5.QtGui import QDesktopServices
from qfluentwidgets import (ScrollArea, CardWidget, TitleLabel, CaptionLabel,
                          PushButton, LineEdit, ComboBox, DateEdit, ProgressBar, PrimaryPushButton, InfoBar)
import pandas as pd
from post_fetcher import InstagramFetcher, PostData
import csv
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import sys
import os
import json
import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QDate, QDateTime
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
from datetime import datetime
from itertools import takewhile, dropwhile, islice
from setting_interface import SettingInterface
from user_data_handler import UserDataHandler
from config_setting import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from post_fetcher import InstagramFetcher, PostData
from typing import List, Dict
import csv
import logging
from login_server.login_client import LoginClient

class GenerationInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("generationInterface")
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = TitleLabel("AI Generation Tools", self)
        title_label.setFixedHeight(28)
        self.layout.addWidget(title_label)

        # Description
        desc_label = CaptionLabel("Generate images and videos using state-of-the-art AI models", self)
        self.layout.addWidget(desc_label)

        # Scroll area for generation tools
        self.scroll = ScrollArea()
        self.scroll.setWidgetResizable(True)
        
        # Container widget for generation tools
        container = QWidget()
        container_layout = QVBoxLayout(container)

        # Add generation tools
        self.add_generation_tool(container_layout, "Tegr.ai", "Advanced AI model deployment and scaling platform")
        self.add_generation_tool(container_layout, "Runway", "AI-powered creative tools for video editing")
        self.add_generation_tool(container_layout, "Ideogram", "AI image generation and artistic style transfer")
        self.add_generation_tool(container_layout, "Grok", "Advanced AI chatbot with real-time knowledge")
        self.add_generation_tool(container_layout, "Eleven Labs", "State-of-the-art AI voice synthesis")

        self.scroll.setWidget(container)
        self.layout.addWidget(self.scroll)

    def add_generation_tool(self, layout, name, description):
        tool_widget = QWidget()
        tool_layout = QVBoxLayout(tool_widget)

        # Tool header
        header_layout = QHBoxLayout()
        tool_name = QLabel(name)
        tool_name.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        header_layout.addWidget(tool_name)
        
        generate_button = QPushButton("Try It")
        generate_button.clicked.connect(lambda: self.open_tool_website(name))
        header_layout.addWidget(generate_button)
        tool_layout.addLayout(header_layout)

        # Tool description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("QLabel { color: gray; }")
        tool_layout.addWidget(desc_label)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("QFrame { background-color: #e0e0e0; }")
        
        layout.addWidget(tool_widget)
        layout.addWidget(separator)

    def open_tool_website(self, tool_name):
        urls = {
            "Tegr.ai": "https://tegr.ai/",
            "Runway": "https://runway.ml/",
            "Ideogram": "https://ideogram.ai/",
            "Grok": "https://grok.x.ai/",
            "Eleven Labs": "https://elevenlabs.io/"
        }
        if tool_name in urls:
            QDesktopServices.openUrl(QUrl(urls[tool_name]))

class ScrollableGenerationInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Instantiate the generation interface
        self.generation_interface = GenerationInterface()  # Your actual interface
        self.expandLayout.addWidget(self.generation_interface)
        
        # Set layout for scrollWidget
        self.scrollWidget.setLayout(self.expandLayout)
        
        self.scrollArea = ScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scrollArea)

class ToolsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("toolsInterface")
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = TitleLabel("AI Tools", self)
        title_label.setFixedHeight(28)
        self.layout.addWidget(title_label)

        # Description
        desc_label = CaptionLabel("Explore our collection of AI-powered tools", self)
        self.layout.addWidget(desc_label)

        # Scroll area for tools
        self.scroll = ScrollArea()
        self.scroll.setWidgetResizable(True)
        
        # Container widget for tools
        container = QWidget()
        container_layout = QVBoxLayout(container)

        # Add tools
        self.add_tool(container_layout, "ChatGPT", "Advanced language model for conversation and text generation")
        self.add_tool(container_layout, "DALL-E", "AI system that creates images from textual descriptions")
        self.add_tool(container_layout, "Midjourney", "AI art generator with stunning visual capabilities")
        self.add_tool(container_layout, "Claude", "Advanced AI assistant for analysis and writing")
        self.add_tool(container_layout, "Stable Diffusion", "Open-source image generation model")

        self.scroll.setWidget(container)
        self.layout.addWidget(self.scroll)

    def add_tool(self, layout, name, description):
        tool_widget = QWidget()
        tool_layout = QVBoxLayout(tool_widget)

        # Tool header
        header_layout = QHBoxLayout()
        tool_name = QLabel(name)
        tool_name.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        header_layout.addWidget(tool_name)
        
        try_button = QPushButton("Try It")
        try_button.clicked.connect(lambda: self.open_tool_website(name))
        header_layout.addWidget(try_button)
        tool_layout.addLayout(header_layout)

        # Tool description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("QLabel { color: gray; }")
        tool_layout.addWidget(desc_label)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("QFrame { background-color: #e0e0e0; }")
        
        layout.addWidget(tool_widget)
        layout.addWidget(separator)

    def open_tool_website(self, tool_name):
        urls = {
            "ChatGPT": "https://chat.openai.com/",
            "DALL-E": "https://labs.openai.com/",
            "Midjourney": "https://www.midjourney.com/",
            "Claude": "https://claude.ai/",
            "Stable Diffusion": "https://stability.ai/"
        }
        if tool_name in urls:
            QDesktopServices.openUrl(QUrl(urls[tool_name]))

class ScrollableToolsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Instantiate the tools interface
        self.tools_interface = ToolsInterface()  # Your actual interface
        self.expandLayout.addWidget(self.tools_interface)
        
        # Set layout for scrollWidget
        self.scrollWidget.setLayout(self.expandLayout)
        
        self.scrollArea = ScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scrollArea)

class AnalyticsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("analyticsInterface")
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = TitleLabel("Instagram Analytics", self)
        title_label.setFixedHeight(28)
        self.layout.addWidget(title_label)

        # Description
        desc_label = CaptionLabel("Analyze Instagram profiles and posts", self)
        self.layout.addWidget(desc_label)

        # Username input
        self.username_edit = LineEdit(self)
        self.username_edit.setPlaceholderText("Enter Instagram username")
        self.layout.addWidget(self.username_edit)

        # Method selection
        self.method_combo = ComboBox(self)
        self.method_combo.addItems(["All Posts", "Top Posts", "Recent Posts", "Date Range"])
        self.method_combo.currentTextChanged.connect(self.on_method_changed)
        self.layout.addWidget(self.method_combo)

        # Date range inputs (hidden by default)
        self.date_range_widget = QWidget()
        date_range_layout = QVBoxLayout(self.date_range_widget)
        
        self.since_date = DateEdit(self)
        self.until_date = DateEdit(self)
        
        date_range_layout.addWidget(QLabel("Since Date:"))
        date_range_layout.addWidget(self.since_date)
        date_range_layout.addWidget(QLabel("Until Date:"))
        date_range_layout.addWidget(self.until_date)
        
        self.date_range_widget.hide()
        self.layout.addWidget(self.date_range_widget)

        # Save location
        save_layout = QHBoxLayout()
        self.save_path_edit = LineEdit(self)
        self.save_path_edit.setPlaceholderText("Save location...")
        self.save_path_edit.setReadOnly(True)
        
        browse_button = PushButton("Browse")
        browse_button.clicked.connect(self.choose_save_location)
        
        save_layout.addWidget(self.save_path_edit)
        save_layout.addWidget(browse_button)
        self.layout.addLayout(save_layout)

        # Start button
        self.start_button = PrimaryPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)
        self.layout.addWidget(self.start_button)

        # Progress bar
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

    def on_method_changed(self, method):
        self.date_range_widget.setVisible(method == "Date Range")

    def choose_save_location(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Analysis Results",
            "",
            "Excel files (*.xlsx);;CSV files (*.csv)"
        )
        if file_name:
            self.save_path_edit.setText(file_name)

    def start_analysis(self):
        username = self.username_edit.text().strip()
        save_path = self.save_path_edit.text()
        method = self.method_combo.currentText()

        if not username:
            self.show_error("Please enter an Instagram username")
            return

        if not save_path:
            self.show_error("Please select a save location")
            return

        # Show progress bar
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)

        # Create analyzer thread
        self.analyzer = InstagramAnalyzer(
            username=username,
            save_path=save_path,
            method=method,
            since_date=self.since_date.date().toPyDate() if method == "Date Range" else None,
            until_date=self.until_date.date().toPyDate() if method == "Date Range" else None
        )

        # Connect signals
        self.analyzer.progress.connect(self.update_progress)
        self.analyzer.error.connect(self.show_error)
        self.analyzer.finished.connect(self.analysis_complete)

        # Start analysis
        self.analyzer.run()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message} ({value}%)")

    def show_error(self, error_message):
        InfoBar.error(
            title='Error',
            content=error_message,
            parent=self
        )

    def analysis_complete(self):
        self.progress_bar.hide()
        self.start_button.setEnabled(True)
        InfoBar.success(
            title='Success',
            content='Analysis completed successfully!',
            parent=self
        )

class ScrollableAnalyticsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Instantiate the analytics interface
        self.analytics_interface = AnalyticsInterface()  # Your actual interface
        self.expandLayout.addWidget(self.analytics_interface)
        
        # Set layout for scrollWidget
        self.scrollWidget.setLayout(self.expandLayout)
        
        self.scrollArea = ScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scrollArea)

class InstagramAnalyzer(QObject):
    # Define signals for communication with the UI
    progress = pyqtSignal(int, str)  # Progress percentage and message
    error = pyqtSignal(str)         # Error messages
    finished = pyqtSignal()         # Completion signal

    def __init__(self, username, login_username=None, login_password=None, save_path=None,
                 method="All Posts", percentage=None, count=None, since_date=None, until_date=None, delay=10):
        super().__init__()
        
        self.username = username
        self.login_username = login_username
        self.login_password = login_password
        self.save_path = save_path
        self.method = method
        self.percentage = percentage
        self.count = count
        self.since_date = since_date
        self.until_date = until_date
        self.delay = delay

        # Use GraphQL method by default
        self.fetcher = InstagramFetcher(
            use_graph_api=False,
            max_posts=1000000,  # Set to a very high number to fetch all posts
            login_username=self.login_username,
            login_password=self.login_password
        )

    def run(self):
        try:
            # Fetch posts based on the selected method
            if self.method == "All Posts":
                posts = self._get_all_posts()
            elif self.method == "Top Posts":
                posts = self._get_top_posts()
            elif self.method == "Recent Posts":
                posts = self._get_recent_posts()
            elif self.method == "Date Range Posts":
                posts = self._get_posts_by_date_range()
            else:
                raise ValueError(f"Unsupported method: {self.method}")

            # Save data to Excel
            if posts:
                df = pd.DataFrame([post.to_dict() for post in posts])
                df.to_excel(self.save_path, index=False)
                self.progress.emit(100, f"Data saved to {self.save_path}")

            self.finished.emit()
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

    def _get_all_posts(self):
        self.progress.emit(20, "Fetching all posts")
        posts = self.fetcher.fetch_user_posts(
            username=self.username, 
            method="all"
        )
        return self._process_posts(posts)

    def _get_top_posts(self):
        if self.percentage is None:
            raise ValueError("Percentage value is required for Top Posts method")

        self.progress.emit(20, f"Fetching top {self.percentage}% posts")
        posts = self.fetcher.fetch_user_posts(
            username=self.username, 
            method="top"
        )
        
        # Sort posts by engagement and select top percentage
        sorted_posts = sorted(posts, key=lambda p: p.likes + p.comments, reverse=True)
        top_count = int(len(sorted_posts) * self.percentage / 100)
        return self._process_posts(sorted_posts[:top_count])

    def _get_recent_posts(self):
        if self.count is None:
            raise ValueError("Count value is required for Recent Posts method")

        self.progress.emit(20, f"Fetching {self.count} most recent posts")
        posts = self.fetcher.fetch_user_posts(
            username=self.username, 
            method="recent", 
            count=self.count
        )
        return self._process_posts(posts)

    def _get_posts_by_date_range(self):
        """Fetch posts within a specific date range"""
        if not self.since_date or not self.until_date:
            raise ValueError("Both since_date and until_date are required for Date Range Posts method")

        # Convert dates to datetime for consistent comparison
        since_datetime = datetime.combine(self.since_date, datetime.min.time())
        until_datetime = datetime.combine(self.until_date, datetime.max.time())

        self.progress.emit(20, f"Fetching posts between {since_datetime} and {until_datetime}")
        posts = self.fetcher.fetch_user_posts(
            username=self.username,
            method="date_range", 
            since_date=since_datetime, 
            until_date=until_datetime
        )
        return self._process_posts(posts)

    def _process_posts(self, posts: List[PostData]) -> List[PostData]:
        """
        Process and filter posts with enhanced error handling
        
        Args:
            posts: List of raw posts to process
        
        Returns:
            Processed and filtered list of posts
        """
        processed_posts = []
        
        for post in posts:
            try:
                # Emit progress for each processed post
                progress = min(100, len(processed_posts) * 2)
                self.progress.emit(progress, f"Processing post {len(processed_posts) + 1}")

                # Respect delay to prevent rate limiting
                time.sleep(1)
                
                processed_posts.append(post)
            
            except Exception as e:
                pass
        
        return processed_posts

class DataFetchThread(QThread):
    """Thread for fetching Instagram data with robust error handling"""
    progress_update = pyqtSignal(int, str)
    error_signal = pyqtSignal(str)

    def __init__(self, username, method, params=None, login_username=None, login_password=None, excel_file=None):
        super().__init__()
        
        # Ensure params is a dictionary
        self.params = params or {}
        
        # Validate and set parameters with default values
        self.username = username
        self.method = method
        self.login_username = login_username
        self.login_password = login_password
        self.excel_file = excel_file
        
        # Initialize fetcher with robust configuration
        self.fetcher = InstagramFetcher(
            use_graph_api=False,
            max_posts=1000000,  # Set to a very high number to fetch all posts
            login_username=login_username,
            login_password=login_password
        )

    def _safe_get_param(self, key, default=None):
        """
        Safely retrieve a parameter with a default value
        
        Args:
            key (str): Parameter key to retrieve
            default (Any, optional): Default value if key is not found
        
        Returns:
            Any: Parameter value or default
        """
        return self.params.get(key, default)

    def _convert_post_data(self, posts: List[PostData]):
        """
        Convert InstagramFetcher PostData to dictionary compatible with original method
        
        Args:
            posts: List of PostData objects
        
        Returns:
            List of dictionaries with post information
        """
        converted_posts = []
        for post in posts:
            try:
                converted_posts.append(post.to_dict())
            except Exception as e:
                self.error_signal.emit(f"Error converting post: {str(e)}")
        return converted_posts

    def _get_posts_by_date_range(self, writer):
        """Fetch posts within a specific date range"""
        since_date = self._safe_get_param('since_date')
        until_date = self._safe_get_param('until_date')
        
        if not since_date or not until_date:
            self.error_signal.emit("Both since_date and until_date are required for date range method")
            return
            
        try:
            posts = self.fetcher.fetch_user_posts(
                username=self.username,
                method='date_range',
                since_date=since_date,
                until_date=until_date
            )
            
            converted_posts = self._convert_post_data(posts)
            if converted_posts:
                writer.writerows(converted_posts)
                
        except Exception as e:
            self.error_signal.emit(f"Error fetching posts by date range: {str(e)}")

    def _get_top_posts(self, writer):
        """Fetch top posts"""
        percentage = self._safe_get_param('percentage', 10)
        try:
            posts = self.fetcher.fetch_user_posts(
                username=self.username,
                method='top'
            )
            
            # Sort by engagement and get top percentage
            sorted_posts = sorted(posts, key=lambda p: p.likes + p.comments, reverse=True)
            top_count = int(len(sorted_posts) * percentage / 100)
            top_posts = sorted_posts[:top_count]
            
            converted_posts = self._convert_post_data(top_posts)
            if converted_posts:
                writer.writerows(converted_posts)
                
        except Exception as e:
            self.error_signal.emit(f"Error fetching top posts: {str(e)}")

    def _get_recent_posts(self, writer):
        """Fetch most recent posts"""
        count = self._safe_get_param('count', 10)
        try:
            posts = self.fetcher.fetch_user_posts(
                username=self.username,
                method='recent',
                count=count
            )
            
            converted_posts = self._convert_post_data(posts)
            if converted_posts:
                writer.writerows(converted_posts)
                
        except Exception as e:
            self.error_signal.emit(f"Error fetching recent posts: {str(e)}")

    def _get_all_posts(self, writer):
        """Fetch all posts for the given username"""
        try:
            posts = self.fetcher.fetch_user_posts(
                username=self.username,
                method='all'
            )
            
            converted_posts = self._convert_post_data(posts)
            if converted_posts:
                writer.writerows(converted_posts)
                
        except Exception as e:
            self.error_signal.emit(f"Error fetching all posts: {str(e)}")

    def run(self):
        """Main thread execution method"""
        try:
            with open(self.excel_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'shortcode', 'timestamp', 'likes', 'comments', 'caption',
                    'is_video', 'video_url', 'display_url'
                ])
                writer.writeheader()
                
                if self.method == 'all':
                    self._get_all_posts(writer)
                elif self.method == 'top':
                    self._get_top_posts(writer)
                elif self.method == 'recent':
                    self._get_recent_posts(writer)
                elif self.method == 'date_range':
                    self._get_posts_by_date_range(writer)
                else:
                    self.error_signal.emit(f"Unsupported method: {self.method}")
                    return
                    
        except Exception as e:
            self.error_signal.emit(f"Error in data fetching thread: {str(e)}")

class ProfileInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("profileInterface")
        self.login_client = None
        self.setup_ui()
        
        # Start the timer to update user info periodically
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_user_info)
        self.update_timer.start(5000)  # Update every 5 seconds

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = TitleLabel("User Profile", self)
        title_label.setFixedHeight(28)
        layout.addWidget(title_label)

        # Profile picture
        self.profile_pic = QLabel(self)
        self.profile_pic.setFixedSize(150, 150)
        self.profile_pic.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border-radius: 75px;
            }
        """)
        layout.addWidget(self.profile_pic, alignment=Qt.AlignCenter)

        # Change profile picture button
        self.change_pic_button = PrimaryPushButton("Change Profile Picture", self)
        self.change_pic_button.clicked.connect(self.change_profile_picture)
        layout.addWidget(self.change_pic_button, alignment=Qt.AlignCenter)

        # User info
        info_group = QGroupBox("User Information", self)
        info_layout = QFormLayout(info_group)

        # Username
        self.username_value = QLabel("Not logged in", self)
        info_layout.addRow("Username:", self.username_value)

        # Email
        self.email_value = QLabel("Not logged in", self)
        info_layout.addRow("Email:", self.email_value)

        layout.addWidget(info_group)
        layout.addStretch()

        # Load initial profile picture
        self.load_profile_picture()

    def set_login_client(self, client):
        self.login_client = client
        self.update_user_info()

    def update_user_info(self):
        if not self.login_client or not self.login_client.username:
            self.username_value.setText('Not logged in')
            self.email_value.setText('Not logged in')
            return
            
        try:
            response, status_code = self.login_client.list_users()
            if status_code == 200:
                users = response.get('users', [])
                # Find the current user's info
                current_user = None
                for user in users:
                    if user.get('username') == self.login_client.username:
                        current_user = user
                        break
                
                if current_user:
                    self.username_value.setText(current_user.get('username', 'N/A'))
                    self.email_value.setText(current_user.get('email', 'N/A'))
                else:
                    InfoBar.error(
                        title='Error',
                        content=f'Could not find user {self.login_client.username}',
                        parent=self
                    )
            else:
                InfoBar.error(
                    title='Error',
                    content='Failed to load user information',
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=str(e),
                parent=self
            )

    def load_profile_picture(self):
        if not self.login_client:
            return

        try:
            # Get profile picture data
            picture_data, status_code = self.login_client.get_profile_picture()
            
            if status_code == 200 and picture_data:
                # Create QPixmap from the image data
                pixmap = QPixmap()
                pixmap.loadFromData(picture_data)
                
                # Create a circular mask
                rounded = QPixmap(pixmap.size())
                rounded.fill(Qt.transparent)
                
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QBrush(pixmap))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(rounded.rect())
                painter.end()
                
                # Scale the pixmap to fit the label
                scaled_pixmap = rounded.scaled(
                    self.profile_pic.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.profile_pic.setPixmap(scaled_pixmap)
            else:
                # Set default profile picture or show error
                self.profile_pic.setText("No\nProfile\nPicture")
                self.profile_pic.setAlignment(Qt.AlignCenter)
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=f'Failed to load profile picture: {str(e)}',
                parent=self
            )

    def change_profile_picture(self):
        if not self.login_client or not self.login_client.token:
            InfoBar.error(
                title='Error',
                content='Please log in first',
                parent=self
            )
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Image files (*.jpg *.jpeg *.png)"
        )
        
        if file_name:
            try:
                response, status_code = self.login_client.upload_profile_picture(file_name)
                
                if status_code == 200:
                    InfoBar.success(
                        title='Success',
                        content='Profile picture updated successfully',
                        parent=self
                    )
                    self.load_profile_picture()  # Reload the profile picture
                else:
                    error_msg = response.get('error', 'Unknown error occurred')
                    InfoBar.error(
                        title='Error',
                        content=f'Failed to update profile picture: {error_msg}',
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='Error',
                    content=f'Failed to update profile picture: {str(e)}',
                    parent=self
                )

class ScrollableProfileInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("scrollableProfileInterface")
        self.profile_interface = ProfileInterface(self)
        self.setWidget(self.profile_interface)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
