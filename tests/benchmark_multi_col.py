"""多列压力测试：100列 × 10000行"""
import sys, os, time, random
sys.path.insert(0, 'src')
import pandas as pd
from core.comparator import TableComparator

NUM_COLS = 100
NUM_ROWS = 10000

print(f'生成 {NUM_COLS} 列 × {NUM_ROWS} 行 数据...')

# 构建列名
col_names = [f'列_{i:03d}' for i in range(NUM_COLS)]

# 生成数据
data_old = {'ID': [f'K{i:06d}' for i in range(NUM_ROWS)]}
data_new = {'ID': [f'K{i:06d}' for i in range(NUM_ROWS)]}

for col in col_names:
    data_old[col] = [f'v{r}_{col}' for r in range(NUM_ROWS)]
    data_new[col] = [f'v{r}_{col}' for r in range(NUM_ROWS)]

df_old = pd.DataFrame(data_old)
df_new = pd.DataFrame(data_new)

# 修改 5% 的行 × 10% 的列
random.seed(42)
modified_rows = random.sample(range(NUM_ROWS), NUM_ROWS // 20)
modified_cols = random.sample(col_names, NUM_COLS // 10)

for r in modified_rows:
    for c in modified_cols:
        df_new.at[r, c] = f'modified_{r}_{c}'

print(f'旧表: {df_old.shape}, 新表: {df_new.shape}')
print(f'修改行: {len(modified_rows)}, 修改列: {len(modified_cols)}')

c = TableComparator()
import time
start = time.perf_counter()
result = c.compare(df_old, df_new, key_column='ID', compare_columns=col_names)
elapsed = time.perf_counter() - start

print(f'\n对比耗时: {elapsed:.3f} 秒')
print(f'  总行: {len(result.merged_df):,}')
print(f'  修改: {result.stats["modified"]:,}')
print(f'  changed_cells: {len(result.changed_cells):,} 处')
print(f'  merged_df 列数: {len(result.merged_df.columns)}')
print(f'\n{"✅ 多列测试通过" if elapsed < 10 else "⚠️ 需要关注"}')
