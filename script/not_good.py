import sys
import os
import json
import requests
import pandas as pd
import time
import logging
from datetime import datetime
from itertools import takewhile, dropwhile, islice
from typing import List, Dict

from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QRectF, 
                         QDate, QDateTime, QObject)
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QFileDialog, QTextEdit, QFormLayout, 
                           QComboBox, QDateEdit, QLineEdit, QGroupBox, QSpinBox, 
                           QGridLayout, QDockWidget, QStackedWidget, QDialog)
from PyQt5.QtGui import (QIcon, QDesktopServices, QPixmap, QPainter, QColor, QBrush)

from qfluentwidgets import (FluentIcon, PushButton, ToolButton, TransparentToolButton,
                         LineEdit, PrimaryPushButton, SpinBox, ProgressBar, PushSettingCard,
                         OptionsSettingCard, TitleLabel, CaptionLabel, SubtitleLabel,
                         TextEdit, DateTimeEdit, setTheme, Theme, setThemeColor, NavigationPushButton,
                         FluentWindow, NavigationItemPosition, MessageBox, SplashScreen,
                         ScrollArea, CardWidget, IconWidget, FlowLayout, BodyLabel,
                         ComboBoxSettingCard, OptionsConfigItem, CalendarPicker, PillPushButton,
                         DropDownPushButton, RoundMenu, Action, TransparentPushButton,
                         PrimarySplitPushButton, InfoBar, InfoBarPosition, ComboBox,
                         NavigationInterface)

from qframelesswindow import FramelessWindow, StandardTitleBar

from setting_interface import SettingInterface
from post_fetcher import InstagramFetcher, PostData
from login_server.login_client import LoginClient

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

