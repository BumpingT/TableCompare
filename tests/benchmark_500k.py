"""50万行压力测试"""
import sys, os, time, random
sys.path.insert(0, 'src')
import pandas as pd
from core.comparator import TableComparator

N = 500000
print(f'生成 {N:,} 行数据 (每行 5 列: ID + 4 对比列)...')
df_old = pd.DataFrame({
    'ID': [f'K{i:08d}' for i in range(N)],
    'A': [str(i) for i in range(N)],
    'B': [str(i*2) for i in range(N)],
    'C': [str(i*3) for i in range(N)],
    'D': [str(i*4) for i in range(N)],
})
df_new = df_old.copy()
random.seed(42)
for r in random.sample(range(N), N // 50):
    df_new.at[r, 'A'] = str(random.randint(0, N*10))
print(f'旧表: {len(df_old):,} 行, 新表: {len(df_new):,} 行')
print(f'内存预估: ~{N * 5 * 20 // 1024 // 1024} MB (字符串缓存不计)')

c = TableComparator()
start = time.perf_counter()
result = c.compare(df_old, df_new, key_column='ID', compare_columns=['A','B','C','D'])
elapsed = time.perf_counter() - start
print(f'\n对比耗时: {elapsed:.3f} 秒')
print(f'  修改: {result.stats["modified"]:,} / 相同: {result.stats["same"]:,}')
print(f'  changed_cells: {len(result.changed_cells):,} 处')
print(f'  merged_df 行数: {len(result.merged_df):,}')
print(f'\n{"✅ 通过" if elapsed < 30 else "⚠️ 需要关注"}')
