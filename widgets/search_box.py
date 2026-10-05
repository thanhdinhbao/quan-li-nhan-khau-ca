from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import qtawesome as qta
from config import COLOR_WHITE, COLOR_BORDER, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY_BURGUNDY

class SearchBox(QWidget):
    searched = pyqtSignal(str)

    def __init__(self, placeholder: str = "Tìm kiếm theo Họ tên, CCCD, Mã nhân khẩu, SĐT...", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
            QWidget:focus-within {{
                border: 1.5px solid {COLOR_PRIMARY_BURGUNDY};
            }}
        """)
        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(10, 4, 10, 4)
        c_layout.setSpacing(6)

        # Search Icon
        search_icon = QLabel()
        try:
            search_icon.setPixmap(qta.icon('fa5s.search', color=COLOR_TEXT_MUTED).pixmap(16, 16))
        except Exception:
            search_icon.setText("🔍")
        c_layout.addWidget(search_icon)

        # Input Field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
        """)
        c_layout.addWidget(self.input_field, stretch=1)

        # Clear Button
        self.clear_btn = QPushButton()
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
        """)
        try:
            self.clear_btn.setIcon(qta.icon('fa5s.times-circle', color=COLOR_TEXT_MUTED))
        except Exception:
            self.clear_btn.setText("×")
        self.clear_btn.hide()
        self.clear_btn.clicked.connect(self.clear_text)
        c_layout.addWidget(self.clear_btn)

        layout.addWidget(container)

        # Debounce Timer (300ms)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timeout)

        self.input_field.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        if text.strip():
            self.clear_btn.show()
        else:
            self.clear_btn.hide()
        self.timer.start(300)

    def _on_timeout(self):
        self.searched.emit(self.input_field.text().strip())

    def clear(self):
        self.clear_text()

    def clear_text(self):
        self.input_field.clear()
        self.searched.emit("")

    def text(self) -> str:
        return self.input_field.text().strip()
