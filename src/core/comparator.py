"""
表格对比器模块
对两个 DataFrame 进行逐行逐列对比，标记差异
v2 — 使用 pd.merge + 向量化对比，支持大数据量
"""
import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger('table_diff.comparator')

# 状态常量
STATUS_SAME = 'same'
STATUS_MODIFIED = 'modified'
STATUS_ADDED = 'added'
STATUS_DELETED = 'deleted'

STATUS_COL = '__status__'
KEY_COL = '__key__'


@dataclass
class DiffResult:
    """对比结果数据模型"""
    merged_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    """合并后的完整对比表，包含 __status__ 列"""

    stats: dict = field(default_factory=dict)
    """{'added': int, 'deleted': int, 'modified': int, 'same': int, 'total_old': int, 'total_new': int}"""

    diff_rows: list = field(default_factory=list)
    """所有差异行在 merged_df 中的索引列表"""

    changed_cells: dict = field(default_factory=dict)
    """{(row_idx, col_name): (old_val, new_val)} 记录每个修改单元格的旧值和新值"""

    key_column: str = ''
    """使用的键列名"""

    compare_columns: list = field(default_factory=list)
    """参与对比的列名列表"""


class TableComparator:
    """表格对比器 — v2 向量化实现"""

    def compare(
        self,
        df_old: pd.DataFrame,
        df_new: pd.DataFrame,
        key_column: str,
        compare_columns: list[str] | None = None,
        use_row_index: bool = False,
    ) -> DiffResult:
        """
        执行表格对比（O(n) 向量化版本）

        Args:
            df_old: 初始版 DataFrame
            df_new: 修改版 DataFrame
            key_column: 用作键的列名，用于匹配两表的行
            compare_columns: 需要对比的列名列表，None 表示对比所有共有列
            use_row_index: 为 True 时使用行号匹配（适用于无键列的单列数据）

        Returns:
            DiffResult 包含合并后的对比结果
        """
        logger.info(f"开始对比: key_column='{key_column}', "
                     f"旧表={len(df_old)}行, 新表={len(df_new)}行, "
                     f"use_row_index={use_row_index}")

        df_old = df_old.copy()
        df_new = df_new.copy()

        # === 行号匹配模式：适用于无键列的单列/多行数据 ===
        if use_row_index:
            # 把所有列都视为对比列
            common_cols = list(set(df_old.columns) & set(df_new.columns))
            if compare_columns is None:
                compare_columns = common_cols[:]
            else:
                compare_columns = [c for c in compare_columns if c in common_cols]

            if not compare_columns:
                raise ValueError("两表没有共同的列可供对比")

            # 添加临时行号作为键
            key_column = '__row_index__'
            df_old[key_column] = range(len(df_old))
            df_new[key_column] = range(len(df_new))

            logger.info(f"行号匹配模式: 对比列 ({len(compare_columns)}): {compare_columns[:5]}...")

        else:
            # === 标准模式：使用用户指定的键列 ===

            # 校验键列是否存在
            if key_column not in df_old.columns:
                raise ValueError(f"键列 '{key_column}' 在初始版中不存在")
            if key_column not in df_new.columns:
                raise ValueError(f"键列 '{key_column}' 在修改版中不存在")

            # 检测键列是否有重复值（会导致合并爆炸）
            old_dup = df_old[key_column].duplicated().sum()
            new_dup = df_new[key_column].duplicated().sum()
            if old_dup > 0 or new_dup > 0:
                dup_total = old_dup + new_dup
                raise ValueError(
                    f"键列 '{key_column}' 中有 {dup_total} 个重复值！\n\n"
                    f"键列的值必须唯一，才能正确匹配两表的行。\n"
                    f"请选择其他列作为键列，如「员工编号」「订单号」等。\n\n"
                    f"（初始版重复 {old_dup} 行，修改版重复 {new_dup} 行）"
                )

            # 确定对比列
            common_cols = list(set(df_old.columns) & set(df_new.columns))
            if compare_columns is None:
                compare_columns = [c for c in common_cols if c != key_column]
            else:
                # 只取既在 compare_columns 中又在两表共有的列
                compare_columns = [c for c in compare_columns if c in common_cols and c != key_column]

            if not compare_columns:
                raise ValueError("没有可供对比的列（所有共有列均已排除或不存在）")

            logger.info(f"对比列 ({len(compare_columns)}): {compare_columns[:5]}...")

            # 标准化键值（避免类型不一致导致匹配失败）
            df_old[key_column] = df_old[key_column].astype(str).str.strip()
            df_new[key_column] = df_new[key_column].astype(str).str.strip()

        # 仅保留需要的列以节省内存
        cols_old = [key_column] + compare_columns
        cols_new = [key_column] + compare_columns

        # === O(n) merge 前统一转为字符串 ===
        for col in compare_columns:
            df_old[col] = df_old[col].fillna('').astype(str)
            df_new[col] = df_new[col].fillna('').astype(str)

        merged = pd.merge(
            df_old[cols_old],
            df_new[cols_new],
            on=key_column,
            how='outer',
            suffixes=('_旧', '_新'),
            indicator=True,
        )

        # _merge 列: 'left_only' → 删除, 'right_only' → 新增, 'both' → 共有
        # 使用 object dtype 避免 Categorical 限制（后面要添加 STATUS_MODIFIED）
        merged[STATUS_COL] = merged['_merge'].map({
            'left_only': STATUS_DELETED,
            'right_only': STATUS_ADDED,
            'both': STATUS_SAME,
        }).astype(object).fillna(STATUS_SAME)

        # === 第三步：向量化检测共有行差异 ===
        both_mask = merged['_merge'] == 'both'
        is_modified = pd.Series(False, index=merged.index)

        if both_mask.any():
            # 为 'both' 行构建旧/新值 DataFrame
            old_cols = [f'{c}_旧' for c in compare_columns]
            new_cols = [f'{c}_新' for c in compare_columns]

            both_idx = merged.index[both_mask]
            old_vals = merged.loc[both_idx, old_cols]
            old_vals.columns = compare_columns
            new_vals = merged.loc[both_idx, new_cols]
            new_vals.columns = compare_columns

            # 向量化逐列比较 — .ne() 是 pandas 内置的 !=
            cell_diff = old_vals.ne(new_vals)
            row_modified = cell_diff.any(axis=1)

            # 标记修改行
            is_modified[both_idx] = row_modified.values
            merged.loc[is_modified, STATUS_COL] = STATUS_MODIFIED

        # === 第四步：构建 changed_cells 字典（仅差异单元格）===
        changed_cells = {}
        modified_mask = is_modified & both_mask

        if modified_mask.any():
            mod_idx = merged.index[modified_mask]
            old_cols_list = [f'{c}_旧' for c in compare_columns]
            new_cols_list = [f'{c}_新' for c in compare_columns]

            for idx in mod_idx:
                row = merged.loc[idx]
                for ci, col in enumerate(compare_columns):
                    old_val = row.iloc[merged.columns.get_loc(old_cols_list[ci])]
                    new_val = row.iloc[merged.columns.get_loc(new_cols_list[ci])]
                    if old_val != new_val:
                        changed_cells[(idx, col)] = (old_val, new_val)

        # === 第五步：清理并构建结果 ===
        merged.drop(columns='_merge', inplace=True)
        merged.rename(columns={key_column: KEY_COL}, inplace=True)

        # 计算统计
        stats = {
            'added': int((merged[STATUS_COL] == STATUS_ADDED).sum()),
            'deleted': int((merged[STATUS_COL] == STATUS_DELETED).sum()),
            'modified': int((merged[STATUS_COL] == STATUS_MODIFIED).sum()),
            'same': int((merged[STATUS_COL] == STATUS_SAME).sum()),
            'total_old': len(df_old),
            'total_new': len(df_new),
        }

        diff_rows = merged[merged[STATUS_COL] != STATUS_SAME].index.tolist()

        logger.info(f"对比完成: "
                     f"新增={stats['added']}, 删除={stats['deleted']}, "
                     f"修改={stats['modified']}, 相同={stats['same']}")

        return DiffResult(
            merged_df=merged,
            stats=stats,
            diff_rows=diff_rows,
            changed_cells=changed_cells,
            key_column=key_column,
            compare_columns=compare_columns,
        )
