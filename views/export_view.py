from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QMessageBox, QFileDialog, QGroupBox, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt
import qtawesome as qta
from datetime import datetime

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from controllers.person_controller import PersonController
from controllers.area_controller import AreaController
from services.excel_service import ExcelExportService
from services.auth_service import AuthService
from utils.constants import RESIDENCE_STATUS_LIST, GENDER_LIST

class ExportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.person_ctrl = PersonController()
        self.area_ctrl = AreaController()

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header
        title_lbl = QLabel("Xuất dữ liệu báo cáo ra File Excel")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        main_layout.addWidget(title_lbl)

        # Filter Options Card
        card = QGroupBox("Cấu hình điều kiện Xuất dữ liệu")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        # Area Filter
        area_box = QHBoxLayout()
        area_box.addWidget(QLabel("Chọn Khu vực / Thôn:"), stretch=1)
        self.combo_area = QComboBox()
        self.combo_area.addItem("Tất cả các khu vực", 0)
        areas = self.area_ctrl.get_all_areas()
        for a in areas:
            self.combo_area.addItem(a.name, a.id)
        area_box.addWidget(self.combo_area, stretch=3)
        card_layout.addLayout(area_box)

        # Gender Filter
        gender_box = QHBoxLayout()
        gender_box.addWidget(QLabel("Chọn Giới tính:"), stretch=1)
        self.combo_gender = QComboBox()
        self.combo_gender.addItem("Tất cả")
        self.combo_gender.addItems(GENDER_LIST)
        gender_box.addWidget(self.combo_gender, stretch=3)
        card_layout.addLayout(gender_box)

        # Residence Status Filter
        res_box = QHBoxLayout()
        res_box.addWidget(QLabel("Trạng thái cư trú:"), stretch=1)
        self.combo_res = QComboBox()
        self.combo_res.addItem("Tất cả")
        self.combo_res.addItems(RESIDENCE_STATUS_LIST)
        res_box.addWidget(self.combo_res, stretch=3)
        card_layout.addLayout(res_box)

        main_layout.addWidget(card)

        # Columns selection group box
        col_box = QGroupBox("Tùy chọn cột dữ liệu xuất")
        col_layout = QVBoxLayout(col_box)
        col_layout.addWidget(QLabel("Mặc định các cột chuẩn: STT, Mã NK, Họ tên, Ngày sinh, Giới tính, CCCD, SĐT, Khu vực, Địa chỉ thường trú, Trạng thái."))
        main_layout.addWidget(col_box)

        main_layout.addStretch()

        # Action button
        act_layout = QHBoxLayout()
        act_layout.addStretch()

        self.btn_export = QPushButton("  XUẤT DỮ LIỆU BÁO CÁO EXCEL")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setFixedHeight(44)
        try:
            self.btn_export.setIcon(qta.icon('fa5s.file-excel', color=COLOR_WHITE))
        except Exception:
            pass
        self.btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_BURGUNDY};
                color: white;
                font-weight: 800;
                border-radius: 6px;
                padding: 0 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SECONDARY_DARK_RED};
            }}
        """)
        self.btn_export.clicked.connect(self.do_export)
        act_layout.addWidget(self.btn_export)

        main_layout.addLayout(act_layout)

    def do_export(self):
        if not AuthService.check_permission("EXPORT_EXCEL"):
            QMessageBox.warning(self, "Từ chối truy cập", "Bạn không có quyền Xuất dữ liệu Excel.")
            return

        default_filename = f"Danh_sach_nhan_khau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file Excel", default_filename, "Excel Files (*.xlsx)")
        if not file_path:
            return

        area_id = self.combo_area.currentData()
        gender = self.combo_gender.currentText()
        res_status = self.combo_res.currentText()

        # Fetch records
        persons, total = self.person_ctrl.get_persons_paged(
            area_id=area_id,
            gender=gender,
            residence_status=res_status,
            page=1,
            page_size=10000 # Large export batch
        )

        if not persons:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu nhân khẩu thỏa mãn điều kiện lọc.")
            return

        user = AuthService.get_current_user()
        has_full_perm = user.has_permission("PERSON_VIEW_ID_FULL") if user else True

        success = ExcelExportService.export_persons_to_excel(file_path, persons, has_full_permission=has_full_perm)
        if success:
            QMessageBox.information(self, "Thành công", f"Đã xuất thành công {len(persons)} bản ghi nhân khẩu ra file Excel:\n{file_path}")
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể ghi file Excel. Vui lòng kiểm tra file có đang được mở bởi chương trình khác hay không.")
