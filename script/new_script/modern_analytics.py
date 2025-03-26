# modern_analytics.py
import sys
import os
import json
import requests
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QDate, QDateTime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QFileDialog, QTextEdit, QFormLayout, QComboBox, QDateEdit, QLineEdit, QGroupBox,
    QSpinBox, QGridLayout, QDockWidget, QDateTimeEdit, QCalendarWidget
)
from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QColor, QBrush

from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, FluentIcon, setTheme, Theme, setThemeColor,
    PushButton, ToolButton, TransparentToolButton, LineEdit, PrimaryPushButton, SpinBox,
    ProgressBar, PushSettingCard, OptionsSettingCard, TitleLabel, CaptionLabel, SubtitleLabel,
    TextEdit, DateTimeEdit, MessageBox, SplashScreen, ScrollArea, CardWidget, IconWidget,
    FlowLayout, BodyLabel, ComboBoxSettingCard, CalendarPicker, PillPushButton, DropDownPushButton,
    RoundMenu, Action, TransparentPushButton, PrimarySplitPushButton, InfoBar
)

from setting_interface import SettingInterface
from user_data_handler import UserDataHandler
from config_setting import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from post_fetcher import InstagramFetcher, PostData

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

def init_app():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication.instance()
    app.setApplicationName("ModernAnalytics")
    app.setStyleSheet("")  # Fluent widgets handle styling

class FeatureCard(CardWidget):
    clicked = pyqtSignal()

    def __init__(self, icon_path, title, description, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setFixedSize(240, 260)
        
        layout = QVBoxLayout(self)
        self.iconLabel = IconWidget(FluentIcon.APPLICATION, self)
        self.iconLabel.setFixedSize(120, 120)
        
        if os.path.exists(icon_path):
            self.iconLabel.setIcon(QIcon(icon_path))
        else:
            self.iconLabel.setIcon(FluentIcon.INFO)

        self.titleLabel = TitleLabel(title, self)
        self.descLabel = CaptionLabel(description, self)
        self.descLabel.setWordWrap(True)
        
        self.actionButton = PrimaryPushButton('Explore', self)
        self.actionButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url)))

        layout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.descLabel)
        layout.addWidget(self.actionButton)

class AnalyticsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        mainLayout = QVBoxLayout(self)
        
        # Input Section
        inputGroup = QGroupBox("Analysis Parameters")
        formLayout = QFormLayout(inputGroup)
        
        self.usernameInput = LineEdit()
        self.methodCombo = ComboBoxSettingCard(
            cfg.method, FluentIcon.SCROLL,
            'Analysis Method', 
            ['All Posts', 'Top Posts', 'Recent Posts', 'Date Range'],
            parent=self
        )
        
        # Date inputs
        self.sinceDate = CalendarPicker(self)
        self.untilDate = CalendarPicker(self)
        
        # Progress bar
        self.progressBar = ProgressBar()
        self.progressBar.setVisible(False)
        
        # Action buttons
        self.analyzeBtn = PrimaryPushButton("Start Analysis")
        self.exportBtn = PushButton("Export Results")
        
        formLayout.addRow("Username:", self.usernameInput)
        formLayout.addRow("Method:", self.methodCombo)
        formLayout.addRow("Since:", self.sinceDate)
        formLayout.addRow("Until:", self.untilDate)
        
        mainLayout.addWidget(inputGroup)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(self.analyzeBtn)
        mainLayout.addWidget(self.exportBtn)

class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agency Analytics Suite")
        self.resize(1200, 800)
        
        # Interfaces
        self.analyticsInterface = AnalyticsInterface()
        self.settingsInterface = SettingInterface()
        
        # Navigation
        self.addSubInterface(
            self.analyticsInterface,
            FluentIcon.CHART,
            "Analytics",
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.settingsInterface,
            FluentIcon.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM
        )
        
        # Theme configuration
        setTheme(Theme.AUTO)
        self.setMicaEffectEnabled(True)
        setThemeColor('#0078D4')

if __name__ == '__main__':
    init_app()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())