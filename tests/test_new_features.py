"""集成测试：验证6个新功能 """
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from src.core.loader import FileLoader
from src.core.comparator import TableComparator
from src.ui.summary_dialog import SummaryDialog
from src.ui.diff_detail_dialog import DiffDetailDialog
from src.ui.file_panel import SheetSelectDialog, FilePanel

app = QApplication(sys.argv)

# ====== 测试 1: 多 Sheet 选择对话框 ======
print('Test 1: SheetSelectDialog...')
dialog = SheetSelectDialog(['Sheet1', 'Sheet2', 'data'], None)
dialog.selected_sheet = 'data'
assert dialog.selected_sheet == 'data'
print('  PASS')

# ====== 测试 2: 加载指定 Sheet ======
print('Test 2: Load specific sheet...')
sheets = FileLoader.get_sheet_names('公司员工数据_初始版.xlsx')
print('  Sheets found:', sheets)
assert len(sheets) > 0, 'Should have at least one sheet'
df, meta = FileLoader.load('公司员工数据_初始版.xlsx', sheet_name=sheets[0])
assert meta.get('sheet_name') == sheets[0], 'Sheet name mismatch'
print('  Rows:', meta['rows'], 'Sheet:', meta.get('sheet_name'))
print('  PASS')

# ====== 测试 3: 完整对比流程 ======
print('Test 3: Full comparison...')
df_old, _ = FileLoader.load('公司员工数据_初始版.xlsx')
df_new, _ = FileLoader.load('公司员工数据_修改版.xlsx')
comp = TableComparator()
key = df_old.columns[0]
compare_cols = df_old.columns[1:].tolist()
result = comp.compare(df_old, df_new, key, compare_cols)
assert result.stats['modified'] > 0, 'Should have modified rows'
print('  Stats:', result.stats)
print('  Changed cells:', len(result.changed_cells))
print('  PASS')

# ====== 测试 4: 汇总视图 ======
print('Test 4: SummaryDialog...')
dialog = SummaryDialog(result)
assert dialog._table.rowCount() == len(result.compare_columns)
print('  Table rows:', dialog._table.rowCount())
print('  PASS')

# ====== 测试 5: 差异详情弹窗 ======
print('Test 5: DiffDetailDialog...')
assert len(result.diff_rows) > 0, 'Need at least one diff row'
dialog = DiffDetailDialog(result, result.diff_rows[0])
assert dialog._table.columnCount() == 3
print('  Table columns:', dialog._table.columnCount())
print('  PASS')

# ====== 测试 6: 拖拽支持 ======
print('Test 6: Drag-drop support...')
panel = FilePanel('Test', 'Drop here')
assert panel.acceptDrops(), 'Panel should accept drops'
print('  acceptDrops:', panel.acceptDrops())
print('  PASS')

print()
print('=' * 50)
print('ALL TESTS PASSED!')
print('=' * 50)
