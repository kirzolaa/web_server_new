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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('analytics.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class FeatureCard(CardWidget):
    """ Feature card for AI tools """

    clicked = pyqtSignal()

    def __init__(self, icon_path, title, description, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setupUi(icon_path, title, description)

    def setupUi(self, icon_path, title, description):
        self.setFixedSize(220, 240)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon
        self.iconWidget = IconWidget(self)
        self.iconWidget.setFixedSize(120, 120)
        
        # Debug print
        print(f"Loading icon from: {icon_path}")
        
        # Check if file exists
        if not icon_path.startswith(':/'): 
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self.iconWidget.setIcon(icon)
                else:
                    print(f"Failed to load icon: {icon_path}")
                    self.iconWidget.setIcon(FluentIcon.PEOPLE)
            else:
                print(f"Icon file not found: {icon_path}")
                self.iconWidget.setIcon(FluentIcon.PEOPLE)
        else:
            self.iconWidget.setIcon(FluentIcon.PEOPLE)
        
        # Labels
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 14px;
                font-weight: bold;
                margin: 10px 0;
            }
        """)
        
        self.descriptionLabel = QLabel(description, self)
        self.descriptionLabel.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 12px;
            }
        """)
        self.descriptionLabel.setWordWrap(True)
        
        # Visit button
        self.visitButton = TransparentToolButton(self)
        self.visitButton.setText('Visit Website')
        self.visitButton.clicked.connect(self.openUrl)
        
        # Add widgets to layout
        layout.addWidget(self.iconWidget, 0, Qt.AlignCenter)
        layout.addWidget(self.titleLabel, 0, Qt.AlignCenter)
        layout.addWidget(self.descriptionLabel, 0, Qt.AlignCenter)
        layout.addWidget(self.visitButton, 0, Qt.AlignCenter)
        
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

    def openUrl(self):
        QDesktopServices.openUrl(QUrl(self.url))

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
        title_label = TitleLabel("AI Agency Tools", self)
        title_label.setFixedHeight(28)
        self.layout.addWidget(title_label)

        # Description
        desc_label = CaptionLabel("Explore our curated selection of cutting-edge AI tools and services", self)
        self.layout.addWidget(desc_label)

        # Feature cards in a flow layout
        self.card_widget = QWidget()
        self.flow_layout = FlowLayout(self.card_widget, needAni=True)
        
        # Add feature cards
        features = [
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'tengr_ai.png'),
                'title': 'Tengr.ai',
                'description': 'Advanced AI model deployment and scaling platform',
                'url': 'https://tengr.ai/'
            },
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'seduced.png'),
                'title': 'Seduced',
                'description': 'Advanced AI model deployment and scaling platform',
                'url': 'https://https://www.seduced.ai//'
            },
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'runway.png'),
                'title': 'Runway',
                'description': 'AI-powered creative tools for video editing and generation',
                'url': 'https://runway.ml/'
            },
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'ideogram.png'),
                'title': 'Ideogram',
                'description': 'AI image generation and artistic style transfer',
                'url': 'https://ideogram.ai/'
            },
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'grok.png'),
                'title': 'Grok',
                'description': 'Advanced AI chatbot with real-time knowledge',
                'url': 'https://grok.x.ai/'
            },
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'elevenL.png'),
                'title': 'Eleven Labs',
                'description': 'State-of-the-art AI voice synthesis and cloning platform',
                'url': 'https://elevenlabs.io/'
            },
            {
                'icon': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'google-drive.png'),
                'title': 'Google Drive',
                'description': 'Cloud storage and file sharing platform for project assets',
                'url': 'https://drive.google.com/'
            }
        ]

        for feature in features:
            card = FeatureCard(
                feature['icon'],
                feature['title'],
                feature['description'],
                feature['url'],
                self.card_widget
            )
            self.flow_layout.addWidget(card)

        # Add card widget to main layout
        self.layout.addWidget(self.card_widget)
        self.layout.addStretch()

class AnalyticsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("analyticsInterface")
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 24, 36, 24)
        self.layout.setSpacing(20)
        
        # Title
        title_label = TitleLabel("Instagram Analytics", self)
        title_label.setFixedHeight(28)
        self.layout.addWidget(title_label)

        # Description
        desc_label = CaptionLabel("Analyze Instagram profiles and posts", self)
        self.layout.addWidget(desc_label)

        # Login credentials
        self.login_group = QGroupBox("Login (Optional)", self)
        self.login_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
        """)
        login_layout = QFormLayout()
        self.login_group.setLayout(login_layout)
        login_layout.setSpacing(15)
        login_layout.setContentsMargins(20, 20, 20, 20)
        
        # Login username
        self.login_username = LineEdit(self)
        self.login_username.setPlaceholderText("Enter Instagram login username")
        self.login_username.setFixedWidth(300)
        login_layout.addRow("Login Username:", self.login_username)
        
        # Optional Login email
        self.login_email = LineEdit(self)
        self.login_email.setPlaceholderText("Optional: Enter email (for registration)")
        self.login_email.setFixedWidth(300)
        login_layout.addRow("Email:", self.login_email)
        
        # Login password
        self.login_password = LineEdit(self)
        self.login_password.setPlaceholderText("Enter Instagram login password")
        self.login_password.setEchoMode(LineEdit.Password)
        self.login_password.setFixedWidth(300)
        login_layout.addRow("Login Password:", self.login_password)
        
        self.layout.addWidget(self.login_group)
        
        # Target username input
        target_group = QGroupBox("Target Account", self)
        target_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
        """)
        target_layout = QFormLayout()
        target_group.setLayout(target_layout)
        target_layout.setSpacing(15)
        target_layout.setContentsMargins(20, 20, 20, 20)
        
        self.username_input = LineEdit(self)
        self.username_input.setPlaceholderText("Enter Instagram username to analyze")
        self.username_input.setFixedWidth(300)
        target_layout.addRow("Target Username:", self.username_input)
        
        self.layout.addWidget(target_group)
        
        # Method selection
        method_group = QGroupBox("Analysis Settings", self)
        method_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
        """)
        method_layout = QVBoxLayout()
        method_group.setLayout(method_layout)
        method_layout.setSpacing(15)
        method_layout.setContentsMargins(20, 20, 20, 20)

        # Create method menu
        self.method_menu = RoundMenu(parent=self)
        self.method_menu.addAction(Action(FluentIcon.HISTORY, 'Recent Posts', triggered=lambda: self.on_method_changed("Recent Posts")))
        self.method_menu.addAction(Action(FluentIcon.SHARE, 'Top Posts', triggered=lambda: self.on_method_changed("Top Posts")))
        self.method_menu.addAction(Action(FluentIcon.CALENDAR, 'Date Range Posts', triggered=lambda: self.on_method_changed("Date Range Posts")))
        self.method_menu.addAction(Action(FluentIcon.SEARCH, 'All Posts', triggered=lambda: self.on_method_changed("All Posts")))

        # Create split button
        self.method_button = PrimarySplitPushButton('Recent Posts', self)
        self.method_button.setFlyout(self.method_menu)
        self.method_button.setFixedWidth(300)
        
        method_layout.addWidget(self.method_button)
        self.layout.addWidget(method_group)

        # Date range inputs
        self.date_group = QGroupBox("Date Range Settings", self)
        self.date_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 4px 0px 4px;
            }
        """)
        date_layout = QVBoxLayout()
        date_layout.setSpacing(10)
        date_layout.setContentsMargins(20, 20, 20, 20)
        
        # Start date sub-box
        start_date_group = QGroupBox("Start Date", self)
        start_date_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 4px 0px 4px;
            }
        """)
        start_date_layout = QVBoxLayout()
        start_date_layout.setContentsMargins(10, 10, 10, 10)
        
        self.since_date = CalendarPicker(self)
        self.since_date.setFixedWidth(200)
        self.since_date.setDate(QDate.currentDate())
        start_date_layout.addWidget(self.since_date)
        start_date_group.setLayout(start_date_layout)
        
        # End date sub-box
        end_date_group = QGroupBox("End Date", self)
        end_date_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 4px 0px 4px;
            }
        """)
        end_date_layout = QVBoxLayout()
        end_date_layout.setContentsMargins(10, 10, 10, 10)
        
        self.until_date = CalendarPicker(self)
        self.until_date.setFixedWidth(200)
        self.until_date.setDate(QDate.currentDate())
        end_date_layout.addWidget(self.until_date)
        end_date_group.setLayout(end_date_layout)
        
        # Add date groups to main layout
        date_layout.addWidget(start_date_group)
        date_layout.addWidget(end_date_group)
        self.date_group.setLayout(date_layout)
        
        self.layout.addWidget(self.date_group)

        # Top posts percentage input
        self.percentage_group = QGroupBox("Top Posts Settings", self)
        self.percentage_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
        """)
        percentage_layout = QFormLayout(self.percentage_group)
        percentage_layout.setSpacing(15)
        percentage_layout.setContentsMargins(20, 20, 20, 20)
        
        self.percentage_input = SpinBox(self)
        self.percentage_input.setRange(1, 100)
        self.percentage_input.setValue(10)
        self.percentage_input.setSuffix("%")
        self.percentage_input.setFixedWidth(300)
        percentage_layout.addRow("Top Posts Percentage:", self.percentage_input)
        
        self.layout.addWidget(self.percentage_group)

        # Recent posts count input
        self.count_group = QGroupBox("Recent Posts Settings", self)
        self.count_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
        """)
        count_layout = QFormLayout(self.count_group)
        count_layout.setSpacing(15)
        count_layout.setContentsMargins(20, 20, 20, 20)
        
        self.count_input = SpinBox(self)
        self.count_input.setRange(1, 1000)
        self.count_input.setValue(10)
        self.count_input.setFixedWidth(300)
        count_layout.addRow("Recent Posts Count:", self.count_input)
        
        self.layout.addWidget(self.count_group)

        # Command prompt
        self.command_group = QGroupBox("Output Log", self)
        self.command_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
        """)
        output_layout = QVBoxLayout(self.command_group)
        output_layout.setContentsMargins(20, 20, 20, 20)
        
        self.command_prompt = TextEdit(self)
        self.command_prompt.setReadOnly(True)
        self.command_prompt.setStyleSheet("""
            TextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Consolas, monospace;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.command_prompt.setMinimumHeight(150)
        self.command_prompt.setPlaceholderText("Analysis output will appear here...")
        output_layout.addWidget(self.command_prompt)
        self.layout.addWidget(self.command_group)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Save file button
        self.save_path = None
        self.save_button = PrimaryPushButton("Choose Save Location", self)
        self.save_button.setIcon(FluentIcon.SAVE)
        self.save_button.clicked.connect(self.choose_save_location)
        button_layout.addWidget(self.save_button)

        # Start button
        self.start_button = PrimaryPushButton("Start Analysis", self)
        self.start_button.setIcon(FluentIcon.PLAY)
        self.start_button.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.start_button)
        
        self.layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.layout.addWidget(self.progress_bar)

        # Initialize method-specific inputs visibility
        self.on_method_changed(self.method_button.text())

    def on_method_changed(self, method):
        """Handle visibility of input fields based on selected method"""
        self.method_button.setText(method)
        self.date_group.setVisible(method == "Date Range Posts")
        self.percentage_group.setVisible(method == "Top Posts")
        self.count_group.setVisible(method == "Recent Posts")

    def choose_save_location(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            self.save_path = file_path

    def start_analysis(self):
        if not self.username_input.text():
            self.command_prompt.append("Error: Please enter a username")
            return
            
        if not self.save_path:
            self.command_prompt.append("Error: Please choose a save location first")
            return
            
        method = self.method_button.text()
        
        # Convert QDate to Python date
        since_date = None
        until_date = None
        if method == "Date Range Posts":
            # Safely convert since_date
            since_date = self.since_date.getDate().toPyDate()
            
            # Safely convert until_date
            until_date = self.until_date.getDate().toPyDate()
            
            # Validate date range
            if not since_date or not until_date:
                self.show_error("Please select both start and end dates for Date Range method")
                return

        # Create analyzer thread
        self.analyzer = InstagramAnalyzer(
            username=self.username_input.text(),
            login_username=self.login_username.text(),
            login_password=self.login_password.text(),
            save_path=self.save_path,
            method=method,
            percentage=self.percentage_input.value() if method == "Top Posts" else None,
            count=self.count_input.value() if method == "Recent Posts" else None,
            since_date=since_date,
            until_date=until_date
        )
        
        # Move analyzer to worker thread
        self.worker = QThread()
        self.analyzer.moveToThread(self.worker)
        
        # Connect signals
        self.worker.started.connect(self.analyzer.run)
        self.analyzer.progress.connect(self.update_progress)
        self.analyzer.error.connect(self.show_error)
        self.analyzer.finished.connect(self.analysis_complete)
        self.analyzer.finished.connect(self.worker.quit)
        self.analyzer.finished.connect(self.analyzer.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        
        # Disable UI elements
        self.start_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.username_input.setEnabled(False)
        self.method_button.setEnabled(False)
        
        # Start analysis
        self.command_prompt.append(f"Starting analysis for user: {self.username_input.text()}")
        self.worker.start()
        
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.command_prompt.append(message)
        
    def show_error(self, error_message):
        """Show error message in command prompt"""
        self.command_prompt.append(f"Error: {error_message}")
        self.enable_ui_elements()
        
    def analysis_complete(self):
        """Handle analysis completion"""
        self.command_prompt.append("Analysis complete!")
        self.enable_ui_elements()
        
    def enable_ui_elements(self):
        self.start_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.username_input.setEnabled(True)
        self.method_button.setEnabled(True)

    def _update_selected_date(self, qdate):
        """Update the selected date input based on which one has focus"""
        if self.since_date.hasFocus():
            self.since_date.setDate(qdate)
        elif self.until_date.hasFocus():
            self.until_date.setDate(qdate)

from PyQt5.QtCore import QObject, pyqtSignal

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
                # Validate post data
                # if not post or not hasattr(post, 'timestamp'):
                #     logger.warning(f"Skipping invalid post: {post}")
                #     continue
                
                # Emit progress for each processed post
                progress = min(100, len(processed_posts) * 2)
                self.progress.emit(progress, f"Processing post {len(processed_posts) + 1}")

                # Respect delay to prevent rate limiting
                time.sleep(1)
                
                processed_posts.append(post)
            
            except Exception as e:
                # logger.error(f"Error processing post: {e}")
                # logger.error(f"Problematic post details: {post}")
                pass
        
        return processed_posts

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
        # Handle different parameter input scenarios
        if isinstance(self.params, dict):
            return self.params.get(key, default)
        elif hasattr(self.params, key):
            return getattr(self.params, key, default)
        else:
            return default
    
    def _convert_post_data(self, posts: List[PostData]) -> List[Dict]:
        """
        Convert InstagramFetcher PostData to dictionary compatible with original method
        
        Args:
            posts: List of PostData objects
        
        Returns:
            List of dictionaries with post information
        """
        converted_posts = []
        for post in posts:
            converted_post = {
                "Date": post.timestamp,
                "Caption": post.caption or "",
                "Likes": post.likes or 0,
                "Comments": post.comments or 0,
                "Is Video": post.media_type == 'VIDEO',
                "URL": post.url or "",
                "Location": post.location or "Unknown",
                "Hashtags": ', '.join(post.hashtags) if post.hashtags else '',
            }
            converted_posts.append(converted_post)
        return converted_posts
    
    def _get_posts_by_date_range(self, writer):
        """Fetch posts within a specific date range"""
        try:
            # Safely retrieve and convert date parameters
            since_date = self._safe_get_param('since_date')
            until_date = self._safe_get_param('until_date')
            
            # Convert QDate to datetime if necessary
            if hasattr(since_date, 'toPyDate'):
                since_date = since_date.toPyDate()
            if hasattr(until_date, 'toPyDate'):
                until_date = until_date.toPyDate()
            
            # Validate dates
            if not since_date or not until_date:
                raise ValueError("Both since_date and until_date must be provided")
            
            posts = self.fetcher.fetch_user_posts(
                username=self.username, 
                method="date_range", 
                since_date=since_date, 
                until_date=until_date
            )
            
            converted_posts = self._convert_post_data(posts)
            writer.writerows(converted_posts)
            self.progress_update.emit(100, f"Fetched {len(posts)} posts in date range")
        
        except Exception as e:
            error_msg = f"Error fetching posts by date range: {str(e)}"
            self.error_signal.emit(error_msg)
            logger.error(error_msg, exc_info=True)
    
    def _get_top_posts(self, writer):
        """Fetch top posts"""
        try:
            # Safely retrieve percentage, default to 10%
            percentage = self._safe_get_param('percentage', 10)
            
            posts = self.fetcher.fetch_user_posts(
                username=self.username, 
                method="top"
            )
            
            # Sort posts by engagement
            sorted_posts = sorted(posts, key=lambda p: (p.likes or 0) + (p.comments or 0), reverse=True)
            top_count = int(len(sorted_posts) * percentage / 100)
            
            converted_posts = self._convert_post_data(sorted_posts[:top_count])
            writer.writerows(converted_posts)
            self.progress_update.emit(100, f"Fetched top {top_count} posts")
        
        except Exception as e:
            error_msg = f"Error fetching top posts: {str(e)}"
            self.error_signal.emit(error_msg)
            logger.error(error_msg)
    
    def _get_recent_posts(self, writer):
        """Fetch most recent posts"""
        try:
            # Safely retrieve count, default to 50
            count = self._safe_get_param('count', 50)
            
            posts = self.fetcher.fetch_user_posts(
                username=self.username, 
                method="recent", 
                count=count
            )
            
            converted_posts = self._convert_post_data(posts)
            writer.writerows(converted_posts)
            self.progress_update.emit(100, f"Fetched {len(posts)} recent posts")
        
        except Exception as e:
            error_msg = f"Error fetching recent posts: {str(e)}"
            self.error_signal.emit(error_msg)
            logger.error(error_msg)
    
    def _get_all_posts(self, writer):
        """Fetch all posts for the given username"""
        try:
            # Fetch posts
            posts, _ = self.fetcher._get_user_posts_graphql(
                user_id=self.fetcher._get_user_id(self.username)
            )
            
            # Convert and validate posts
            if not posts:
                self.progress_update.emit(0, f"No posts found for {self.username}")
                logger.warning(f"No posts found for username: {self.username}")
                return
            
            # Convert posts to dictionaries
            converted_posts = self._convert_post_data(posts)
            
            # Log specific details in the built-in console
            self.progress_update.emit(50, f"Total posts count: {len(posts)}")
            self.progress_update.emit(60, f"Number of post edges: {len(posts)}")
            self.progress_update.emit(70, f"Successfully fetched {len(posts)} posts")
            
            # Write posts to CSV
            writer.writerows(converted_posts)
            
            # Emit progress and completion signals
            logger.info(f"Fetched {len(posts)} posts for {self.username}")
            self.progress_update.emit(100, f"Successfully fetched {len(posts)} posts for {self.username}")
        
        except Exception as e:
            error_msg = f"Error fetching all posts: {str(e)}"
            self.error_signal.emit(error_msg)
            logger.error(error_msg, exc_info=True)
    
    def run(self):
        """Main thread execution method"""
        try:
            # Create a CSV writer
            with open(self.excel_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "Date", "Caption", "Likes", "Comments", 
                    "Is Video", "URL", "Location", "Hashtags"
                ])
                
                # Select method based on input
                if self.method == "Date Range Posts":
                    self._get_posts_by_date_range(writer)
                elif self.method == "Top Posts":
                    self._get_top_posts(writer)
                elif self.method == "Recent Posts":
                    self._get_recent_posts(writer)
                elif self.method == "All Posts":
                    self._get_all_posts(writer)
                else:
                    raise ValueError(f"Unsupported method: {self.method}")
        
        except Exception as e:
            error_msg = f"Unexpected error in data fetch thread: {str(e)}"
            self.error_signal.emit(error_msg)
            logger.error(error_msg, exc_info=True)
        
        finally:
            self.quit()

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agency")
        
        # Set custom application icon
        app_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'ai.png')
        self.setWindowIcon(QIcon(app_icon_path))
        self.resize(1000, 750)
        
        # Initialize interfaces
        self.tools_interface = ScrollableToolsInterface(self)
        self.analytics_interface = ScrollableAnalyticsInterface(self)
        self.generation_interface = ScrollableGenerationInterface(self)
        self.login_interface = QWidget(self)  # For Login
        self.settings_interface = QWidget(self)  # For Settings

        # Assign unique object names
        self.tools_interface.setObjectName("toolsInterface")
        self.analytics_interface.setObjectName("analyticsInterface")
        self.generation_interface.setObjectName("generationInterface")
        self.login_interface.setObjectName("loginInterface")
        self.settings_interface.setObjectName("settingsInterface")

        # Navigation icons
        resources_dir = os.path.dirname(os.path.dirname(__file__)) + '/resources'
        tools_icon_path = os.path.join(resources_dir, 'ai.png')
        analytics_icon_path = os.path.join(resources_dir, 'ig.png')
        generation_icon_path = os.path.join(resources_dir, 'generation.png')
        login_icon_path = os.path.join(resources_dir, 'login.png')
        settings_icon_path = os.path.join(resources_dir, 'settings.png')

        # Add navigation items
        self.addSubInterface(
            self.tools_interface,
            QIcon(tools_icon_path),
            "AI Tools",
            NavigationItemPosition.TOP
        )

        self.addSubInterface(
            self.analytics_interface,
            QIcon(analytics_icon_path),
            "Instagram Analytics",
            NavigationItemPosition.TOP
        )

        self.addSubInterface(
            self.generation_interface,
            QIcon(generation_icon_path),
            "AI Generation",
            NavigationItemPosition.TOP
        )

        self.addSubInterface(
            self.login_interface,
            QIcon(login_icon_path),
            "Login",
            NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(
            self.settings_interface,
            QIcon(settings_icon_path),
            "Settings",
            NavigationItemPosition.BOTTOM
        )

        # Setup additional UI elements for Login and Settings
        self.setup_login_ui()
        self.setup_settings_ui()

        # Set theme
        setTheme(Theme.AUTO)

    def setup_login_ui(self):
        """Setup the Login interface UI."""
        layout = QVBoxLayout(self.login_interface)  # Create a vertical layout for the login interface
        layout.setContentsMargins(20, 20, 20, 20)  # Set margins for the layout
        layout.setSpacing(10)  # Set spacing between widgets

        # Logo
        logo_label = QLabel(self.login_interface)
        logo_label.setPixmap(QPixmap("I:/discord/py_bot/AI Agency/resources/login.png"))  # Path to your logo
        logo_label.setScaledContents(True)
        logo_label.setFixedSize(100, 100)  # Set a fixed size for the logo
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label, 0, Qt.AlignCenter)  # Center the logo

        # Username input
        username_label = QLabel("Username:", self.login_interface)
        layout.addWidget(username_label, 0, Qt.AlignCenter)

        self.username_input = QLineEdit(self.login_interface)
        self.username_input.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_input, 0, Qt.AlignCenter)

        # Email input
        email_label = QLabel("Email:", self.login_interface)
        layout.addWidget(email_label, 0, Qt.AlignCenter)

        self.email_input = QLineEdit(self.login_interface)
        self.email_input.setPlaceholderText("Enter your email")
        layout.addWidget(self.email_input, 0, Qt.AlignCenter)

        # Password input
        password_label = QLabel("Password:", self.login_interface)
        layout.addWidget(password_label, 0, Qt.AlignCenter)

        self.password_input = QLineEdit(self.login_interface)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)  # Mask the password input
        layout.addWidget(self.password_input, 0, Qt.AlignCenter)

        # Login button
        login_button = QPushButton("Login", self.login_interface)
        login_button.clicked.connect(self.handle_login)  # Connect to the login handler
        layout.addWidget(login_button, 0, Qt.AlignCenter)

        # Register button
        register_button = QPushButton("Register", self.login_interface)
        register_button.clicked.connect(self.handle_register)  # Connect to the register handler
        layout.addWidget(register_button, 0, Qt.AlignCenter)

        # Add stretch at the end to keep layout clean
        layout.addStretch()
        
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        email = self.email_input.text().strip()

        if not username or not password:
            InfoBar.error(
                title='Error',
                content='Username and Password cannot be empty.',
                parent=self
            )
            return

        try:
            response = requests.post('http://192.168.56.1:5000/login', json={
                'username': username,
                'password': password,
                'email': email
            })

            if response.status_code == 200:
                token = response.json().get('token')
                # Optional: Store token for future authenticated requests
                self.login_token = token
                InfoBar.success(
                    title='Success',
                    content='Login successful!',
                    parent=self
                )
            else:
                error_message = response.json().get('error', 'Login failed')
                InfoBar.error(
                    title='Error',
                    content=error_message,
                    parent=self
                )
        except requests.RequestException as e:
            InfoBar.error(
                title='Error',
                content=f'Network error: {str(e)}',
                parent=self
            )

    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        email = self.email_input.text().strip()

        if not username or not password or not email:
            InfoBar.error(
                title='Error',
                content='Username, Password and Email cannot be empty.',
                parent=self
            )
            return

        try:
            response = requests.post('http://192.168.56.1:5000/register', json={
                'username': username,
                'password': password,
                'email': email
            })

            if response.status_code == 201:
                InfoBar.success(
                    title='Success',
                    content='Registration successful!',
                    parent=self
                )
            else:
                error_message = response.json().get('error', 'Registration failed')
                InfoBar.error(
                    title='Error',
                    content=error_message,
                    parent=self
                )
        except requests.RequestException as e:
            InfoBar.error(
                title='Error',
                content=f'Network error: {str(e)}',
                parent=self
            )

    def setup_settings_ui(self):
        """Setup the Settings interface UI."""
        layout = QHBoxLayout(self)  # Create a horizontal layout
        self.settingInterface = SettingInterface(self)  # Create an instance of SettingInterface
        layout.setContentsMargins(0, 0, 0, 0)  # Set margins for the layout
        layout.addWidget(self.settingInterface)  # Add the settings interface to the layout

        self.settings_interface.setLayout(layout)  # Apply the layout to the settings interface

def load_icon(icon_name):
    """
    Safely load an icon with multiple fallback paths.
    
    :param icon_name: Name of the icon file
    :return: QIcon object
    """
    # Possible paths to search for the icon
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'resources', icon_name),  # Relative to script
        os.path.join(os.path.dirname(__file__), 'resources', icon_name),  # In script directory
        os.path.join(os.getcwd(), 'resources', icon_name),  # Current working directory
        os.path.join(os.path.dirname(sys.executable), 'resources', icon_name)  # Executable directory
    ]
    
    # Try each path
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Loading icon from: {path}")
            return QIcon(path)
    
    # If no icon found, print warning and return empty icon
    print(f"Icon file not found: {icon_name}")
    return QIcon()  # Returns a null icon

def init_app():
    # Set high DPI scaling environment variables BEFORE importing Qt
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

    # Create application with high DPI support
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and setup window
    w = MainWindow()
    w.show()
    
    # Set theme
    setTheme(Theme.LIGHT)
    setThemeColor('#0078d4')
    
    # Run application
    sys.exit(app.exec_())

if __name__ == '__main__':
    init_app()