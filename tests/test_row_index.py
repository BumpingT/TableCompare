"""测试行号匹配模式"""
import sys, os
sys.path.insert(0, 'src')
import pandas as pd
from core.comparator import TableComparator

# 一长列数据：纯名单
df_old = pd.DataFrame({'产品': ['苹果', '香蕉', '橙子', '葡萄']})
df_new = pd.DataFrame({'产品': ['苹果', '香蕉', '草莓', '葡萄', '芒果']})

c = TableComparator()
result = c.compare(df_old, df_new, key_column='',
                   compare_columns=['产品'], use_row_index=True)

print('行号匹配模式 — 一列数据对比:')
print(result.merged_df.to_string(index=False))
print()
print(f'  新增: {result.stats["added"]}')
print(f'  删除: {result.stats["deleted"]}')
print(f'  修改: {result.stats["modified"]}')
print(f'  相同: {result.stats["same"]}')

assert result.stats['added'] == 1, f'预期新增1, 实际{result.stats["added"]}'
assert result.stats['deleted'] == 0, f'预期删除0, 实际{result.stats["deleted"]}'
assert result.stats['modified'] == 1, f'预期修改1, 实际{result.stats["modified"]}'
assert result.stats['same'] == 3, f'预期相同3, 实际{result.stats["same"]}'

# 两列数据测试
print('\n--- 两列数据（无键列） ---')
df_old2 = pd.DataFrame({
    '姓名': ['张三', '李四', '王五'],
    '分数': ['85', '92', '78'],
})
df_new2 = pd.DataFrame({
    '姓名': ['张三', '李四', '赵六'],
    '分数': ['90', '92', '88'],
})
result2 = c.compare(df_old2, df_new2, key_column='',
                    compare_columns=['姓名', '分数'], use_row_index=True)
print(result2.merged_df.to_string(index=False))
print(f'  新增: {result2.stats["added"]}, 修改: {result2.stats["modified"]}, 相同: {result2.stats["same"]}')
assert result2.stats['added'] == 0  # 行号模式：位置对应，无新增
assert result2.stats['modified'] == 2  # 张三分数 85→90, 王五→赵六(88)
assert result2.stats['same'] == 1  # 李四

print('\n✅ 全部行号匹配测试通过！')
