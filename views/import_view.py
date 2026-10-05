import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog, QFrame,
    QProgressBar, QCheckBox, QGroupBox, QHeaderView, QTextEdit
)
from PyQt5.QtCore import Qt
import qtawesome as qta
from pathlib import Path

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_SECONDARY_DARK_RED, COLOR_BORDER, COLOR_NAVY_SIDEBAR
)
from services.excel_service import ExcelImportWorker
from services.auth_service import AuthService

class ImportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file_path = ""
        self.excel_df = None
        self.worker = None

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        title_lbl = QLabel("Nhập dữ liệu Nhân khẩu từ File Excel")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        main_layout.addWidget(title_lbl)

        # 1. Step 1 Card: File & Sheet Selector
        step1_card = QGroupBox("Bước 1: Chọn Tệp dữ liệu Excel (.xlsx, .xls)")
        step1_layout = QHBoxLayout(step1_card)

        self.btn_select_file = QPushButton("  Chọn File Excel...")
        self.btn_select_file.setFixedHeight(36)
        try:
            self.btn_select_file.setIcon(qta.icon('fa5s.folder-open', color=COLOR_WHITE))
        except Exception:
            pass
        self.btn_select_file.setStyleSheet(f"QPushButton {{ background-color: {COLOR_PRIMARY_BURGUNDY}; color: white; font-weight: 700; border-radius: 6px; padding: 0 14px; }}")
        self.btn_select_file.clicked.connect(self.select_file)
        step1_layout.addWidget(self.btn_select_file)

        self.lbl_file_name = QLabel("Chưa chọn file nào")
        self.lbl_file_name.setStyleSheet("font-size: 13px; font-weight: 600; color: #6C757D;")
        step1_layout.addWidget(self.lbl_file_name, stretch=1)

        step1_layout.addWidget(QLabel("Chọn Sheet:"))
        self.combo_sheets = QComboBox()
        self.combo_sheets.setFixedWidth(160)
        self.combo_sheets.currentIndexChanged.connect(self.on_sheet_changed)
        step1_layout.addWidget(self.combo_sheets)

        main_layout.addWidget(step1_card)

        # 2. Step 2 Card: Column Mapping
        step2_card = QGroupBox("Bước 2: Ánh xạ Cột Excel sang Cột Cơ sở dữ liệu")
        step2_layout = QHBoxLayout(step2_card)

        # Mapping dictionaries: db_field -> QComboBox
        self.mapping_combos = {}
        db_fields = [
            ("full_name", "Họ và tên (*)"),
            ("id_card_number", "Số CCCD/CMND"),
            ("dob", "Ngày sinh"),
            ("gender", "Giới tính"),
            ("phone", "Số điện thoại"),
            ("hometown", "Quê quán"),
            ("area_name", "Khu vực / Thôn"),
            ("permanent_address", "Địa chỉ thường trú")
        ]

        for field_key, field_name in db_fields:
            v_box = QVBoxLayout()
            lbl = QLabel(field_name)
            lbl.setStyleSheet("font-size: 11px; font-weight: 700;")
            cb = QComboBox()
            cb.addItem("-- Bỏ qua --", "")
            self.mapping_combos[field_key] = cb
            v_box.addWidget(lbl)
            v_box.addWidget(cb)
            step2_layout.addLayout(v_box)

        main_layout.addWidget(step2_card)

        # Options: Update existing
        opt_layout = QHBoxLayout()
        self.chk_update_dup = QCheckBox("Nếu phát hiện trùng CCCD: Cập nhật đè dữ liệu mới (Nếu bỏ chọn sẽ Bỏ qua dòng trùng)")
        self.chk_update_dup.setStyleSheet("font-size: 13px; font-weight: 600; color: #17365D;")
        opt_layout.addWidget(self.chk_update_dup)
        main_layout.addLayout(opt_layout)

        # 3. Step 3: Data Preview (First 20 rows)
        preview_lbl = QLabel("Xem trước 20 dòng dữ liệu đầu tiên:")
        preview_lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
        main_layout.addWidget(preview_lbl)

        self.table_preview = QTableWidget()
        self.table_preview.setStyleSheet("QTableWidget { background: white; gridline-color: #DEE2E6; }")
        main_layout.addWidget(self.table_preview, stretch=1)

        # Progress bar & Actions
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        act_layout = QHBoxLayout()
        act_layout.addStretch()

        self.btn_start_import = QPushButton("XÁC NHẬN NHẬP DỮ LIỆU INTO SYSTEM")
        self.btn_start_import.setCursor(Qt.PointingHandCursor)
        self.btn_start_import.setFixedHeight(40)
        self.btn_start_import.setEnabled(False)
        self.btn_start_import.setStyleSheet(f"""
            QPushButton {{
                background-color: #198754;
                color: white;
                font-weight: 800;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 14px;
            }}
            QPushButton:disabled {{
                background-color: #6C757D;
            }}
        """)
        self.btn_start_import.clicked.connect(self.start_import)
        act_layout.addWidget(self.btn_start_import)

        main_layout.addLayout(act_layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
        
        self.selected_file_path = file_path
        self.lbl_file_name.setText(Path(file_path).name)

        try:
            xl = pd.ExcelFile(file_path)
            self.combo_sheets.blockSignals(True)
            self.combo_sheets.clear()
            self.combo_sheets.addItems(xl.sheet_names)
            self.combo_sheets.blockSignals(False)
            self.load_sheet_preview(xl.sheet_names[0])
        except Exception as e:
            QMessageBox.critical(self, "Lỗi đọc file Excel", f"Không thể mở file Excel: {e}")

    def on_sheet_changed(self, index: int):
        sheet_name = self.combo_sheets.currentText()
        if sheet_name and self.selected_file_path:
            self.load_sheet_preview(sheet_name)

    def load_sheet_preview(self, sheet_name: str):
        try:
            df = pd.read_excel(self.selected_file_path, sheet_name=sheet_name, nrows=20, dtype=str)
            df = df.fillna("")
            self.excel_df = df

            # Populate combo mappings
            cols = list(df.columns)
            for field_key, cb in self.mapping_combos.items():
                cb.blockSignals(True)
                cb.clear()
                cb.addItem("-- Bỏ qua --", "")
                for c in cols:
                    cb.addItem(str(c), str(c))
                
                # Auto detect common column names
                matched_col = self.auto_detect_column(field_key, cols)
                if matched_col:
                    idx = cb.findText(matched_col)
                    if idx >= 0:
                        cb.setCurrentIndex(idx)
                cb.blockSignals(False)

            # Display preview in table
            self.table_preview.setColumnCount(len(cols))
            self.table_preview.setHorizontalHeaderLabels([str(c) for c in cols])
            self.table_preview.setRowCount(len(df))

            for r_idx, row in df.iterrows():
                for c_idx, col_name in enumerate(cols):
                    self.table_preview.setItem(r_idx, c_idx, QTableWidgetItem(str(row[col_name])))

            self.btn_start_import.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Preview", f"Lỗi đọc sheet dữ liệu: {e}")

    def auto_detect_column(self, field_key: str, cols: list) -> str:
        keywords = {
            "full_name": ["họ tên", "họ và tên", "họ tên nhân khẩu", "full name", "tên"],
            "id_card_number": ["cccd", "số cccd", "cmnd", "số cmnd", "số định danh"],
            "dob": ["ngày sinh", "dob", "năm sinh"],
            "gender": ["giới tính", "gender"],
            "phone": ["số điện thoại", "sđt", "phone", "điện thoại"],
            "hometown": ["quê quán", "hometown"],
            "area_name": ["khu vực", "thôn", "xóm", "tổ dân phố", "địa bàn"],
            "permanent_address": ["địa chỉ", "thường trú", "địa chỉ thường trú"]
        }
        target_kw = keywords.get(field_key, [])
        for c in cols:
            c_lower = str(c).strip().lower()
            for kw in target_kw:
                if kw in c_lower:
                    return str(c)
        return ""

    def start_import(self):
        if not AuthService.check_permission("IMPORT_EXCEL"):
            QMessageBox.warning(self, "Từ chối truy cập", "Bạn không có quyền Nhập dữ liệu Excel.")
            return

        # Prepare column mapping
        mapping = {}
        for field_key, cb in self.mapping_combos.items():
            val = cb.currentData()
            if val:
                mapping[field_key] = val

        if "full_name" not in mapping:
            QMessageBox.warning(self, "Cảnh báo ánh xạ", "Vui lòng ánh xạ cột 'Họ và tên' trước khi nhập dữ liệu.")
            return

        user = AuthService.get_current_user()
        user_id = user.id if user else None

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.btn_start_import.setEnabled(False)

        sheet_name = self.combo_sheets.currentText()
        update_existing = self.chk_update_dup.isChecked()

        self.worker = ExcelImportWorker(self.selected_file_path, sheet_name, mapping, update_existing, user_id)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished_import.connect(self.on_import_finished)
        self.worker.error_occurred.connect(self.on_import_error)
        self.worker.start()

    def update_progress(self, current: int, total: int):
        pct = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)

    def on_import_finished(self, summary: dict):
        self.progress_bar.hide()
        self.btn_start_import.setEnabled(True)

        msg = (
            f"NHẬP DỮ LIỆU HOÀN TẤT!\n\n"
            f"• Tổng số dòng trong Excel: {summary['total']}\n"
            f"• Số bản ghi nhập thành công: {summary['success']}\n"
            f"• Số bản ghi bị bỏ qua (trùng CCCD): {summary['skipped']}\n"
            f"• Số bản ghi bị lỗi: {summary['error']}\n"
            f"• Thời gian thực hiện: {summary['elapsed_seconds']} giây"
        )
        QMessageBox.information(self, "Kết quả Nhập dữ liệu Excel", msg)

    def on_import_error(self, err_msg: str):
        self.progress_bar.hide()
        self.btn_start_import.setEnabled(True)
        QMessageBox.critical(self, "Lỗi Nhập Dữ Liệu", f"Quá trình Import thất bại: {err_msg}")
