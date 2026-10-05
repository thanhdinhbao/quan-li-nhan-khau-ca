from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import qtawesome as qta

from config import (
    APP_NAME, APP_SUBTITLE, COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED,
    COLOR_WHITE, COLOR_NAVY_SIDEBAR, COLOR_BG_LIGHT, COLOR_TEXT_MUTED, DB_PATH
)
from widgets.sidebar import SidebarWidget
from views.dashboard import DashboardView
from views.person_view import PersonView
from views.household_view import HouseholdView
from views.area_view import AreaView
from views.import_view import ImportView
from views.export_view import ExportView
from views.advanced_search_view import AdvancedSearchView
from views.settings_view import SettingsView
from services.auth_service import AuthService
from database.db_manager import DatabaseManager

class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - {APP_SUBTITLE}")
        self.resize(1366, 768)
        self.setMinimumSize(1200, 700)

        # Central Main Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Header Bar ( Burgundy #A6192E )
        header_frame = QFrame()
        header_frame.setFixedHeight(64)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_PRIMARY_BURGUNDY};
                border-bottom: 2px solid {COLOR_SECONDARY_DARK_RED};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(12)

        # Header Logo Icon
        logo_lbl = QLabel()
        try:
            logo_lbl.setPixmap(qta.icon('fa5s.shield-alt', color=COLOR_WHITE).pixmap(36, 36))
        except Exception:
            logo_lbl.setText("🛡️")
            logo_lbl.setStyleSheet("font-size: 28px; color: white;")
        header_layout.addWidget(logo_lbl)

        # Header Titles
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        main_title = QLabel(APP_NAME)
        main_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 0.5px;")

        sub_title = QLabel(APP_SUBTITLE)
        sub_title.setStyleSheet("color: #FFCCD5; font-size: 12px; font-weight: 600;")

        title_box.addWidget(main_title)
        title_box.addWidget(sub_title)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # User Profile Block
        self.user_lbl = QLabel("Nguyễn Văn An\nCán bộ quản lý")
        self.user_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_lbl.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 600;")
        header_layout.addWidget(self.user_lbl)

        user_icon = QLabel()
        try:
            user_icon.setPixmap(qta.icon('fa5s.user-circle', color=COLOR_WHITE).pixmap(32, 32))
        except Exception:
            user_icon.setText("👤")
        header_layout.addWidget(user_icon)

        header_layout.addSpacing(16)

        # Realtime Clock Widget
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet("color: #FFCCD5; font-size: 12px; font-weight: 500;")
        header_layout.addWidget(self.clock_lbl)

        header_layout.addSpacing(16)

        # Logout Button
        self.logout_btn = QPushButton(" Đăng xuất")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setFixedHeight(34)
        try:
            self.logout_btn.setIcon(qta.icon('fa5s.sign-out-alt', color=COLOR_WHITE))
        except Exception:
            pass
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.logout_btn.clicked.connect(self.confirm_logout)
        header_layout.addWidget(self.logout_btn)

        root_layout.addWidget(header_frame)

        # 2. Main Middle Workspace Layout (Sidebar + Stacked Content)
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # Sidebar Left
        self.sidebar = SidebarWidget()
        self.sidebar.menu_selected.connect(self.switch_page)
        workspace_layout.addWidget(self.sidebar)

        # Central Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        # Page 0: Dashboard
        self.dashboard_page = DashboardView()
        self.stacked_widget.addWidget(self.dashboard_page)

        # Page 1: Person Management
        self.person_page = PersonView()
        self.stacked_widget.addWidget(self.person_page)

        # Page 2: Household Management
        self.household_page = HouseholdView()
        self.stacked_widget.addWidget(self.household_page)

        # Page 3: Area Management
        self.area_page = AreaView()
        self.stacked_widget.addWidget(self.area_page)

        # Page 4: Import Excel
        self.import_page = ImportView()
        self.stacked_widget.addWidget(self.import_page)

        # Page 5: Export Excel
        self.export_page = ExportView()
        self.stacked_widget.addWidget(self.export_page)

        # Page 6: Thống kê báo cáo & Tra cứu nâng cao
        self.reports_page = AdvancedSearchView()
        self.stacked_widget.addWidget(self.reports_page)

        # Page 7: Nhật ký hoạt động
        self.audit_page = SettingsView()
        self.stacked_widget.addWidget(self.audit_page)

        # Page 8: Sao lưu và phục hồi
        self.backup_page = SettingsView()
        self.stacked_widget.addWidget(self.backup_page)

        # Page 9: Cài đặt hệ thống
        self.settings_page = SettingsView()
        self.stacked_widget.addWidget(self.settings_page)

        workspace_layout.addWidget(self.stacked_widget, stretch=1)
        root_layout.addLayout(workspace_layout, stretch=1)

        # 3. Bottom Status Bar (Footer)
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #E9ECEF; color: #495057; font-size: 12px; }")
        self.setStatusBar(self.status_bar)

        self.db_status_lbl = QLabel(f" Cơ sở dữ liệu: {DB_PATH.name}")
        self.record_count_lbl = QLabel("Tổng số bản ghi: 0")
        self.sys_status_lbl = QLabel("● Hệ thống hoạt động bình thường")
        self.sys_status_lbl.setStyleSheet("color: #198754; font-weight: 700;")

        self.status_bar.addWidget(self.db_status_lbl)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.record_count_lbl)
        self.status_bar.addPermanentWidget(self.sys_status_lbl)

        # Realtime Timer (Updates every 1s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def update_user_info(self):
        user = AuthService.get_current_user()
        if user:
            self.user_lbl.setText(f"{user.full_name}\n{user.position or user.role_name}")
        else:
            self.user_lbl.setText("Chưa đăng nhập")
        self.update_status_bar()

    def update_clock(self):
        now = datetime.now()
        day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        weekday = day_names[now.weekday()]
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d/%m/%Y")
        self.clock_lbl.setText(f"🕒 {time_str}\n{weekday}, {date_str}")

    def update_status_bar(self):
        try:
            db = DatabaseManager()
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM persons WHERE is_deleted = 0")
            count = cursor.fetchone()["count"]
            self.record_count_lbl.setText(f"Tổng số bản ghi: {count}")
            conn.close()
        except Exception:
            pass

    def switch_page(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 0:
            self.dashboard_page.load_data()
        elif index == 1:
            self.person_page.load_data()
        elif index == 2:
            self.household_page.load_data()
        elif index == 3:
            self.area_page.load_data()
        self.update_status_bar()

    def confirm_logout(self):
        reply = QMessageBox.question(
            self,
            "Xác nhận đăng xuất",
            "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            AuthService.logout()
            self.logout_requested.emit()
