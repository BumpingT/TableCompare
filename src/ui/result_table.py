"""
结果表格控件
展示对比结果，支持颜色标记、差异筛选和导航
v3 — 增加双击详情弹窗 + 汇总视图按钮
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QCheckBox, QLabel, QFrame, QSizePolicy,
    QAbstractItemView, QStyledItemDelegate, QStyleOptionViewItem
)
from PySide6.QtCore import (
    Signal, Slot, Qt, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel, QRect
)
from PySide6.QtGui import QColor, QFont, QBrush, QPainter
from PySide6.QtWidgets import QStyle

from ..core.comparator import (
    DiffResult, STATUS_COL, KEY_COL,
    STATUS_ADDED, STATUS_DELETED, STATUS_MODIFIED, STATUS_SAME
)

from .diff_detail_dialog import DiffDetailDialog
from .summary_dialog import SummaryDialog

logger = logging.getLogger('table_diff.ui.result_table')

# 颜色定义
COLOR_ADDED_BG = QColor(213, 245, 227)        # 浅绿
COLOR_DELETED_BG = QColor(250, 219, 216)       # 浅红
COLOR_MODIFIED_BG = QColor(254, 249, 231)      # 浅黄
COLOR_CHANGED_CELL_BG = QColor(245, 203, 167)  # 橙色
COLOR_HEADER_BG = QColor(44, 62, 80)           # 深蓝
COLOR_HEADER_FG = QColor(255, 255, 255)         # 白色
COLOR_DIFF_ROW_FG = QColor(220, 38, 38)         # 差异导航标记色
COLOR_ADDED_TEXT = QColor(22, 163, 74)           # 深绿
COLOR_DELETED_TEXT = QColor(220, 38, 38)         # 深红
COLOR_MODIFIED_TEXT = QColor(217, 119, 6)        # 深黄
COLOR_SAME_TEXT = QColor(100, 116, 139)          # 灰色
COLOR_EVEN_ROW = QColor(248, 250, 252)           # 交替行色
COLOR_BORDER = QColor(226, 232, 240)             # 边框色

STATUS_LABELS = {
    STATUS_ADDED: '新增',
    STATUS_DELETED: '删除',
    STATUS_MODIFIED: '修改',
    STATUS_SAME: '相同',
}

STATUS_COLORS = {
    STATUS_ADDED: COLOR_ADDED_BG,
    STATUS_DELETED: COLOR_DELETED_BG,
    STATUS_MODIFIED: COLOR_MODIFIED_BG,
    STATUS_SAME: None,
}

STATUS_TEXT_COLORS = {
    STATUS_ADDED: COLOR_ADDED_TEXT,
    STATUS_DELETED: COLOR_DELETED_TEXT,
    STATUS_MODIFIED: COLOR_MODIFIED_TEXT,
    STATUS_SAME: COLOR_SAME_TEXT,
}

# ============================================================
#  表头数据模型 — 管理对比结果数据，仅按需提供 data()
# ============================================================

class DiffTableModel(QAbstractTableModel):
    """
    对比结果数据模型

    将对比数据预提取为 Python 列表，data() 回调直接返回，O(1) 访问。
    Qt 仅在 UI 需要渲染可见区域时调用 data()，不会为不可见行创建任何对象。
    """

    def __init__(self, diff_result: DiffResult, parent=None):
        super().__init__(parent)
        self._result = diff_result
        df = diff_result.merged_df
        self._compare_cols = diff_result.compare_columns
        self._num_compare = len(self._compare_cols)

        # 预提取为 Python 列表 — 访问 O(1)，无 pandas 开销
        self._status_list = df[STATUS_COL].tolist()
        self._key_list = df[KEY_COL].tolist()

        self._old_data = []
        self._new_data = []
        for col in self._compare_cols:
            self._old_data.append(df[f'{col}_旧'].tolist())
            self._new_data.append(df[f'{col}_新'].tolist())

        # 预计算修改单元格掩码 — 用于快速判断某个单元格是否变橙
        # _changed_set: set of (row_idx, col_idx_in_view) 其中 col 是 view 中的列号
        # 对于旧值列 (1..n)：col_idx_in_view = col_index_in_compare + 1
        # 对于新值列 (n+1..2n)：col_idx_in_view = col_index_in_compare + 1 + n
        self._changed_set: set[tuple[int, int]] = set()
        col_to_old_view = {col: i + 1 for i, col in enumerate(self._compare_cols)}
        col_to_new_view = {col: i + 1 + self._num_compare for i, col in enumerate(self._compare_cols)}

        for (row_key, col_name), _ in diff_result.changed_cells.items():
            if col_name in col_to_old_view:
                self._changed_set.add((row_key, col_to_old_view[col_name]))
                self._changed_set.add((row_key, col_to_new_view[col_name]))

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._status_list)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 1 + 2 * self._num_compare  # 状态列 + 旧值列 + 新值列

    # ---------- 核心：逐单元格按需提供数据 ----------

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row, col = index.row(), index.column()
        status = self._status_list[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display(row, col)

        if role == Qt.ItemDataRole.BackgroundRole:
            return self._get_background(row, col, status)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 0:
                return STATUS_TEXT_COLORS.get(status, COLOR_SAME_TEXT)
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        if role == Qt.ItemDataRole.FontRole:
            if col == 0:
                font = QFont()
                font.setBold(True)
                font.setPointSize(11)
                return font
            return None

        if role == Qt.ItemDataRole.UserRole:
            # 用于排序/过滤的状态值
            return status

        return None

    def _get_display(self, row: int, col: int) -> str:
        if col == 0:
            return STATUS_LABELS.get(self._status_list[row], '')

        n = self._num_compare
        if 1 <= col <= n:
            # 旧值列
            val = self._old_data[col - 1][row]
            return str(val) if val is not None and val != '' else ''
        elif n + 1 <= col <= 2 * n:
            # 新值列
            val = self._new_data[col - n - 1][row]
            return str(val) if val is not None and val != '' else ''

        return ''

    def _get_background(self, row: int, col: int, status: str):
        """返回单元格背景色"""
        if col == 0:
            return STATUS_COLORS.get(status, None)

        # 整行背景
        if status == STATUS_ADDED:
            return COLOR_ADDED_BG
        if status == STATUS_DELETED:
            return COLOR_DELETED_BG
        if status == STATUS_MODIFIED:
            # 检查是否为具体变化单元格
            if (row, col) in self._changed_set:
                return COLOR_CHANGED_CELL_BG
            return COLOR_MODIFIED_BG

        # 相同行 — 交替行底色
        if row % 2 == 1:
            return COLOR_EVEN_ROW

        return None

    # ---------- 表头 ----------

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if section == 0:
                    return '状态'
                n = self._num_compare
                if 1 <= section <= n:
                    return f'{self._compare_cols[section - 1]} (旧版)'
                elif n + 1 <= section <= 2 * n:
                    return f'{self._compare_cols[section - n - 1]} (新版)'
                return ''

            if role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                return font

            if role == Qt.ItemDataRole.ForegroundRole:
                return COLOR_HEADER_FG

            if role == Qt.ItemDataRole.BackgroundRole:
                return COLOR_HEADER_BG

            if role == Qt.ItemDataRole.TextAlignmentRole:
                return int(Qt.AlignmentFlag.AlignCenter)

        # 垂直表头隐藏
        return None

    # ---------- 公开辅助方法 ----------

    def get_status(self, row: int) -> str:
        """获取指定行的状态"""
        if 0 <= row < len(self._status_list):
            return self._status_list[row]
        return ''

    def is_diff_row(self, row: int) -> bool:
        """是否为差异行（新增/删除/修改）"""
        return self.get_status(row) != STATUS_SAME

    def is_changed_cell(self, row: int, col: int) -> bool:
        """是否为修改单元格"""
        return (row, col) in self._changed_set

    def get_diff_result(self) -> DiffResult | None:
        return self._result


# ============================================================
#  筛选代理模型 — 仅显示差异行  / 全量显示
# ============================================================

class DiffFilterProxyModel(QSortFilterProxyModel):
    """
    对比结果筛选代理

    通过 QSortFilterProxyModel 实现"仅显示差异行"，不需重建表格。
    与模型解耦，仅基于行的状态过滤。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_diff_only = False
        # 禁用排序（保持原始顺序）
        self.setSortRole(Qt.ItemDataRole.UserRole)

    def set_filter_diff_only(self, enabled: bool):
        """设置是否仅显示差异行"""
        if self._filter_diff_only != enabled:
            self._filter_diff_only = enabled
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._filter_diff_only:
            return True
        model = self.sourceModel()
        if isinstance(model, DiffTableModel):
            return model.is_diff_row(source_row)
        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        # 保持原始插入顺序（基于行号排序）
        return left.row() < right.row()


