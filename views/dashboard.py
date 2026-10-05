import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import qtawesome as qta

from config import (
    COLOR_WHITE, COLOR_BG_LIGHT, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY_BURGUNDY, COLOR_BORDER, COLOR_SUCCESS_GREEN, COLOR_WARNING_ORANGE, COLOR_NAVY_SIDEBAR
)
from widgets.stat_card import StatCard
from controllers.person_controller import PersonController
from controllers.area_controller import AreaController
from database.db_manager import DatabaseManager
from utils.formatters import format_number

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.person_ctrl = PersonController()
        self.area_ctrl = AreaController()
        self.db = DatabaseManager()

        self.setStyleSheet(f"background-color: {COLOR_BG_LIGHT};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Top Header Bar (Title & Area Filter)
        top_bar = QHBoxLayout()
        title_lbl = QLabel("Tổng quan")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_NAVY_SIDEBAR};")
        top_bar.addWidget(title_lbl)

        top_bar.addStretch()

        filter_label = QLabel("Khu vực:")
        filter_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT_MUTED};")
        top_bar.addWidget(filter_label)

        self.area_combo = QComboBox()
        self.area_combo.setFixedWidth(180)
        self.area_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                color: {COLOR_TEXT_MAIN};
            }}
        """)
        self.area_combo.addItem("Tất cả khu vực", 0)
        self.area_combo.currentIndexChanged.connect(self.load_data)
        top_bar.addWidget(self.area_combo)

        main_layout.addLayout(top_bar)

        # 2. Main Scroll Content Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Left Column: Stat Cards & 4 Charts Grid (Stretch 3)
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Stat Cards Grid 1
        cards_grid1 = QGridLayout()
        cards_grid1.setSpacing(12)

        self.card_total = StatCard("Tổng số nhân khẩu", "0", "fa5s.users", "#0D6EFD", "người", "#198754")
        self.card_hh = StatCard("Tổng số hộ gia đình", "0", "fa5s.home", "#198754", "hộ", "#198754")
        self.card_areas = StatCard("Tổng số khu vực", "0", "fa5s.map-marker-alt", "#6F42C1", "khu", "#6C757D")
        self.card_males = StatCard("Nam", "0", "fa5s.male", "#0D6EFD", "0%", "#0D6EFD")
        self.card_females = StatCard("Nữ", "0", "fa5s.female", "#D63384", "0%", "#D63384")

        cards_grid1.addWidget(self.card_total, 0, 0)
        cards_grid1.addWidget(self.card_hh, 0, 1)
        cards_grid1.addWidget(self.card_areas, 0, 2)
        cards_grid1.addWidget(self.card_males, 1, 0)
        cards_grid1.addWidget(self.card_females, 1, 1)

        left_col.addLayout(cards_grid1)

        # Stat Cards Grid 2 (Warnings / Incomplete)
        cards_grid2 = QHBoxLayout()
        cards_grid2.setSpacing(12)

        self.card_check = StatCard("Hồ sơ cần kiểm tra", "0", "fa5s.exclamation-triangle", "#F39C12", "thiếu CCCD/SĐT", "#F39C12")
        self.card_incomp = StatCard("Hồ sơ chưa đầy đủ thông tin", "0", "fa5s.info-circle", "#0DCAF0", "thiếu quê quán/nghề nghiệp", "#0DCAF0")

        cards_grid2.addWidget(self.card_check)
        cards_grid2.addWidget(self.card_incomp)

        left_col.addLayout(cards_grid2)

        # 4 Matplotlib Charts (2x2 Grid)
        charts_grid = QGridLayout()
        charts_grid.setSpacing(12)

        # Chart 1: Bar chart (Dân số theo khu vực)
        self.fig1 = Figure(figsize=(4, 3), dpi=100)
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")

        # Chart 2: Donut chart (Cơ cấu giới tính)
        self.fig2 = Figure(figsize=(4, 3), dpi=100)
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")

        # Chart 3: Line chart (Cơ cấu độ tuổi)
        self.fig3 = Figure(figsize=(4, 3), dpi=100)
        self.canvas3 = FigureCanvas(self.fig3)
        self.canvas3.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")

        # Chart 4: Pie chart (Hộ theo từng khu)
        self.fig4 = Figure(figsize=(4, 3), dpi=100)
        self.canvas4 = FigureCanvas(self.fig4)
        self.canvas4.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")

        charts_grid.addWidget(self.canvas1, 0, 0)
        charts_grid.addWidget(self.canvas2, 0, 1)
        charts_grid.addWidget(self.canvas3, 1, 0)
        charts_grid.addWidget(self.canvas4, 1, 1)

        left_col.addLayout(charts_grid)
        content_layout.addLayout(left_col, stretch=3)

        # Right Column: Area Summary & Recent Audit Log (Stretch 1)
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # Area Summary Table Frame
        area_frame = QFrame()
        area_frame.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        area_layout = QVBoxLayout(area_frame)
        area_layout.setContentsMargins(12, 12, 12, 12)

        area_header = QLabel("Danh sách khu vực")
        area_header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_NAVY_SIDEBAR};")
        area_layout.addWidget(area_header)

        self.area_table = QTableWidget()
        self.area_table.setColumnCount(3)
        self.area_table.setHorizontalHeaderLabels(["Khu vực", "Nhân khẩu", "Hộ gia đình"])
        self.area_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.area_table.verticalHeader().setVisible(False)
        self.area_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.area_table.setStyleSheet("QTableWidget { border: none; font-size: 12px; } QHeaderView::section { font-weight: 700; background: #F4F6F9; border: none; }")
        area_layout.addWidget(self.area_table)

        right_col.addWidget(area_frame, stretch=1)

        # Recent Activity Feed Frame
        activity_frame = QFrame()
        activity_frame.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        act_layout = QVBoxLayout(activity_frame)
        act_layout.setContentsMargins(12, 12, 12, 12)

        act_header = QLabel("Hoạt động gần đây")
        act_header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_NAVY_SIDEBAR};")
        act_layout.addWidget(act_header)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(2)
        self.activity_table.setHorizontalHeaderLabels(["Thao tác", "Thời gian"])
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activity_table.setStyleSheet("QTableWidget { border: none; font-size: 12px; } QHeaderView::section { font-weight: 700; background: #F4F6F9; border: none; }")
        act_layout.addWidget(self.activity_table)

        right_col.addWidget(activity_frame, stretch=1)

        content_layout.addLayout(right_col, stretch=1)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Initial load
        self.load_areas_combo()
        self.load_data()

    def load_areas_combo(self):
        self.area_combo.blockSignals(True)
        self.area_combo.clear()
        self.area_combo.addItem("Tất cả khu vực", 0)
        areas = self.area_ctrl.get_all_areas()
        for a in areas:
            self.area_combo.addItem(a.name, a.id)
        self.area_combo.blockSignals(False)

    def load_data(self):
        selected_area_id = self.area_combo.currentData()
        stats = self.person_ctrl.get_dashboard_statistics(area_id=selected_area_id)
        if not stats:
            return

        total_p = stats.get("total_persons", 0)
        males = stats.get("total_males", 0)
        females = stats.get("total_females", 0)
        hh_count = stats.get("total_households", 0)
        areas_count = stats.get("total_areas", 0)
        check_cnt = stats.get("records_needing_check", 0)
        incomp_cnt = stats.get("incomplete_records", 0)

        male_pct = (males / total_p * 100) if total_p > 0 else 0
        female_pct = (females / total_p * 100) if total_p > 0 else 0

        self.card_total.update_value(format_number(total_p), "nhân khẩu đang quản lý")
        self.card_hh.update_value(format_number(hh_count), "hộ gia đình")
        self.card_areas.update_value(format_number(areas_count), "khu vực/thôn")
        self.card_males.update_value(format_number(males), f"{male_pct:.1f}% tổng số")
        self.card_females.update_value(format_number(females), f"{female_pct:.1f}% tổng số")
        self.card_check.update_value(format_number(check_cnt), "hồ sơ thiếu CCCD/SĐT")
        self.card_incomp.update_value(format_number(incomp_cnt), "hồ sơ chưa đầy đủ")

        # Update Charts
        self.render_chart1_bar(stats.get("pop_by_area", {}))
        self.render_chart2_donut(males, females)
        self.render_chart3_line(stats.get("age_demographics", {}))
        self.render_chart4_pie(stats.get("hh_by_area", {}))

        # Update Right Panel Tables
        self.load_area_table()
        self.load_recent_activities()

    def render_chart1_bar(self, pop_data: dict):
        self.fig1.clear()
        ax = self.fig1.add_subplot(111)
        if pop_data:
            labels = list(pop_data.keys())
            values = list(pop_data.values())
            ax.bar(labels, values, color='#0D6EFD', width=0.5, edgecolor='#0B5ED7')
            ax.set_title("Dân số theo khu vực", fontsize=11, fontweight='bold', color='#17365D')
            ax.tick_params(axis='x', rotation=30, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
        self.fig1.tight_layout()
        self.canvas1.draw()

    def render_chart2_donut(self, males: int, females: int):
        self.fig2.clear()
        ax = self.fig2.add_subplot(111)
        if males > 0 or females > 0:
            labels = ['Nam', 'Nữ']
            sizes = [males, females]
            colors = ['#0D6EFD', '#D63384']
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops=dict(width=0.4, edgecolor='w'))
            for t in texts + autotexts:
                t.set_fontsize(8)
            ax.set_title("Cơ cấu giới tính", fontsize=11, fontweight='bold', color='#17365D')
        self.fig2.tight_layout()
        self.canvas2.draw()

    def render_chart3_line(self, age_data: dict):
        self.fig3.clear()
        ax = self.fig3.add_subplot(111)
        if age_data:
            labels = list(age_data.keys())
            values = list(age_data.values())
            ax.plot(labels, values, marker='o', color='#198754', linewidth=2, markersize=6)
            ax.fill_between(labels, values, color='#198754', alpha=0.15)
            ax.set_title("Cơ cấu độ tuổi", fontsize=11, fontweight='bold', color='#17365D')
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            ax.grid(True, linestyle='--', alpha=0.5)
        self.fig3.tight_layout()
        self.canvas3.draw()

    def render_chart4_pie(self, hh_data: dict):
        self.fig4.clear()
        ax = self.fig4.add_subplot(111)
        if hh_data and sum(hh_data.values()) > 0:
            labels = list(hh_data.keys())
            values = list(hh_data.values())
            colors = ['#0D6EFD', '#198754', '#F39C12', '#D63384', '#6F42C1', '#20C997', '#FD7E14', '#6C757D']
            ax.pie(values, labels=labels, autopct='%1.0f%%', colors=colors[:len(labels)], textprops={'fontsize': 7})
            ax.set_title("Số lượng hộ theo từng khu", fontsize=11, fontweight='bold', color='#17365D')
        self.fig4.tight_layout()
        self.canvas4.draw()

    def load_area_table(self):
        areas = self.area_ctrl.get_all_areas()
        self.area_table.setRowCount(len(areas))
        for row_idx, a in enumerate(areas):
            self.area_table.setItem(row_idx, 0, QTableWidgetItem(a.name))
            self.area_table.setItem(row_idx, 1, QTableWidgetItem(str(a.person_count)))
            self.area_table.setItem(row_idx, 2, QTableWidgetItem(str(a.household_count)))

    def load_recent_activities(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT action, details, created_at FROM audit_logs ORDER BY id DESC LIMIT 5")
            logs = cursor.fetchall()
            self.activity_table.setRowCount(len(logs))
            for r_idx, l in enumerate(logs):
                action_text = f"{l['action']}: {l['details']}"
                time_str = l['created_at'].split(" ")[-1] if l['created_at'] else ""
                self.activity_table.setItem(r_idx, 0, QTableWidgetItem(action_text))
                self.activity_table.setItem(r_idx, 1, QTableWidgetItem(time_str))
        except Exception:
            pass
        finally:
            conn.close()
