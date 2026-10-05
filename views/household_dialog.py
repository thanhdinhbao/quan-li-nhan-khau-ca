from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QHeaderView
)
from PyQt5.QtCore import Qt
from config import COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_BORDER
from database.models import Household, Person
from controllers.household_controller import HouseholdController
from controllers.person_controller import PersonController
from controllers.area_controller import AreaController
from utils.constants import RELATIONSHIP_LIST

class HouseholdDialog(QDialog):
    def __init__(self, household: Household = None, parent=None):
        super().__init__(parent)
        self.hh = household or Household()
        self.hh_ctrl = HouseholdController()
        self.person_ctrl = PersonController()
        self.area_ctrl = AreaController()

        title_action = "Chi tiết Hộ gia đình" if self.hh.id else "Tạo Hộ gia đình mới"
        self.setWindowTitle(f"{title_action} - Quản lý Hộ gia đình")
        self.resize(700, 560)
        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title_lbl = QLabel(title_action.upper())
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_PRIMARY_BURGUNDY}; border-bottom: 2px solid {COLOR_PRIMARY_BURGUNDY}; padding-bottom: 6px;")
        layout.addWidget(title_lbl)

        # Info Group Box
        info_box = QGroupBox("Thông tin hộ gia đình")
        info_layout = QFormLayout(info_box)

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("Tự động sinh (Mã HK)")
        if self.hh.household_code:
            self.txt_code.setText(self.hh.household_code)
            self.txt_code.setReadOnly(True)

        self.txt_number = QLineEdit()
        self.txt_number.setPlaceholderText("Số sổ hộ khẩu (Ví dụ: HK-0101)")
        if self.hh.household_number:
            self.txt_number.setText(self.hh.household_number)

        self.combo_area = QComboBox()
        areas = self.area_ctrl.get_all_areas()
        for a in areas:
            self.combo_area.addItem(a.name, a.id)
        if self.hh.area_id:
            idx = self.combo_area.findData(self.hh.area_id)
            if idx >= 0:
                self.combo_area.setCurrentIndex(idx)

        self.txt_address = QLineEdit()
        self.txt_address.setPlaceholderText("Số nhà, đường/thôn...")
        if self.hh.address_street:
            self.txt_address.setText(self.hh.address_street)

        info_layout.addRow("Mã hộ gia đình:", self.txt_code)
        info_layout.addRow("Số hộ khẩu:", self.txt_number)
        info_layout.addRow("Khu vực / Thôn:", self.combo_area)
        info_layout.addRow("Địa chỉ chi tiết:", self.txt_address)

        layout.addWidget(info_box)

        # Members List Group Box (Only shown if household exists)
        if self.hh.id:
            members_box = QGroupBox("Danh sách thành viên trong hộ")
            members_layout = QVBoxLayout(members_box)

            # Toolbar for member actions
            mem_btn_bar = QHBoxLayout()
            self.add_mem_btn = QPushButton("+ Thêm thành viên vào hộ")
            self.add_mem_btn.setStyleSheet("QPushButton { background-color: #198754; color: white; font-weight: 600; padding: 4px 10px; border-radius: 4px; }")
            self.add_mem_btn.clicked.connect(self.add_member_dialog)

            self.remove_mem_btn = QPushButton("Tách khỏi hộ")
            self.remove_mem_btn.setStyleSheet("QPushButton { background-color: #DC3545; color: white; font-weight: 600; padding: 4px 10px; border-radius: 4px; }")
            self.remove_mem_btn.clicked.connect(self.remove_selected_member)

            mem_btn_bar.addWidget(self.add_mem_btn)
            mem_btn_bar.addWidget(self.remove_mem_btn)
            mem_btn_bar.addStretch()
            members_layout.addLayout(mem_btn_bar)

            self.members_table = QTableWidget()
            self.members_table.setColumnCount(5)
            self.members_table.setHorizontalHeaderLabels(["Mã NK", "Họ và tên", "Ngày sinh", "Giới tính", "Quan hệ chủ hộ"])
            self.members_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.members_table.verticalHeader().setVisible(False)
            members_layout.addWidget(self.members_table)

            layout.addWidget(members_box, stretch=1)
            self.load_members_table()

        # Bottom Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        cancel_btn = QPushButton("Đóng")
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(cancel_btn)

        save_btn = QPushButton("Lưu hộ gia đình")
        save_btn.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY_BURGUNDY}; color: white; font-weight: 700; padding: 6px 14px; border-radius: 4px; }}")
        save_btn.clicked.connect(self.save_household)
        btn_bar.addWidget(save_btn)

        layout.addLayout(btn_bar)

    def load_members_table(self):
        if not self.hh.id:
            return
        details = self.hh_ctrl.get_household_details(self.hh.id)
        if not details:
            return
        self.hh.members = details.members
        self.members_table.setRowCount(len(details.members))
        for r_idx, m in enumerate(details.members):
            item = QTableWidgetItem(m.person_code)
            item.setData(Qt.UserRole, m.id)
            self.members_table.setItem(r_idx, 0, item)
            self.members_table.setItem(r_idx, 1, QTableWidgetItem(m.full_name))
            self.members_table.setItem(r_idx, 2, QTableWidgetItem(m.dob or ""))
            self.members_table.setItem(r_idx, 3, QTableWidgetItem(m.gender))
            self.members_table.setItem(r_idx, 4, QTableWidgetItem(m.relationship_with_head or ""))

    def save_household(self):
        code = self.txt_code.text().strip()
        num = self.txt_number.text().strip()
        area_id = self.combo_area.currentData()
        addr = self.txt_address.text().strip()
        full_addr = f"{addr}, {self.combo_area.currentText()}"

        if not self.hh.id:
            success, msg, hh_id = self.hh_ctrl.add_household(code, num, area_id, addr, full_addr)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", msg)
        else:
            self.accept()

    def add_member_dialog(self):
        # Select person dialog
        persons, _ = self.person_ctrl.get_persons_paged(page_size=300)
        unassigned = [p for p in persons if p.household_id != self.hh.id]
        if not unassigned:
            QMessageBox.information(self, "Thông báo", "Tất cả nhân khẩu khả dụng đã ở trong hộ gia đình này.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Thêm thành viên vào hộ gia đình")
        dlg.setFixedSize(400, 220)
        d_layout = QFormLayout(dlg)

        p_combo = QComboBox()
        for p in unassigned:
            p_combo.addItem(f"[{p.person_code}] {p.full_name} - {p.area_name}", p.id)

        rel_combo = QComboBox()
        rel_combo.addItems(RELATIONSHIP_LIST)

        d_layout.addRow("Chọn Nhân khẩu:", p_combo)
        d_layout.addRow("Quan hệ với chủ hộ:", rel_combo)

        btn_box = QHBoxLayout()
        add_btn = QPushButton("Đồng ý thêm")
        add_btn.setStyleSheet("QPushButton { background-color: #198754; color: white; font-weight: 700; }")
        add_btn.clicked.connect(dlg.accept)
        btn_box.addWidget(add_btn)
        d_layout.addRow(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            pid = p_combo.currentData()
            rel = rel_combo.currentText()
            success, msg = self.hh_ctrl.add_member_to_household(self.hh.id, pid, rel)
            if success:
                self.load_members_table()
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def remove_selected_member(self):
        row = self.members_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn thành viên cần tách khỏi hộ.")
            return
        item = self.members_table.item(row, 0)
        pid = item.data(Qt.UserRole)
        success, msg = self.hh_ctrl.remove_member_from_household(self.hh.id, pid)
        if success:
            self.load_members_table()
        else:
            QMessageBox.critical(self, "Lỗi", msg)
