from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog, QTabWidget,
    QGroupBox, QFormLayout, QLineEdit, QHeaderView
)
from PyQt5.QtCore import Qt
import qtawesome as qta
from pathlib import Path

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from services.backup_service import BackupService
from services.auth_service import AuthService
from database.db_manager import DatabaseManager
from widgets.custom_table import CustomTableWidget

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        title_lbl = QLabel("Cài đặt & Quản trị Hệ thống")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        main_layout.addWidget(title_lbl)

        # Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_WHITE};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background: #E9ECEF;
                color: {COLOR_TEXT_MAIN};
                font-weight: 600;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {COLOR_PRIMARY_BURGUNDY};
                color: {COLOR_WHITE};
            }}
        """)

        # Build 3 Settings Tabs
        self.tab_backup = self._build_backup_tab()
        self.tab_audit = self._build_audit_tab()
        self.tab_users = self._build_users_tab()

        self.tabs.addTab(self.tab_backup, "Sao lưu & Khôi phục DB")
        self.tabs.addTab(self.tab_audit, "Nhật ký hoạt động")
        self.tabs.addTab(self.tab_users, "Quản lý Tài khoản & Phân quyền")

        main_layout.addWidget(self.tabs, stretch=1)

    def _build_backup_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        btn_bar = QHBoxLayout()
        self.btn_create_backup = QPushButton("  Tạo bản Sao lưu Database mới")
        self.btn_create_backup.setFixedHeight(38)
        self.btn_create_backup.setCursor(Qt.PointingHandCursor)
        self.btn_create_backup.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY_BURGUNDY}; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px; }}")
        self.btn_create_backup.clicked.connect(self.create_backup_action)
        btn_bar.addWidget(self.btn_create_backup)

        self.btn_restore_file = QPushButton("  Khôi phục từ File (.db)...")
        self.btn_restore_file.setFixedHeight(38)
        self.btn_restore_file.setCursor(Qt.PointingHandCursor)
        self.btn_restore_file.setStyleSheet("QPushButton { background-color: #198754; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px; }")
        self.btn_restore_file.clicked.connect(self.restore_backup_action)
        btn_bar.addWidget(self.btn_restore_file)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        layout.addWidget(QLabel("Danh sách các bản Sao lưu tự động trong hệ thống:"))
        self.backup_table = CustomTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Tên File Sao lưu", "Kích thước (MB)", "Thời gian tạo", "Đường dẫn chi tiết"])
        self.backup_table.set_column_widths({0: 240, 1: 120, 2: 160})
        layout.addWidget(self.backup_table, stretch=1)

        self.load_backups_table()
        return widget

    def _build_audit_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.audit_table = CustomTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels(["STT", "Thời gian", "Người dùng", "Hành động", "Chi tiết thao tác"])
        self.audit_table.set_column_widths({0: 45, 1: 150, 2: 130, 3: 140})
        layout.addWidget(self.audit_table, stretch=1)

        self.load_audit_logs()
        return widget

    def _build_users_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.users_table = CustomTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels(["STT", "Tên đăng nhập", "Họ và tên cán bộ", "Vai trò", "Chức danh", "Trạng thái"])
        self.users_table.set_column_widths({0: 45, 1: 130, 2: 180, 3: 160, 4: 150})
        layout.addWidget(self.users_table, stretch=1)

        self.load_users_table()
        return widget

    def load_backups_table(self):
        backups = BackupService.list_backups()
        self.backup_table.setRowCount(len(backups))
        for r_idx, b in enumerate(backups):
            self.backup_table.setItem(r_idx, 0, QTableWidgetItem(b["filename"]))
            self.backup_table.setItem(r_idx, 1, QTableWidgetItem(f"{b['size_mb']} MB"))
            self.backup_table.setItem(r_idx, 2, QTableWidgetItem(b["created_at"]))
            self.backup_table.setItem(r_idx, 3, QTableWidgetItem(b["filepath"]))

    def load_audit_logs(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")
            logs = cursor.fetchall()
            self.audit_table.setRowCount(len(logs))
            for r_idx, l in enumerate(logs):
                self.audit_table.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
                self.audit_table.setItem(r_idx, 1, QTableWidgetItem(l["created_at"] or ""))
                self.audit_table.setItem(r_idx, 2, QTableWidgetItem(l["username"] or ""))
                self.audit_table.setItem(r_idx, 3, QTableWidgetItem(l["action"] or ""))
                self.audit_table.setItem(r_idx, 4, QTableWidgetItem(l["details"] or ""))
        finally:
            conn.close()

    def load_users_table(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT u.*, r.role_name FROM users u JOIN roles r ON u.role_id = r.id ORDER BY u.id ASC")
            users = cursor.fetchall()
            self.users_table.setRowCount(len(users))
            for r_idx, u in enumerate(users):
                self.users_table.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
                self.users_table.setItem(r_idx, 1, QTableWidgetItem(u["username"]))
                self.users_table.setItem(r_idx, 2, QTableWidgetItem(u["full_name"]))
                self.users_table.setItem(r_idx, 3, QTableWidgetItem(u["role_name"]))
                self.users_table.setItem(r_idx, 4, QTableWidgetItem(u["position"] or ""))
                st = "Đang hoạt động" if u["is_active"] else "Bị khóa"
                self.users_table.setItem(r_idx, 5, QTableWidgetItem(st))
        finally:
            conn.close()

    def create_backup_action(self):
        if not AuthService.check_permission("BACKUP_RESTORE"):
            QMessageBox.warning(self, "Từ chối truy cập", "Bạn không có quyền Sao lưu Database.")
            return

        success, msg, path = BackupService.create_backup()
        if success:
            AuthService.log_audit_action("BACKUP_DB", "SYSTEM", None, "Tạo sao lưu cơ sở dữ liệu thành công.")
            QMessageBox.information(self, "Thành công", msg)
            self.load_backups_table()
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def restore_backup_action(self):
        if not AuthService.check_permission("BACKUP_RESTORE"):
            QMessageBox.warning(self, "Từ chối truy cập", "Bạn không có quyền Phục hồi Database.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Sao lưu Database", "", "SQLite Database (*.db)")
        if not file_path:
            return

        reply = QMessageBox.warning(
            self,
            "Xác nhận Khôi phục Cơ sở dữ liệu",
            "CẢNH BÁO: Phục hồi Database sẽ ghi đè dữ liệu hiện tại bằng dữ liệu trong file sao lưu.\nHệ thống sẽ tự tạo bản ảnh chụp khẩn cấp trước khi khôi phục.\n\nBạn có chắc chắn muốn tiếp tục?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = BackupService.restore_backup(file_path)
            if success:
                AuthService.log_audit_action("RESTORE_DB", "SYSTEM", None, f"Khôi phục cơ sở dữ liệu từ file '{Path(file_path).name}'.")
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.critical(self, "Lỗi", msg)
