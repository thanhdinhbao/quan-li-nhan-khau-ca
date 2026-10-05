from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QTableWidgetItem, QMessageBox,
    QFrame, QFileDialog
)
from PyQt5.QtCore import Qt
import qtawesome as qta

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from widgets.custom_table import CustomTableWidget
from services.search_service import SearchService
from controllers.area_controller import AreaController
from services.excel_service import ExcelExportService
from services.auth_service import AuthService
from utils.constants import GENDER_LIST, RESIDENCE_STATUS_LIST
from utils.formatters import format_date_vn, mask_id_card, mask_phone, format_number

class AdvancedSearchView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.area_ctrl = AreaController()
        self.current_page = 1
        self.page_size = 20
        self.total_records = 0

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        title_lbl = QLabel("Tra cứu & Tìm kiếm Nâng cao")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        top_bar.addWidget(title_lbl)

        top_bar.addStretch()

        self.btn_export_results = QPushButton("  Xuất kết quả ra Excel")
        self.btn_export_results.setCursor(Qt.PointingHandCursor)
        self.btn_export_results.setFixedHeight(36)
        try:
            self.btn_export_results.setIcon(qta.icon('fa5s.file-excel', color=COLOR_WHITE))
        except Exception:
            pass
        self.btn_export_results.setStyleSheet(f"""
            QPushButton {{
                background-color: #198754;
                color: white;
                font-weight: 700;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #146c43; }}
        """)
        self.btn_export_results.clicked.connect(self.export_search_results)
        top_bar.addWidget(self.btn_export_results)

        main_layout.addLayout(top_bar)

        # Query Form Card
        query_card = QGroupBox("Bộ lọc Tìm kiếm Nâng cao (Kết hợp nhiều điều kiện)")
        query_layout = QGridLayout(query_card)
        query_layout.setSpacing(10)

        # Row 0
        query_layout.addWidget(QLabel("Từ khóa tổng hợp:"), 0, 0)
        self.txt_keyword = QLineEdit()
        self.txt_keyword.setPlaceholderText("Tìm bất kỳ Họ tên, CCCD, SĐT, Địa chỉ...")
        query_layout.addWidget(self.txt_keyword, 0, 1)

        query_layout.addWidget(QLabel("Số CCCD/CMND:"), 0, 2)
        self.txt_cccd = QLineEdit()
        self.txt_cccd.setPlaceholderText("Chính xác hoặc 1 phần CCCD")
        query_layout.addWidget(self.txt_cccd, 0, 3)

        # Row 1
        query_layout.addWidget(QLabel("Khu vực / Thôn:"), 1, 0)
        self.combo_area = QComboBox()
        self.combo_area.addItem("Tất cả khu vực", 0)
        areas = self.area_ctrl.get_all_areas()
        for a in areas:
            self.combo_area.addItem(a.name, a.id)
        query_layout.addWidget(self.combo_area, 1, 1)

        query_layout.addWidget(QLabel("Giới tính:"), 1, 2)
        self.combo_gender = QComboBox()
        self.combo_gender.addItem("Tất cả")
        self.combo_gender.addItems(GENDER_LIST)
        query_layout.addWidget(self.combo_gender, 1, 3)

        # Row 2
        query_layout.addWidget(QLabel("Cơ cấu độ tuổi:"), 2, 0)
        self.combo_age = QComboBox()
        self.combo_age.addItems(["Tất cả", "0-18", "19-30", "31-45", "46-60", "Trên 60"])
        query_layout.addWidget(self.combo_age, 2, 1)

        query_layout.addWidget(QLabel("Trạng thái cư trú:"), 2, 2)
        self.combo_res = QComboBox()
        self.combo_res.addItem("Tất cả")
        self.combo_res.addItems(RESIDENCE_STATUS_LIST)
        query_layout.addWidget(self.combo_res, 2, 3)

        # Row 3
        query_layout.addWidget(QLabel("Quê quán:"), 3, 0)
        self.txt_hometown = QLineEdit()
        query_layout.addWidget(self.txt_hometown, 3, 1)

        query_layout.addWidget(QLabel("Nghề nghiệp:"), 3, 2)
        self.txt_occupation = QLineEdit()
        query_layout.addWidget(self.txt_occupation, 3, 3)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_reset = QPushButton("Đặt lại bộ lọc")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_form)
        btn_box.addWidget(self.btn_reset)

        self.btn_search = QPushButton("  TÌM KIẾM DỮ LIỆU")
        self.btn_search.setCursor(Qt.PointingHandCursor)
        self.btn_search.setFixedHeight(36)
        try:
            self.btn_search.setIcon(qta.icon('fa5s.search', color=COLOR_WHITE))
        except Exception:
            pass
        self.btn_search.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_BURGUNDY};
                color: white;
                font-weight: 700;
                border-radius: 6px;
                padding: 0 18px;
            }}
            QPushButton:hover {{ background-color: {COLOR_SECONDARY_DARK_RED}; }}
        """)
        self.btn_search.clicked.connect(self.execute_search)
        btn_box.addWidget(self.btn_search)

        query_layout.addLayout(btn_box, 4, 0, 1, 4)
        main_layout.addWidget(query_card)

        # Results Info Label
        self.lbl_result_info = QLabel("Kết quả tìm kiếm: 0 nhân khẩu thỏa mãn")
        self.lbl_result_info.setStyleSheet("font-size: 13px; font-weight: 700; color: #17365D;")
        main_layout.addWidget(self.lbl_result_info)

        # Table
        self.table = CustomTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "STT", "Mã NK", "Họ và tên", "Ngày sinh", "Giới tính",
            "Số CCCD", "Số điện thoại", "Khu vực", "Địa chỉ thường trú", "Trạng thái"
        ])
        self.table.set_column_widths({0: 45, 1: 90, 2: 160, 3: 95, 4: 75, 5: 120, 6: 105, 7: 110, 9: 100})
        main_layout.addWidget(self.table, stretch=1)

        # Initial Search
        self.execute_search()

    def reset_form(self):
        self.txt_keyword.clear()
        self.txt_cccd.clear()
        self.txt_hometown.clear()
        self.txt_occupation.clear()
        self.combo_area.setCurrentIndex(0)
        self.combo_gender.setCurrentIndex(0)
        self.combo_age.setCurrentIndex(0)
        self.combo_res.setCurrentIndex(0)
        self.execute_search()

    def execute_search(self):
        kw = self.txt_keyword.text().strip()
        cccd = self.txt_cccd.text().strip()
        ht = self.txt_hometown.text().strip()
        occ = self.txt_occupation.text().strip()
        area_id = self.combo_area.currentData()
        gender = self.combo_gender.currentText()
        age_group = self.combo_age.currentText()
        res_status = self.combo_res.currentText()

        user = AuthService.get_current_user()
        has_full_perm = user.has_permission("PERSON_VIEW_ID_FULL") if user else True

        persons, total = SearchService.search_persons_advanced(
            keyword=kw,
            id_card=cccd,
            hometown=ht,
            occupation=occ,
            area_id=area_id,
            gender=gender,
            age_group=age_group,
            residence_status=res_status,
            page=self.current_page,
            page_size=self.page_size
        )
        self.search_results = persons
        self.total_records = total

        self.lbl_result_info.setText(f"Kết quả tìm kiếm: {format_number(total)} nhân khẩu thỏa mãn điều kiện")
        self.table.setRowCount(len(persons))

        for r_idx, p in enumerate(persons):
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
            self.table.setItem(r_idx, 1, QTableWidgetItem(p.person_code))
            self.table.setItem(r_idx, 2, QTableWidgetItem(p.full_name))
            self.table.setItem(r_idx, 3, QTableWidgetItem(format_date_vn(p.dob)))
            self.table.setItem(r_idx, 4, QTableWidgetItem(p.gender))
            self.table.setItem(r_idx, 5, QTableWidgetItem(mask_id_card(p.id_card_number, has_full_perm)))
            self.table.setItem(r_idx, 6, QTableWidgetItem(mask_phone(p.phone, has_full_perm)))
            self.table.setItem(r_idx, 7, QTableWidgetItem(p.area_name or ""))
            self.table.setItem(r_idx, 8, QTableWidgetItem(p.permanent_address or ""))
            
            st_item = QTableWidgetItem(p.residence_status)
            st_item.setForeground(Qt.darkGreen if p.residence_status == "Thường trú" else Qt.blue)
            self.table.setItem(r_idx, 9, st_item)

    def export_search_results(self):
        if not hasattr(self, 'search_results') or not self.search_results:
            QMessageBox.warning(self, "Cảnh báo", "Không có kết quả tìm kiếm nào để xuất Excel.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu kết quả tìm kiếm Excel", "Ket_qua_tim_kiem_nhan_khau.xlsx", "Excel Files (*.xlsx)")
        if not file_path:
            return

        user = AuthService.get_current_user()
        has_full_perm = user.has_permission("PERSON_VIEW_ID_FULL") if user else True

        ok = ExcelExportService.export_persons_to_excel(file_path, self.search_results, has_full_permission=has_full_perm)
        if ok:
            QMessageBox.information(self, "Thành công", f"Đã xuất {len(self.search_results)} bản ghi tìm kiếm ra file Excel:\n{file_path}")
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể ghi file Excel.")
