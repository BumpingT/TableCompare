"""
对比设置面板
选择键列和对比列
v2 — 增加列搜索功能
"""
import logging

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QScrollArea, QWidget, QGridLayout,
    QGroupBox, QSizePolicy, QApplication, QLineEdit
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

logger = logging.getLogger('table_diff.ui.compare_panel')


class ComparePanel(QFrame):
    """对比设置面板"""

    compare_requested = Signal(str, list, bool)  # (key_column, compare_columns, use_row_index)
    columns_changed = Signal(list)          # 可用列列表变化

    def __init__(self, parent=None):
        super().__init__(parent)
        self._columns = []
        self._checkboxes = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel("⚙️  对比设置")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 键列选择
        key_layout = QHBoxLayout()
        key_label = QLabel("键列（用于匹配行）:")
        key_label.setStyleSheet("color: #1E293B; font-size: 12px;")
        key_layout.addWidget(key_label)

        # 帮助按钮 — 点击弹窗解释键列的作用
        self._help_btn = QPushButton("?")
        self._help_btn.setFixedSize(22, 22)
        self._help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 11px;
                font-size: 11px;
                font-weight: bold;
                color: #64748B;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #2563EB;
                color: white;
                border-color: #2563EB;
            }
        """)
        self._help_btn.clicked.connect(self._show_key_help)
        key_layout.addWidget(self._help_btn)

        self._key_combo = QComboBox()
        self._key_combo.setMinimumWidth(200)
        self._key_combo.setMinimumHeight(32)
        self._key_combo.addItem("（请先加载文件）")
        key_layout.addWidget(self._key_combo)

        # 行号匹配模式
        self._row_index_cb = QCheckBox("按行号匹配（用于无键列的单列数据）")
        self._row_index_cb.setStyleSheet("color: #0891B2; font-size: 12px;")
        self._row_index_cb.stateChanged.connect(self._on_row_index_changed)
        key_layout.addWidget(self._row_index_cb)
        key_layout.addStretch()
        layout.addLayout(key_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        layout.addWidget(line)

        # 对比列选择
        col_title = QLabel("对比列（选择需要对比的列）:")
        col_title.setStyleSheet("color: #1E293B; font-size: 12px;")
        layout.addWidget(col_title)

        # 列搜索框（新增）
        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  搜索列名...")
        self._search_input.setMinimumHeight(30)
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input, 1)

        self._search_count_label = QLabel("")
        self._search_count_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        search_layout.addWidget(self._search_count_label)

        layout.addLayout(search_layout)

        # 全选/取消
        sel_layout = QHBoxLayout()
        self._select_all_cb = QCheckBox("全选")
        self._select_all_cb.setStyleSheet("color: #2563EB; font-size: 12px;")
        self._select_all_cb.stateChanged.connect(self._on_select_all)
        sel_layout.addWidget(self._select_all_cb)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        # 列复选框区域（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._col_widget = QWidget()
        self._col_layout = QGridLayout(self._col_widget)
        self._col_layout.setContentsMargins(0, 0, 0, 0)
        self._col_layout.setSpacing(4)
        scroll.setWidget(self._col_widget)
        scroll.setMaximumHeight(120)

        layout.addWidget(scroll)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._compare_btn = QPushButton("▶  开始对比")
        self._compare_btn.setMinimumHeight(40)
        self._compare_btn.setMinimumWidth(150)
        self._compare_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._compare_btn.setEnabled(False)
        self._compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 28px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
            QPushButton:disabled {
                background-color: #94A3B8;
                color: #E2E8F0;
            }
        """)
        self._compare_btn.clicked.connect(self._on_compare)
        btn_layout.addWidget(self._compare_btn)

        layout.addLayout(btn_layout)

        # 设置面板样式
        self.setStyleSheet("""
            ComparePanel {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)

    def set_columns(self, columns: list[str]):
        """设置可用的列列表"""
        self._columns = columns
        self._checkboxes.clear()

        # 清空布局
        while self._col_layout.count():
            item = self._col_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 重新填充复选框
        for i, col in enumerate(columns):
            cb = QCheckBox(col)
            cb.setChecked(True)
            self._checkboxes[col] = cb
            row, col_idx = divmod(i, 4)
            self._col_layout.addWidget(cb, row, col_idx)

        # 更新键列选择器
        self._key_combo.clear()
        self._key_combo.addItems(columns)
        if columns:
            self._key_combo.setCurrentIndex(0)

        # 更新全选状态
        self._select_all_cb.setChecked(True)

        # 启用/禁用对比按钮（需要列数>0）
        has_cols = len(columns) > 0
        self._compare_btn.setEnabled(has_cols)

        # 清空搜索
        self._search_input.clear()
        self._search_count_label.setText("")

        self.columns_changed.emit(columns)

    def get_selected_columns(self) -> list[str]:
        """获取用户勾选的对比列（排除键列）"""
        key_col = self._key_combo.currentText()
        return [col for col, cb in self._checkboxes.items()
                if cb.isChecked() and col != key_col]

    def get_key_column(self) -> str:
        return self._key_combo.currentText()

    # ========== 列搜索 ==========

    def _on_search_changed(self, text: str):
        """搜索文本变化时过滤复选框"""
        if not self._checkboxes:
            self._search_count_label.setText("")
            return

        keyword = text.strip().lower()
        visible_count = 0
        total = len(self._checkboxes)

        for col, cb in self._checkboxes.items():
            if not keyword or keyword in col.lower():
                cb.show()
                visible_count += 1
            else:
                cb.hide()

        # 更新搜索计数
        if keyword:
            self._search_count_label.setText(f"匹配 {visible_count}/{total}")
        else:
            self._search_count_label.setText("")

    def _on_select_all(self, state):
        """全选/取消全选"""
        checked = (state == Qt.CheckState.Checked.value)
        for cb in self._checkboxes.values():
            cb.setChecked(checked)

    def _on_row_index_changed(self, state):
        """行号匹配模式切换"""
        use_index = (state == Qt.CheckState.Checked.value)
        self._key_combo.setEnabled(not use_index)
        self._help_btn.setEnabled(not use_index)
        # 行号模式下，所有列自动全选作为对比列
        if use_index:
            self._select_all_cb.setChecked(True)
            self._select_all_cb.setEnabled(False)
        else:
            self._select_all_cb.setEnabled(True)

    def _show_key_help(self):
        """显示键列帮助弹窗"""
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("键列 vs 行号匹配")
        msg.setText(
            "【🔑 普通模式】— 不勾选「按行号匹配」\n\n"
            "用键列的值来匹配两表的行。\n"
            "适合有「员工编号」「订单号」等唯一标识的数据。\n\n"
            "  例：A001张三→A001张三 → 同一个人，对比内容\n"
            "  例：A003王五→(无)      → 删除了\n\n"
            "【📏 行号匹配模式】— 勾选「按行号匹配」\n\n"
            "按第1行对第1行、第2行对第2行…\n"
            "适合纯名单、清单等没有唯一列的数据。\n\n"
            "  例：第3行橙子→草莓 → 修改了\n"
            "  例：第5行(无)→芒果  → 新增了\n\n"
            "──────────────\n"
            "💡 键列的值必须唯一，不能有重复！\n"
            "   选错了工具会弹窗提示你。"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _on_compare(self):
        """点击开始对比"""
        use_row_index = self._row_index_cb.isChecked()
        key_col = '' if use_row_index else self.get_key_column()
        compare_cols = self.get_selected_columns()

        if not use_row_index and not key_col:
            return

        if not compare_cols:
            logger.warning("未选择任何对比列")
            return

        self.compare_requested.emit(key_col, compare_cols, use_row_index)

    def reset(self):
        """重置状态"""
        self._columns = []
        self._checkboxes.clear()
        self._search_input.clear()
        self._search_count_label.setText("")
        self._key_combo.clear()
        self._key_combo.addItem("（请先加载文件）")
        self._key_combo.setEnabled(True)
        self._help_btn.setEnabled(True)
        self._row_index_cb.setChecked(False)
        self._row_index_cb.setEnabled(True)
        self._select_all_cb.setEnabled(True)
        self._compare_btn.setEnabled(False)

    def set_controls_enabled(self, enabled: bool):
        """启用/禁用操作控件（保留对比列复选框可见）"""
        self._key_combo.setEnabled(enabled)
        self._help_btn.setEnabled(enabled)
        self._row_index_cb.setEnabled(enabled)
        self._select_all_cb.setEnabled(enabled)
        self._search_input.setEnabled(enabled)
        # 对比列复选框保持可见，只禁用关键操作按钮
        self._compare_btn.setEnabled(enabled)

        # 注意：不清空复选框布局！否则对比列会消失
