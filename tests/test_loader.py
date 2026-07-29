"""测试 sheet 回退加载"""
import sys; sys.path.insert(0, 'src')
from core.loader import FileLoader

# 正常加载
df, meta = FileLoader.load('公司员工数据_初始版.xlsx')
print('正常加载:', meta['sheet_name'], '-', meta['rows'], '行')

# sheet 名不存在时自动回退
df2, meta2 = FileLoader.load('公司员工数据_初始版.xlsx', sheet_name='不存在的Sheet')
print('回退加载:', meta2['sheet_name'], '-', meta2['rows'], '行')

print('✅ 测试通过')
