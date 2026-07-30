"""
统计栏控件
显示新增、删除、修改的行数统计
"""
import logging

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logger = logging.getLogger('table_diff.ui.stats_bar')


class StatsBar(QFrame):
    """差异统计栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # 标题
        self._title_label = QLabel("📊  对比统计")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        layout.addWidget(self._title_label)

        layout.addStretch()

        # 统计项
        self._stats_labels = {}

        stats_config = [
            ('added', '🟢  新增', '#10B981'),
            ('deleted', '🔴  删除', '#EF4444'),
            ('modified', '🟡  修改', '#F59E0B'),
            ('same', '⚪  相同', '#64748B'),
        ]

        for key, prefix, color in stats_config:
            label = QLabel(f"{prefix}: —")
            label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600; padding: 2px 0;")
            self._stats_labels[key] = label
            layout.addWidget(label)

        # 背景
        self.setStyleSheet("""
            StatsBar {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)

    def _apply_style(self):
        pass

    def update_stats(self, stats: dict):
        """更新统计显示"""
        if not stats:
            return

        mapping = {
            'added': ('added', '🟢  新增'),
            'deleted': ('deleted', '🔴  删除'),
            'modified': ('modified', '🟡  修改'),
            'same': ('same', '⚪  相同'),
        }

        for key, (stat_key, prefix) in mapping.items():
            val = stats.get(stat_key, 0)
            label = self._stats_labels.get(key)
            if label:
                label.setText(f"{prefix}: {val}")

    def reset(self):
        """重置统计显示"""
        for key, label in self._stats_labels.items():
            label.setText(f"{label.text().split(':')[0]}: —")
