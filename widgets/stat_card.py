from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import qtawesome as qta
from config import COLOR_WHITE, COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED

class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon_name: str, icon_color: str, subtext: str = "", subtext_color: str = "#198754", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
            StatCard:hover {{
                border: 1.5px solid {icon_color};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Left Info Layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; font-weight: 600;")
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-size: 24px; font-weight: 700;")

        info_layout.addWidget(self.title_lbl)
        info_layout.addWidget(self.val_lbl)

        if subtext:
            self.sub_lbl = QLabel(subtext)
            self.sub_lbl.setStyleSheet(f"color: {subtext_color}; font-size: 11px; font-weight: 500;")
            info_layout.addWidget(self.sub_lbl)

        info_layout.addStretch()
        layout.addLayout(info_layout, stretch=1)

        # Icon Container Right
        icon_container = QWidget()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet(f"""
            background-color: {icon_color}18;
            border-radius: 24px;
        """)
        icon_box = QVBoxLayout(icon_container)
        icon_box.setContentsMargins(0, 0, 0, 0)
        
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        try:
            pixmap = qta.icon(icon_name, color=icon_color).pixmap(24, 24)
            icon_lbl.setPixmap(pixmap)
        except Exception:
            icon_lbl.setText("●")
            icon_lbl.setStyleSheet(f"color: {icon_color}; font-size: 20px;")
            
        icon_box.addWidget(icon_lbl)
        layout.addWidget(icon_container, alignment=Qt.AlignTop | Qt.AlignRight)

    def update_value(self, new_value: str, new_subtext: str = None):
        self.val_lbl.setText(str(new_value))
        if new_subtext is not None and hasattr(self, 'sub_lbl'):
            self.sub_lbl.setText(new_subtext)
