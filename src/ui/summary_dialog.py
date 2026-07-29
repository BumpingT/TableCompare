"""
汇总视图对话框
显示各列差异统计：哪些列有差异、差异数量、差异率
"""
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from ..core.comparator import DiffResult, STATUS_COL, STATUS_SAME, STATUS_MODIFIED

logger = logging.getLogger('table_diff.ui.summary_dialog')

# 颜色
COLOR_HEADER_BG = QColor(44, 62, 80)
COLOR_HEADER_FG = QColor(255, 255, 255)
COLOR_ADDED_BG = QColor(213, 245, 227)
COLOR_DELETED_BG = QColor(250, 219, 216)
COLOR_MODIFIED_BG = QColor(254, 249, 231)
COLOR_SAME = QColor(100, 116, 139)
COLOR_HIGHLIGHT = QColor(245, 203, 167)


class SummaryDialog(QDialog):
    """列差异汇总对话框"""

    def __init__(self, diff_result: DiffResult, parent=None):
        super().__init__(parent)
        self._result = diff_result
        self.setWindowTitle("📊 列差异汇总")
        self.setMinimumSize(650, 500)
        self.resize(700, 550)
        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📊  列差异汇总")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1E293B;")
        layout.addWidget(title)

        # 说明
        desc = QLabel(
            "每列参与对比的差异统计，快速定位有问题的列。\n"
            "修改次数越多 = 该列变化越集中，值得重点关注。\n"
            "例如：基本工资改 320 次、部门改 0 次 → 调薪是本次变动重点。"
        )
        desc.setStyleSheet("color: #64748B; font-size: 12px; padding-bottom: 4px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 总体统计
        stats = self._result.stats
        summary_layout = QHBoxLayout()
        total_diff = stats.get('added', 0) + stats.get('deleted', 0) + stats.get('modified', 0)
        total_rows = len(self._result.merged_df)

        info_items = [
            ("总行数", str(total_rows), "#1E293B"),
            ("差异行", str(total_diff), "#F59E0B"),
            ("差异率", f"{total_diff / total_rows * 100:.1f}%" if total_rows > 0 else "0%", "#EF4444"),
            ("对比列数", str(len(self._result.compare_columns)), "#2563EB"),
        ]
        for label, value, color in info_items:
            item = QFrame()
            item.setStyleSheet("""
                QFrame {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(12, 8, 12, 8)
            item_layout.setSpacing(4)

            lbl = QLabel(label)
            lbl.setStyleSheet("color: #64748B; font-size: 11px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item_layout.addWidget(lbl)

            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item_layout.addWidget(val_lbl)

            summary_layout.addWidget(item)

        layout.addLayout(summary_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        layout.addWidget(line)

        # 表格：每列的差异统计
        table_label = QLabel("各列差异详情：")
        table_label.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "列名", "修改次数", "新增行影响", "删除行影响", "差异小计"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().hide()
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 12px;
                background-color: white;
                alternate-background-color: #F8FAFC;
            }
            QTableWidget::item {
                padding: 6px 10px;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 8px;
                border: none;
                border-right: 1px solid #3D566E;
            }
        """)
        layout.addWidget(self._table, 1)

        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 24px;
                font-size: 13px;
                color: #1E293B;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_data(self):
        """填充数据"""
        result = self._result
        compare_cols = result.compare_columns
        changed_cells = result.changed_cells
        df = result.merged_df

        # 统计每列的差异次数
        col_modified_count = {col: 0 for col in compare_cols}
        for (row_key, col_name), _ in changed_cells.items():
            if col_name in col_modified_count:
                col_modified_count[col_name] += 1

        # 统计新增/删除行的列影响
        col_added_affected = {col: 0 for col in compare_cols}
        col_deleted_affected = {col: 0 for col in compare_cols}

        # 遍历所有差异行
        for idx in result.diff_rows:
            status = df.loc[idx, STATUS_COL]
            if status == 'added':
                for col in compare_cols:
                    col_added_affected[col] += 1
            elif status == 'deleted':
                for col in compare_cols:
                    col_deleted_affected[col] += 1

        # 填充表格
        self._table.setRowCount(len(compare_cols))

        for i, col in enumerate(compare_cols):
            modified = col_modified_count.get(col, 0)
            added = col_added_affected.get(col, 0)
            deleted = col_deleted_affected.get(col, 0)
            total = modified + added + deleted

            # 列名
            name_item = QTableWidgetItem(col)
            name_item.setFont(QFont('', 10, QFont.Weight.Bold))
            self._table.setItem(i, 0, name_item)

            # 修改次数
            mod_item = QTableWidgetItem(str(modified))
            if modified > 0:
                mod_item.setBackground(COLOR_HIGHLIGHT)
            self._table.setItem(i, 1, mod_item)

            # 新增影响
            add_item = QTableWidgetItem(str(added))
            if added > 0:
                add_item.setBackground(COLOR_ADDED_BG)
            self._table.setItem(i, 2, add_item)

            # 删除影响
            del_item = QTableWidgetItem(str(deleted))
            if deleted > 0:
                del_item.setBackground(COLOR_DELETED_BG)
            self._table.setItem(i, 3, del_item)

            # 差异小计
            total_item = QTableWidgetItem(str(total))
            total_item.setFont(QFont('', 10, QFont.Weight.Bold))
            if total > 0:
                total_item.setBackground(QColor(254, 249, 231))  # 浅黄
            self._table.setItem(i, 4, total_item)

        # 自动调整行高
        self._table.resizeRowsToContents()
