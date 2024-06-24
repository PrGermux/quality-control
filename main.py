import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtCore import Qt
from WEK import WEK
from EPOL0E import EPOL0E
from ISD1A import ISD1A

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quality Control")
        self.setGeometry(0, 0, 800, 1000)
        self.setWindowIcon(QIcon(resource_path('icon.png')))

        self.apply_dark_theme() # Apply dark theme

        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)

        self.WEK = WEK()
        self.EPOL0E = EPOL0E()
        self.ISD1A = ISD1A()

        self.tabWidget.addTab(self.WEK, "WEK")
        self.tabWidget.addTab(self.EPOL0E, "EPOL0E")
        self.tabWidget.addTab(self.ISD1A, "ISD1A")

        self.make_tab_titles_bold()

    def make_tab_titles_bold(self):
        # Set the font for the tab titles to be bold
        font = QFont()  # Create a new font object
        font.setBold(True)  # Set the font to be bold
        font.setPointSize(11)
        
        # Apply the bold font to each tab title
        for i in range(self.tabWidget.count()):
            self.tabWidget.tabBar().setFont(font)

    def apply_dark_theme(self):
        # Set the application to use a dark color scheme.
        app.setStyle("Fusion")

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        app.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    mainApp = MainApp()
    mainApp.show()
    sys.exit(app.exec_())