from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidgetItem, QMessageBox, QFrame, QHeaderView
)
from PyQt5.QtCore import Qt
import qtawesome as qta

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from widgets.search_box import SearchBox
from widgets.custom_table import CustomTableWidget
from controllers.household_controller import HouseholdController
from controllers.area_controller import AreaController
from views.household_dialog import HouseholdDialog
from services.auth_service import AuthService

class HouseholdView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hh_ctrl = HouseholdController()
        self.area_ctrl = AreaController()

        self.current_page = 1
        self.page_size = 20
        self.total_records = 0

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Top Bar
        top_bar = QHBoxLayout()
        title_lbl = QLabel("Quản lý Hộ gia đình")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        top_bar.addWidget(title_lbl)

        top_bar.addStretch()

        self.add_btn = QPushButton("  Tạo hộ mới")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(36)
        try:
            self.add_btn.setIcon(qta.icon('fa5s.plus-circle', color=COLOR_WHITE))
        except Exception:
            pass
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_BURGUNDY};
                color: {COLOR_WHITE};
                font-weight: 700;
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SECONDARY_DARK_RED};
            }}
        """)
        self.add_btn.clicked.connect(self.open_add_dialog)
        top_bar.addWidget(self.add_btn)

        self.refresh_btn = QPushButton("  Làm mới")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setFixedHeight(36)
        try:
            self.refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color=COLOR_NAVY_SIDEBAR))
        except Exception:
            pass
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_WHITE};
                color: {COLOR_NAVY_SIDEBAR};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #E9ECEF; }}
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        top_bar.addWidget(self.refresh_btn)

        main_layout.addLayout(top_bar)

        # Filter Bar
        filter_card = QFrame()
        filter_card.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        self.search_box = SearchBox(placeholder="Tìm theo Mã hộ, Số hộ, Địa chỉ, Tên chủ hộ...")
        self.search_box.setMinimumWidth(320)
        self.search_box.searched.connect(lambda: self.load_data())
        filter_layout.addWidget(self.search_box)

        self.combo_area = QComboBox()
        self.combo_area.setFixedWidth(180)
        self.combo_area.addItem("Tất cả khu vực", 0)
        areas = self.area_ctrl.get_all_areas()
        for a in areas:
            self.combo_area.addItem(a.name, a.id)
        self.combo_area.currentIndexChanged.connect(lambda: self.load_data())
        filter_layout.addWidget(self.combo_area)

        filter_layout.addStretch()
        main_layout.addWidget(filter_card)

        # Custom Table Widget
        self.table = CustomTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "STT", "Mã hộ", "Số hộ khẩu", "Khu vực", "Địa chỉ chi tiết", "Chủ hộ", "Số thành viên", "Trạng thái"
        ])
        self.table.set_column_widths({0: 45, 1: 100, 2: 110, 3: 120, 5: 160, 6: 100, 7: 100})
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        main_layout.addWidget(self.table, stretch=1)

        self.load_data()

    def load_data(self):
        kw = self.search_box.text()
        area_id = self.combo_area.currentData()

        households, total = self.hh_ctrl.get_households_paged(
            keyword=kw,
            area_id=area_id,
            page=self.current_page,
            page_size=self.page_size
        )
        self.total_records = total
        self.table.setRowCount(len(households))

        start_idx = (self.current_page - 1) * self.page_size
        for r_idx, h in enumerate(households):
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(start_idx + r_idx + 1)))

            code_item = QTableWidgetItem(h.household_code)
            code_item.setData(Qt.UserRole, h.id)
            self.table.setItem(r_idx, 1, code_item)

            self.table.setItem(r_idx, 2, QTableWidgetItem(h.household_number or ""))
            self.table.setItem(r_idx, 3, QTableWidgetItem(h.area_name or ""))
            self.table.setItem(r_idx, 4, QTableWidgetItem(h.full_address or ""))
            self.table.setItem(r_idx, 5, QTableWidgetItem(h.head_full_name or "Chưa có"))
            self.table.setItem(r_idx, 6, QTableWidgetItem(f"{h.member_count} người"))

            status_item = QTableWidgetItem("Đang hoạt động" if h.status == "ACTIVE" else h.status)
            status_item.setForeground(Qt.darkGreen if h.status == "ACTIVE" else Qt.gray)
            self.table.setItem(r_idx, 7, status_item)

    def on_row_double_clicked(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 1)
            hh_id = item.data(Qt.UserRole)
            hh = self.hh_ctrl.get_household_details(hh_id)
            if hh:
                dlg = HouseholdDialog(household=hh, parent=self)
                if dlg.exec_() == HouseholdDialog.Accepted:
                    self.load_data()

    def open_add_dialog(self):
        if not AuthService.check_permission("HOUSEHOLD_ADD"):
            QMessageBox.warning(self, "Từ chối truy cập", "Bạn không có quyền tạo hộ gia đình mới.")
            return
        dlg = HouseholdDialog(parent=self)
        if dlg.exec_() == HouseholdDialog.Accepted:
            self.load_data()
