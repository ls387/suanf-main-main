# 技术修复与优化参考

> 系统遇到的技术问题和解决方案的详细记录

---

## 📚 目录

1. [时间重叠检测修复](#时间重叠检测修复)
2. [其他技术优化](#其他技术优化)
3. [调试指南](#调试指南)

---

## 时间重叠检测修复

### 🐛 问题背景

**现象**: 在排课时出现数据库重复键错误

```
IntegrityError: (1062, "Duplicate entry '1-X2221-2-3' for key 'schedules.uk_version_time_space'")
```

**根本原因**: 多个课程在时间重叠的情况下被分配到了同一教室，导致同一教室的同一时间槽被分配多次。

### 📊 问题分析

#### 错误的逻辑（修复前）

系统使用**时间范围**作为检测的单位：

```python
# ❌ 粗粒度检测（错误方式）
time_range = (weekday, start_slot, end_slot)
allocated_classrooms[time_range] = set(classroom_ids)

# 例子：
课程A: 周二 第3-5节 → time_range = (2, 3, 5) → 可用教室: {X2221, X2222}
课程B: 周二 第3-4节 → time_range = (2, 3, 4) → 这是不同的键！
                          → 系统认为可用教室: {X2221, X2222, ...}
```

**为什么有问题？**

```
课程A: 周二 3-5节 (占用第3, 4, 5节)
课程B: 周二 3-4节 (占用第3, 4节)

按时间范围检测:
- (2, 3, 5) vs (2, 3, 4) 是不同的键
- 系统不知道 (2, 3, 4) 与 (2, 3, 5) 部分重叠
- 都可以分配X2221教室
- 最后: X2221在周二第3-4节被分配了2次 ✗ 数据库约束冲突！
```

#### 数据库表现

```sql
-- 冲突的数据
INSERT INTO schedules VALUES
('1', 'X2221', '2', '3'),  -- 课程A
('1', 'X2221', '2', '3');  -- 课程B 重复！

-- 主键约束: (版本, 教室, 周几, 节次)
-- 违反了唯一性约束 (uk_version_time_space)
```

### ✅ 修复方案

#### 正确的逻辑（修复后）

系统改为**逐个时间槽**进行检测：

```python
# ✅ 细粒度检测（正确方式）
allocated_classrooms[(weekday, slot)] = set(classroom_ids)

# 检测时，遍历所有涉及的时间槽
occupied = set()
for slot in range(start_slot, end_slot + 1):
    occupied.update(allocated_classrooms[(weekday, slot)])

# 标记时，标记所有涉及的时间槽
for slot in range(start_slot, end_slot + 1):
    allocated_classrooms[(weekday, slot)].add(classroom_id)
```

**修复后的流程**：

```
课程A: 周二 3-5节
  [检测阶段]
    检查 (2,3), (2,4), (2,5) 的占用情况
    都未被占用 → X2221可用
  [分配阶段]
    标记 (2,3)→X2221, (2,4)→X2221, (2,5)→X2221

课程B: 周二 3-4节
  [检测阶段]
    检查 (2,3) → 已被占用！(X2221)
    检查 (2,4) → 已被占用！(X2221)
    X2221不可用 ✓
  [分配阶段]
    选择其他可用教室 ✓
```

#### 数据结构对比

**修复前** (粗粒度):

```python
allocated_classrooms = {
    (2, 3, 5): {X2221, X2222},    # 周二3-5节整体
    (2, 3, 4): {X2221, X2223},    # 周二3-4节整体
    (2, 6, 8): {X2222},           # 周二6-8节整体
}
# 问题: 无法检测部分重叠
```

**修复后** (细粒度):

```python
allocated_classrooms = {
    (2, 3): {X2221, X2222},       # 周二第3节
    (2, 4): {X2221, X2223},       # 周二第4节
    (2, 5): {X2221},              # 周二第5节
    (2, 6): {X2222},              # 周二第6节
    (2, 7): {X2222},              # 周二第7节
    (2, 8): {X2222},              # 周二第8节
}
# 优点: 能精确检测任何重叠关系
```

### 🎯 测试案例验证

#### 案例1: 完全重叠（应该冲突）

```
课程A: 周二 第3-5节 (3节课)
课程B: 周二 第3-5节 (3节课)

[修复前] ❌ 冲突（未能检测）
[修复后] ✅ 正确检测冲突
```

#### 案例2: 部分重叠（应该冲突）

```
课程A: 周二 第3-5节 (3节课)
课程B: 周二 第4-6节 (3节课)
重叠部分: 第4-5节

[修复前] ❌ 未能检测（键不同）
[修复后] ✅ 正确检测第4-5节冲突
```

#### 案例3: 不重叠（应该兼容）

```
课程A: 周二 第3-5节 (3节课)
课程B: 周二 第6-8节 (3节课)

[修复前] ✅ 可以兼容（碰巧没问题）
[修复后] ✅ 正确判断可兼容
```

#### 案例4: 相邻但不重叠（应该兼容）

```
课程A: 周二 第3-5节 (第5节结束)
课程B: 周二 第6-8节 (第6节开始)
间隔: 1节课

[修复前] ✅ 可以兼容（碰巧没问题）
[修复后] ✅ 正确判断可兼容
```

### 🔍 检测逻辑详解

#### 伪代码

```python
def can_assign_classroom(classroom_id, weekday, start_slot, end_slot):
    """检查教室是否可用"""
    for slot in range(start_slot, end_slot + 1):
        if classroom_id in allocated_classrooms[(weekday, slot)]:
            return False  # 有冲突
    return True  # 没有冲突

def mark_classroom_occupied(classroom_id, weekday, start_slot, end_slot):
    """标记教室被占用"""
    for slot in range(start_slot, end_slot + 1):
        allocated_classrooms[(weekday, slot)].add(classroom_id)
```

#### Python 实现

```python
from collections import defaultdict

class ClassroomAllocator:
    def __init__(self):
        # 键: (weekday, slot)
        # 值: 该时间槽被占用的教室集合
        self.allocated = defaultdict(set)

    def is_available(self, classroom_id, weekday, start_slot, end_slot):
        """检查教室在指定时间段是否可用"""
        for slot in range(start_slot, end_slot + 1):
            if classroom_id in self.allocated[(weekday, slot)]:
                return False
        return True

    def allocate(self, classroom_id, weekday, start_slot, end_slot):
        """分配教室，标记为已占用"""
        for slot in range(start_slot, end_slot + 1):
            self.allocated[(weekday, slot)].add(classroom_id)

    def get_occupied_classrooms(self, weekday, start_slot, end_slot):
        """获取指定时间段所有被占用的教室"""
        occupied = set()
        for slot in range(start_slot, end_slot + 1):
            occupied.update(self.allocated[(weekday, slot)])
        return occupied
```

#### 查询示例

```python
# 查询课程 "周二 3-5节" 的占用教室
occupied = allocator.get_occupied_classrooms(2, 3, 5)
# 结果: {X2221, X2222, X2223}
#   - (2,3) 被占用: {X2221, X2222}
#   - (2,4) 被占用: {X2221, X2223}
#   - (2,5) 被占用: {X2221}
# 这三个教室都有冲突
```

---

## 其他技术优化

### 周次感知的冲突检测

参考 [修复报告 - 周次支持修复](REPAIR_REPORTS.md) 获取详细信息。

**核心改进**:

- 班级冲突检测考虑周次
- 教室冲突检测考虑周次
- 单周和双周课程可共享时间

### 数据库性能优化

涉及内容：

- 索引优化
- 查询性能
- 数据导入优化

参考 [数据库设置](DATABASE_SETUP.md) 获取数据库相关信息。

---

## 调试指南

### 检查时间重叠

如果遇到教室分配冲突，可以运行以下检查：

```python
# 检查版本1的所有课程
python analyze_conflicts.py 1

# 输出中查找重叠的教室时间
# 若有类似"教室X2221周二3-5节重复分配"的信息，属于此问题
```

### 验证修复

重新排课后验证修复：

```python
# 重新排课（生成版本2）
python suan2.py

# 查看新版本的课程表
python view_schedule.py 2

# 分析新版本的冲突（应该大幅减少）
python analyze_conflicts.py 2
```

### 常见症状

| 症状             | 原因             | 解决方案                             |
| ---------------- | ---------------- | ------------------------------------ |
| 数据库重复键错误 | 教室时间重复分配 | 使用修复后的算法重新排课             |
| 教室资源浪费     | 未考虑周次       | 更新算法版本，重新排课               |
| 某些教室频繁冲突 | 检测逻辑问题     | 检查 allocated_classrooms 的构建方法 |

---

## 相关文档

- [修复报告](REPAIR_REPORTS.md) - 周次支持修复详情
- [参数调优](PARAMETER_TUNING.md) - 算法参数调优
- [系统设计](SYSTEM_DESIGN.md) - 系统架构和算法原理
- [数据库设置](DATABASE_SETUP.md) - 数据库表结构和操作

---

**最后更新**: 2025-11-25
**维护者**: 排课系统开发团队
