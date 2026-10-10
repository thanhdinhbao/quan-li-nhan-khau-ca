from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QPushButton, QLabel,
    QMessageBox, QFileDialog, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap, QFont
import qtawesome as qta
from datetime import datetime

from config import (
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_WHITE,
    COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from database.models import Person
from controllers.person_controller import PersonController
from controllers.area_controller import AreaController
from controllers.household_controller import HouseholdController
from services.auth_service import AuthService
from utils.constants import (
    GENDER_LIST, MARITAL_STATUS_LIST, RESIDENCE_STATUS_LIST, RELATIONSHIP_LIST
)
from utils.validators import validate_full_name, validate_id_card, validate_dob, validate_phone
from utils.formatters import format_date_vn, parse_date_to_iso

class PersonDialog(QDialog):
    def __init__(self, person: Person = None, is_read_only: bool = False, parent=None):
        super().__init__(parent)
        self.person = person or Person()
        self.is_read_only = is_read_only
        self.person_ctrl = PersonController()
        self.area_ctrl = AreaController()
        self.hh_ctrl = HouseholdController()

        title_action = "Chi tiết hồ sơ" if is_read_only else ("Chỉnh sửa nhân khẩu" if self.person.id else "Thêm mới nhân khẩu")
        self.setWindowTitle(f"{title_action} - Quản lý Nhân khẩu")
        self.resize(750, 620)
        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Dialog Title Header
        title_lbl = QLabel(title_action.upper())
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_PRIMARY_BURGUNDY}; border-bottom: 2px solid {COLOR_PRIMARY_BURGUNDY}; padding-bottom: 6px;")
        main_layout.addWidget(title_lbl)

        # Tab Widget
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
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {COLOR_PRIMARY_BURGUNDY};
                color: {COLOR_WHITE};
            }}
        """)

        # Build 4 Tabs
        self.tab1 = self._build_tab1_personal()
        self.tab2 = self._build_tab2_residence()
        self.tab3 = self._build_tab3_family()
        self.tab4 = self._build_tab4_additional()

        self.tabs.addTab(self.tab1, "1. Thông tin cá nhân")
        self.tabs.addTab(self.tab2, "2. Thông tin cư trú")
        self.tabs.addTab(self.tab3, "3. Thông tin gia đình")
        self.tabs.addTab(self.tab4, "4. Thông tin bổ sung")

        main_layout.addWidget(self.tabs, stretch=1)

        # Bottom Buttons Bar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Hủy bỏ" if not is_read_only else "Đóng")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("QPushButton { padding: 8px 16px; font-size: 13px; }")
        btn_layout.addWidget(self.cancel_btn)

        if not is_read_only:
            self.save_btn = QPushButton("Lưu hồ sơ")
            self.save_btn.setFixedWidth(120)
            self.save_btn.setCursor(Qt.PointingHandCursor)
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_PRIMARY_BURGUNDY};
                    color: {COLOR_WHITE};
                    font-weight: 700;
                    padding: 8px 16px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_SECONDARY_DARK_RED};
                }}
            """)
            self.save_btn.clicked.connect(self.save_person)
            btn_layout.addWidget(self.save_btn)

        main_layout.addLayout(btn_layout)

        # Fill Form Data if editing or viewing
        if self.person.id:
            self.populate_form()

        if self.is_read_only:
            self.set_read_only_mode()

    def _build_tab1_personal(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.txt_code = QLineEdit()
        self.txt_code.setReadOnly(True)
        self.txt_code.setPlaceholderText("Tự động sinh (Mã NK)")
        layout.addRow("Mã nhân khẩu:", self.txt_code)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Nhập đầy đủ Họ và tên (Bắt buộc)")
        layout.addRow("Họ và tên (*):", self.txt_name)

        dob_layout = QHBoxLayout()
        self.date_dob = QDateEdit()
        self.date_dob.setCalendarPopup(True)
        self.date_dob.setDisplayFormat("dd/mm/yyyy")
        self.date_dob.setDate(QDate.currentDate().addYears(-25))

        self.combo_gender = QComboBox()
        self.combo_gender.addItems(GENDER_LIST)
        dob_layout.addWidget(self.date_dob, stretch=2)
        dob_layout.addWidget(QLabel("Giới tính:"), stretch=1)
        dob_layout.addWidget(self.combo_gender, stretch=2)
        layout.addRow("Ngày sinh (*):", dob_layout)

        # CCCD Row
        cccd_layout = QHBoxLayout()
        self.txt_cccd = QLineEdit()
        self.txt_cccd.setPlaceholderText("Số CCCD/CMND (9 hoặc 12 số)")
        
        self.date_cccd = QDateEdit()
        self.date_cccd.setCalendarPopup(True)
        self.date_cccd.setDisplayFormat("dd/mm/yyyy")
        self.date_cccd.setDate(QDate.currentDate().addYears(-3))

        cccd_layout.addWidget(self.txt_cccd, stretch=2)
        cccd_layout.addWidget(QLabel("Ngày cấp:"), stretch=1)
        cccd_layout.addWidget(self.date_cccd, stretch=2)
        layout.addRow("Số CCCD/CMND:", cccd_layout)

        self.txt_cccd_place = QLineEdit()
        self.txt_cccd_place.setText("Cục CSQLHC về TTXH")
        layout.addRow("Nơi cấp CCCD:", self.txt_cccd_place)

        self.txt_hometown = QLineEdit()
        self.txt_hometown.setPlaceholderText("Tỉnh / Thành phố quê quán")
        layout.addRow("Quê quán:", self.txt_hometown)

        eth_rel_layout = QHBoxLayout()
        self.txt_ethnicity = QLineEdit("Kinh")
        self.txt_religion = QLineEdit("Không")
        self.txt_nationality = QLineEdit("Việt Nam")
        eth_rel_layout.addWidget(self.txt_ethnicity)
        eth_rel_layout.addWidget(QLabel("Tôn giáo:"))
        eth_rel_layout.addWidget(self.txt_religion)
        eth_rel_layout.addWidget(QLabel("Quốc tịch:"))
        eth_rel_layout.addWidget(self.txt_nationality)
        layout.addRow("Dân tộc:", eth_rel_layout)

        self.txt_occupation = QLineEdit()
        self.txt_workplace = QLineEdit()
        occ_layout = QHBoxLayout()
        occ_layout.addWidget(self.txt_occupation, stretch=2)
        occ_layout.addWidget(QLabel("Nơi làm việc:"), stretch=1)
        occ_layout.addWidget(self.txt_workplace, stretch=2)
        layout.addRow("Nghề nghiệp:", occ_layout)

        self.txt_phone = QLineEdit()
        self.txt_email = QLineEdit()
        contact_layout = QHBoxLayout()
        contact_layout.addWidget(self.txt_phone, stretch=2)
        contact_layout.addWidget(QLabel("Email:"), stretch=1)
        contact_layout.addWidget(self.txt_email, stretch=2)
        layout.addRow("Số điện thoại:", contact_layout)

        self.combo_marital = QComboBox()
        self.combo_marital.addItems(MARITAL_STATUS_LIST)
        layout.addRow("Tình trạng hôn nhân:", self.combo_marital)

        return widget

    def _build_tab2_residence(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.combo_area = QComboBox()
        areas = self.area_ctrl.get_all_areas()
        for a in areas:
            self.combo_area.addItem(a.name, a.id)
        layout.addRow("Khu vực / Thôn (*):", self.combo_area)

        self.txt_house_num = QLineEdit()
        self.txt_street = QLineEdit()
        addr_num_layout = QHBoxLayout()
        addr_num_layout.addWidget(self.txt_house_num, stretch=1)
        addr_num_layout.addWidget(QLabel("Tên Đường/Thôn/Xóm:"), stretch=1)
        addr_num_layout.addWidget(self.txt_street, stretch=2)
        layout.addRow("Số nhà:", addr_num_layout)

        self.txt_perm_addr = QLineEdit()
        layout.addRow("Địa chỉ thường trú:", self.txt_perm_addr)

        self.txt_temp_addr = QLineEdit()
        layout.addRow("Địa chỉ tạm trú:", self.txt_temp_addr)

        self.txt_curr_addr = QLineEdit()
        layout.addRow("Địa chỉ hiện tại:", self.txt_curr_addr)

        reg_dates_layout = QHBoxLayout()
        self.date_perm_reg = QDateEdit()
        self.date_perm_reg.setCalendarPopup(True)
        self.date_perm_reg.setDisplayFormat("dd/mm/yyyy")
        self.date_perm_reg.setDate(QDate.currentDate())

        self.date_temp_reg = QDateEdit()
        self.date_temp_reg.setCalendarPopup(True)
        self.date_temp_reg.setDisplayFormat("dd/mm/yyyy")
        self.date_temp_reg.setDate(QDate.currentDate())

        reg_dates_layout.addWidget(self.date_perm_reg)
        reg_dates_layout.addWidget(QLabel("Ngày ĐK Tạm trú:"))
        reg_dates_layout.addWidget(self.date_temp_reg)
        layout.addRow("Ngày ĐK Thường trú:", reg_dates_layout)

        self.combo_res_status = QComboBox()
        self.combo_res_status.addItems(RESIDENCE_STATUS_LIST)
        layout.addRow("Trạng thái cư trú:", self.combo_res_status)

        return widget

    def _build_tab3_family(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.combo_household = QComboBox()
        self.combo_household.addItem("-- Chọn hộ gia đình (Nếu có) --", 0)
        households, _ = self.hh_ctrl.get_households_paged(page_size=200)
        for h in households:
            self.combo_household.addItem(f"{h.household_code} - Chủ hộ: {h.head_full_name or 'Chưa chọn'} ({h.address_street})", h.id)
        layout.addRow("Mã hộ gia đình:", self.combo_household)

        self.combo_rel_head = QComboBox()
        self.combo_rel_head.addItems(RELATIONSHIP_LIST)
        layout.addRow("Quan hệ với chủ hộ:", self.combo_rel_head)

        father_layout = QHBoxLayout()
        self.txt_father_name = QLineEdit()
        self.txt_father_card = QLineEdit()
        father_layout.addWidget(self.txt_father_name, stretch=2)
        father_layout.addWidget(QLabel("CCCD Cha:"), stretch=1)
        father_layout.addWidget(self.txt_father_card, stretch=2)
        layout.addRow("Họ tên cha:", father_layout)

        mother_layout = QHBoxLayout()
        self.txt_mother_name = QLineEdit()
        self.txt_mother_card = QLineEdit()
        mother_layout.addWidget(self.txt_mother_name, stretch=2)
        mother_layout.addWidget(QLabel("CCCD Mẹ:"), stretch=1)
        mother_layout.addWidget(self.txt_mother_card, stretch=2)
        layout.addRow("Họ tên mẹ:", mother_layout)

        spouse_layout = QHBoxLayout()
        self.txt_spouse_name = QLineEdit()
        self.txt_spouse_card = QLineEdit()
        spouse_layout.addWidget(self.txt_spouse_name, stretch=2)
        spouse_layout.addWidget(QLabel("CCCD Vợ/Chồng:"), stretch=1)
        spouse_layout.addWidget(self.txt_spouse_card, stretch=2)
        layout.addRow("Họ tên vợ/chồng:", spouse_layout)

        return widget

    def _build_tab4_additional(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left Column: Avatar Upload & Preview Box
        avatar_group = QGroupBox("Ảnh chân dung nhân khẩu")
        avatar_layout = QVBoxLayout(avatar_group)
        avatar_layout.setAlignment(Qt.AlignCenter)

        self.lbl_avatar_img = QLabel()
        self.lbl_avatar_img.setFixedSize(120, 160)
        self.lbl_avatar_img.setStyleSheet("border: 2px dashed #CBD5E1; background-color: #F8FAFC; border-radius: 6px;")
        self.lbl_avatar_img.setAlignment(Qt.AlignCenter)
        self.lbl_avatar_img.setText("Chưa có ảnh")

        avatar_layout.addWidget(self.lbl_avatar_img, alignment=Qt.AlignCenter)

        btn_avatar_box = QHBoxLayout()
        self.btn_select_avatar = QPushButton("Chọn ảnh...")
        self.btn_select_avatar.clicked.connect(self.select_avatar_image)
        self.btn_clear_avatar = QPushButton("Xóa ảnh")
        self.btn_clear_avatar.clicked.connect(self.clear_avatar_image)

        btn_avatar_box.addWidget(self.btn_select_avatar)
        btn_avatar_box.addWidget(self.btn_clear_avatar)
        avatar_layout.addLayout(btn_avatar_box)

        layout.addWidget(avatar_group, stretch=1)

        # Right Column: Notes & System Audit Info
        right_box = QVBoxLayout()
        right_box.setSpacing(10)

        right_box.addWidget(QLabel("Ghi chú nghiệp vụ Công an:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Nhập các ghi chú theo dõi địa bàn, lưu ý nghiệp vụ...")
        right_box.addWidget(self.txt_notes, stretch=1)

        self.lbl_meta_info = QLabel("Hồ sơ mới - Chưa có nhật ký chỉnh sửa")
        self.lbl_meta_info.setStyleSheet("font-size: 11px; color: #64748B; font-style: italic;")
        right_box.addWidget(self.lbl_meta_info)

        layout.addLayout(right_box, stretch=2)

        self.avatar_filepath = ""
        return widget

    def select_avatar_image(self):
        from config import AVATARS_DIR
        import shutil
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh chân dung", "", "Image Files (*.jpg *.jpeg *.png)")
        if not file_path:
            return
        
        try:
            dest_name = f"avatar_{datetime.now().strftime('%Y%m%d_%H%M%S')}{Path(file_path).suffix}"
            dest_path = AVATARS_DIR / dest_name
            shutil.copy2(file_path, dest_path)
            
            self.avatar_filepath = str(dest_name)
            pix = QPixmap(str(dest_path)).scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_avatar_img.setPixmap(pix)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu ảnh chân dung: {e}")

    def clear_avatar_image(self):
        self.avatar_filepath = ""
        self.lbl_avatar_img.clear()
        self.lbl_avatar_img.setText("Chưa có ảnh")

    def populate_form(self):
        p = self.person
        self.txt_code.setText(p.person_code)
        self.txt_name.setText(p.full_name)
        if p.dob:
            dt = QDate.fromString(p.dob, "yyyy-MM-dd")
            if dt.isValid():
                self.date_dob.setDate(dt)
        
        idx = self.combo_gender.findText(p.gender)
        if idx >= 0:
            self.combo_gender.setCurrentIndex(idx)

        self.txt_cccd.setText(p.id_card_number or "")
        if p.id_card_date:
            dt = QDate.fromString(p.id_card_date, "yyyy-MM-dd")
            if dt.isValid():
                self.date_cccd.setDate(dt)
        self.txt_cccd_place.setText(p.id_card_place or "Cục CSQLHC về TTXH")
        self.txt_hometown.setText(p.hometown or "")
        self.txt_ethnicity.setText(p.ethnicity or "Kinh")
        self.txt_religion.setText(p.religion or "Không")
        self.txt_nationality.setText(p.nationality or "Việt Nam")
        self.txt_occupation.setText(p.occupation or "")
        self.txt_workplace.setText(p.workplace or "")
        self.txt_phone.setText(p.phone or "")
        self.txt_email.setText(p.email or "")

        idx = self.combo_marital.findText(p.marital_status or "Độc thân")
        if idx >= 0:
            self.combo_marital.setCurrentIndex(idx)

        # Tab 2 Residence
        idx = self.combo_area.findData(p.area_id)
        if idx >= 0:
            self.combo_area.setCurrentIndex(idx)

        self.txt_house_num.setText(p.house_number or "")
        self.txt_street.setText(p.street_village or "")
        self.txt_perm_addr.setText(p.permanent_address or "")
        self.txt_temp_addr.setText(p.temporary_address or "")
        self.txt_curr_addr.setText(p.current_address or "")

        if p.permanent_reg_date:
            dt = QDate.fromString(p.permanent_reg_date, "yyyy-MM-dd")
            if dt.isValid():
                self.date_perm_reg.setDate(dt)

        idx = self.combo_res_status.findText(p.residence_status or "Thường trú")
        if idx >= 0:
            self.combo_res_status.setCurrentIndex(idx)

        # Tab 3 Family
        if p.household_id:
            idx = self.combo_household.findData(p.household_id)
            if idx >= 0:
                self.combo_household.setCurrentIndex(idx)

        idx = self.combo_rel_head.findText(p.relationship_with_head or "Khác")
        if idx >= 0:
            self.combo_rel_head.setCurrentIndex(idx)

        self.txt_father_name.setText(p.father_name or "")
        self.txt_father_card.setText(p.father_id_card or "")
        self.txt_mother_name.setText(p.mother_name or "")
        self.txt_mother_card.setText(p.mother_id_card or "")
        self.txt_spouse_name.setText(p.spouse_name or "")
        self.txt_spouse_card.setText(p.spouse_id_card or "")

        # Tab 4
        self.txt_notes.setText(p.notes or "")
        if p.avatar_path:
            self.avatar_filepath = p.avatar_path
            from config import AVATARS_DIR
            av_file = AVATARS_DIR / p.avatar_path
            if av_file.exists():
                pix = QPixmap(str(av_file)).scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_avatar_img.setPixmap(pix)
        
        if p.created_at:
            self.lbl_meta_info.setText(f"Ngày tạo: {format_date_vn(p.created_at)} | Ngày cập nhật gần nhất: {format_date_vn(p.updated_at or p.created_at)}")

    def set_read_only_mode(self):
        for widget in self.findChildren((QLineEdit, QComboBox, QDateEdit, QTextEdit)):
            widget.setEnabled(False)

    def save_person(self):
        name = self.txt_name.text().strip()
        valid, msg = validate_full_name(name)
        if not valid:
            QMessageBox.warning(self, "Cảnh báo lỗi nhập liệu", msg)
            self.tabs.setCurrentIndex(0)
            self.txt_name.setFocus()
            return

        dob_str = self.date_dob.date().toString("yyyy-MM-dd")
        valid, msg = validate_dob(dob_str)
        if not valid:
            QMessageBox.warning(self, "Cảnh báo lỗi nhập liệu", msg)
            self.tabs.setCurrentIndex(0)
            return

        cccd = self.txt_cccd.text().strip()
        if cccd:
            valid, msg = validate_id_card(cccd)
            if not valid:
                QMessageBox.warning(self, "Cảnh báo lỗi nhập liệu", msg)
                self.tabs.setCurrentIndex(0)
                self.txt_cccd.setFocus()
                return

        phone = self.txt_phone.text().strip()
        if phone:
            valid, msg = validate_phone(phone)
            if not valid:
                QMessageBox.warning(self, "Cảnh báo lỗi nhập liệu", msg)
                self.tabs.setCurrentIndex(0)
                self.txt_phone.setFocus()
                return

        # Bind Form values to Person object
        p = self.person
        p.full_name = name
        p.dob = dob_str
        p.gender = self.combo_gender.currentText()
        p.id_card_number = cccd
        p.id_card_date = self.date_cccd.date().toString("yyyy-MM-dd")
        p.id_card_place = self.txt_cccd_place.text().strip()
        p.hometown = self.txt_hometown.text().strip()
        p.ethnicity = self.txt_ethnicity.text().strip() or "Kinh"
        p.religion = self.txt_religion.text().strip() or "Không"
        p.nationality = self.txt_nationality.text().strip() or "Việt Nam"
        p.occupation = self.txt_occupation.text().strip()
        p.workplace = self.txt_workplace.text().strip()
        p.phone = phone
        p.email = self.txt_email.text().strip()
        p.marital_status = self.combo_marital.currentText()

        p.area_id = self.combo_area.currentData() or 1
        p.house_number = self.txt_house_num.text().strip()
        p.street_village = self.txt_street.text().strip()
        p.permanent_address = self.txt_perm_addr.text().strip() or f"{p.house_number} {p.street_village}, {self.combo_area.currentText()}"
        p.temporary_address = self.txt_temp_addr.text().strip()
        p.current_address = self.txt_curr_addr.text().strip() or p.permanent_address
        p.permanent_reg_date = self.date_perm_reg.date().toString("yyyy-MM-dd")
        p.residence_status = self.combo_res_status.currentText()

        hh_id = self.combo_household.currentData()
        p.household_id = hh_id if hh_id > 0 else None
        p.relationship_with_head = self.combo_rel_head.currentText()
        p.father_name = self.txt_father_name.text().strip()
        p.father_id_card = self.txt_father_card.text().strip()
        p.mother_name = self.txt_mother_name.text().strip()
        p.mother_id_card = self.txt_mother_card.text().strip()
        p.spouse_name = self.txt_spouse_name.text().strip()
        p.spouse_id_card = self.txt_spouse_card.text().strip()

        p.notes = self.txt_notes.toPlainText().strip()
        p.avatar_path = getattr(self, 'avatar_filepath', '')

        user = AuthService.get_current_user()
        user_id = user.id if user else None

        if p.id:
            success, result_msg = self.person_ctrl.update_person(p, user_id=user_id)
        else:
            success, result_msg, pid = self.person_ctrl.add_person(p, user_id=user_id)

        if success:
            QMessageBox.information(self, "Thành công", result_msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi lưu dữ liệu", result_msg)