# ============================================================
#  自定义委托 — 绘制边框和选中效果
# ============================================================

class DiffItemDelegate(QStyledItemDelegate):
    """自定义单元格绘制委托 — 选中时显示状态对应颜色（修改=黄、新增=绿、删除=红）"""

    # 选中色（比普通状态色更深）
    SELECTED_COLORS = {
        STATUS_ADDED: QColor(167, 219, 186),      # 深绿
        STATUS_DELETED: QColor(235, 170, 165),     # 深红
        STATUS_MODIFIED: QColor(245, 225, 120),    # 深黄
    }

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # 获取该行的状态
        status = index.data(Qt.ItemDataRole.UserRole) if index.isValid() else None

        if option.state & QStyle.StateFlag.State_Selected and status in self.SELECTED_COLORS:
            # 选中行：用状态对应的深色填充
            painter.save()
            painter.fillRect(option.rect, self.SELECTED_COLORS[status])
            painter.restore()
            # 只绘制文本，不绘制默认选中背景
            opt = QStyleOptionViewItem(option)
            opt.state &= ~QStyle.StateFlag.State_Selected
            super().paint(painter, opt, index)
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QRect:
        # 为表头提供合理的尺寸
        base = super().sizeHint(option, index)
        base.setHeight(32)  # 统一行高
        return base


