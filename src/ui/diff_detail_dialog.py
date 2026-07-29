"""
差异详情弹窗
双击某行时弹出，展示该行的前后对比详情
"""
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

import pandas as pd

from ..core.comparator import (
    DiffResult, STATUS_COL, KEY_COL,
    STATUS_ADDED, STATUS_DELETED, STATUS_MODIFIED, STATUS_SAME,
)

logger = logging.getLogger('table_diff.ui.diff_detail_dialog')

# 颜色（更深更饱和，确保明显）
COLOR_ADDED_BG = QColor(167, 219, 186)        # 深绿
COLOR_DELETED_BG = QColor(235, 170, 165)       # 深红
COLOR_MODIFIED_BG = QColor(250, 240, 190)      # 深黄
COLOR_CHANGED_BG = QColor(239, 171, 105)       # 深橙
COLOR_HEADER_BG = QColor(44, 62, 80)
COLOR_HEADER_FG = QColor(255, 255, 255)
COLOR_EVEN_ROW = QColor(248, 250, 252)

STATUS_ICONS = {
    STATUS_ADDED: '🟢',
    STATUS_DELETED: '🔴',
    STATUS_MODIFIED: '🟡',
    STATUS_SAME: '⚪',
}

STATUS_LABELS = {
    STATUS_ADDED: '新增',
    STATUS_DELETED: '删除',
    STATUS_MODIFIED: '修改',
    STATUS_SAME: '相同',
}


