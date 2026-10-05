from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidgetItem, QMessageBox, QFrame, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt
import qtawesome as qta

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from widgets.custom_table import CustomTableWidget
from controllers.area_controller import AreaController
from services.auth_service import AuthService

class AreaView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.area_ctrl = AreaController()

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Bar
        top_bar = QHBoxLayout()
        title_lbl = QLabel("Quản lý Khu vực / Thôn / Tổ dân phố")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        top_bar.addWidget(title_lbl)

        top_bar.addStretch()

        self.add_btn = QPushButton("  Thêm khu vực")
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
            QPushButton:hover {{ background-color: {COLOR_SECONDARY_DARK_RED}; }}
        """)
        self.add_btn.clicked.connect(self.open_add_dialog)
        top_bar.addWidget(self.add_btn)

        self.transfer_btn = QPushButton("  Chuyển nhân khẩu giữa các khu")
        self.transfer_btn.setCursor(Qt.PointingHandCursor)
        self.transfer_btn.setFixedHeight(36)
        self.transfer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #198754;
                color: {COLOR_WHITE};
                font-weight: 700;
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #146c43; }}
        """)
        self.transfer_btn.clicked.connect(self.open_transfer_dialog)
        top_bar.addWidget(self.transfer_btn)

        self.edit_btn = QPushButton("  Chỉnh sửa")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedHeight(36)
        self.edit_btn.setStyleSheet(f"QPushButton {{ background-color: {COLOR_WHITE}; color: {COLOR_NAVY_SIDEBAR}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 0 12px; font-size: 13px; font-weight: 600; }}")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        top_bar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("  Xóa khu vực")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setFixedHeight(36)
        self.delete_btn.setStyleSheet("QPushButton { background-color: #DC3545; color: white; border: none; border-radius: 6px; padding: 0 12px; font-size: 13px; font-weight: 600; }")
        self.delete_btn.clicked.connect(self.delete_selected_area)
        top_bar.addWidget(self.delete_btn)

        main_layout.addLayout(top_bar)

        # Table
        self.table = CustomTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "STT", "Mã khu vực", "Tên khu vực", "Mô tả chi tiết", "Tổng số Nhân khẩu", "Tổng số Hộ gia đình"
        ])
        self.table.set_column_widths({0: 45, 1: 110, 2: 180, 4: 140, 5: 140})
        main_layout.addWidget(self.table, stretch=1)

        self.load_data()

    def load_data(self):
        areas = self.area_ctrl.get_all_areas()
        self.table.setRowCount(len(areas))
        for r_idx, a in enumerate(areas):
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
            
            code_item = QTableWidgetItem(a.code)
            code_item.setData(Qt.UserRole, a.id)
            self.table.setItem(r_idx, 1, code_item)

            self.table.setItem(r_idx, 2, QTableWidgetItem(a.name))
            self.table.setItem(r_idx, 3, QTableWidgetItem(a.description or ""))
            self.table.setItem(r_idx, 4, QTableWidgetItem(f"{a.person_count} người"))
            self.table.setItem(r_idx, 5, QTableWidgetItem(f"{a.household_count} hộ"))

    def get_selected_area_id(self) -> int:
        row = self.table.currentRow()
        if row < 0:
            return 0
        item = self.table.item(row, 1)
        return item.data(Qt.UserRole) if item else 0

    def open_edit_dialog(self):
        area_id = self.get_selected_area_id()
        if not area_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn khu vực cần chỉnh sửa.")
            return

        area = self.area_ctrl.get_area_by_id(area_id)
        if not area:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Chỉnh sửa thông tin khu vực")
        dlg.setFixedSize(400, 250)
        layout = QFormLayout(dlg)

        txt_code = QLineEdit(area.code)
        txt_name = QLineEdit(area.name)
        txt_desc = QTextEdit()
        txt_desc.setText(area.description or "")

        layout.addRow("Mã khu vực (*):", txt_code)
        layout.addRow("Tên khu vực (*):", txt_name)
        layout.addRow("Mô tả:", txt_desc)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("Cập nhật")
        save_btn.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY_BURGUNDY}; color: white; font-weight: 700; }}")
        save_btn.clicked.connect(dlg.accept)
        btn_box.addWidget(save_btn)
        layout.addRow(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            c = txt_code.text().strip()
            n = txt_name.text().strip()
            d = txt_desc.toPlainText().strip()
            success, msg = self.area_ctrl.update_area(area_id, c, n, d)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def delete_selected_area(self):
        area_id = self.get_selected_area_id()
        if not area_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn khu vực cần xóa.")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa khu vực",
            "Bạn có chắc chắn muốn xóa khu vực này?\n(Lưu ý: Chỉ có thể xóa nếu không còn nhân khẩu hoặc hộ gia đình sinh sống).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = self.area_ctrl.delete_area(area_id)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Không thể xóa", msg)

    def open_add_dialog(self):
        dlg = QDialog(self)
        dlg.setFixedSize(400, 250)
        layout = QFormLayout(dlg)

        txt_code = QLineEdit()
        txt_code.setPlaceholderText("Mã khu (Ví dụ: KHU05, THON_D)")
        txt_name = QLineEdit()
        txt_name.setPlaceholderText("Tên khu vực (Ví dụ: Thôn D)")
        txt_desc = QTextEdit()

        layout.addRow("Mã khu vực (*):", txt_code)
        layout.addRow("Tên khu vực (*):", txt_name)
        layout.addRow("Mô tả:", txt_desc)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("Lưu khu vực")
        save_btn.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY_BURGUNDY}; color: white; font-weight: 700; }}")
        save_btn.clicked.connect(dlg.accept)
        btn_box.addWidget(save_btn)
        layout.addRow(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            c = txt_code.text().strip()
            n = txt_name.text().strip()
            d = txt_desc.toPlainText().strip()
            success, msg, _ = self.area_ctrl.add_area(c, n, d)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def open_transfer_dialog(self):
        areas = self.area_ctrl.get_all_areas()
        if len(areas) < 2:
            QMessageBox.warning(self, "Cảnh báo", "Cần ít nhất 2 khu vực để thực hiện chuyển địa bàn.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Chuyển nhân khẩu giữa các khu vực")
        dlg.setFixedSize(450, 220)
        layout = QFormLayout(dlg)

        src_combo = QComboBox()
        dst_combo = QComboBox()
        for a in areas:
            src_combo.addItem(f"{a.name} ({a.person_count} người)", a.id)
            dst_combo.addItem(f"{a.name} ({a.person_count} người)", a.id)

        if len(areas) > 1:
            dst_combo.setCurrentIndex(1)

        layout.addRow("Khu vực nguồn (Chuyển đi):", src_combo)
        layout.addRow("Khu vực đích (Chuyển đến):", dst_combo)

        btn_box = QHBoxLayout()
        trans_btn = QPushButton("Xác nhận chuyển địa bàn")
        trans_btn.setStyleSheet("QPushButton { background-color: #198754; color: white; font-weight: 700; }")
        trans_btn.clicked.connect(dlg.accept)
        btn_box.addWidget(trans_btn)
        layout.addRow(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            src_id = src_combo.currentData()
            dst_id = dst_combo.currentData()
            success, msg, cnt = self.area_ctrl.transfer_population(src_id, dst_id)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Lỗi", msg)