# ============================================================
#  结果表格控件（外部接口与 v1 保持一致）
# ============================================================

class ResultTable(QFrame):
    """对比结果表格 — v3 增加双击详情 + 汇总视图"""

    status_message = Signal(str)   # 状态栏消息
    export_requested = Signal()    # 请求导出
    summary_requested = Signal()   # 请求汇总视图

    def __init__(self, parent=None):
        super().__init__(parent)
        self._diff_result = None
        self._model = None         # DiffTableModel 实例
        self._proxy = DiffFilterProxyModel(self)  # 筛选代理
        self._filter_diff_only = False
        self._current_nav_index = -1
        self._diff_row_indices = []  # 所有差异行的 source 索引

        self._setup_ui()
        self._apply_style()

    # ---------- UI 构建 ----------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 0, 4, 0)

        # 标题
        title_label = QLabel("📋  对比结果")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar.addWidget(title_label)

        toolbar.addStretch()

        # 汇总视图按钮（新增）
        self._summary_btn = QPushButton("📊  汇总视图")
        self._summary_btn.setMinimumHeight(28)
        self._summary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._summary_btn.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6D28D9; }
            QPushButton:disabled { background-color: #DDD6FE; color: #C4B5FD; }
        """)
        self._summary_btn.clicked.connect(self._on_summary)
        self._summary_btn.setEnabled(False)
        toolbar.addWidget(self._summary_btn)

        # 仅显示差异行 checkbox
        self._filter_cb = QCheckBox("☑  仅显示差异行")
        self._filter_cb.setStyleSheet("font-size: 12px; color: #1E293B;")
        self._filter_cb.stateChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._filter_cb)

        # 导出按钮
        self._export_btn = QPushButton("📥  导出 Excel")
        self._export_btn.setMinimumHeight(28)
        self._export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #047857; }
            QPushButton:disabled { background-color: #A7F3D0; color: #D1FAE5; }
        """)
        self._export_btn.clicked.connect(self._on_export)
        self._export_btn.setEnabled(False)
        toolbar.addWidget(self._export_btn)

        # 差异导航
        self._nav_label = QLabel("")
        self._nav_label.setStyleSheet("color: #64748B; font-size: 12px; margin: 0 8px;")
        toolbar.addWidget(self._nav_label)

        self._prev_btn = QPushButton("◀  上一条")
        self._prev_btn.setMinimumHeight(28)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                color: #1E293B;
            }
            QPushButton:hover { background-color: #E2E8F0; }
            QPushButton:disabled { color: #CBD5E1; }
        """)
        self._prev_btn.clicked.connect(self.navigate_to_prev_diff)
        self._prev_btn.setEnabled(False)
        toolbar.addWidget(self._prev_btn)

        self._next_btn = QPushButton("下一条  ▶")
        self._next_btn.setMinimumHeight(28)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._next_btn.clicked.connect(self.navigate_to_next_diff)
        self._next_btn.setEnabled(False)
        toolbar.addWidget(self._next_btn)

        layout.addLayout(toolbar)

        # ---------- QTableView（替代 QTableWidget）----------
        self._table = QTableView()
        self._table.setModel(self._proxy)

        self._table.setAlternatingRowColors(False)  # 我们自己在模型中处理
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # 双击打开差异详情（新增）
        self._table.doubleClicked.connect(self._on_row_double_clicked)

        # 自定义委托
        self._delegate = DiffItemDelegate(self._table)
        self._table.setItemDelegate(self._delegate)

        # 行高
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.verticalHeader().hide()

        # 表头设置
        h_header = self._table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setStretchLastSection(True)
        h_header.setDefaultSectionSize(160)
        h_header.setMinimumSectionSize(60)
        # 状态列宽度固定
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h_header.resizeSection(0, 72)

        # 选中行高亮样式
        self._table.setStyleSheet("""
            QTableView {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                background-color: #FFFFFF;
                gridline-color: #F1F5F9;
                font-size: 12px;
                outline: none;
            }
            QTableView::item:selected {
                background-color: transparent;
                color: #1E293B;
            }
            QTableView::item:hover {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 8px;
                border: none;
                border-right: 1px solid #3D566E;
                border-bottom: 1px solid #3D566E;
            }
        """)

        layout.addWidget(self._table)

        # 空状态提示
        self._empty_label = QLabel('📄  请先加载两个文件并点击"开始对比"\n\n💡 提示：双击结果行可查看详细的字段对比')
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #94A3B8; font-size: 16px; padding: 60px;")
        self._empty_label.setMinimumHeight(200)
        layout.addWidget(self._empty_label)

        self._table.hide()
        self._empty_label.show()

    def _apply_style(self):
        self.setStyleSheet("""
            ResultTable {
                background-color: transparent;
            }
        """)

    # ---------- 显示结果 ----------

    def show_result(self, diff_result: DiffResult):
        """显示对比结果（设置模型，代理自动生效）"""
        self._diff_result = diff_result

        if diff_result.merged_df.empty:
            self._show_empty("暂无数据")
            return

        # 隐藏空状态
        self._empty_label.hide()
        self._table.show()

        # 确保表格绑定到我们的代理模型上
        self._table.setModel(self._proxy)

        # 创建模型
        self._model = DiffTableModel(diff_result, self)
        self._proxy.setSourceModel(self._model)

        # 存储差异行索引（source 层面）
        df = diff_result.merged_df
        self._diff_row_indices = df[df[STATUS_COL] != STATUS_SAME].index.tolist()

        # 重置导航
        self._current_nav_index = -1
        self._filter_diff_only = False
        self._filter_cb.setChecked(False)

        # 启用导出和汇总按钮
        self._export_btn.setEnabled(True)
        self._summary_btn.setEnabled(True)

        # 列宽适配
        self._auto_resize_columns()

        # 更新导航按钮
        self._update_nav_state()

        # 发出统计消息
        self.status_message.emit(
            f"对比完成 — "
            f"新增 {diff_result.stats.get('added', 0)} | "
            f"删除 {diff_result.stats.get('deleted', 0)} | "
            f"修改 {diff_result.stats.get('modified', 0)} | "
            f"共 {len(df)} 行"
        )

    def _auto_resize_columns(self):
        """自适应列宽"""
        if not self._model:
            return

        h_header = self._table.horizontalHeader()
        n_cols = self._model.columnCount()

        # 状态列已固定，其余列给默认值
        for col in range(1, n_cols):
            h_header.resizeSection(col, 150)

    # ---------- 汇总视图（新增）----------

    def _on_summary(self):
        """打开汇总视图"""
        if self._diff_result is None:
            return
        dialog = SummaryDialog(self._diff_result, self)
        dialog.exec()

    # ---------- 双击行差异详情（新增）----------

    def _on_row_double_clicked(self, index: QModelIndex):
        """双击行 — 打开差异详情弹窗"""
        if self._diff_result is None or self._model is None:
            return

        # 获取 source 模型中的行索引
        proxy_index = self._proxy.mapToSource(index)
        source_row = proxy_index.row()

        if 0 <= source_row < len(self._diff_result.merged_df):
            dialog = DiffDetailDialog(self._diff_result, source_row, self)
            dialog.exec()

    # ---------- 筛选 ----------

    def set_filter_diff_only(self, enabled: bool):
        """设置仅显示差异行"""
        self._filter_cb.setChecked(enabled)

    def _on_filter_changed(self, state):
        """筛选状态变化"""
        self._filter_diff_only = (state == Qt.CheckState.Checked.value)
        self._current_nav_index = -1

        if self._proxy:
            self._proxy.set_filter_diff_only(self._filter_diff_only)

        self._update_nav_state()

    # ---------- 差异导航 ----------

    def navigate_to_next_diff(self):
        """导航到下一条差异"""
        if not self._diff_row_indices:
            return

        visible_diff = self._get_visible_diff_indices()
        if not visible_diff:
            return

        if self._current_nav_index < len(visible_diff) - 1:
            self._current_nav_index += 1
        else:
            self._current_nav_index = 0  # 循环

        self._scroll_to_diff(visible_diff[self._current_nav_index])

    def navigate_to_prev_diff(self):
        """导航到上一条差异"""
        if not self._diff_row_indices:
            return

        visible_diff = self._get_visible_diff_indices()
        if not visible_diff:
            return

        if self._current_nav_index > 0:
            self._current_nav_index -= 1
        else:
            self._current_nav_index = len(visible_diff) - 1  # 循环

        self._scroll_to_diff(visible_diff[self._current_nav_index])

    def _get_visible_diff_indices(self) -> list:
        """
        获取当前视图中的差异行索引列表（proxy 层面）
        """
        if not self._proxy or not self._model:
            return []

        if self._filter_diff_only:
            return list(range(self._proxy.rowCount()))

        visible = []
        for source_row in self._diff_row_indices:
            proxy_idx = self._proxy.mapFromSource(
                self._model.index(source_row, 0)
            )
            if proxy_idx.isValid():
                visible.append(proxy_idx.row())
        return visible

    def _scroll_to_diff(self, proxy_row: int):
        """滚动到指定差异行"""
        if not self._proxy or not self._model:
            return

        if 0 <= proxy_row < self._proxy.rowCount():
            self._table.selectRow(proxy_row)
            self._table.scrollTo(
                self._proxy.index(proxy_row, 0),
                QAbstractItemView.ScrollHint.PositionAtCenter
            )
            self._update_nav_state()

    def _update_nav_state(self):
        """更新导航按钮状态"""
        visible_diff = self._get_visible_diff_indices()
        total = len(visible_diff)
        has_diff = total > 0

        self._prev_btn.setEnabled(has_diff)
        self._next_btn.setEnabled(has_diff)

        if has_diff:
            current = self._current_nav_index + 1 if self._current_nav_index >= 0 else 1
            self._nav_label.setText(f"差异 {current}/{total}")
        else:
            self._nav_label.setText("无差异")

    # ---------- 清空与空状态 ----------

    def clear(self):
        """清空结果"""
        self._diff_result = None
        self._diff_row_indices = []
        self._current_nav_index = -1

        if self._proxy:
            self._proxy.setSourceModel(None)
        self._model = None

        self._export_btn.setEnabled(False)
        self._summary_btn.setEnabled(False)
        self._table.hide()
        self._empty_label.show()
        self._empty_label.setText('📄  请先加载两个文件并点击"开始对比"\n\n💡 提示：双击结果行可查看详细的字段对比')
        self._nav_label.setText("")
        self._prev_btn.setEnabled(False)
        self._next_btn.setEnabled(False)

    def _show_empty(self, message: str):
        """显示空状态"""
        self._table.hide()
        self._empty_label.setText(f"📄  {message}")
        self._empty_label.show()

    def _on_export(self):
        """点击导出按钮"""
        self.export_requested.emit()
