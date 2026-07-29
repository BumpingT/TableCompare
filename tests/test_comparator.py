"""快速功能测试 — 验证对比逻辑是否正确"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.core.loader import FileLoader
from src.core.comparator import TableComparator


def test_comparison():
    print("=" * 50)
    print("📋 表格对比工具 — 功能测试")
    print("=" * 50)

    # 创建测试数据：初始版
    df_old = pd.DataFrame({
        'ID': ['A001', 'A002', 'A003', 'A004', 'A005'],
        '姓名': ['张三', '李四', '王五', '赵六', '钱七'],
        '年龄': ['28', '32', '45', '19', '36'],
        '部门': ['技术部', '市场部', '财务部', '技术部', '人事部'],
        '薪资': ['12000', '15000', '18000', '8000', '14000'],
    })

    # 创建测试数据：修改版（有新增、删除、修改）
    df_new = pd.DataFrame({
        'ID': ['A001', 'A002', 'A003', 'A005', 'A006', 'A007'],
        '姓名': ['张三', '李四', '王五', '钱七', '孙八', '周九'],
        '年龄': ['29', '32', '45', '36', '25', '41'],  # 张三年龄改为29
        '部门': ['技术部', '市场部', '财务部', '人事部', '研发部', '行政部'],
        '薪资': ['12500', '15000', '18000', '14500', '16000', '13000'],  # 张三薪资改为12500
    })

    print(f"\n📄 初始版数据 ({len(df_old)}行):")
    print(df_old.to_string(index=False))
    print(f"\n📄 修改版数据 ({len(df_new)}行):")
    print(df_new.to_string(index=False))

    # 执行对比
    comparator = TableComparator()
    result = comparator.compare(
        df_old, df_new,
        key_column='ID',
        compare_columns=['姓名', '年龄', '部门', '薪资']
    )

    # 打印结果
    print(f"\n{'=' * 50}")
    print("📊 对比结果")
    print(f"{'=' * 50}")
    print(f"  新增行: {result.stats['added']}")
    print(f"  删除行: {result.stats['deleted']}")
    print(f"  修改行: {result.stats['modified']}")
    print(f"  相同行: {result.stats['same']}")
    print(f"\n📋 详细对比表:")
    print(result.merged_df.to_string(index=False))

    # 验证
    assert result.stats['added'] == 2, f"预期新增2行，实际 {result.stats['added']}"
    assert result.stats['deleted'] == 1, f"预期删除1行，实际 {result.stats['deleted']}"
    assert result.stats['modified'] == 2, f"预期修改2行，实际 {result.stats['modified']}"
    assert result.stats['same'] == 2, f"预期相同2行，实际 {result.stats['same']}"
    assert len(result.diff_rows) == 5, f"预期差异行5条，实际 {len(result.diff_rows)}"

    # 检查修改的单元格
    # A001 的 年龄 和 薪资 发生了修改
    # A005 的 薪资 发生了修改
    changed_keys = [(idx, col) for (idx, col), _ in result.changed_cells.items()]
    print(f"\n📌 变化的单元格: {len(result.changed_cells)} 处")
    for (idx, col), (old, new) in result.changed_cells.items():
        print(f"  行{idx}, 列'{col}': '{old}' → '{new}'")

    print(f"\n{'=' * 50}")
    print("✅ 所有测试通过！")
    print(f"{'=' * 50}")

    return result


def test_excel_export(result):
    """测试 Excel 导出"""
    from src.core.exporter import ResultExporter

    output_path = os.path.join(os.path.dirname(__file__), '..', 'test_export.xlsx')
    ResultExporter.to_excel(result, output_path, only_diff=False)
    print(f"\n📥 导出成功: {output_path}")
    assert os.path.exists(output_path), "导出文件未生成"

    os.remove(output_path)
    print(f"🧹 清理临时文件: {output_path}")
    print("✅ 导出测试通过！")


if __name__ == '__main__':
    result = test_comparison()
    test_excel_export(result)
