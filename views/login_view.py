from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import qtawesome as qta
from config import (
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_NAVY_SIDEBAR,
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_BORDER
)
from services.auth_service import AuthService

class LoginDialog(QDialog):
    login_successful = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng nhập - Hệ thống Quản lý Nhân khẩu Cấp xã")
        self.setFixedSize(450, 520)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.CustomizeWindowHint)
        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Main Card Frame
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)

        # Emblem Icon
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        try:
            icon_lbl.setPixmap(qta.icon('fa5s.shield-alt', color=COLOR_PRIMARY_BURGUNDY).pixmap(56, 56))
        except Exception:
            icon_lbl.setText("🛡️")
            icon_lbl.setStyleSheet(f"font-size: 48px; color: {COLOR_PRIMARY_BURGUNDY};")
        card_layout.addWidget(icon_lbl)

        # Title Block
        title_lbl = QLabel("HỆ THỐNG QUẢN LÝ NHÂN KHẨU")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_BURGUNDY}; font-size: 16px; font-weight: 800;")

        subtitle_lbl = QLabel("CÔNG AN PHƯỜNG NÔNG TRANG")
        subtitle_lbl.setAlignment(Qt.AlignCenter)
        subtitle_lbl.setStyleSheet(f"color: {COLOR_NAVY_SIDEBAR}; font-size: 13px; font-weight: 700;")

        card_layout.addWidget(title_lbl)
        card_layout.addWidget(subtitle_lbl)
        card_layout.addSpacing(10)

        # Username Field
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText(" Tên đăng nhập")
        self.user_input.setHeight = 42
        self.user_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_PRIMARY_BURGUNDY};
            }}
        """)
        card_layout.addWidget(self.user_input)

        # Password Field
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText(" Mật khẩu")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_PRIMARY_BURGUNDY};
            }}
        """)
        card_layout.addWidget(self.pass_input)

        # Error Message Label
        self.error_lbl = QLabel("")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.setStyleSheet("color: #DC3545; font-size: 12px; font-weight: 600;")
        self.error_lbl.hide()
        card_layout.addWidget(self.error_lbl)

        # Login Button
        self.login_btn = QPushButton("ĐĂNG NHẬP HỆ THỐNG")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setFixedHeight(44)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_BURGUNDY};
                color: {COLOR_WHITE};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SECONDARY_DARK_RED};
            }}
            QPushButton:pressed {{
                background-color: #690000;
            }}
        """)
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        main_layout.addWidget(card)

        # Shortcuts
        self.pass_input.returnPressed.connect(self.handle_login)
        self.user_input.returnPressed.connect(self.handle_login)

        # Default focus
        self.user_input.setFocus()

    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            self.show_error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            return

        success, msg, user = AuthService.login(username, password)
        if success:
            self.error_lbl.hide()
            self.accept()
            self.login_successful.emit()
        else:
            self.show_error(msg)

    def show_error(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.show()
