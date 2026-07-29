"""
文件导入面板控件
左右各一个实例，用于选择并显示文件信息
v2 — 增加拖拽导入 + 文件历史
"""
import os
import logging

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QSizePolicy, QWidget, QApplication, QMenu,
    QDialog, QListWidget, QDialogButtonBox, QMessageBox,
)
import json
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QDragEnterEvent, QDropEvent

from ..core.loader import FileLoader

logger = logging.getLogger('table_diff.ui.file_panel')

# 文件历史最大数量
MAX_RECENT_FILES = 10


class SheetSelectDialog(QDialog):
    """多 Sheet 选择对话框"""

    def __init__(self, sheet_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择工作表（Sheet）")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.selected_sheet = sheet_names[0] if sheet_names else None

        layout = QVBoxLayout(self)

        label = QLabel(f"该 Excel 文件包含 {len(sheet_names)} 个工作表，请选择要加载的 Sheet：")
        label.setStyleSheet("font-size: 13px; color: #1E293B; margin-bottom: 8px;")
        layout.addWidget(label)

        self._list = QListWidget()
        for name in sheet_names:
            self._list.addItem(name)
        self._list.setCurrentRow(0)
        self._list.setStyleSheet("""
            QListWidget {
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 14px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
            }
            QListWidget::item:hover {
                background-color: #F1F5F9;
            }
        """)
        layout.addWidget(self._list)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet("""
            QPushButton {
                padding: 6px 20px;
                font-size: 12px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(btn_box)

    def _on_accept(self):
        item = self._list.currentItem()
        if item:
            self.selected_sheet = item.text()
        self.accept()


class FilePanel(QFrame):
    """单个文件导入面板"""

    file_selected = Signal(str, str)    # (文件路径, sheet_name)
    file_cleared = Signal()             # 清除文件

    # 支持的格式
    SUPPORTED_FILTER = "表格文件 (*.xlsx *.xls *.csv);;Excel 文件 (*.xlsx *.xls);;CSV 文件 (*.csv);;所有文件 (*.*)"

    # 类变量：记住上次打开的目录
    _last_dir = ''

    def __init__(self, title: str = "选择文件", placeholder: str = "请选择表格文件...", parent=None):
        super().__init__(parent)
        self._title = title
        self._placeholder = placeholder
        self._file_path = None
        self._sheet_name = None

        # 读取文件历史（JSON 文件，exe 同目录）
        self._recent_files = self._load_recent_files()

        self._setup_ui()
        self._apply_style()
        # 启用拖拽
        self.setAcceptDrops(True)

    def _setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title_label)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # "选择文件" 按钮 + 下拉菜单（文件历史）
        self._select_btn = QPushButton("📁  选择文件...")
        self._select_btn.setMinimumHeight(36)
        self._select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_btn.clicked.connect(self._on_select_file)
        btn_layout.addWidget(self._select_btn)

        # 文件历史下拉箭头按钮
        self._history_btn = QPushButton("▼")
        self._history_btn.setFixedSize(32, 36)
        self._history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._history_btn.setToolTip("最近打开的文件")
        self._history_btn.clicked.connect(self._show_history_menu)
        btn_layout.addWidget(self._history_btn)

        self._clear_btn = QPushButton("✕  清除")
        self._clear_btn.setMinimumHeight(36)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._on_clear)
        self._clear_btn.setEnabled(False)
        btn_layout.addWidget(self._clear_btn)

        layout.addLayout(btn_layout)

        # 拖拽提示标签
        self._drag_hint = QLabel("💡 或将文件拖拽到此处")
        self._drag_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drag_hint.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 2px;")
        layout.addWidget(self._drag_hint)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        layout.addWidget(line)

        # 文件信息区
        self._info_widget = QWidget()
        info_layout = QVBoxLayout(self._info_widget)
        info_layout.setContentsMargins(0, 4, 0, 4)
        info_layout.setSpacing(4)

        self._name_label = QLabel(self._placeholder)
        name_font = QFont()
        name_font.setPointSize(10)
        self._name_label.setFont(name_font)
        self._name_label.setWordWrap(True)
        self._name_label.setStyleSheet("color: #64748B;")
        info_layout.addWidget(self._name_label)

        self._detail_label = QLabel("")
        detail_font = QFont()
        detail_font.setPointSize(9)
        self._detail_label.setFont(detail_font)
        self._detail_label.setStyleSheet("color: #94A3B8;")
        info_layout.addWidget(self._detail_label)

        layout.addWidget(self._info_widget)

        # 弹性空间
        layout.addStretch()

        # 设置面板样式
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(280)

    def _apply_style(self):
        self.setStyleSheet("""
            FilePanel {
                background-color: #FFFFFF;
                border: 2px dashed #CBD5E1;
                border-radius: 8px;
            }
            FilePanel[file_loaded="true"] {
                border: 2px solid #2563EB;
                background-color: #F8FAFC;
            }
            FilePanel[drag_over="true"] {
                border: 2px dashed #2563EB;
                background-color: #EFF6FF;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton#selectBtn {
                background-color: #2563EB;
                color: white;
                border: none;
            }
            QPushButton#selectBtn:hover {
                background-color: #1D4ED8;
            }
            QPushButton#historyBtn {
                background-color: #E2E8F0;
                color: #475569;
                border: 1px solid #CBD5E1;
                padding: 6px 4px;
            }
            QPushButton#historyBtn:hover {
                background-color: #CBD5E1;
            }
            QPushButton#clearBtn {
                background-color: transparent;
                color: #EF4444;
                border: 1px solid #FCA5A5;
            }
            QPushButton#clearBtn:hover {
                background-color: #FEF2F2;
            }
            QPushButton#clearBtn:disabled {
                color: #CBD5E1;
                border-color: #E2E8F0;
            }
        """)
        self._select_btn.setObjectName("selectBtn")
        self._history_btn.setObjectName("historyBtn")
        self._clear_btn.setObjectName("clearBtn")

    # ========== 文件历史 ==========

    @staticmethod
    def _history_path() -> str:
        """历史记录 JSON 文件路径（exe 同级目录或当前目录）"""
        import sys
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.getcwd()
        return os.path.join(base, 'TableDiff_history.json')

    def _load_recent_files(self) -> list[dict]:
        """加载文件历史"""
        path = self._history_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_recent_files(self):
        """保存文件历史"""
        path = self._history_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._recent_files[:MAX_RECENT_FILES], f,
                         ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f'保存历史失败: {e}')

    def _add_to_recent_files(self, file_path: str, sheet_name: str = ''):
        """将文件加入历史（去重，移到最前）"""
        self._recent_files = [
            f for f in self._recent_files
            if f['path'] != file_path
        ]
        self._recent_files.insert(0, {'path': file_path, 'sheet': sheet_name})
        # 限制数量
        self._recent_files = self._recent_files[:MAX_RECENT_FILES]
        self._save_recent_files()

    def _show_history_menu(self):
        """显示文件历史下拉菜单"""
        if not self._recent_files:
            menu = QMenu(self)
            action = menu.addAction("（暂无历史文件）")
            action.setEnabled(False)
            menu.exec(self._history_btn.mapToGlobal(
                self._history_btn.rect().bottomLeft()
            ))
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #F1F5F9;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 8px;
            }
        """)

        for i, f in enumerate(self._recent_files):
            path = f['path']
            sheet = f.get('sheet', '')
            basename = os.path.basename(path)
            dirname = os.path.dirname(path)

            # 菜单项只显示文件名 + sheet
            label = f"{basename}"
            if sheet:
                label += f"  [Sheet: {sheet}]"

            action = menu.addAction(label)
            action.setData(path)
            # 完整路径放在 tooltip 里（鼠标悬停可见）
            action.setToolTip(f"{path}\nSheet: {sheet or '默认'}")

        menu.addSeparator()
        clear_action = menu.addAction("🗑  清除历史记录")
        clear_action.setData(None)  # 特殊标记

        # 连接点击
        action = menu.exec(self._history_btn.mapToGlobal(
            self._history_btn.rect().bottomLeft()
        ))

        if action is None:
            return

        data = action.data()
        if data is None:
            # 清除历史
            self._recent_files.clear()
            self._save_recent_files()
            return

        if data:
            # 从历史加载
            file_path = data
            # 查找对应的 sheet
            sheet = ''
            for f in self._recent_files:
                if f['path'] == file_path:
                    sheet = f.get('sheet', '')
                    break
            self._load_file(file_path, sheet_name=sheet if sheet else None)

    # ========== 拖拽导入 ==========

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            # 检查是否包含支持的文件
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    ext = os.path.splitext(url.toLocalFile())[1].lower()
                    if ext in FileLoader.SUPPORTED_EXTENSIONS:
                        event.acceptProposedAction()
                        self.setProperty("drag_over", True)
                        self.style().unpolish(self)
                        self.style().polish(self)
                        return
        event.ignore()

    def dragMoveEvent(self, event: QDropEvent):
        """拖拽移动"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        """拖拽离开"""
        self.setProperty("drag_over", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        """放下文件"""
        self.setProperty("drag_over", False)
        self.style().unpolish(self)
        self.style().polish(self)

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in FileLoader.SUPPORTED_EXTENSIONS:
                        self._load_file(file_path)
                        event.acceptProposedAction()
                        return
        event.ignore()

    # ========== 文件选择与加载 ==========

    def _on_select_file(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择 {self._title}",
            FilePanel._last_dir,
            self.SUPPORTED_FILTER,
        )
        if file_path:
            FilePanel._last_dir = os.path.dirname(file_path)
            self._load_file(file_path)

    def _load_file(self, file_path: str, sheet_name: str | None = None):
        """加载文件 — 先处理多 Sheet，再发出信号"""
        ext = os.path.splitext(file_path)[1].lower()

        # 检查是否为 Excel 且有多 Sheet
        if ext in ('.xlsx', '.xls') and sheet_name is None:
            sheet_names = FileLoader.get_sheet_names(file_path)
            if len(sheet_names) > 1:
                # 弹出选择对话框
                dialog = SheetSelectDialog(sheet_names, self)
                if dialog.exec() == QDialog.Accepted:
                    sheet_name = dialog.selected_sheet
                else:
                    return  # 用户取消
            elif len(sheet_names) == 1:
                sheet_name = sheet_names[0]
            else:
                sheet_name = None
        elif sheet_name is None:
            sheet_name = None  # CSV 无 sheet

        # 显示文件信息（先显示，不等实际加载完成）
        self._file_path = file_path
        self._sheet_name = sheet_name
        filename = os.path.basename(file_path)
        ext_upper = os.path.splitext(file_path)[1].upper()
        size = os.path.getsize(file_path)
        size_str = self._format_size(size)

        display_name = f"📄  {filename}"
        if sheet_name:
            display_name += f"  [Sheet: {sheet_name}]"

        self._name_label.setText(display_name)
        self._name_label.setStyleSheet("color: #1E293B; font-weight: bold;")
        self._detail_label.setText(f"格式: {ext_upper}  |  大小: {size_str}  |  正在加载...")
        self._clear_btn.setEnabled(True)

        self.setProperty("file_loaded", True)
        self.style().unpolish(self)
        self.style().polish(self)

        # 加入文件历史
        self._add_to_recent_files(file_path, sheet_name or '')

        # 发出信号（携带 sheet_name）
        self.file_selected.emit(file_path, sheet_name or '')

    def _on_clear(self):
        """清除已加载的文件"""
        self._file_path = None
        self._sheet_name = None
        self._name_label.setText(self._placeholder)
        self._name_label.setStyleSheet("color: #64748B;")
        self._detail_label.setText("")
        self._clear_btn.setEnabled(False)

        self.setProperty("file_loaded", False)
        self.style().unpolish(self)
        self.style().polish(self)

        self.file_cleared.emit()

    def get_file_path(self) -> str | None:
        return self._file_path

    def get_sheet_name(self) -> str | None:
        return self._sheet_name

    def clear(self):
        self._on_clear()

    def set_controls_enabled(self, enabled: bool):
        """启用/禁用面板上的所有操作按钮"""
        self._select_btn.setEnabled(enabled)
        self._history_btn.setEnabled(enabled)
        # 清除按钮只在有文件时启用
        if enabled and self._file_path:
            self._clear_btn.setEnabled(True)
        elif not enabled:
            self._clear_btn.setEnabled(False)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.2f} MB"