# enable dpi scale
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

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
        self.tools_interface.setObjectName("toolsInterface")
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
        self.analytics_interface.setObjectName("analyticsInterface")
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
        self.generation_interface.setObjectName("generationInterface")
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
        self.card_widget.setObjectName("cardWidget")
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
            card.setObjectName("featureCard")
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
        self.username_input.setClearButtonEnabled(True)
        target_layout.addRow("Target Username:", self.username_input)
        
        self.layout.addWidget(target_group)

        # Optional Instagram login for private accounts
        insta_login_group = QGroupBox("Optional Instagram Login (for private accounts)", self)
        insta_login_group.setStyleSheet("""
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
        insta_login_layout = QFormLayout()
        insta_login_group.setLayout(insta_login_layout)
        insta_login_layout.setSpacing(15)
        insta_login_layout.setContentsMargins(20, 20, 20, 20)
        
        self.insta_username = LineEdit(self)
        self.insta_username.setPlaceholderText("Enter Instagram login username")
        self.insta_username.setClearButtonEnabled(True)
        insta_login_layout.addRow("Instagram Username:", self.insta_username)
        
        self.insta_password = LineEdit(self)
        self.insta_password.setPlaceholderText("Enter Instagram login password")
        self.insta_password.setEchoMode(LineEdit.Password)
        self.insta_password.setClearButtonEnabled(True)
        insta_login_layout.addRow("Instagram Password:", self.insta_password)
        
        self.layout.addWidget(insta_login_group)

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
        self.until_date.setDate(QDate.currentDate())
        end_date_layout.addWidget(self.until_date)
        end_date_group.setLayout(end_date_layout)
        
        # Add date groups to main layout
        date_layout.addWidget(start_date_group)
        date_layout.addWidget(end_date_group)
        self.date_group.setLayout(date_layout)
        
        self.layout.addWidget(self.date_group)
        self.date_group.hide()  # Initially hidden

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
        percentage_layout = QHBoxLayout()
        self.percentage_group.setLayout(percentage_layout)
        percentage_layout.setSpacing(15)
        percentage_layout.setContentsMargins(20, 20, 20, 20)

        self.percentage_input = SpinBox(self)
        self.percentage_input.setRange(1, 100)
        self.percentage_input.setValue(10)
        self.percentage_input.setSuffix("%")
        percentage_layout.addWidget(QLabel("Percentage of Top Posts:"))
        percentage_layout.addWidget(self.percentage_input)
        percentage_layout.addStretch()

        self.layout.addWidget(self.percentage_group)
        self.percentage_group.hide()  # Initially hidden

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
        count_layout = QHBoxLayout()
        self.count_group.setLayout(count_layout)
        count_layout.setSpacing(15)
        count_layout.setContentsMargins(20, 20, 20, 20)

        self.count_input = SpinBox(self)
        self.count_input.setRange(1, 100)
        self.count_input.setValue(10)
        self.count_input.setSuffix(" posts")
        count_layout.addWidget(QLabel("Number of Recent Posts:"))
        count_layout.addWidget(self.count_input)
        count_layout.addStretch()

        self.layout.addWidget(self.count_group)
        self.count_group.hide()  # Initially hidden

        # Save location
        save_group = QGroupBox("Save Settings", self)
        save_group.setStyleSheet("""
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
        save_layout = QHBoxLayout()
        save_group.setLayout(save_layout)
        save_layout.setSpacing(15)
        save_layout.setContentsMargins(20, 20, 20, 20)

        self.save_path = None
        self.save_path_label = LineEdit(self)
        self.save_path_label.setPlaceholderText("Choose save location...")
        self.save_path_label.setReadOnly(True)
        save_layout.addWidget(QLabel("Save Location:"))
        save_layout.addWidget(self.save_path_label)

        self.browse_button = PushButton("Browse", self)
        self.browse_button.setIcon(FluentIcon.FOLDER)
        self.browse_button.clicked.connect(self.choose_save_location)
        save_layout.addWidget(self.browse_button)
        save_layout.addStretch()

        self.layout.addWidget(save_group)

        # Progress bar and start button
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(15)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()
        bottom_layout.addWidget(self.progress_bar)

        self.analyze_button = PrimaryPushButton("Start Analysis", self)
        self.analyze_button.setIcon(FluentIcon.PLAY)
        self.analyze_button.clicked.connect(self.start_analysis)
        bottom_layout.addWidget(self.analyze_button, alignment=Qt.AlignCenter)

        self.layout.addLayout(bottom_layout)

    def on_method_changed(self, method):
        """Handle visibility of input fields based on selected method"""
        self.method_button.setText(method)
        self.date_group.setVisible(method == "Date Range Posts")
        self.percentage_group.setVisible(method == "Top Posts")
        self.count_group.setVisible(method == "Recent Posts")

    def choose_save_location(self):
        """Open file dialog to choose save location"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Analysis Results",
            "",
            "Excel files (*.xlsx)"
        )
        if file_name:
            self.save_path = file_name
            self.save_path_label.setText(file_name)

    def start_analysis(self):
        """Start the Instagram analysis"""
        if not self.username_input.text():
            InfoBar.error(
                title='Error',
                content='Please enter a target username',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not self.save_path:
            InfoBar.error(
                title='Error',
                content='Please choose a save location',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # Get the selected method
        method = self.method_button.text()

        # Prepare parameters based on method
        params = {}
        if method == "Top Posts":
            params['percentage'] = self.percentage_input.value()
        elif method == "Recent Posts":
            params['count'] = self.count_input.value()
        elif method == "Date Range Posts":
            params['since_date'] = self.since_date.getDate().toPyDate()
            params['until_date'] = self.until_date.getDate().toPyDate()

        # Create and start worker thread
        self.worker = DataFetchThread(
            username=self.username_input.text(),
            method=method,
            params=params,
            login_username=self.insta_username.text(),
            login_password=self.insta_password.text(),
            excel_file=self.save_path
        )

        self.worker.progress_update.connect(self.update_progress)
        self.worker.error_signal.connect(self.show_error)
        self.worker.finished.connect(self.analysis_complete)

        # Disable UI elements
        self.analyze_button.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        # Start the thread
        self.worker.start()

    def update_progress(self, value, message):
        """Update progress bar value and message"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message} ({value}%)")

    def show_error(self, error_message):
        """Show error message in command prompt"""
        InfoBar.error(
            title='Error',
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.enable_ui_elements()

    def analysis_complete(self):
        """Handle analysis completion"""
        InfoBar.success(
            title='Success',
            content='Analysis completed successfully!',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        self.enable_ui_elements()

    def enable_ui_elements(self):
        """Re-enable UI elements after analysis"""
        self.analyze_button.setEnabled(True)
        self.progress_bar.hide()

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
        container.setObjectName("containerWidget")
        container_layout = QVBoxLayout(container)

        # Add generation tools
        self.add_generation_tool(container_layout, "Tengr.ai", "Advanced AI model deployment and scaling platform")
        self.add_generation_tool(container_layout, "Runway", "AI-powered creative tools for video editing")
        self.add_generation_tool(container_layout, "Ideogram", "AI image generation and artistic style transfer")
        self.add_generation_tool(container_layout, "Grok", "Advanced AI chatbot with real-time knowledge")
        self.add_generation_tool(container_layout, "Eleven Labs", "State-of-the-art AI voice synthesis")

        self.scroll.setWidget(container)
        self.layout.addWidget(self.scroll)

    def add_generation_tool(self, layout, name, description):
        tool_widget = QWidget()
        tool_widget.setObjectName("toolWidget")
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
            "Tengr.ai": "https://tengr.ai/",
            "Runway": "https://runway.ml/",
            "Ideogram": "https://ideogram.ai/",
            "Grok": "https://grok.x.ai/",
            "Eleven Labs": "https://elevenlabs.io/"
        }
        if tool_name in urls:
            QDesktopServices.openUrl(QUrl(urls[tool_name]))

class InstagramAnalyzerWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, target_account, username=None, password=None):
        super().__init__()
        self.target_account = target_account
        self.username = username
        self.password = password

    def run(self):
        try:
            self.progress.emit("Starting analysis...")
            
            # Simulate analysis delay
            time.sleep(2)
            
            # Mock data for demonstration
            results = {
                "Followers": "10,000",
                "Following": "1,200",
                "Posts": "342",
                "Engagement Rate": "3.2%",
                "Average Likes": "320",
                "Average Comments": "15",
                "Most Active Time": "18:00-20:00 UTC",
                "Top Hashtags": "#photography #nature #travel",
                "Account Type": "Business",
                "Bio Links": "1",
                "Account Created": "2020-01-15"
            }
            
            self.progress.emit("Analysis completed successfully!")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class DataFetchThread(QThread):
    """Thread for fetching Instagram data"""
    progress_update = pyqtSignal(int, str)
    error_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, username, method, params, login_username=None, login_password=None, excel_file=None):
        super().__init__()
        self.username = username
        self.method = method
        self.params = params or {}
        self.login_username = login_username
        self.login_password = login_password
        self.excel_file = excel_file
        self.is_running = True
        
        # Initialize Instagram API client
        self.api = None
        try:
            import instaloader
            self.api = instaloader.Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False
            )
            # Login if credentials provided
            if login_username and login_password:
                self.api.login(login_username, login_password)
        except Exception as e:
            self.error_signal.emit(f"Failed to initialize Instagram API: {str(e)}")

    def fetch_posts(self):
        """Fetch posts based on selected method"""
        try:
            import instaloader
            profile = instaloader.Profile.from_username(self.api.context, self.username)
            posts = []
            total_posts = profile.mediacount
            processed = 0
            
            # Get posts based on method
            if self.method == "Recent Posts":
                count = self.params.get('count', 10)
                for post in profile.get_posts():
                    if not self.is_running:
                        break
                    if len(posts) >= count:
                        break
                    posts.append(post)
                    processed += 1
                    progress = min(100, int((processed / count) * 100))
                    self.progress_update.emit(progress, f"Fetched {processed} of {count} posts")
            
            elif self.method == "Top Posts":
                percentage = self.params.get('percentage', 10)
                target_count = int(total_posts * percentage / 100)
                all_posts = []
                for post in profile.get_posts():
                    if not self.is_running:
                        break
                    all_posts.append(post)
                    processed += 1
                    progress = min(90, int((processed / total_posts) * 100))
                    self.progress_update.emit(progress, f"Fetched {processed} posts")
                
                # Sort by likes + comments and take top percentage
                all_posts.sort(key=lambda x: x.likes + x.comments, reverse=True)
                posts = all_posts[:target_count]
            
            elif self.method == "Date Range Posts":
                since_date = self.params.get('since_date')
                until_date = self.params.get('until_date')
                for post in profile.get_posts():
                    if not self.is_running:
                        break
                    post_date = post.date.date()
                    if since_date <= post_date <= until_date:
                        posts.append(post)
                    processed += 1
                    progress = min(90, int((processed / total_posts) * 100))
                    self.progress_update.emit(progress, f"Fetched {len(posts)} posts")
            
            else:  # All Posts
                for post in profile.get_posts():
                    if not self.is_running:
                        break
                    posts.append(post)
                    processed += 1
                    progress = min(90, int((processed / total_posts) * 100))
                    self.progress_update.emit(progress, f"Fetched {processed} of {total_posts} posts")
            
            return posts
            
        except Exception as e:
            self.error_signal.emit(f"Error fetching posts: {str(e)}")
            return []

    def save_to_excel(self, posts):
        """Save posts to Excel file"""
        try:
            import pandas as pd
            
            # Convert posts to DataFrame
            data = []
            for post in posts:
                data.append({
                    'Shortcode': post.shortcode,
                    'Date': post.date,
                    'Likes': post.likes,
                    'Comments': post.comments,
                    'Caption': post.caption if post.caption else '',
                    'Location': post.location if post.location else '',
                    'URL': f"https://www.instagram.com/p/{post.shortcode}/",
                    'Is Video': post.is_video,
                    'Video View Count': post.video_view_count if post.is_video else 0,
                })
            
            df = pd.DataFrame(data)
            df.to_excel(self.excel_file, index=False)
            return True
        except Exception as e:
            self.error_signal.emit(f"Error saving to Excel: {str(e)}")
            return False

    def run(self):
        """Main thread execution"""
        try:
            if not self.api:
                self.error_signal.emit("Instagram API not initialized")
                return
            
            # Fetch posts
            self.progress_update.emit(10, "Initializing data fetch...")
            posts = self.fetch_posts()
            
            if not self.is_running:
                return
                
            if not posts:
                self.error_signal.emit("No posts found")
                return
            
            # Save to Excel
            self.progress_update.emit(95, "Saving data to Excel...")
            if self.save_to_excel(posts):
                self.progress_update.emit(100, "Analysis complete!")
                self.finished.emit()
            
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.is_running = False

    def stop(self):
        """Stop the thread"""
        self.is_running = False

