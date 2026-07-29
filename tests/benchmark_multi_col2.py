"""200列 x 5万行 极限压力测试"""
import sys, os, time, random, pandas as pd
sys.path.insert(0, 'src')
from core.comparator import TableComparator

cols, rows = 200, 50000
col_names = [f'C{i:03d}' for i in range(cols)]
print(f'生成 {cols} 列 x {rows:,} 行...')

data = {'ID': [f'K{i:06d}' for i in range(rows)]}
for c in col_names:
    data[c] = [f'v{r}_{c}' for r in range(rows)]
df_old = pd.DataFrame(data)
df_new = df_old.copy()

random.seed(42)
for r in random.sample(range(rows), rows // 50):
    for c in random.sample(col_names, 5):
        df_new.at[r, c] = f'mod_{r}_{c}'

c = TableComparator()
start = time.perf_counter()
result = c.compare(df_old, df_new, 'ID', col_names)
elapsed = time.perf_counter() - start

print(f'对比耗时: {elapsed:.3f} 秒')
print(f'  merged_df: {result.merged_df.shape}')
print(f'  修改: {result.stats["modified"]:,}')
print(f'  changed_cells: {len(result.changed_cells):,} 处')
print(f'  结果表总列数: {len(result.merged_df.columns)}')
print(f'{"✅" if elapsed < 10 else "⚠️"} {cols}列 x {rows:,}行 = {elapsed:.3f}秒')
