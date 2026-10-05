import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config import APP_NAME, APP_SUBTITLE, STYLES_DIR
from database.db_manager import DatabaseManager
from database.migrations import MigrationManager
from views.login_view import LoginDialog
from views.main_window import MainWindow
from services.auth_service import AuthService
from utils.logger import log_info, log_error

def main():
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Set default modern font (Segoe UI / Arial)
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    log_info("Starting application...")

    # Run Database Setup & Schema Migrations
    try:
        db = DatabaseManager()
        MigrationManager.run_migrations()
    except Exception as e:
        log_error(f"Fatal startup error: {e}", exc_info=True)
        sys.exit(1)

    main_win = None

    def start_session():
        nonlocal main_win
        main_win = MainWindow()
        main_win.update_user_info()
        main_win.logout_requested.connect(show_login)
        main_win.show()

    def show_login():
        nonlocal main_win
        if main_win:
            main_win.close()
            main_win = None

        login_dialog = LoginDialog()
        login_dialog.login_successful.connect(start_session)
        if login_dialog.exec_() != LoginDialog.Accepted and not AuthService.is_authenticated():
            sys.exit(0)

    show_login()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