class DiffDetailDialog(QDialog):
    """差异行详情弹窗"""

    def __init__(self, diff_result: DiffResult, row_index: int, parent=None):
        """
        Args:
            diff_result: 对比结果
            row_index: 在 merged_df 中的行索引（source 索引）
        """
        super().__init__(parent)
        self._result = diff_result
        self._row_index = row_index
        self._compare_cols = diff_result.compare_columns
        self._df = diff_result.merged_df

        self.setWindowTitle("🔍  行差异详情")
        self.setMinimumSize(750, 450)
        self.resize(800, 500)
        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 行信息头
        self._header_frame = QFrame()
        self._header_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        header_layout = QVBoxLayout(self._header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(6)

        self._status_label = QLabel("")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self._status_label.setFont(status_font)
        header_layout.addWidget(self._status_label)

        self._key_label = QLabel("")
        self._key_label.setStyleSheet("color: #475569; font-size: 12px;")
        header_layout.addWidget(self._key_label)

        layout.addWidget(self._header_frame)

        # 对比表格
        table_label = QLabel("字段对比（旧值 → 新值）：")
        table_label.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold;")
        layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["字段名", "旧值（初始版）", "新值（修改版）"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
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
                padding: 8px 12px;
                border-bottom: 1px solid #F1F5F9;
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

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("📋  复制为文本")
        copy_btn.setMinimumHeight(32)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                color: #1E293B;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _populate_data(self):
        """填充行数据"""
        row_idx = self._row_index
        df = self._df
        status = df.loc[row_idx, STATUS_COL]
        key_val = df.loc[row_idx, KEY_COL]
        compare_cols = self._compare_cols
        changed_cells = self._result.changed_cells

        # 状态头
        icon = STATUS_ICONS.get(status, '⚪')
        label = STATUS_LABELS.get(status, status)
        status_text = f"{icon}  {label} — 键值: {key_val}"
        self._status_label.setText(status_text)

        # 根据状态设置颜色
        if status == STATUS_ADDED:
            self._status_label.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold;")
        elif status == STATUS_DELETED:
            self._status_label.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
        elif status == STATUS_MODIFIED:
            self._status_label.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: bold;")
        else:
            self._status_label.setStyleSheet("color: #64748B; font-size: 14px; font-weight: bold;")

        # 补充信息
        extra_info = []
        if status == STATUS_ADDED:
            extra_info.append("💡 该行仅在修改版（新版）中存在，属于新增数据")
        elif status == STATUS_DELETED:
            extra_info.append("💡 该行仅在初始版（旧版）中存在，属于删除数据")
        elif status == STATUS_MODIFIED:
            extra_info.append("💡 该行在两表中都存在但内容有变化，橙色标记的字段为差异字段")
        else:
            extra_info.append("💡 该行在两表中完全一致")

        self._key_label.setText("  ".join(extra_info))

        # 填充对比表格
        n = len(compare_cols)
        self._table.setRowCount(n)

        for i, col in enumerate(compare_cols):
            # 判断该字段是否有变化
            is_changed = status == STATUS_MODIFIED and (row_idx, col) in changed_cells
            prefix = ' 🔸' if is_changed else ''
            name_item = QTableWidgetItem(f'{col}{prefix}')
            name_item.setFont(QFont('', 10, QFont.Weight.Bold))
            self._table.setItem(i, 0, name_item)

            # 旧值
            old_val = df.loc[row_idx, f'{col}_旧'] if f'{col}_旧' in df.columns else ''
            old_str = str(old_val) if old_val is not None and old_val != '' and not pd.isna(old_val) else '（空）'
            old_item = QTableWidgetItem(old_str)
            self._table.setItem(i, 1, old_item)

            # 新值
            new_val = df.loc[row_idx, f'{col}_新'] if f'{col}_新' in df.columns else ''
            new_str = str(new_val) if new_val is not None and new_val != '' and not pd.isna(new_val) else '（空）'
            new_item = QTableWidgetItem(new_str)
            self._table.setItem(i, 2, new_item)

            # 如果是修改行且该单元格有变化，高亮标记
            if status == STATUS_MODIFIED:
                if (row_idx, col) in changed_cells:
                    old_item.setBackground(COLOR_CHANGED_BG)
                    old_item.setToolTip(f"旧值: {old_str}")
                    new_item.setBackground(COLOR_CHANGED_BG)
                    new_item.setToolTip(f"新值: {new_str}")
                else:
                    # 没变化的单元格也加浅黄底色，表示该行有修改
                    old_item.setBackground(COLOR_MODIFIED_BG)
                    new_item.setBackground(COLOR_MODIFIED_BG)
            elif status == STATUS_ADDED:
                old_item.setBackground(COLOR_ADDED_BG)
                new_item.setBackground(COLOR_ADDED_BG)
            elif status == STATUS_DELETED:
                old_item.setBackground(COLOR_DELETED_BG)
                new_item.setBackground(COLOR_DELETED_BG)

        # 调整行高
        self._table.resizeRowsToContents()

    def _copy_to_clipboard(self):
        """将当前详情复制为文本"""
        row_idx = self._row_index
        df = self._df
        status = df.loc[row_idx, STATUS_COL]
        key_val = df.loc[row_idx, KEY_COL]
        compare_cols = self._compare_cols

        lines = []
        lines.append(f"行差异详情 — 状态: {STATUS_LABELS.get(status, status)} — 键值: {key_val}")
        lines.append("=" * 60)
        lines.append(f"{'字段名':<20} {'旧值':<25} {'新值':<25}")
        lines.append("-" * 70)

        for col in compare_cols:
            old_val = df.loc[row_idx, f'{col}_旧'] if f'{col}_旧' in df.columns else ''
            new_val = df.loc[row_idx, f'{col}_新'] if f'{col}_新' in df.columns else ''
            old_str = str(old_val) if old_val is not None and old_val != '' else '（空）'
            new_str = str(new_val) if new_val is not None and new_val != '' else '（空）'
            lines.append(f"{col:<20} {old_str:<25} {new_str:<25}")

        lines.append("=" * 60)

        text = '\n'.join(lines)

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # 按钮反馈：临时显示"✅ 已复制"
        btn = self.sender()
        if btn:
            original_text = btn.text()
            btn.setText("✅  已复制")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #D1FAE5;
                    border: 1px solid #10B981;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                    color: #065F46;
                    font-weight: bold;
                }
            """)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._restore_copy_btn(btn, original_text))

    def _restore_copy_btn(self, btn, original_text):
        """恢复复制按钮的原始样式"""
        btn.setText(original_text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                color: #1E293B;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
