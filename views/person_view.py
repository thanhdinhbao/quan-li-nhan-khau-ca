from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidgetItem, QMessageBox, QMenu, QAction, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
import qtawesome as qta

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR, COLOR_SUCCESS_GREEN
)
from widgets.search_box import SearchBox
from widgets.custom_table import CustomTableWidget
from controllers.person_controller import PersonController
from controllers.area_controller import AreaController
from services.auth_service import AuthService
from views.person_dialog import PersonDialog
from utils.formatters import format_date_vn, mask_id_card, mask_phone, format_number
from utils.constants import GENDER_LIST, RESIDENCE_STATUS_LIST

class PersonView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.person_ctrl = PersonController()
        self.area_ctrl = AreaController()

        # State variables
        self.current_page = 1
        self.page_size = 20
        self.total_records = 0
        self.is_showing_deleted = False

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Top Header & Primary Action Toolbar
        top_bar = QHBoxLayout()
        title_lbl = QLabel("Quản lý Nhân khẩu")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        top_bar.addWidget(title_lbl)

        top_bar.addStretch()

        # Action Buttons
        self.add_btn = QPushButton("  Thêm nhân khẩu")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(36)
        try:
            self.add_btn.setIcon(qta.icon('fa5s.user-plus', color=COLOR_WHITE))
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
            QPushButton:hover {{
                background-color: #E9ECEF;
            }}
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        top_bar.addWidget(self.refresh_btn)

        self.trash_btn = QPushButton(" Thùng rác")
        self.trash_btn.setCursor(Qt.PointingHandCursor)
        self.trash_btn.setFixedHeight(36)
        self.trash_btn.setCheckable(True)
        self.trash_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_WHITE};
                color: #DC3545;
                border: 1px solid #DC3545;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:checked {{
                background-color: #DC3545;
                color: {COLOR_WHITE};
            }}
        """)
        self.trash_btn.clicked.connect(self.toggle_trash_bin)
        top_bar.addWidget(self.trash_btn)

        main_layout.addLayout(top_bar)

        # 2. Filter Bar
        filter_card = QFrame()
        filter_card.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        # Search box
        self.search_box = SearchBox()
        self.search_box.setMinimumWidth(260)
        self.search_box.searched.connect(self.on_search)
        filter_layout.addWidget(self.search_box)

        # Filters
        self.combo_area = QComboBox()
        self.combo_area.setFixedWidth(150)
        self.combo_area.addItem("Tất cả khu vực", 0)
        self.combo_area.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_area)

        self.combo_gender = QComboBox()
        self.combo_gender.setFixedWidth(110)
        self.combo_gender.addItem("Tất cả giới tính")
        self.combo_gender.addItems(GENDER_LIST)
        self.combo_gender.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_gender)

        self.combo_age = QComboBox()
        self.combo_age.setFixedWidth(120)
        self.combo_age.addItems(["Tất cả độ tuổi", "0-18", "19-30", "31-45", "46-60", "Trên 60"])
        self.combo_age.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_age)

        self.combo_res = QComboBox()
        self.combo_res.setFixedWidth(140)
        self.combo_res.addItem("Tất cả cư trú")
        self.combo_res.addItems(RESIDENCE_STATUS_LIST)
        self.combo_res.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_res)

        filter_layout.addStretch()
        main_layout.addWidget(filter_card)

        # 3. Custom Data Table
        self.table = CustomTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "STT", "Mã NK", "Họ và tên", "Ngày sinh", "Giới tính",
            "Số CCCD", "Số điện thoại", "Khu vực", "Địa chỉ thường trú", "Trạng thái"
        ])
        self.table.set_column_widths({0: 45, 1: 90, 2: 160, 3: 95, 4: 75, 5: 120, 6: 105, 7: 110, 9: 100})
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        main_layout.addWidget(self.table, stretch=1)

        # 4. Pagination Bar
        page_bar = QHBoxLayout()
        self.page_info_lbl = QLabel("Hiển thị 0 bản ghi")
        self.page_info_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT_MUTED};")
        page_bar.addWidget(self.page_info_lbl)

        page_bar.addStretch()

        self.btn_first = QPushButton("<<")
        self.btn_prev = QPushButton("<")
        self.lbl_page_num = QLabel("Trang 1 / 1")
        self.lbl_page_num.setStyleSheet("font-weight: 700; padding: 0 8px;")
        self.btn_next = QPushButton(">")
        self.btn_last = QPushButton(">>")

        for b in [self.btn_first, self.btn_prev, self.btn_next, self.btn_last]:
            b.setFixedWidth(36)
            b.setStyleSheet(f"QPushButton {{ background: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 4px; font-weight: 700; }} QPushButton:hover {{ background: #E9ECEF; }}")

        self.btn_first.clicked.connect(lambda: self.go_page(1))
        self.btn_prev.clicked.connect(lambda: self.go_page(self.current_page - 1))
        self.btn_next.clicked.connect(lambda: self.go_page(self.current_page + 1))
        self.btn_last.clicked.connect(lambda: self.go_page(self.get_max_pages()))

        page_bar.addWidget(self.btn_first)
        page_bar.addWidget(self.btn_prev)
        page_bar.addWidget(self.lbl_page_num)
        page_bar.addWidget(self.btn_next)
        page_bar.addWidget(self.btn_last)

        main_layout.addLayout(page_bar)

        # Populate Filters & Data
        self.load_areas_filter()
        self.load_data()

    def load_areas_filter(self):
        current_id = self.combo_area.currentData() if self.combo_area.count() > 0 else 0
        self.combo_area.blockSignals(True)
        self.combo_area.clear()
        self.combo_area.addItem("Tất cả khu vực", 0)
        areas = self.area_ctrl.get_all_areas()
        target_idx = 0
        for i, a in enumerate(areas, 1):
            self.combo_area.addItem(a.name, a.id)
            if current_id and a.id == current_id:
                target_idx = i
        self.combo_area.setCurrentIndex(target_idx)
        self.combo_area.blockSignals(False)

    def on_search(self, text: str):
        self.current_page = 1
        self.load_data()

    def on_filter_changed(self):
        self.current_page = 1
        self.load_data()

    def toggle_trash_bin(self, checked: bool):
        self.is_showing_deleted = checked
        self.current_page = 1
        self.load_data()

    def refresh_data(self):
        self.trash_btn.setChecked(False)
        self.is_showing_deleted = False
        self.search_box.clear()
        self.current_page = 1
        self.load_areas_filter()
        self.combo_area.setCurrentIndex(0)
        self.combo_gender.setCurrentIndex(0)
        self.combo_age.setCurrentIndex(0)
        self.combo_res.setCurrentIndex(0)
        self.load_data()

    def load_data(self):
        keyword = self.search_box.text()
        
        area_data = self.combo_area.currentData()
        if self.combo_area.currentText().startswith("Tất cả") or area_data is None:
            area_id = 0
        else:
            try:
                area_id = int(area_data)
            except (TypeError, ValueError):
                area_id = 0

        gender = self.combo_gender.currentText()
        if gender.startswith("Tất cả"):
            gender = "Tất cả"

        age_group = self.combo_age.currentText()
        if age_group.startswith("Tất cả"):
            age_group = "Tất cả"

        res_status = self.combo_res.currentText()
        if res_status.startswith("Tất cả"):
            res_status = "Tất cả"

        is_deleted = 1 if self.is_showing_deleted else 0

        user = AuthService.get_current_user()
        has_full_id_perm = user.has_permission("PERSON_VIEW_ID_FULL") if user else True

        persons, total = self.person_ctrl.get_persons_paged(
            keyword=keyword,
            area_id=area_id,
            gender=gender,
            age_group=age_group,
            residence_status=res_status,
            is_deleted=is_deleted,
            page=self.current_page,
            page_size=self.page_size
        )
        self.total_records = total
        self.persons_list = persons

        self.table.setRowCount(len(persons))
        start_idx = (self.current_page - 1) * self.page_size

        for r_idx, p in enumerate(persons):
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(start_idx + r_idx + 1)))
            
            code_item = QTableWidgetItem(p.person_code)
            code_item.setData(Qt.UserRole, p.id)
            self.table.setItem(r_idx, 1, code_item)

            self.table.setItem(r_idx, 2, QTableWidgetItem(p.full_name))
            self.table.setItem(r_idx, 3, QTableWidgetItem(format_date_vn(p.dob)))
            self.table.setItem(r_idx, 4, QTableWidgetItem(p.gender))
            self.table.setItem(r_idx, 5, QTableWidgetItem(mask_id_card(p.id_card_number, has_full_id_perm)))
            self.table.setItem(r_idx, 6, QTableWidgetItem(mask_phone(p.phone, has_full_id_perm)))
            self.table.setItem(r_idx, 7, QTableWidgetItem(p.area_name or ""))
            self.table.setItem(r_idx, 8, QTableWidgetItem(p.permanent_address or ""))
            
            status_item = QTableWidgetItem(p.residence_status)
            if p.residence_status == "Thường trú":
                status_item.setForeground(Qt.darkGreen)
            elif p.residence_status == "Tạm trú":
                status_item.setForeground(Qt.blue)
            elif p.residence_status == "Tạm vắng":
                status_item.setForeground(Qt.darkYellow)
            self.table.setItem(r_idx, 9, status_item)

        # Update Pagination UI
        max_p = self.get_max_pages()
        start_count = start_idx + 1 if total > 0 else 0
        end_count = min(start_idx + self.page_size, total)
        trash_mode_text = " [THÙNG RÁC]" if self.is_showing_deleted else ""
        self.page_info_lbl.setText(f"Hiển thị {start_count}-{end_count} / Tổng số {format_number(total)} nhân khẩu{trash_mode_text}")
        self.lbl_page_num.setText(f"Trang {self.current_page} / {max_p}")

        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_first.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < max_p)
        self.btn_last.setEnabled(self.current_page < max_p)

    def get_max_pages(self) -> int:
        if self.total_records == 0:
            return 1
        return (self.total_records + self.page_size - 1) // self.page_size

    def go_page(self, page_num: int):
        max_p = self.get_max_pages()
        if 1 <= page_num <= max_p:
            self.current_page = page_num
            self.load_data()

    def get_selected_person_id(self) -> int:
        curr_row = self.table.currentRow()
        if curr_row < 0:
            return 0
        item = self.table.item(curr_row, 1)
        return item.data(Qt.UserRole) if item else 0

    def on_row_double_clicked(self):
        pid = self.get_selected_person_id()
        if pid:
            self.open_edit_dialog(pid)

    def open_add_dialog(self):
        if not AuthService.check_permission("PERSON_ADD"):
            QMessageBox.warning(self, "Từ chối truy cập", "Bạn không có quyền thêm mới nhân khẩu.")
            return

        dlg = PersonDialog(parent=self)
        if dlg.exec_() == PersonDialog.Accepted:
            self.load_data()

    def open_edit_dialog(self, person_id: int):
        p = self.person_ctrl.get_person_by_id(person_id)
        if not p:
            return

        can_edit = AuthService.check_permission("PERSON_EDIT")
        dlg = PersonDialog(person=p, is_read_only=not can_edit, parent=self)
        if dlg.exec_() == PersonDialog.Accepted:
            self.load_data()

    def open_context_menu(self, position):
        pid = self.get_selected_person_id()
        if not pid:
            return

        menu = QMenu(self)
        view_action = QAction("Xem chi tiết", self)
        view_action.triggered.connect(lambda: self.open_edit_dialog(pid))
        menu.addAction(view_action)

        if not self.is_showing_deleted:
            if AuthService.check_permission("PERSON_EDIT"):
                edit_action = QAction("Chỉnh sửa thông tin", self)
                edit_action.triggered.connect(lambda: self.open_edit_dialog(pid))
                menu.addAction(edit_action)

            if AuthService.check_permission("PERSON_DELETE"):
                delete_action = QAction("Chuyển vào thùng rác (Xóa mềm)", self)
                delete_action.triggered.connect(lambda: self.delete_person(pid))
                menu.addAction(delete_action)
        else:
            if AuthService.check_permission("PERSON_RESTORE"):
                restore_action = QAction("Khôi phục bản ghi", self)
                restore_action.triggered.connect(lambda: self.restore_person(pid))
                menu.addAction(restore_action)

        menu.exec_(QCursor.pos())

    def delete_person(self, person_id: int):
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa mềm",
            "Bạn có chắc chắn muốn chuyển hồ sơ nhân khẩu này vào Thùng rác?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            user = AuthService.get_current_user()
            user_id = user.id if user else None
            success, msg = self.person_ctrl.soft_delete_person(person_id, user_id=user_id)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def restore_person(self, person_id: int):
        user = AuthService.get_current_user()
        user_id = user.id if user else None
        success, msg = self.person_ctrl.restore_person(person_id, user_id=user_id)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.load_data()
        else:
            QMessageBox.critical(self, "Lỗi", msg)
