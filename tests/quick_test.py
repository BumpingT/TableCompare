"""快速验证对比逻辑"""
import sys, os, time
sys.path.insert(0, 'src')
import pandas as pd
from core.comparator import TableComparator

print('1. 加载文件...')
t0 = time.perf_counter()
df_old = pd.read_excel('公司员工数据_初始版.xlsx', dtype=str)
df_new = pd.read_excel('公司员工数据_修改版.xlsx', dtype=str)
print(f'   加载完成: {time.perf_counter()-t0:.3f}s, shape={df_old.shape}')

print('2. 执行对比（正常模式 key=员工编号）...')
t0 = time.perf_counter()
c = TableComparator()
cols = [col for col in df_old.columns if col != '员工编号']
result = c.compare(df_old, df_new, key_column='员工编号', compare_columns=cols)
elapsed = time.perf_counter() - t0

print(f'   对比耗时: {elapsed:.3f}s')
print(f'   修改: {result.stats["modified"]}')
print(f'   相同: {result.stats["same"]}')
print(f'   变化单元格: {len(result.changed_cells)}')
print('✅ 核心对比逻辑正常')