class RegistrationDialog(QDialog):
    """Registration dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Register')
        self.setFixedSize(400, 500)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)
        
        # Username field
        self.username = LineEdit(self)
        self.username.setPlaceholderText("Username")
        self.username.setClearButtonEnabled(True)
        layout.addWidget(self.username)
        
        # Email field
        self.email = LineEdit(self)
        self.email.setPlaceholderText("Email")
        self.email.setClearButtonEnabled(True)
        layout.addWidget(self.email)
        
        # Password field
        self.password = LineEdit(self)
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(LineEdit.Password)
        self.password.setClearButtonEnabled(True)
        layout.addWidget(self.password)
        
        # Confirm password field
        self.confirm_password = LineEdit(self)
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(LineEdit.Password)
        self.confirm_password.setClearButtonEnabled(True)
        layout.addWidget(self.confirm_password)
        
        # Register button
        self.register_button = PrimaryPushButton('Register', self)
        self.register_button.clicked.connect(self.handle_register)
        layout.addWidget(self.register_button)
        
        # Add stretch at the end
        layout.addStretch()
        
        # Set modern style
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

    def handle_register(self):
        """Handle registration button click"""
        username = self.username.text().strip()
        email = self.email.text().strip()
        password = self.password.text().strip()
        confirm_password = self.confirm_password.text().strip()
        
        # Validate inputs
        if not all([username, email, password, confirm_password]):
            InfoBar.error(
                title='Error',
                content="Please fill in all fields",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        if password != confirm_password:
            InfoBar.error(
                title='Error',
                content="Passwords do not match",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        try:
            # Try to register
            success = self.parent().user_handler.register(username, email, password)
            if success:
                InfoBar.success(
                    title='Success',
                    content="Registration successful! Please login.",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.accept()
            else:
                InfoBar.error(
                    title='Error',
                    content="Registration failed. Username or email may already exist.",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title='Error',
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

class LoginWindow(QWidget):
    """Login window shown after splash screen"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("loginWindow")
        self.login_client = LoginClient()  # Initialize login client
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the login window UI"""
        # Set window properties
        self.setWindowTitle("Login - AI Agency")
        self.setFixedSize(1000, 600)
        self.setWindowFlag(Qt.FramelessWindowHint)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left side - Image
        left_widget = QWidget()
        left_widget.setFixedWidth(500)
        left_widget.setStyleSheet("background-color: #f5f5f5;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        image_label = QLabel()
        resources_dir = os.path.dirname(os.path.dirname(__file__)) + '/resources'
        image_path = os.path.join(resources_dir, 'ai.png')
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap.scaled(500, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(image_label)
        
        # Right side - Login form
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: white;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(50, 50, 50, 50)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(resources_dir, 'ai.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(logo_label)
        
        # Title
        title = TitleLabel('Welcome Back!')
        title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(title)
        
        subtitle = SubtitleLabel('Please login to continue')
        subtitle.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(subtitle)
        
        right_layout.addSpacing(30)
        
        # Form
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        self.username = LineEdit()
        self.username.setPlaceholderText('Username')
        self.username.setClearButtonEnabled(True)
        form_layout.addWidget(self.username)
        
        self.password = LineEdit()
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(LineEdit.Password)
        self.password.setClearButtonEnabled(True)
        form_layout.addWidget(self.password)
        
        self.login_button = PrimaryPushButton('Login')
        self.login_button.clicked.connect(self.handle_login)
        form_layout.addWidget(self.login_button)
        
        register_widget = QWidget()
        register_layout = QHBoxLayout(register_widget)
        register_layout.setContentsMargins(0, 0, 0, 0)
        register_label = BodyLabel("Don't have an account?")
        register_button = TransparentToolButton('Register')
        register_button.clicked.connect(self.show_registration)
        register_layout.addWidget(register_label)
        register_layout.addWidget(register_button)
        register_layout.addStretch()
        form_layout.addWidget(register_widget)
        
        right_layout.addWidget(form_widget)
        right_layout.addStretch()
        
        # Add close button
        close_button = TransparentToolButton()
        close_button.setIcon(QIcon(os.path.join(resources_dir, 'close.png')))
        close_button.clicked.connect(self.close)
        close_button.setFixedSize(32, 32)
        close_button_layout = QHBoxLayout()
        close_button_layout.setContentsMargins(0, 10, 10, 0)
        close_button_layout.addStretch()
        close_button_layout.addWidget(close_button)
        right_layout.insertLayout(0, close_button_layout)
        
        # Add both sides to main layout
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        # Center window
        self.center_on_screen()
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username.text().strip()
        password = self.password.text().strip()
        
        if not username or not password:
            InfoBar.error(
                title='Error',
                content="Please enter both username and password",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # Attempt login
        response, status_code = self.login_client.login(username, password)
        
        if status_code == 200:
            InfoBar.success(
                title='Success',
                content=f'Welcome back, {username}!',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            # Create and show main window
            main_window = MainWindow(self.login_client)
            main_window.show()
            self.close()
        else:
            error_msg = response.get('error', 'Login failed')
            InfoBar.error(
                title='Error',
                content=error_msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def show_registration(self):
        """Show registration dialog"""
        dialog = RegistrationDialog(self)
        dialog.exec_()
    
    def center_on_screen(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

class MainWindow(FramelessWindow):
    """Main window of the application."""
    
    def __init__(self, login_client: LoginClient = None):
        super().__init__()
        self.login_client = login_client
        self.setTitleBar(StandardTitleBar(self))
        self.setWindowTitle("AI Agency")
        
        # Set custom application icon
        app_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'ai.png')
        self.setWindowIcon(QIcon(app_icon_path))
        self.resize(1000, 750)
        
        # Create main layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create and setup navigation interface
        self.navigation = NavigationInterface(self)
        self.navigation.setFixedWidth(200)
        self.main_layout.addWidget(self.navigation)
        
        # Create stacked widget for content
        self.stack_widget = QStackedWidget()
        self.main_layout.addWidget(self.stack_widget)
        
        # Initialize interfaces
        self.tools_interface = ScrollableToolsInterface(self)
        self.analytics_interface = ScrollableAnalyticsInterface(self)
        self.generation_interface = ScrollableGenerationInterface(self)
        self.settings_interface = SettingInterface(self)
        
        # Add interfaces to stack
        self.stack_widget.addWidget(self.tools_interface)
        self.stack_widget.addWidget(self.analytics_interface)
        self.stack_widget.addWidget(self.generation_interface)
        self.stack_widget.addWidget(self.settings_interface)
        
        # Create container widget and set layout
        container = QWidget(self)
        container.setLayout(self.main_layout)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(container)
        
        # Navigation icons
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        tools_icon_path = os.path.join(resources_dir, 'ai.png')
        analytics_icon_path = os.path.join(resources_dir, 'ig.png')
        generation_icon_path = os.path.join(resources_dir, 'generation.png')
        settings_icon_path = os.path.join(resources_dir, 'settings.png')
        
        # Add navigation items
        self.navigation.addItem(
            routeKey='tools',
            icon=QIcon(tools_icon_path),
            text='AI Tools',
            onClick=lambda: self.stack_widget.setCurrentWidget(self.tools_interface),
            position=NavigationItemPosition.TOP
        )
        
        self.navigation.addItem(
            routeKey='analytics',
            icon=QIcon(analytics_icon_path),
            text='Instagram Analytics',
            onClick=lambda: self.stack_widget.setCurrentWidget(self.analytics_interface),
            position=NavigationItemPosition.TOP
        )
        
        self.navigation.addItem(
            routeKey='generation',
            icon=QIcon(generation_icon_path),
            text='AI Generation',
            onClick=lambda: self.stack_widget.setCurrentWidget(self.generation_interface),
            position=NavigationItemPosition.TOP
        )
        
        # Add logout button at the bottom
        logout_button = PushButton('Logout')
        logout_button.clicked.connect(self.handle_logout)
        self.navigation.addWidget(
            routeKey='logout',
            widget=logout_button,
            onClick=self.handle_logout,
            position=NavigationItemPosition.BOTTOM
        )
        
        self.navigation.addItem(
            routeKey='settings',
            icon=QIcon(settings_icon_path),
            text='Settings',
            onClick=lambda: self.stack_widget.setCurrentWidget(self.settings_interface),
            position=NavigationItemPosition.BOTTOM
        )
        
        # Set theme
        setTheme(Theme.AUTO)
    
    def handle_logout(self):
        """Handle logout action"""
        if self.login_client:
            self.login_client.logout()
        
        # Create and show login window
        login_window = LoginWindow()
        login_window.show()
        
        # Close main window
        self.close()

def init_app():
    # Enable high DPI display
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Instagram Analytics")
    app.setOrganizationName("AI Agency")
    
    # Set theme
    setTheme(Theme.AUTO)
    
    # Show splash screen
    splash_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'splash.png'))
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    
    # Process events to ensure splash screen is displayed
    app.processEvents()
    
    # Create and show login window
    login_window = LoginWindow()
    login_window.show()
    splash.finish(login_window)
    
    sys.exit(app.exec_())