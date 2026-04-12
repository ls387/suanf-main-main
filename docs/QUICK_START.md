# 排课系统快速开始指南

## 环境准备

```powershell
# Python 版本 >= 3.9
python -m venv .venv
.\.venv\Scripts\activate
pip install pymysql openpyxl
```

## 数据库配置

```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "pk"
$env:DB_PASSWORD = "123456"
$env:DB_NAME = "paike"
```

## 基本工作流

### 1️⃣ 检查数据规模和推荐参数

```powershell
python check_data_scale.py
```

### 2️⃣ 运行排课

```powershell
# 标准运行（推荐）
python suan2.py --version 1 --population 200 --generations 300

# 快速测试
python suan2.py --version 1 --population 80 --generations 100
```

**参数说明：**

- `--version` _(必需)_：排课版本 ID
- `--population`：种群大小（默认200）
- `--generations`：进化代数（默认300）
- `--crossover-rate`：交叉率（默认0.7）
- `--mutation-rate`：变异率（默认0.2）
- `--elitism-size`：精英保留数（默认5）
- `--max-stagnation`：最大停滞代数（默认50）

### 3️⃣ 分析排课结果

```powershell
# 查看/导出结果
python view_schedule.py 1

# 分析冲突
python analyze_conflicts.py 1

# 分析未满足的约束
python show_unsatisfied_constraints.py 1
```

### 4️⃣ 优化排课结果（可选）

```powershell
# 交互式优化冲突
python analyze_conflicts.py 1
# 按提示选择 y 进行优化
```

## 常见命令速查

| 任务     | 命令                                                             |
| -------- | ---------------------------------------------------------------- |
| 检查数据 | `python check_data_scale.py`                                     |
| 排课     | `python suan2.py --version 1 --population 200 --generations 300` |
| 导出结果 | `python view_schedule.py 1`                                      |
| 冲突分析 | `python analyze_conflicts.py 1`                                  |
| 约束分析 | `python show_unsatisfied_constraints.py 1`                       |

## 输出文件位置

- **Excel 排课表**：运行 `view_schedule.py` 时自动生成
- **冲突报告**：运行 `analyze_conflicts.py` 时自动生成
- **约束报告**：运行 `show_unsatisfied_constraints.py` 时自动生成
- **日志文件**：`scheduling.log`

## 更多帮助

- 系统设计详情 👉 [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)
- 优化功能指南 👉 [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- 问题诊断方案 👉 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 工具使用详解 👉 [TOOLS_USAGE.md](TOOLS_USAGE.md)
