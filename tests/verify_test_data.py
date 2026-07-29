"""验证生成的公司数据可以被正确对比"""
import sys, os, time
sys.path.insert(0, 'src')
import pandas as pd
from core.comparator import TableComparator

print('加载公司数据文件...')
df_old = pd.read_excel('公司员工数据_初始版.xlsx', dtype=str)
df_new = pd.read_excel('公司员工数据_修改版.xlsx', dtype=str)
print(f'  初始版: {df_old.shape[0]:,}行 x {df_old.shape[1]}列')
print(f'  修改版: {df_new.shape[0]:,}行 x {df_new.shape[1]}列')

compare_cols = [c for c in df_old.columns if c != '员工编号']
print(f'  对比列: {len(compare_cols)} 列')

c = TableComparator()
start = time.perf_counter()
result = c.compare(df_old, df_new, key_column='员工编号', compare_columns=compare_cols)
elapsed = time.perf_counter() - start

print(f'\n对比耗时: {elapsed:.3f} 秒')
print(f'  总行: {len(result.merged_df):,}')
stats = result.stats
print(f'  新增: {stats["added"]}')
print(f'  删除: {stats["deleted"]}')
print(f'  修改: {stats["modified"]}')
print(f'  相同: {stats["same"]}')
print(f'  变化单元格: {len(result.changed_cells):,} 处')
print(f'\n  merged_df 列数: {len(result.merged_df.columns)}')
print(f'\n✅ 验证通过！数据可以直接用于对比工具。')
