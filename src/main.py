"""
表格对比工具 TableDiff — 主入口

使用方式:
    python src/main.py

功能:
    导入两个表格文件（Excel/CSV），自动对比差异并高亮展示
"""
import sys
import os
import logging

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings

from src.ui.main_window import MainWindow


def setup_logging():
    """配置日志（写入 exe 所在目录或项目目录）"""
    # 判断是否在 PyInstaller 打包环境中
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

    log_file = os.path.join(log_dir, 'TableDiff_debug.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )

    # 降低 PySide6 和 pandas 的日志级别
    logging.getLogger('PySide6').setLevel(logging.WARNING)
    logging.getLogger('pandas').setLevel(logging.WARNING)

    return logging.getLogger('table_diff')


def main():
    """应用主入口"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("表格对比工具 TableDiff 启动")
    logger.info("=" * 60)

    # 启用高分屏适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("TableDiff")
    app.setApplicationDisplayName("表格对比工具")
    app.setOrganizationName("TableDiff")

    # 使用 INI 格式保存设置（避免注册表权限问题）
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)

    # 设置应用全局字体
    font = app.font()
    font.setPointSize(10)
    font.setFamily("Microsoft YaHei")
    app.setFont(font)

    window = MainWindow()
    window.show()

    logger.info("应用窗口已显示")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
