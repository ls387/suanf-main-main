# 排课系统文档索引

欢迎使用排课系统文档。本文件为您提供快速导航和实用指南。

## 📚 文档结构

```
docs/
├── README.md （本文件）
├── QUICK_START.md          ⭐ 新手从这里开始
├── SYSTEM_DESIGN.md        系统设计和核心逻辑
├── OPTIMIZATION_GUIDE.md   优化功能（容量、约束、冲突）
├── TROUBLESHOOTING.md      问题诊断和排查
└── TOOLS_USAGE.md          工具详细使用手册
```

---

## 🚀 快速导航

### 我是新手，不知道从哪里开始

👉 **阅读顺序：**

1. [QUICK_START.md](QUICK_START.md) - 5 分钟快速了解基本操作
2. [TOOLS_USAGE.md](TOOLS_USAGE.md) - 学习每个工具的用法
3. 动手试验：

```powershell
# Step 1: 检查数据
python check_data_scale.py

# Step 2: 排课
python suan2.py --version 1 --population 200 --generations 300

# Step 3: 查看结果
python view_schedule.py 1
```

---

### 我要解决一个具体问题

**班级冲突多？** 👉 [TROUBLESHOOTING.md#班级冲突问题](TROUBLESHOOTING.md#班级冲突问题)

**教室利用率低？** 👉 [TROUBLESHOOTING.md#教室利用率过低问题](TROUBLESHOOTING.md#教室利用率过低问题)

**教师冲突？** 👉 [TROUBLESHOOTING.md#教师时间冲突问题](TROUBLESHOOTING.md#教师时间冲突问题)

**不知道怎么用工具？** 👉 [TOOLS_USAGE.md](TOOLS_USAGE.md)

---

### 我想深入了解系统

👉 **阅读顺序：**

1. [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) - 了解架构和算法
2. [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - 了解优化策略
3. 查看源代码：
   - `genetic_algorithm.py` - 遗传算法核心
   - `db_connector.py` - 数据加载
   - `analyze_conflicts.py` - 冲突分析

---

### 我要优化排课结果

👉 **阅读顺序：**

1. [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - 了解可用的优化方法
2. [TOOLS_USAGE.md#4-冲突分析与优化工具](TOOLS_USAGE.md#4-冲突分析与优化工具) - 学习优化工具
3. 执行优化：

```powershell
# 方法 A：使用优化工具（快速）
python analyze_conflicts.py 1

# 方法 B：重新排课（小时级）
python suan2.py --version 2 --population 300 --generations 500

# 方法 C：分析未满足约束
python show_unsatisfied_constraints.py 1
```

---

## 📖 文档详细说明

### QUICK_START.md ⭐ 最常用

**摘要：** 快速开始指南，包含基本命令和工作流
**目对象：** 所有人
**阅读时间：** 5 分钟
**内容：**

- 环境准备
- 数据库配置
- 基本工作流
- 常见命令速查

### SYSTEM_DESIGN.md

**摘要：** 系统设计、架构和核心算法
**目标对象：** 开发者、深度用户
**阅读时间：** 30 分钟
**内容：**

- 系统概述
- 主要模块介绍
- 完整约束体系
- 容量优化机制
- 周次支持
- 参数调优建议

### OPTIMIZATION_GUIDE.md

**摘要：** 所有优化功能的完整指南
**目标对象：** 所有想优化排课的用户
**阅读时间：** 30 分钟
**内容：**

- 容量优化详解
- 冲突优化工具使用
- 约束分析使用
- 完整工作流
- 常见问题 Q&A

### TROUBLESHOOTING.md

**摘要：** 常见问题的诊断和解决方案
**目标对象：** 遇到问题的用户
**阅读时间：** 需要时查看相关部分
**内容：**

- 班级冲突问题
- 容量问题
- 利用率问题
- 教师冲突问题
- 其他 7+ 常见问题

### TOOLS_USAGE.md

**摘要：** 5 个工具的详细使用手册
**目标对象：** 需要学习工具的用户
**阅读时间：** 每个工具 5-10 分钟
**内容：**

- 每个工具的功能、参数、输出
- 工作流程详解
- 输出示例
- 参数推荐方案
- 性能参考

---

## 🎯 使用场景速查

| 场景       | 推荐文档                                                | 预计时间   |
| ---------- | ------------------------------------------------------- | ---------- |
| 首次使用   | QUICK_START.md                                          | 5 分钟     |
| 学习工具   | TOOLS_USAGE.md                                          | 30 分钟    |
| 遇到问题   | TROUBLESHOOTING.md + 对应章节                           | 10-30 分钟 |
| 优化排课   | OPTIMIZATION_GUIDE.md                                   | 20-40 分钟 |
| 深入学习   | SYSTEM_DESIGN.md                                        | 30-60 分钟 |
| 参数调优   | SYSTEM_DESIGN.md + TOOLS_USAGE.md                       | 20 分钟    |
| 完整工作流 | QUICK_START.md → TOOLS_USAGE.md → OPTIMIZATION_GUIDE.md | 2+ 小时    |

---

## 📖 按教程

### 教程 1：新手 5 分钟快速开始

```
1. 阅读 QUICK_START.md (5 分钟)
   ↓
2. 运行命令：python check_data_scale.py
   ↓
3. 运行排课：python suan2.py --version 1 --population 200 --generations 300
   ↓
4. 查看结果：python view_schedule.py 1
   ↓
✅ 完成！你已经成功排课了
```

### 教程 2：工具学习 (30 分钟)

```
1. 阅读 TOOLS_USAGE.md 中的各个工具介绍 (20 分钟)
   ↓
2. 动手练习每个工具 (10 分钟)
   - python check_data_scale.py
   - python view_schedule.py 1
   - python analyze_conflicts.py 1
   - python show_unsatisfied_constraints.py 1
   ↓
✅ 完成！你已经掌握了所有工具
```

### 教程 3：问题排查 (30-60 分钟)

```
1. 识别问题
   - 班级冲突？ → TROUBLESHOOTING.md#班级冲突问题
   - 利用率低？ → TROUBLESHOOTING.md#教室利用率过低问题
   - 其他问题？ → TROUBLESHOOTING.md 中查找
   ↓
2. 按照诊断步骤操作 (5-15 分钟)
   ↓
3. 选择合适的解决方案 (10-30 分钟)
   ↓
✅ 完成！问题解决了
```

### 教程 4：优化排课 (1-2 小时)

```
1. 阅读 OPTIMIZATION_GUIDE.md (20 分钟)
   ↓
2. 查看 TOOLS_USAGE.md 中的优化工具部分 (10 分钟)
   ↓
3. 执行优化：
   python analyze_conflicts.py 1
   python show_unsatisfied_constraints.py 1
   (20-30 分钟)
   ↓
4. 如果还需要深度优化：
   python suan2.py --version 2 --population 300 --generations 500
   (2+ 小时)
   ↓
✅ 完成！排课质量大幅提升
```

---

## 🔍 按关键词查找

**"容量"** → [SYSTEM_DESIGN.md#四容量优化](SYSTEM_DESIGN.md#四容量优化) / [OPTIMIZATION_GUIDE.md#一容量优化](OPTIMIZATION_GUIDE.md#一容量优化)

**"参数"** → [QUICK_START.md](QUICK_START.md#参数说明) / [TOOLS_USAGE.md#参数详解](TOOLS_USAGE.md#参数详解) / [SYSTEM_DESIGN.md#九参数调优建议](SYSTEM_DESIGN.md#九参数调优建议)

**"周次"** → [SYSTEM_DESIGN.md#五周次支持](SYSTEM_DESIGN.md#五周次支持) / [TROUBLESHOOTING.md#周次冲突问题](TROUBLESHOOTING.md#周次冲突问题)

**"优化"** → [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)

**"工具"** → [TOOLS_USAGE.md](TOOLS_USAGE.md)

**"冲突"** → [TROUBLESHOOTING.md#班级冲突问题](TROUBLESHOOTING.md#班级冲突问题) / [OPTIMIZATION_GUIDE.md#二冲突分析与优化工具](OPTIMIZATION_GUIDE.md#二冲突分析与优化工具)

---

## 🆘 需要帮助？

**问题：** 我不知道从哪开始

**答案：** 阅读 [QUICK_START.md](QUICK_START.md)

---

**问题：** 工具怎么用？

**答案：** 阅读 [TOOLS_USAGE.md](TOOLS_USAGE.md)

---

**问题：** 排课结果不好，怎么优化？

**答案：** 阅读 [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)

---

**问题：** 遇到了一个问题，不知道怎么解决

**答案：** 查找 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 中对应的问题类型

---

**问题：** 想深入了解系统原理

**答案：** 阅读 [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)

---

## 📋 最后更新

- **创建时间：** 2026-04-12
- **文档版本：** 1.0
- **系统版本：** 排课系统 with 遗传算法
- **兼容性：** Python 3.9+

---

## 📞 反馈与建议

如果在使用中发现文档有问题或有改进建议，请：

1. 查看对应的源代码文件
2. 检查数据库架构
3. 查阅日志文件 `scheduling.log`

---

**祝您使用愉快！**
