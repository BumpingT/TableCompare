# src/ui/__init__.py
from .main_window import MainWindow
from .file_panel import FilePanel
from .compare_panel import ComparePanel
from .result_table import ResultTable
from .stats_bar import StatsBar
from .summary_dialog import SummaryDialog
from .diff_detail_dialog import DiffDetailDialog

__all__ = [
    'MainWindow', 'FilePanel', 'ComparePanel', 'ResultTable', 'StatsBar',
    'SummaryDialog', 'DiffDetailDialog',
]
