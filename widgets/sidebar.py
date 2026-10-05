from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont
import qtawesome as qta
from config import (
    COLOR_NAVY_SIDEBAR, COLOR_NAVY_DARK, COLOR_PRIMARY_BURGUNDY,
    COLOR_WHITE, COLOR_TEXT_MUTED
)

class SidebarWidget(QWidget):
    menu_selected = pyqtSignal(int)  # Emits selected page index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet(f"""
            SidebarWidget {{
                background-color: {COLOR_NAVY_SIDEBAR};
                border-right: 1px solid #0D213A;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Top Sidebar Logo & Branding Area
        brand_frame = QFrame()
        brand_frame.setStyleSheet(f"background-color: {COLOR_NAVY_DARK}; border-bottom: 1px solid #1E4270;")
        brand_frame.setFixedHeight(64)
        brand_layout = QVBoxLayout(brand_frame)
        brand_layout.setContentsMargins(16, 10, 16, 10)

        brand_lbl = QLabel("QUẢN LÝ NHÂN KHẨU")
        brand_lbl.setStyleSheet(f"color: {COLOR_WHITE}; font-size: 14px; font-weight: 800; letter-spacing: 0.5px;")
        sub_lbl = QLabel("CÔNG AN PHƯỜNG NÔNG TRANG")
        sub_lbl.setStyleSheet("color: #9DB2CE; font-size: 11px; font-weight: 600;")
        
        brand_layout.addWidget(brand_lbl)
        brand_layout.addWidget(sub_lbl)
        layout.addWidget(brand_frame)

        # 2. Scroll Area for Menu Items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background-color: {COLOR_NAVY_SIDEBAR}; border: none; }}
            QWidget {{ background-color: {COLOR_NAVY_SIDEBAR}; }}
            QScrollBar:vertical {{
                background: {COLOR_NAVY_SIDEBAR};
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: #254F85;
                border-radius: 3px;
            }}
        """)

        menu_container = QWidget()
        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(8, 12, 8, 12)
        menu_layout.setSpacing(4)

        # Menu definition: (Index, Title, IconName)
        self.menu_items_def = [
            (0, "Tổng quan", "fa5s.tachometer-alt"),
            (1, "Quản lý nhân khẩu", "fa5s.users"),
            (2, "Quản lý hộ gia đình", "fa5s.home"),
            (3, "Quản lý khu vực", "fa5s.map-marker-alt"),
            (4, "Import Excel", "fa5s.file-excel"),
            (5, "Export dữ liệu", "fa5s.file-export"),
            (6, "Thống kê báo cáo", "fa5s.chart-bar"),
            (7, "Nhật ký hoạt động", "fa5s.history"),
            (8, "Sao lưu và phục hồi", "fa5s.database"),
            (9, "Cài đặt hệ thống", "fa5s.cog"),
        ]

        self.buttons = []
        for idx, title, icon_name in self.menu_items_def:
            btn = QPushButton(f"  {title}")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(42)
            
            try:
                btn.setIcon(qta.icon(icon_name, color='#B0C4DE'))
                btn.setIconSize(QSize(18, 18))
            except Exception:
                pass

            btn.setStyleSheet(f"""
                QPushButton {{
                    color: #E2E8F0;
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: #21487A;
                    color: {COLOR_WHITE};
                }}
                QPushButton:checked {{
                    background-color: {COLOR_PRIMARY_BURGUNDY};
                    color: {COLOR_WHITE};
                    font-weight: 700;
                }}
            """)
            btn.clicked.connect(lambda checked, i=idx: self._on_btn_clicked(i))
            menu_layout.addWidget(btn)
            self.buttons.append(btn)

        menu_layout.addStretch()
        scroll.setWidget(menu_container)
        layout.addWidget(scroll, stretch=1)

        # 3. Bottom Decorative Motto Card
        motto_frame = QFrame()
        motto_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_NAVY_DARK};
                border-top: 1px solid #1E4270;
                padding: 12px;
            }}
        """)
        motto_box = QVBoxLayout(motto_frame)
        motto_box.setContentsMargins(8, 8, 8, 8)
        
        motto_txt1 = QLabel("Vì an ninh Tổ quốc")
        motto_txt1.setAlignment(Qt.AlignCenter)
        motto_txt1.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 700; italic;")

        motto_txt2 = QLabel("Vì hạnh phúc nhân dân")
        motto_txt2.setAlignment(Qt.AlignCenter)
        motto_txt2.setStyleSheet(f"color: {COLOR_PRIMARY_BURGUNDY}; font-size: 12px; font-weight: 800;")

        motto_box.addWidget(motto_txt1)
        motto_box.addWidget(motto_txt2)
        layout.addWidget(motto_frame)

        # Select first item by default
        if self.buttons:
            self.buttons[0].setChecked(True)

    def _on_btn_clicked(self, index: int):
        self.menu_selected.emit(index)

    def select_menu(self, index: int):
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
