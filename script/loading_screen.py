from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from qfluentwidgets import BodyLabel, CardWidget
import os

class LoadingScreen(CardWidget):
    def __init__(self, parent=None, message="Initializing", dot_count=3, interval=500):
        """
        A modern loading screen with animated dots and centered logo.
        
        Args:
            parent: Parent widget
            message: Base message to display (default: "Initializing")
            dot_count: Maximum number of dots to show (default: 3)
            interval: Animation interval in milliseconds (default: 500)
        """
        super().__init__(parent)
        self.message = message
        self.dot_count = dot_count
        self.current_dots = 0
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # Add logo
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'ai.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.logo_label)
        
        # Create loading text label
        self.loading_label = BodyLabel(self.message)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.loading_label)
        
        # Set up timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dots)
        self.timer.setInterval(interval)
        
        # Style
        self.setFixedSize(250, 200)  # Increased size to accommodate logo
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Initially hide the loading screen
        self.hide()
        
    def start(self):
        """Start the loading animation."""
        self.timer.start()
        self.show()  # Make sure the widget is visible
        
    def stop(self):
        """Stop the loading animation."""
        self.timer.stop()
        self.loading_label.setText(self.message)
        self.hide()
        
    def update_dots(self):
        """Update the dots in the loading message."""
        self.current_dots = (self.current_dots + 1) % (self.dot_count + 1)
        dots = "." * self.current_dots
        self.loading_label.setText(f"{self.message}{dots}")
        
    def set_message(self, message):
        """Change the loading message."""
        self.message = message
        self.loading_label.setText(message)
