"""大数据量性能基准测试"""
import sys, os, time, random
sys.path.insert(0, 'src')

import pandas as pd
from core.comparator import TableComparator

# 生成 10 万行测试数据
N = 100000
print(f'\n生成 {N:,} 行测试数据...')
df_old = pd.DataFrame({
    'ID': [f'K{i:08d}' for i in range(N)],
    '姓名': [f'姓名{i}' for i in range(N)],
    '年龄': [str(20 + (i % 40)) for i in range(N)],
    '部门': [['技术部','市场部','财务部','人事部','研发部'][i % 5] for i in range(N)],
    '薪资': [str(8000 + i * 10) for i in range(N)],
})
df_new = df_old.copy()

# 修改 1% 的数据
random.seed(42)
modified_rows = random.sample(range(N), N // 100)
for r in modified_rows:
    df_new.at[r, '年龄'] = str(random.randint(20, 60))
    df_new.at[r, '薪资'] = str(random.randint(8000, 50000))

# 删除 500 行，新增 500 行
df_new = df_new[~df_new['ID'].isin([f'K{i:08d}' for i in range(500)])]
new_rows = pd.DataFrame({
    'ID': [f'N{i:08d}' for i in range(500)],
    '姓名': [f'新姓名{i}' for i in range(500)],
    '年龄': [str(random.randint(20, 60)) for _ in range(500)],
    '部门': [['技术部','市场部','财务部','人事部','研发部'][i % 5] for i in range(500)],
    '薪资': [str(random.randint(8000, 50000)) for _ in range(500)],
})
df_new = pd.concat([df_new, new_rows], ignore_index=True)
print(f'旧表: {len(df_old):,} 行, 新表: {len(df_new):,} 行')

# 计时对比
c = TableComparator()
start = time.perf_counter()
result = c.compare(df_old, df_new, key_column='ID',
                   compare_columns=['姓名','年龄','部门','薪资'])
elapsed = time.perf_counter() - start
print(f'\n对比耗时: {elapsed:.3f} 秒')
print(f'  新增: {result.stats["added"]:,}')
print(f'  删除: {result.stats["deleted"]:,}')
print(f'  修改: {result.stats["modified"]:,}')
print(f'  相同: {result.stats["same"]:,}')
print(f'  changed_cells: {len(result.changed_cells):,} 处')
print(f'  merged_df 行数: {len(result.merged_df):,}')
print(f'\n{"✅ 性能测试通过" if elapsed < 30 else "⚠️ 性能可能需要关注"}')
