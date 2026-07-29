"""
生成超大型公司数据测试文件
生成 2 个 Excel: 初始版 + 修改版（含差异）
"""
import os, random, string
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

random.seed(42)
np.random.seed(42)

NUM_ROWS = 10000
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== 辅助数据 ====================
LAST_NAMES = ['张','李','王','赵','刘','陈','杨','黄','周','吴',
              '徐','孙','胡','朱','高','林','何','郭','马','罗',
              '梁','宋','郑','谢','韩','唐','冯','于','董','萧',
              '程','曹','袁','邓','许','傅','沈','曾','彭','吕']

FIRST_NAMES = ['伟','芳','娜','敏','静','丽','强','磊','军','洋',
               '勇','艳','杰','娟','涛','明','超','秀英','霞','桂英',
               '华','飞','鑫','浩','雪','晨','宇','琳','洋','鹏',
               '宁','婷','旭','阳','璐','颖','恒','琪','轩','宸']

DEPARTMENTS = ['技术研发部','市场部','财务部','人事部','行政部',
               '销售部','客服部','产品部','数据部','运维部',
               '法务部','审计部','采购部','供应链部','质量部',
               '战略部','公关部','设计部','测试部','安全部']

POSITIONS = ['专员','高级专员','主管','高级主管','经理','高级经理',
             '总监','高级总监','副总裁','高级副总裁','CTO','CFO','COO']

LEVELS = ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10','M1','M2','M3','M4']

EDUCATIONS = ['高中','大专','本科','硕士','博士','MBA']

SCHOOLS = ['北京大学','清华大学','复旦大学','上海交通大学','浙江大学',
           '南京大学','武汉大学','华中科技大学','中山大学','西安交通大学',
           '哈尔滨工业大学','北京航空航天大学','中国人民大学','南开大学',
           '天津大学','山东大学','厦门大学','同济大学','北京师范大学',
           '四川大学','电子科技大学','重庆大学','兰州大学','西北工业大学']

MAJORS = ['计算机科学与技术','软件工程','信息管理','金融学','会计学',
          '工商管理','市场营销','人力资源管理','法学','经济学',
          '数学与应用数学','统计学','电子信息工程','通信工程','自动化',
          '机械工程','材料科学','生物工程','化学工程','环境科学']

CONTRACT_TYPES = ['固定期限','无固定期限','劳务派遣','实习','顾问']

CITIES = ['北京','上海','广州','深圳','杭州','成都','南京','武汉',
          '西安','重庆','苏州','天津','长沙','郑州','东莞']

PERF_LEVELS = ['A','B+','B','C','D']
PERF_WEIGHTS = [0.15, 0.30, 0.35, 0.15, 0.05]

# ==================== 生成数据 ====================
print(f'正在生成 {NUM_ROWS:,} 行公司数据...')

data = {}

# 1. 员工ID（键列）
data['员工编号'] = [f'EMP{i:06d}' for i in range(NUM_ROWS)]

# 2. 姓名
data['姓名'] = [f'{random.choice(LAST_NAMES)}{random.choice(FIRST_NAMES)}' for _ in range(NUM_ROWS)]

# 3. 性别
data['性别'] = [random.choice(['男','女','男','男','女']) for _ in range(NUM_ROWS)]

# 4. 部门
data['部门'] = [random.choice(DEPARTMENTS) for _ in range(NUM_ROWS)]

# 5. 职位
data['职位'] = [random.choice(POSITIONS) for _ in range(NUM_ROWS)]

# 6. 职级
data['职级'] = [random.choice(LEVELS) for _ in range(NUM_ROWS)]

# 7. 入职日期
start_date = datetime(2010, 1, 1)
date_range = (datetime(2025, 12, 31) - start_date).days
data['入职日期'] = [
    (start_date + timedelta(days=random.randint(0, date_range))).strftime('%Y-%m-%d')
    for _ in range(NUM_ROWS)
]

# 8. 出生日期
data['出生日期'] = [
    (datetime(1970,1,1) + timedelta(days=random.randint(8000, 16000))).strftime('%Y-%m-%d')
    for _ in range(NUM_ROWS)
]

# 9. 年龄
birth_years = [int(d[:4]) for d in data['出生日期']]
data['年龄'] = [2026 - y for y in birth_years]

# 10. 手机号
data['手机号'] = [f'1{random.choice([3,5,7,8,9])}{random.randint(10000000,99999999)}' for _ in range(NUM_ROWS)]

# 11. 邮箱
data['邮箱'] = [
    f'{data["姓名"][i]}.{data["员工编号"][i].lower()}@company.com'
    for i in range(NUM_ROWS)
]

# 12. 学历
data['学历'] = [random.choice(EDUCATIONS) for _ in range(NUM_ROWS)]

