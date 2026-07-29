# 📋 表格对比工具 TableDiff

[![下载](https://img.shields.io/badge/Download-v1.0-brightgreen?style=for-the-badge&logo=github)](https://github.com/BumpingT/TableCompare/releases/latest)

一个简洁高效的桌面端表格对比工具，轻松找出两个 Excel/CSV 表格之间的数据差异。

---

## ✨ 功能特性

### 基础功能
| 功能 | 说明 |
|------|------|
| 📂 支持多格式 | 支持 .xlsx, .xls, .csv 格式的表格文件 |
| 🔍 自动对比 | 基于键列的行匹配 + 逐列数据对比 |
| 🎨 差异高亮 | 新增（绿色）、删除（红色）、修改（黄色）、单元格变化（橙色） |
| ⚙️ 灵活配置 | 自由选择键列和参与对比的列 |
| 📊 统计面板 | 实时显示新增/删除/修改行数 |
| 🔎 差异筛选 | 一键切换"仅显示差异行" |
| 🧭 差异导航 | 上一条/下一条，快速定位差异 |
| 📥 结果导出 | 导出为带颜色标记的 Excel 文件 |

### 🆕 新增高级功能
| 功能 | 说明 |
|------|------|
| 🖱️ **拖拽导入** | 直接把文件拖到窗口上加载，无需点击选择 |
| 🔍 **列搜索** | 列很多时输入关键词搜索定位特定对比列 |
| 📊 **汇总视图** | 查看每列差异统计：哪些列有差异、差异条数、差异率 |
| 🖱️ **差异详情弹窗** | 双击某行弹窗，只看该行前后逐字段对比 |
| 📂 **文件历史** | 记住最近打开的文件，一键重新加载 |
| 📑 **多 Sheet 支持** | Excel 文件有多个 sheet 时弹出选择对话框 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 10/11（也可在 macOS/Linux 运行）

### 安装步骤

```bash
# 1. 克隆或下载本项目
cd table_diff_tool

# 2. 安装依赖
pip install -r requirements.txt
```

### 运行应用

```bash
python src/main.py
```

---

## 🎯 使用指南

### 基本流程

```
1️⃣ 加载初始版文件      2️⃣ 加载修改版文件
       │                       │
       └─────────┬─────────────┘
                 │
        3️⃣ 选择键列和对比列
                 │
        4️⃣ 点击"开始对比"
                 │
        5️⃣ 查看差异结果（可筛选/导航/双击详情）
                 │
        6️⃣ 导出对比结果（可选）
```

### 详细步骤

1. **加载文件**：
   - 点击左侧"选择文件"加载初始版，右侧加载修改版
   - 或直接将文件拖拽到对应的面板区域
   - 可从"最近打开的文件"菜单快速重新加载
   - 如果 Excel 有多个 Sheet，会弹出选择对话框

2. **设置键列**：在下拉菜单中选择用于匹配行的键列（如 ID、编号）

3. **选择对比列**：
   - 勾选需要参与对比的列（默认全选）
   - 列很多时，使用搜索框输入关键词快速定位

4. **开始对比**：点击蓝色"开始对比"按钮

5. **查看结果**：
   - 绿色行 = 新增数据
   - 红色行 = 删除数据
   - 黄色行 = 数据有修改
   - 橙色单元格 = 该单元格具体值发生变化
   - **双击某行** → 弹出差异详情弹窗，逐字段查看旧值→新值

6. **汇总视图**：点击"汇总视图"按钮，查看每列的差异统计

7. **筛选导航**：可勾选"仅显示差异行"，使用导航按钮快速跳转

8. **导出结果**：点击"导出结果"保存为带标记的 Excel

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 导入初始版文件 |
| Ctrl+Shift+O | 导入修改版文件 |
| Ctrl+R | 开始对比 |
| Ctrl+E | 导出结果 |
| Ctrl+N | 下一条差异 |
| Ctrl+P | 上一条差异 |
| Ctrl+Q | 退出 |

---

## 📁 项目结构

```
table_diff_tool/
├── src/
│   ├── main.py                 # 应用入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── loader.py           # 文件加载器（多 Sheet）
│   │   ├── comparator.py       # 表格对比器
│   │   └── exporter.py         # 结果导出器
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py      # 主窗口
│       ├── file_panel.py       # 文件面板（拖拽+历史）
│       ├── compare_panel.py    # 对比设置（列搜索）
│       ├── result_table.py     # 结果表格（双击详情）
│       ├── stats_bar.py        # 统计栏
│       ├── summary_dialog.py   # 汇总视图对话框
│       └── diff_detail_dialog.py # 差异详情弹窗
├── design_doc.md               # 设计文档
├── architecture.md             # 架构文档
├── project_plan.md             # 项目计划
├── requirements.txt            # 依赖清单
├── README.md                   # 本文件
└── SUMMARY.md                  # 项目总结
```

---

## ⬇️ 下载 exe

点击上方 **Download** 按钮，跳转到 Releases 页面下载 `TableDiff.exe`。

**首次使用需要创建 Release：**
1. 打开 [GitHub 仓库](https://github.com/BumpingT/TableCompare)
2. 点击右侧 **Releases** → **Create a new release**
3. 标签版本填 `v1.0`，标题填 `v1.0` 
4. 把 `C:\Users\Administrator\Documents\table_diff_tool\TableDiff.exe` 拖拽上传
5. 点击 **Publish release**

之后每次更新 exe，重复上述步骤发布新版本即可。

---

## 📦 打包为独立 exe（可选）

如果需要打包为独立的 exe 文件，可以使用 PyInstaller：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "TableDiff" src/main.py
```

打包后的 exe 在 `dist/TableDiff.exe`

---

## ⚠️ 注意事项

1. **表头行**：文件的第一行会被自动识别为表头
2. **列名匹配**：两个表格的列名需要一致才能正确对比
3. **编码问题**：CSV 文件支持 UTF-8 和 GBK 编码，自动检测
4. **大文件**：处理超过 10 万行的大文件时，请耐心等待
5. **数据格式**：所有数据均以文本形式对比，避免类型转换导致的误判
6. **拖拽导入**：仅支持拖拽 .xlsx/.xls/.csv 文件到面板区域

---

## 🛠️ 技术栈

- **Python 3.10+** — 编程语言
- **PySide6** — GUI 框架（Qt for Python）
- **pandas** — 数据处理核心
- **openpyxl** — Excel 文件读写

---

## 📄 许可证

本项目仅供学习交流使用。
