from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_PRIMARY_BURGUNDY,
    COLOR_BORDER, COLOR_NAVY_SIDEBAR
)

class CustomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        
        # Header formatting
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setVisible(False)
        self.setRowHeight(40, 40)
        
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_WHITE};
                alternate-background-color: #F9FAFC;
                gridline-color: {COLOR_BORDER};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
            QHeaderView::section {{
                background-color: #F1F3F7;
                color: {COLOR_NAVY_SIDEBAR};
                font-weight: 700;
                font-size: 13px;
                padding: 8px;
                border: none;
                border-bottom: 2px solid {COLOR_PRIMARY_BURGUNDY};
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background-color: #E8F0FE;
                color: #1a73e8;
                font-weight: 600;
            }}
            QTableWidget::item:hover {{
                background-color: #F0F4F8;
            }}
        """)

    def set_column_widths(self, widths_dict: dict):
        """Allows setting exact pixel width for specific column indices."""
        for col_idx, width in widths_dict.items():
            self.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.Interactive)
            self.setColumnWidth(col_idx, width)
