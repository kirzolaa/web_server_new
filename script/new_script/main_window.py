import sys
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import MSFluentWindow, NavigationItemPosition, FluentIcon, setTheme, Theme

class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Modern Analytics Suite')
        self.resize(1200, 800)
        
        # Create sub interfaces
        self.dashboardInterface = DashboardInterface(self)
        self.analyticsInterface = AnalyticsInterface(self)
        self.settingsInterface = SettingsInterface(self)

        # Add navigation items
        self.addSubInterface(self.dashboardInterface, FluentIcon.HOME, 'Dashboard')
        self.addSubInterface(self.analyticsInterface, FluentIcon.CHART, 'Analytics')
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # Initialize theme
        setTheme(Theme.AUTO)

class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Add dashboard components here

class AnalyticsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Add analytics components here

class SettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Add settings components here

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName('ModernAnalytics')
    app.setStyleSheet(qfluentwidgets__rc)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
