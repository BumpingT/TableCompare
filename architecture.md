# 阶段二：系统架构设计文档

## 1. 技术栈选型

### 1.1 选型清单

| 层次 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 编程语言 | Python | ≥3.10 | 开发效率高，生态丰富，适合桌面工具快速开发 |
| GUI 框架 | PySide6 | ≥6.5 | Qt for Python，控件丰富，表格组件强大，跨平台 |
| 数据处理 | pandas | ≥2.0 | 高性能表格数据操作，对比逻辑的核心引擎 |
| Excel 读写 | openpyxl | ≥3.1 | 支持 .xlsx 格式读写，保留样式 |
| CSV 支持 | csv (内置) | — | Python 标准库，无需额外依赖 |
| 打包工具 | PyInstaller | ≥6.0 | 可选，用于打包为独立 exe |

### 1.2 选型理由

| 技术 | 理由 |
|------|------|
| **PySide6** | 相较 Tkinter 拥有更现代的控件（QTableWidget 支持富文本、颜色标记）；相较 Electron 更轻量（内存占用小），且与 Python 数据栈无缝集成 |
| **pandas** | 内置 DataFrame.compare() 和 merge() 方法，天然适合表格对比任务；处理百万行级别数据性能优秀 |
| **openpyxl** | 纯 Python 实现，无需系统依赖；支持读写样式，方便导出带颜色标记的结果文件 |

---

## 2. 系统分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    UI 层 (Presentation Layer)                │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ MainWindow  │  │ ComparePanel │  │ ResultTable       │  │
│  │ (主窗口)     │  │ (对比设置面板) │  │ (结果表格控件)    │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬──────────┘  │
│         │                │                    │             │
│  ┌──────┴──────┐  ┌──────┴───────┐  ┌────────┴──────────┐  │
│  │ FilePanel   │  │ StatsBar     │  │ DiffNavigator     │  │
│  │ (文件面板)   │  │ (统计栏)      │  │ (差异导航)        │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                业务逻辑层 (Business Logic Layer)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FileLoader (文件加载器)                   │   │
│  │  - 加载 Excel/CSV  →  pandas DataFrame               │   │
│  │  - 自动检测编码、表头、数据类型                        │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │              TableComparator (表格对比器)               │   │
│  │  - 按键列合并两个 DataFrame                            │   │
│  │  - 标记新增/删除/修改行                                │   │
│  │  - 标记修改行中的差异单元格                             │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │              ResultExporter (结果导出器)               │   │
│  │  - 导出带样式标记的 Excel 文件                         │   │
│  │  - 支持只导出差异行选项                                │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 数据层 (Data Layer)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ pandas       │  │ openpyxl     │  │ Python csv       │  │
│  │ DataFrame    │  │ Workbook     │  │ DictReader       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 各层职责

| 层次 | 职责 | 禁止行为 |
|------|------|----------|
| **UI 层** | 用户交互、事件响应、数据显示 | 不直接处理文件 I/O 和对比逻辑 |
| **业务逻辑层** | 文件加载、对比运算、结果导出 | 不依赖任何 Qt 控件 |
| **数据层** | 数据存储结构（DataFrame）、文件格式处理 | 不包含业务逻辑 |

---

## 3. 模块清单及接口定义

### 3.1 业务逻辑模块

#### Module: `core/loader.py` — 文件加载器

```python
class FileLoader:
    @staticmethod
    def load(path: str) -> tuple[pd.DataFrame, dict]
        """加载文件，返回 (DataFrame, 元数据)
        元数据包含: filename, rows, cols, columns_list
        支持 .xlsx, .xls, .csv
        """

    @staticmethod
    def preview(df: pd.DataFrame, n: int = 10) -> pd.DataFrame
        """返回前 n 行预览数据"""
```

#### Module: `core/comparator.py` — 表格对比器

```python
@dataclass
class DiffResult:
    merged_df: pd.DataFrame          # 合并后的完整对比表
    stats: dict                      # {'added': N, 'deleted': N, 'modified': N, 'same': N}
    diff_rows: list[int]             # 差异行索引列表
    changed_cells: dict              # {(row_idx, col_idx): (old_val, new_val)}

class TableComparator:
    def compare(
        self,
        df_old: pd.DataFrame,
        df_new: pd.DataFrame,
        key_column: str,
        compare_columns: list[str] | None = None
    ) -> DiffResult
        """执行对比，返回对比结果"""
```

#### Module: `core/exporter.py` — 结果导出器

```python
class ResultExporter:
    @staticmethod
    def to_excel(
        diff_result: DiffResult,
        output_path: str,
        only_diff: bool = False
    ) -> str
        """导出对比结果到 Excel 文件，带颜色标记
        返回导出文件路径
        """
```

### 3.2 UI 模块

#### Module: `ui/main_window.py` — 主窗口

```python
class MainWindow(QMainWindow):
    """应用主窗口，组装各子控件，管理全局状态"""
    # 信号
    file_loaded_left = Signal(str)      # 左侧文件加载完成
    file_loaded_right = Signal(str)     # 右侧文件加载完成
    compare_started = Signal()          # 开始对比
    compare_finished = Signal(DiffResult)  # 对比完成
```

