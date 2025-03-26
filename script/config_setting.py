# coding:utf-8
from enum import Enum
from PyQt5.QtCore import QStandardPaths, Qt
from PyQt5.QtGui import QColor, QGuiApplication
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                          RangeConfigItem, ColorConfigItem, FolderListValidator, EnumSerializer,
                          FolderValidator, ConfigSerializer, QConfig, ConfigItem, OptionsConfigItem,
                          BoolValidator, OptionsValidator, RangeValidator)


class SongQuality(Enum):
    """ Online song quality enumeration class """

    STANDARD = "Standard quality"
    HIGH = "High quality"
    SUPER = "Super quality"
    LOSSLESS = "Lossless quality"


class MvQuality(Enum):
    """ MV quality enumeration class """

    FULL_HD = "Full HD"
    HD = "HD"
    SD = "SD"
    LD = "LD"


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = "Chinese Simplified"
    CHINESE_TRADITIONAL = "Chinese Traditional"
    ENGLISH = "English"
    AUTO = "Auto"


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(value) if value != "Auto" else Language.AUTO


class Config(QConfig):
    """ Config of application """

    # folders
    musicFolders = ConfigItem(
        "Folders", "LocalMusic", [], FolderListValidator())
    downloadFolder = ConfigItem(
        "Download", "Folder", "", FolderValidator())

    # online
    onlineSongQuality = OptionsConfigItem(
        "Online", "SongQuality", SongQuality.STANDARD, OptionsValidator(SongQuality), EnumSerializer(SongQuality))
    onlinePageSize = RangeConfigItem(
        "Online", "PageSize", 30, RangeValidator(0, 50))
    onlineMvQuality = OptionsConfigItem(
        "Online", "MvQuality", MvQuality.FULL_HD, OptionsValidator(MvQuality), EnumSerializer(MvQuality))

    # main window
    enableAcrylicBackground = ConfigItem(
        "MainWindow", "EnableAcrylicBackground", False, BoolValidator())
    minimizeToTray = ConfigItem(
        "MainWindow", "MinimizeToTray", True, BoolValidator())
    playBarColor = ColorConfigItem("MainWindow", "PlayBarColor", "#225C7F")
    recentPlaysNumber = RangeConfigItem(
        "MainWindow", "RecentPlayNumbers", 300, RangeValidator(10, 300))
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([
            "Auto", "100%", "125%", "150%", "175%", "200%"
        ]))
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO,
        OptionsValidator([Language.AUTO, Language.CHINESE_SIMPLIFIED, Language.CHINESE_TRADITIONAL, Language.ENGLISH]),
        LanguageSerializer()
    )

    # desktop lyric
    deskLyricHighlightColor = ColorConfigItem(
        "DesktopLyric", "HighlightColor", "#0099BC")
    deskLyricFontSize = RangeConfigItem(
        "DesktopLyric", "FontSize", 50, RangeValidator(15, 50))
    deskLyricStrokeSize = RangeConfigItem(
        "DesktopLyric", "StrokeSize", 5, RangeValidator(0, 20))
    deskLyricStrokeColor = ColorConfigItem(
        "DesktopLyric", "StrokeColor", QColor(Qt.black))
    deskLyricFontFamily = ConfigItem(
        "DesktopLyric", "FontFamily", "Microsoft YaHei")
    deskLyricAlignment = OptionsConfigItem(
        "DesktopLyric", "Alignment", "Center", OptionsValidator(["Center", "Left", "Right"]))

    # analysis methods
    methodSelection = OptionsConfigItem(
        "Analysis", "Method", "Recent Posts",
        OptionsValidator(["Recent Posts", "Top Posts", "Date Range Posts"])
    )
    topPostsPercentage = RangeConfigItem(
        "Analysis", "TopPostsPercentage", 10, RangeValidator(1, 100)
    )
    recentPostsCount = RangeConfigItem(
        "Analysis", "RecentPostsCount", 10, RangeValidator(1, 1000)
    )
    requestDelay = RangeConfigItem(
        "Analysis", "RequestDelay", 3, RangeValidator(1, 60)
    )

    # software update
    checkUpdateAtStartUp = ConfigItem(
        "Update", "CheckUpdateAtStartUp", True, BoolValidator())

    @property
    def desktopLyricFont(self):
        """ get the desktop lyric font """
        font = QColor(self.deskLyricFontFamily.value)
        font.setPixelSize(self.deskLyricFontSize.value)
        return font

    @desktopLyricFont.setter
    def desktopLyricFont(self, font: QColor):
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
        self.deskLyricFontFamily.value = font.name()
        self.deskLyricFontSize.value = max(15, int(font.pointSize()*dpi/72))
        self.save()


YEAR = 2025
AUTHOR = "TerminalThor"
VERSION = "1.1.0"
HELP_URL = "https://pyqt-fluent-widgets.readthedocs.io"
FEEDBACK_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues"
RELEASE_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/releases/latest"


cfg = Config()
qconfig.load('config/config.json', cfg)