import sys
from PySide6.QtWidgets import QApplication
from client.ui import MainWindow

def main():
    """Point d'entrée de l'application client"""
    app = QApplication(sys.argv)
    app.setApplicationName("Stark Recruitment - Interview Client")
    app.setOrganizationName("Stark Solutions")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()