#### Module: `ui/file_panel.py` — 文件导入面板

```python
class FilePanel(QFrame):
    """单个文件导入面板（左右各一个实例）"""
    file_selected = Signal(str)         # 选中文件信号

    def set_file_info(self, metadata: dict)
    def clear(self)
```

#### Module: `ui/compare_panel.py` — 对比设置面板

```python
class ComparePanel(QFrame):
    """键列选择 + 对比列选择"""
    compare_requested = Signal(str, list)  # (key_column, compare_columns)
```

#### Module: `ui/result_table.py` — 结果表格

```python
class ResultTable(QTableWidget):
    """展示对比结果的表格控件，支持颜色标记"""
    def show_result(self, diff_result: DiffResult)
    def set_filter_diff_only(self, enabled: bool)
    def navigate_to_next_diff(self)
    def navigate_to_prev_diff(self)
```

#### Module: `ui/stats_bar.py` — 统计栏

```python
class StatsBar(QFrame):
    """显示新增/删除/修改行数统计"""
    def update_stats(self, stats: dict)
```

### 3.3 模块依赖关系

```
main_window
  ├── file_panel (×2)        →  core/loader
  ├── compare_panel          →  (无依赖)
  ├── result_table           →  core/models
  ├── stats_bar              →  (无依赖)
  └── 控制器逻辑              →  core/comparator, core/exporter
```

---

## 4. 数据模型定义

### 4.1 DiffResult 数据模型

```python
@dataclass
class DiffResult:
    merged_df: pd.DataFrame
    """合并后的 DataFrame，包含以下列：
    - __status__: str  — 'same' | 'modified' | 'added' | 'deleted'
    - __key__: any     — 键列的值
    - ...所有原始数据列（来自旧表和新表的合并）
    - 对于修改的行，每个单元格可能是原始值或标记值
    """

    stats: dict
    """统计信息
    {
        'added': int,      # 新增行数
        'deleted': int,    # 删除行数
        'modified': int,   # 修改行数
        'same': int,       # 相同行数
        'total_old': int,  # 原表总行数
        'total_new': int   # 新表总行数
    }
    """

    diff_rows: list[int]
    """所有差异行（added/deleted/modified）在 merged_df 中的索引列表"""

    changed_cells: dict[tuple[int, int], tuple[Any, Any]]
    """发生变化的单元格映射
    key:   (row_index_in_merged, col_index)
    value: (old_value, new_value)
    仅对 status='modified' 的行有效
    """
```

### 4.2 对比算法数据流

```
输入:
  df_old (初始版)          df_new (修改版)
       │                       │
       └───────┬───────────────┘
               │
        ▼ 按 key_column 做 outer join
               │
       ┌───────┴───────────────┐
       │                       │
  只出现在旧表         只出现在新表
  → 标记 deleted      → 标记 added
       │                       │
       └───────┬───────────────┘
               │
        同时出现在两表
               │
        ▼ 逐列比较（仅 compare_columns）
               │
       ┌───────┴───────┐
       │               │
   全部相等         有不等
   → same         → modified（标记差异单元格）
```

---

## 5. 错误处理与日志方案

### 5.1 错误处理策略

| 错误场景 | 处理方式 | 用户提示 |
|----------|----------|----------|
| 文件不存在 | try-except 捕获 FileNotFoundError | "文件未找到，请检查路径" |
| 文件格式不支持 | 检查扩展名后拒绝加载 | "不支持的文件格式，请选择 .xlsx/.xls/.csv" |
| 文件内容为空 | 检查 DataFrame.shape | "文件内容为空，请检查数据" |
| 编码错误 (CSV) | 尝试 UTF-8 → GBK → 自动检测 | "文件编码识别失败" |
| 键列不存在 | 对比前校验列名 | "所选键列在表中不存在" |
| 两表列结构差异大 | 自动取共有列，给出提示 | "两表列不完全一致，将仅对比共有列：列A, 列B..." |
| 数据量过大 | 进度条 + 异步处理（QThread） | "正在处理大量数据，请稍候..." |

### 5.2 日志方案

```python
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('table_diff.log', encoding='utf-8'),
        logging.StreamHandler()  # 也输出到控制台
    ]
)

logger = logging.getLogger('table_diff')
```

日志记录点：
- 文件加载成功/失败
- 对比开始/完成（含数据量）
- 导出开始/完成
- 异常堆栈（ERROR 级别）

---

## 6. 性能考虑

| 场景 | 方案 |
|------|------|
| 大文件加载 (＞10万行) | pandas 分块读取 chunk 策略 |
| 对比运算 | 纯 pandas 向量化操作，避免逐行循环 |
| UI 响应 | 耗时操作放在 QThread 子线程执行，主线程不阻塞 |
| 表格渲染 | 使用 QTableWidget 虚拟模式或分页加载 |

---

## 7. 假设说明
- 两个表格默认有相同的列结构（列名一致），若不一致则自动取交集
- 默认取第一列为键列
- 文件第一行为表头
- CSV 编码自动检测：UTF-8 → GBK → Latin-1
- 运行环境为 Windows 10/11，Python 3.10+