# 13. 毕业院校
data['毕业院校'] = [random.choice(SCHOOLS) for _ in range(NUM_ROWS)]

# 14. 专业
data['专业'] = [random.choice(MAJORS) for _ in range(NUM_ROWS)]

# 15-16. 工作城市 + 办公地点
data['工作城市'] = [random.choice(CITIES) for _ in range(NUM_ROWS)]
data['办公地点'] = [f'{c}{random.choice(["科技园","金融中心","产业园","CBD","创新园"])}' for c in data['工作城市']]

# 17. 工龄（年）
data['工龄(年)'] = [round(random.uniform(0.5, 20.0), 1) for _ in range(NUM_ROWS)]

# 18. 合同类型
data['合同类型'] = [random.choice(CONTRACT_TYPES) for _ in range(NUM_ROWS)]

# 19. 合同到期日
data['合同到期日'] = [
    (datetime(2026,1,1) + timedelta(days=random.randint(0, 1095))).strftime('%Y-%m-%d')
    for _ in range(NUM_ROWS)
]

# 20-24. 薪酬相关
data['基本工资'] = [random.randint(5000, 80000) for _ in range(NUM_ROWS)]
data['绩效工资'] = [random.randint(1000, 30000) for _ in range(NUM_ROWS)]
data['住房补贴'] = [random.randint(500, 8000) for _ in range(NUM_ROWS)]
data['交通补贴'] = [random.randint(200, 3000) for _ in range(NUM_ROWS)]
data['餐补'] = [random.randint(300, 1500) for _ in range(NUM_ROWS)]
data['通讯补贴'] = [random.randint(100, 800) for _ in range(NUM_ROWS)]

# 25. 应发合计
data['应发合计'] = [
    data['基本工资'][i] + data['绩效工资'][i] + data['住房补贴'][i]
    + data['交通补贴'][i] + data['餐补'][i] + data['通讯补贴'][i]
    for i in range(NUM_ROWS)
]

# 26-27. 社保公积金
data['社保基数'] = [min(max(data['基本工资'][i], 5000), 35000) for i in range(NUM_ROWS)]
data['公积金基数'] = [min(max(data['基本工资'][i], 5000), 30000) for i in range(NUM_ROWS)]
data['个人社保'] = [round(d * 0.105, 0) for d in data['社保基数']]
data['个人公积金'] = [round(d * 0.07, 0) for d in data['公积金基数']]
data['个税'] = [round(max(d * 0.03 - 200, 0), 0) for d in data['应发合计']]

# 28. 实发工资
data['实发工资'] = [
    data['应发合计'][i] - data['个人社保'][i] - data['个人公积金'][i] - data['个税'][i]
    for i in range(NUM_ROWS)
]

# 29. 银行卡号
data['银行卡号'] = [
    f'6222{random.randint(1000000000, 9999999999)}'
    for _ in range(NUM_ROWS)
]

# 30-31. 绩效
data['上季度绩效'] = [random.choices(PERF_LEVELS, weights=PERF_WEIGHTS)[0] for _ in range(NUM_ROWS)]
data['年度评级'] = [random.choices(PERF_LEVELS, weights=PERF_WEIGHTS)[0] for _ in range(NUM_ROWS)]

# 32. 是否核心员工
data['是否核心员工'] = [random.choice(['是','否','否','否','否']) for _ in range(NUM_ROWS)]

# 33. 考勤状态
data['考勤状态'] = [random.choice(['正常','正常','正常','迟到','缺勤','请假']) for _ in range(NUM_ROWS)]

# 34. 年假剩余(天)
data['年假剩余(天)'] = [random.randint(0, 20) for _ in range(NUM_ROWS)]

# 35. 备注
remarks_pool = ['','','','','优秀员工','待观察','晋升候选人','需培训','新入职','核心骨干']
data['备注'] = [random.choice(remarks_pool) for _ in range(NUM_ROWS)]

# 构建 DataFrame
df_old = pd.DataFrame(data)

# ==================== 创建修改版 ====================
print('正在生成修改版（随机修改 5% 数据）...')
df_new = df_old.copy()

# 确定要修改的列（薪酬类 + 绩效类 + 基本信息类）
modifiable_cols = ['部门','职位','职级','基本工资','绩效工资','住房补贴',
                   '交通补贴','餐补','通讯补贴','上季度绩效','年度评级',
                   '是否核心员工','考勤状态','年假剩余(天)','备注','工龄(年)',
                   '合同类型','合同到期日']

