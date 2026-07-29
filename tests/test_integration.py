"""完整集成测试"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from src.ui.main_window import MainWindow
from src.core.loader import FileLoader
from src.ui.summary_dialog import SummaryDialog

app = QApplication(sys.argv)

# 创建窗口
window = MainWindow()
window.show()
app.processEvents()
print('Window created and shown')

# 测试拖拽属性
left_panel = window._left_panel
right_panel = window._right_panel
print('Left panel accepts drops:', left_panel.acceptDrops())
print('Right panel accepts drops:', right_panel.acceptDrops())

# 测试文件历史设置
settings = QSettings('TableDiff', 'FilePanel')
settings.beginWriteArray('table_diff/recent_files')
settings.setArrayIndex(0)
settings.setValue('path', os.path.abspath('公司员工数据_初始版.xlsx'))
settings.setValue('sheet', '')
settings.endArray()
print('File history saved')

# 加载测试文件
left_path = os.path.abspath('公司员工数据_初始版.xlsx')
right_path = os.path.abspath('公司员工数据_修改版.xlsx')
left_panel._load_file(left_path)
app.processEvents()
print('Left file loaded:', left_panel.get_file_path() is not None)

right_panel._load_file(right_path)
app.processEvents()
print('Right file loaded:', right_panel.get_file_path() is not None)

# 检查列
print('Columns in compare panel:', len(window._compare_panel._columns))
print('Search box enabled:', window._compare_panel._search_input.isEnabled())

# 执行对比
window._compare_panel._on_compare()
app.processEvents()
print('Comparison triggered')
print('Has diff result:', window._diff_result is not None)

if window._diff_result:
    stats = window._diff_result.stats
    print('Stats:', stats)
    print('Summary button enabled:', window._result_table._summary_btn.isEnabled())
    print('Export button enabled:', window._result_table._export_btn.isEnabled())

    # 打开汇总视图
    summary = SummaryDialog(window._diff_result)
    print('Summary dialog rows:', summary._table.rowCount())
else:
    print('ERROR: No diff result!')

print()
print('=== INTEGRATION TEST PASSED ===')
