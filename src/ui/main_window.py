"""
主窗口
组装所有 UI 控件，连接信号槽，管理应用整体状态
v3 — 增加拖拽导入、列搜索、汇总视图、差异详情、文件历史、多 Sheet 支持
"""
import os
import logging
import traceback

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar, QMessageBox, QFileDialog, QApplication, QFrame,
    QLabel, QPushButton, QProgressBar, QMenu, QMenuBar,
    QDialog, QTableWidget, QAbstractItemView, QCheckBox,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QAction, QIcon

from .file_panel import FilePanel
from .compare_panel import ComparePanel
from .stats_bar import StatsBar
from .result_table import ResultTable
from ..core.loader import FileLoader
from ..core.comparator import TableComparator, DiffResult
from ..core.exporter import ResultExporter

logger = logging.getLogger('table_diff.ui.main_window')


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self):
        super().__init__()
        self._df_old = None
        self._df_new = None
        self._metadata_old = None
        self._metadata_new = None
        self._diff_result = None
        self._settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, 'TableDiff', 'MainWindow')

        self._setup_window()
        self._setup_menu_bar()
        self._setup_ui()
        self._connect_signals()
        self._apply_global_style()
        self._restore_window_state()

    def _setup_window(self):
        self.setWindowTitle("📋 表格对比工具 — TableDiff")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

    def _setup_menu_bar(self):
        """菜单栏 — 包含文件历史和快捷键"""
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("📁  文件")

        # 最近打开的文件子菜单
        self._recent_menu = QMenu("📂  最近打开的文件", self)
        self._recent_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #F1F5F9;
            }
        """)
        self._update_recent_menu()
        file_menu.addMenu(self._recent_menu)

        file_menu.addSeparator()

        exit_action = QAction("退出  Ctrl+Q", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 帮助菜单
        help_menu = menu_bar.addMenu("❓  帮助")
        about_action = QAction("关于 TableDiff", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        shortcut_action = QAction("快捷键说明", self)
        shortcut_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcut_action)

    def _update_recent_menu(self):
        """更新最近打开的文件菜单"""
        self._recent_menu.clear()

        # 读取历史 JSON 文件
        recent_all = self._load_history_file()

        if not recent_all:
            action = self._recent_menu.addAction("（暂无历史文件）")
            action.setEnabled(False)
            return

        for i, f in enumerate(recent_all[:15]):
            path = f['path']
            sheet = f.get('sheet', '')
            basename = os.path.basename(path)

            label = f"{i+1}. {basename}"
            if sheet:
                label += f"  [Sheet: {sheet}]"

            action = self._recent_menu.addAction(label)
            action.setData(path)
            action.setToolTip(f"{path}\nSheet: {sheet or '默认'}")

        self._recent_menu.addSeparator()
        clear_action = self._recent_menu.addAction("🗑  清除所有历史")
        clear_action.setData(None)

        self._recent_menu.triggered.connect(self._on_recent_menu_clicked)

    @staticmethod
    def _load_history_file() -> list:
        """从 JSON 文件读取历史记录"""
        path = MainWindow._history_path()
        if not os.path.exists(path):
            return []
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def _history_path() -> str:
        """历史记录文件路径"""
        import sys
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.getcwd()
        return os.path.join(base, 'TableDiff_history.json')

    @staticmethod
    def _clear_history_file():
        """清空历史记录文件"""
        path = MainWindow._history_path()
        try:
            import json
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([], f)
        except Exception:
            pass

    def _on_recent_menu_clicked(self, action):
        """点击最近文件菜单"""
        data = action.data()
        if data is None:
            # 清除所有历史
            MainWindow._clear_history_file()
            self._update_recent_menu()
            return

        if data:
            # 询问加载到哪一侧
            msg = QMessageBox(self)
            msg.setWindowTitle("加载文件")
            msg.setText(f"将文件加载到哪一侧？\n\n{os.path.basename(data)}")
            msg.setInformativeText(data)
            left_btn = msg.addButton("📄  初始版（左侧）", QMessageBox.ActionRole)
            right_btn = msg.addButton("📄  修改版（右侧）", QMessageBox.ActionRole)
            msg.addButton("取消", QMessageBox.RejectRole)
            msg.exec()

            if msg.clickedButton() == left_btn:
                self._left_panel._load_file(data)
            elif msg.clickedButton() == right_btn:
                self._right_panel._load_file(data)

    def _show_about(self):
        QMessageBox.about(self, "关于 TableDiff",
            "📋 表格对比工具 TableDiff v3.0\n\n"
            "功能：\n"
            "• 导入两个表格文件进行差异对比\n"
            "• 支持 Excel (.xlsx/.xls) 和 CSV 格式\n"
            "• 自动标记新增/删除/修改的差异\n"
            "• 支持拖拽导入、列搜索、多 Sheet\n"
            "• 汇总视图、差异详情弹窗、文件历史\n\n"
            "技术栈：Python + PySide6 + pandas"
        )

    def _show_shortcuts(self):
        QMessageBox.information(self, "快捷键说明",
            "⌨️  快捷键列表\n\n"
            "Ctrl+O      → 导入初始版文件\n"
            "Ctrl+Shift+O → 导入修改版文件\n"
            "Ctrl+R      → 开始对比\n"
            "Ctrl+E      → 导出结果\n"
            "Ctrl+N      → 下一条差异\n"
            "Ctrl+P      → 上一条差异\n"
            "Ctrl+Q      → 退出\n\n"
            "🖱  其他操作\n"
            "拖拽文件     → 直接导入到面板\n"
            "双击结果行   → 查看差异详情\n"
            "列名搜索框   → 快速定位列"
        )

    def _setup_ui(self):
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # === 顶部：文件导入区域（左右并列） ===
        file_layout = QHBoxLayout()
        file_layout.setSpacing(12)

        self._left_panel = FilePanel("📄  初始版（旧版）", "请选择初始版表格文件...")
        self._right_panel = FilePanel("📄  修改版（新版）", "请选择修改版表格文件...")
        file_layout.addWidget(self._left_panel)
        file_layout.addWidget(self._right_panel)

        main_layout.addLayout(file_layout)

        # === 中间：对比设置 + 统计栏 ===
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(12)

        # 对比设置面板
        self._compare_panel = ComparePanel()
        settings_layout.addWidget(self._compare_panel, 2)

        # 统计栏
        self._stats_bar = StatsBar()
        settings_layout.addWidget(self._stats_bar, 1)

        main_layout.addLayout(settings_layout)

        # === 底部：结果表格（主要区域）===
        self._result_table = ResultTable()
        main_layout.addWidget(self._result_table, 1)

        # === 状态栏 ===
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #F1F5F9;
                border-top: 1px solid #E2E8F0;
                padding: 4px 12px;
                font-size: 12px;
                color: #64748B;
            }
        """)
        self.setStatusBar(self._status_bar)

        # 状态栏进度
        self._progress_label = QLabel("")
        self._status_bar.addPermanentWidget(self._progress_label)

        # 状态栏消息
        self._status_label = QLabel("就绪 — 请先加载两个表格文件 | 支持拖拽导入")
        self._status_bar.addWidget(self._status_label)

    def _connect_signals(self):
        """连接所有信号槽"""

        # 文件面板 → 加载文件（信号携带 sheet_name）
        self._left_panel.file_selected.connect(self._on_file_selected_left)
        self._right_panel.file_selected.connect(self._on_file_selected_right)
        self._left_panel.file_cleared.connect(self._on_file_cleared_left)
        self._right_panel.file_cleared.connect(self._on_file_cleared_right)

        # 对比面板
        self._compare_panel.compare_requested.connect(self._on_compare_requested)

        # 结果表格
        self._result_table.status_message.connect(self._on_status_message)
        self._result_table.export_requested.connect(self.export_result)

    def _apply_global_style(self):
        """应用全局样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC;
            }
            QSplitter::handle {
                background-color: #E2E8F0;
                width: 2px;
            }
            QMenuBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
                padding: 2px 0;
                font-size: 12px;
                color: #1E293B;
            }
            QMenuBar::item:selected {
                background-color: #F1F5F9;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #F1F5F9;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #CBD5E1;
                border-radius: 4px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def _restore_window_state(self):
        """恢复窗口位置和大小"""
        geometry = self._settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        """关闭时询问确认并保存窗口状态"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出表格对比工具吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._settings.setValue('geometry', self.saveGeometry())
            super().closeEvent(event)
        else:
            event.ignore()

    # ========== 文件加载处理 ==========

    def _on_file_selected_left(self, file_path: str, sheet_name: str = ''):
        """左侧文件选中（携带 sheet_name）"""
        try:
            self._status_label.setText("正在加载初始版文件...")
            QApplication.processEvents()

            sheet = sheet_name if sheet_name else None
            df, meta = FileLoader.load(file_path, sheet_name=sheet)
            self._df_old = df
            self._metadata_old = meta

            sheet_info = f" [Sheet: {sheet_name}]" if sheet_name else ""
            self._status_label.setText(f"✅ 初始版加载成功: {meta['filename']}{sheet_info} ({meta['rows']}行)")

            # 如果右侧也已加载，取两表共有列
            if self._df_new is not None:
                old_cols = meta['columns']
                new_cols_set = set(self._metadata_new['columns'])
                common_cols = [c for c in old_cols if c in new_cols_set]
                self._compare_panel.set_columns(common_cols if common_cols else meta['columns'])
            else:
                self._compare_panel.set_columns(meta['columns'])

            self._result_table.clear()
            self._stats_bar.reset()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件:\n{e}")
            self._status_label.setText("❌ 文件加载失败")
            self._left_panel.clear()

    def _on_file_selected_right(self, file_path: str, sheet_name: str = ''):
        """右侧文件选中（携带 sheet_name）"""
        try:
            self._status_label.setText("正在加载修改版文件...")
            QApplication.processEvents()

            sheet = sheet_name if sheet_name else None
            df, meta = FileLoader.load(file_path, sheet_name=sheet)
            self._df_new = df
            self._metadata_new = meta

            sheet_info = f" [Sheet: {sheet_name}]" if sheet_name else ""
            self._status_label.setText(f"✅ 修改版加载成功: {meta['filename']}{sheet_info} ({meta['rows']}行)")

            # 如果左侧也加载了，更新列选择器
            if self._df_old is not None:
                old_cols = self._metadata_old['columns']
                new_cols_set = set(meta['columns'])
                common_cols = [c for c in old_cols if c in new_cols_set]
                if common_cols:
                    self._compare_panel.set_columns(common_cols)
                else:
                    self._compare_panel.set_columns(meta['columns'])
            else:
                self._compare_panel.set_columns(meta['columns'])

            self._result_table.clear()
            self._stats_bar.reset()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件:\n{e}")
            self._status_label.setText("❌ 文件加载失败")
            self._right_panel.clear()

    def _on_file_cleared_left(self):
        self._df_old = None
        self._metadata_old = None
        self._result_table.clear()
        self._stats_bar.reset()
        self._status_label.setText("已清除初始版文件")

    def _on_file_cleared_right(self):
        self._df_new = None
        self._metadata_new = None
        self._result_table.clear()
        self._stats_bar.reset()
        self._status_label.setText("已清除修改版文件")

    # ========== 对比处理 ==========

    def _on_compare_requested(self, key_column: str, compare_columns: list, use_row_index: bool = False):
        """收到对比请求"""
        if self._df_old is None or self._df_new is None:
            QMessageBox.warning(self, "提示", "请先加载初始版和修改版两个文件")
            return

        if not compare_columns:
            QMessageBox.warning(self, "提示", "请至少选择一列进行对比")
            return

        if not use_row_index:
            if key_column not in self._df_old.columns:
                QMessageBox.critical(self, "错误", f"键列 '{key_column}' 在初始版中不存在")
                return
            if key_column not in self._df_new.columns:
                QMessageBox.critical(self, "错误", f"键列 '{key_column}' 在修改版中不存在")
                return

        logger.info(f"开始对比: key='{key_column}', cols={compare_columns}, use_row_index={use_row_index}")

        # === 禁用所有控件，显示"对比中" ===
        self._left_panel.set_controls_enabled(False)
        self._right_panel.set_controls_enabled(False)
        self._compare_panel.set_controls_enabled(False)
        self._compare_panel._compare_btn.setText("⏳  对比中...")
        self._status_label.setText("正在对比数据，请稍候...")
        self._progress_label.setText("⏳ 对比中...")

        QApplication.processEvents()

        try:
            comparator = TableComparator()
            result = comparator.compare(
                self._df_old, self._df_new,
                key_column, compare_columns,
                use_row_index=use_row_index,
            )

            # === 显示结果 ===
            self._diff_result = result
            self._result_table.show_result(result)
            self._stats_bar.update_stats(result.stats)

            stats = result.stats
            msg = (f"✅ 对比完成 — "
                   f"新增 {stats['added']} | 删除 {stats['deleted']} | "
                   f"修改 {stats['modified']} | 相同 {stats['same']} | "
                   f"共 {len(result.merged_df)} 行")
            self._status_label.setText(msg)
            logger.info(msg)

        except Exception as e:
            logger.error(f"对比失败: {e}\n{traceback.format_exc()}")
            self._status_label.setText("❌ 对比失败")
            QMessageBox.critical(self, "对比失败", f"对比过程中发生错误:\n{e}")

        finally:
            self._left_panel.set_controls_enabled(True)
            self._right_panel.set_controls_enabled(True)
            self._compare_panel.set_controls_enabled(True)
            self._compare_panel._compare_btn.setText("▶  开始对比")
            self._progress_label.setText("")

    # ========== 导出处理 ==========

    def export_result(self):
        """导出对比结果"""
        if self._diff_result is None:
            QMessageBox.warning(self, "提示", "请先执行对比操作")
            return

        # 弹窗让用户选择要导出的列
        cols = self._diff_result.compare_columns
        if not cols:
            QMessageBox.warning(self, "提示", "没有可导出的列")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("选择要导出的列")
        dialog.setMinimumSize(450, 450)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        label = QLabel("勾选要导出的字段（未勾选的不会出现在 Excel 中）：")
        label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B;")
        layout.addWidget(label)

        # 用 QTableWidget 代替 QScrollArea，更稳定
        table = QTableWidget(len(cols), 1)
        table.verticalHeader().hide()
        table.horizontalHeader().hide()
        table.setShowGrid(False)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        checkboxes = {}
        for i, col in enumerate(cols):
            cb = QCheckBox(col)
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 12px; spacing: 8px; padding: 4px 0;")
            table.setCellWidget(i, 0, cb)
            checkboxes[col] = cb

        table.resizeColumnToContents(0)
        layout.addWidget(table, 1)

        # 按钮行
        btn_row = QHBoxLayout()
        select_all = QPushButton("全选")
        select_all.setFixedHeight(28)
        select_all.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes.values()])
        deselect_all = QPushButton("取消全选")
        deselect_all.setFixedHeight(28)
        deselect_all.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes.values()])
        btn_row.addWidget(select_all)
        btn_row.addWidget(deselect_all)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 确定/取消
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(32)
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn = QPushButton("确定导出")
        ok_btn.setFixedHeight(32)
        ok_btn.setStyleSheet("QPushButton { background-color: #2563EB; color: white; border: none; border-radius: 6px; padding: 8px 24px; font-size: 13px; font-weight: bold; } QPushButton:hover { background-color: #1D4ED8; }")
        ok_btn.clicked.connect(dialog.accept)
        bottom_row.addWidget(cancel_btn)
        bottom_row.addWidget(ok_btn)
        layout.addLayout(bottom_row)

        if dialog.exec() != QDialog.Accepted:
            return

        export_cols = [col for col, cb in checkboxes.items() if cb.isChecked()]
        if not export_cols:
            QMessageBox.warning(self, "提示", "请至少选择一列")
            return

        old_name = self._metadata_old['filename'] if self._metadata_old else '旧表'
        new_name = self._metadata_new['filename'] if self._metadata_new else '新表'
        base_name = f"对比结果_{os.path.splitext(old_name)[0]}_vs_{os.path.splitext(new_name)[0]}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出对比结果",
            base_name,
            "Excel 文件 (*.xlsx)",
        )

        if not file_path:
            return

        try:
            self._status_label.setText("正在导出...")
            self._progress_label.setText("⏳ 导出中...")
            QApplication.processEvents()

            self._result_table._export_btn.setEnabled(False)
            self._compare_panel._compare_btn.setEnabled(False)

            only_diff = self._result_table._filter_cb.isChecked()
            ResultExporter.to_excel(self._diff_result, file_path, only_diff=only_diff, export_columns=export_cols)

            self._status_label.setText(f"✅ 导出成功: {os.path.basename(file_path)}")
            self._progress_label.setText("")
            QMessageBox.information(self, "导出成功", f"对比结果已成功导出至:\n{file_path}")
        except Exception as e:
            logger.error(f"导出失败: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "导出失败", f"导出时发生错误:\n{e}")
            self._status_label.setText("❌ 导出失败")
            self._progress_label.setText("")
        finally:
            self._result_table._export_btn.setEnabled(True)
            self._compare_panel._compare_btn.setEnabled(True)

    # ========== 辅助 ==========

    def _on_status_message(self, msg: str):
        self._status_label.setText(msg)