# 修改策略：随机选 5% 的行，每行随机改 2-5 个字段
modified_indices = random.sample(range(NUM_ROWS), NUM_ROWS // 20)
modified_count = 0

for idx in modified_indices:
    cols_to_modify = random.sample(modifiable_cols, random.randint(2, 5))
    for col in cols_to_modify:
        if col == '部门':
            df_new.at[idx, col] = random.choice(DEPARTMENTS)
        elif col == '职位':
            df_new.at[idx, col] = random.choice(POSITIONS)
        elif col == '职级':
            df_new.at[idx, col] = random.choice(LEVELS)
        elif col == '基本工资':
            old = df_new.at[idx, col]
            delta = random.randint(-5000, 5000)
            df_new.at[idx, col] = max(5000, old + delta)
        elif col == '绩效工资':
            old = df_new.at[idx, col]
            delta = random.randint(-3000, 3000)
            df_new.at[idx, col] = max(0, old + delta)
        elif col in ('住房补贴','交通补贴','餐补','通讯补贴'):
            old = df_new.at[idx, col]
            delta = random.randint(-500, 500)
            df_new.at[idx, col] = max(0, old + delta)
        elif col == '上季度绩效':
            df_new.at[idx, col] = random.choice(PERF_LEVELS)
        elif col == '年度评级':
            df_new.at[idx, col] = random.choice(PERF_LEVELS)
        elif col == '是否核心员工':
            df_new.at[idx, col] = random.choice(['是','否'])
        elif col == '考勤状态':
            df_new.at[idx, col] = random.choice(['正常','迟到','缺勤','请假'])
        elif col == '年假剩余(天)':
            df_new.at[idx, col] = random.randint(0, 20)
        elif col == '备注':
            df_new.at[idx, col] = random.choice(['优秀员工','晋升候选人','需培训','核心骨干','合同续签',''])
        elif col == '工龄(年)':
            df_new.at[idx, col] = round(random.uniform(0.5, 20.0), 1)
        elif col == '合同类型':
            df_new.at[idx, col] = random.choice(CONTRACT_TYPES)
        elif col == '合同到期日':
            df_new.at[idx, col] = (datetime(2026,1,1) + timedelta(days=random.randint(0, 1095))).strftime('%Y-%m-%d')
        modified_count += 1

    # 如果修改了薪酬字段，重新计算合计和实发
    salary_cols = {'基本工资','绩效工资','住房补贴','交通补贴','餐补','通讯补贴'}
    if salary_cols & set(cols_to_modify):
        base = df_new.at[idx, '基本工资']
        perf = df_new.at[idx, '绩效工资']
        house = df_new.at[idx, '住房补贴']
        trans = df_new.at[idx, '交通补贴']
        meal = df_new.at[idx, '餐补']
        comm = df_new.at[idx, '通讯补贴']
        total = base + perf + house + trans + meal + comm
        df_new.at[idx, '应发合计'] = total
        sb_base = min(max(base, 5000), 35000)
        hf_base = min(max(base, 5000), 30000)
        sb = round(sb_base * 0.105, 0)
        hf = round(hf_base * 0.07, 0)
        tax = round(max(total * 0.03 - 200, 0), 0)
        df_new.at[idx, '社保基数'] = sb_base
        df_new.at[idx, '公积金基数'] = hf_base
        df_new.at[idx, '个人社保'] = sb
        df_new.at[idx, '个人公积金'] = hf
        df_new.at[idx, '个税'] = tax
        df_new.at[idx, '实发工资'] = total - sb - hf - tax

# ==================== 导出 Excel ====================
old_path = os.path.join(OUT_DIR, '公司员工数据_初始版.xlsx')
new_path = os.path.join(OUT_DIR, '公司员工数据_修改版.xlsx')

print(f'\n正在写入 Excel...')
print(f'  DataFrame 大小: {df_old.shape[0]:,} 行 × {df_old.shape[1]} 列')

# 分块写入大文件以避免内存问题
with pd.ExcelWriter(old_path, engine='openpyxl') as writer:
    df_old.to_excel(writer, sheet_name='员工数据', index=False)

with pd.ExcelWriter(new_path, engine='openpyxl') as writer:
    df_new.to_excel(writer, sheet_name='员工数据', index=False)

old_size_mb = os.path.getsize(old_path) / 1024 / 1024
new_size_mb = os.path.getsize(new_path) / 1024 / 1024

print(f'\n{"="*50}')
print(f'✅ 文件生成完成！')
print(f'{"="*50}')
print(f'📄 初始版: {old_path}')
print(f'   大小: {old_size_mb:.1f} MB')
print(f'📄 修改版: {new_path}')
print(f'   大小: {new_size_mb:.1f} MB')
print(f'\n📊 数据规格:')
print(f'   行数: {NUM_ROWS:,}')
print(f'   列数: {df_old.shape[1]}')
print(f'   修改行: {len(modified_indices):,} ({len(modified_indices)/NUM_ROWS*100:.1f}%)')
print(f'   修改单元格: {modified_count:,} 处')
print(f'\n💡 启动工具对比这两个文件，看看效果:')
print(f'   python src/main.py')
print(f'   或双击 TableDiff.exe')
