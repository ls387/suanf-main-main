# 问题诊断与排查指南

## 快速导航

**常见问题：**

- [班级冲突](#班级冲突问题)
- [教室容量](#教室容量不足)
- [利用率过低](#教室利用率过低问题)
- [教师冲突](#教师时间冲突问题)
- [连续性差](#教室教师连续性差问题)
- [周末排课](#周末晚上排课过多问题)

---

## 班级冲突问题

### 现象

- 同一班级在同一时间被安排多门课程
- Excel 导出的班级视角显示时间重叠

### 诊断步骤

```powershell
# 1. 查看冲突分析报告
python analyze_conflicts.py 1

# 2. 查看 Excel，定位具体班级和时间
python view_schedule.py 1

# 3. 查看日志中是否有修复记录
Get-Content scheduling.log | Select-String "班级冲突|修复"
```

### 解决方案

#### ✅ 方案 A：增加算法资源（推荐）

```powershell
# 增加种群和代数，给算法更多探索空间
python suan2.py --version 2 --population 300 --generations 500
```

**原理：** 更大的种群和更多代数能更充分地搜索解空间，找到更优解。

**耗时：** 可能需要 1-2 小时

#### ✅ 方案 B：使用冲突优化工具

```powershell
# 自动优化班级冲突
python analyze_conflicts.py 1
# 第二阶段输入: y
```

**优势：** 快速，通常能解决大部分冲突

#### 🔧 方案 C：调整约束权重

编辑 `genetic_algorithm.py`，找到 `penalty_scores` 配置：

```python
"class_conflict": -100000,  # 从 -80000 改为 -100000
```

**原理：** 提高班级冲突的惩罚，使算法更努力避免这类冲突

**备注：** 修改后需要重新排课

#### 🔍 方案 D：检查数据完整性

```sql
-- 检查班级是否正确关联到课程
SELECT co.offering_id, co.course_id, COUNT(oc.class_id) as class_count
FROM course_offerings co
LEFT JOIN offering_classes oc ON co.offering_id = oc.offering_id
GROUP BY co.offering_id
HAVING class_count = 0;

-- 检查班级是否有过多课程（可能无法排课）
SELECT cl.class_name, COUNT(DISTINCT oc.offering_id) as course_count
FROM classes cl
JOIN offering_classes oc ON cl.class_id = oc.class_id
GROUP BY cl.class_name
ORDER BY course_count DESC
LIMIT 10;
```

**如果找到问题：**

- 补充缺失的班级关联
- 考虑分批排课（必修课、选修课分开）

---

## 教室容量不足

### 现象

- 分配的教室容量小于上课人数
- 冲突分析中显示 "容量不足" 错误

### 诊断步骤

```sql
-- 检查教室容量分布
SELECT
    CASE
        WHEN capacity < 30 THEN '小班'
        WHEN capacity < 60 THEN '中班'
        ELSE '大班'
    END as size,
    COUNT(*) as count
FROM classrooms
GROUP BY size;

-- 检查课程人数分布
SELECT
    CASE
        WHEN SUM(cl.student_count) < 30 THEN '小班'
        WHEN SUM(cl.student_count) < 60 THEN '中班'
        ELSE '大班'
    END as size,
    COUNT(*) as count
FROM course_offerings co
JOIN offering_classes oc ON co.offering_id = oc.offering_id
JOIN classes cl ON oc.class_id = cl.class_id
GROUP BY offering_id;
```

### 解决方案

#### ✅ 方案 A：使用自动优化工具

```powershell
python analyze_conflicts.py 1
# 第一阶段输入: y
```

**效果：** 自动为容量不足的课程查找和分配更大教室

#### ✅ 方案 B：增加合适容量的教室

```sql
-- 添加更多中小型教室
INSERT INTO classrooms (classroom_id, classroom_name, capacity, campus, building, features)
VALUES
('CR_NEW_01', '新教室1', 50, '主校区', '教学楼A', ''),
('CR_NEW_02', '新教室2', 100, '主校区', '教学楼B', ''),
('CR_NEW_03', '新教室3', 120, '主校区', '教学楼C', '');
```

**注意：** 添加后需要重新排课

#### 🔧 方案 C：拆分大班课程

```sql
-- 将大班课程拆分为多个小组
INSERT INTO teaching_tasks (offering_id, group_id, slots_count)
SELECT offering_id, group_id + 1, slots_count
FROM teaching_tasks
WHERE offering_id IN (
    SELECT offering_id FROM course_offerings
    WHERE student_count_estimate > 100
);
```

**示例：** 150 人课程可拆分为 2 组 75 人

---

## 教室利用率过低问题

### 现象

- 平均利用率 < 60%
- 大量小班占用大教室
- Excel 显示 "浪费座位数" 较多

### 诊断步骤

```powershell
# 查看详细利用率统计
python view_schedule.py 1

# 生成约束分析报告（包含利用率分析）
python show_unsatisfied_constraints.py 1
```

**输出示例：**

```
⚠️  教室利用率低(<50%): 28 处

[1] 体育课 - 周一第1-2节
    教室: 大操场 (200座)
    学生数: 30
    利用率: 15%
    浪费座位: 170 ✗
```

### 解决方案

#### ✅ 方案 A：使用自动优化工具

```powershell
python analyze_conflicts.py 1
# 第三阶段 - 教室利用率优化输入: y
```

**效果：** 自动为低利用率课程更换更小的教室

#### ✅ 方案 B：调整利用率优化权重

编辑 `genetic_algorithm.py`：

```python
# 当前权重
"utilization_waste": 300

# 提升为更激进的优化
"utilization_waste": 500
```

**原理：** 更高权重使算法更重视利用率

**耗时：** 需要重新排课

#### ✅ 方案 C：增加小型教室

```sql
-- 添加更多 20-50 座教室
INSERT INTO classrooms (classroom_id, classroom_name, capacity, campus, building)
VALUES
('CR_S01', '小教室1', 25, '主校区', '教学楼D'),
('CR_S02', '小教室2', 30, '主校区', '教学楼D'),
('CR_S03', '小教室3', 35, '主校区', '教学楼D'),
('CR_S04', '小教室4', 40, '主校区', '教学楼D');
```

#### 🔧 方案 D：调整容量浪费阈值

编辑 `genetic_algorithm.py` 中的 `_select_classroom` 方法：

```python
# 更严格的浪费限制
max_waste_ratio = {
    小班(<30人): 40%,   # 从 50% 改为 40%
    中班(30-60): 30%,   # 从 40% 改为 30%
    大班(>60人): 20%    # 从 30% 改为 20%
}
```

---

## 教师时间冲突问题

### 现象

- 同一教师在同一时间被分配多门课
- 教师负荷过重

### 诊断步骤

```sql
-- 检查教师课程负荷
SELECT
    t.teacher_name,
    COUNT(DISTINCT tt.offering_id) as course_count,
    SUM(tt.slots_count) as total_slots
FROM teachers t
JOIN offering_teachers ot ON t.teacher_id = ot.teacher_id
JOIN teaching_tasks tt ON ot.offering_id = tt.offering_id
GROUP BY t.teacher_id
ORDER BY total_slots DESC
LIMIT 20;

-- 查找教师冲突
python analyze_conflicts.py 1
```

### 解决方案

#### ✅ 方案 A：使用自动优化工具

```powershell
python analyze_conflicts.py 1
# 第二阶段输入: y
```

#### ✅ 方案 B：增加备选教师

```sql
-- 为需要的课程添加更多可选教师
INSERT INTO offering_teachers (offering_id, teacher_id)
SELECT DISTINCT co.offering_id, t.teacher_id
FROM course_offerings co
CROSS JOIN teachers t
WHERE t.teacher_id NOT IN (
    SELECT teacher_id FROM offering_teachers
    WHERE offering_id = co.offering_id
)
AND t.department = co.department;  -- 根据实际逻辑匹配
```

#### 🔧 方案 C：设置教师黑名单时间

```sql
-- 为负荷重的教师设置休息时间
INSERT INTO teacher_blackout_times
(teacher_id, week_day, start_slot, end_slot, reason)
VALUES
(1, 3, 11, 13, '科研时间'),  -- 周三晚上
(2, 5, 9, 10, '会议时间');   -- 周五上午
```

#### 🔧 方案 D：调整教师冲突惩罚

编辑 `genetic_algorithm.py`：

```python
"teacher_conflict": -70000,  # 从 -50000 提升到 -70000
```

---

## 教室/教师连续性差问题

### 现象

- 同一教师/班级连续课程在不同教室
- 师生频繁换教室

### 诊断步骤

```powershell
# 查看 Excel 导出的教师/班级视角
python view_schedule.py 1
# 检查同一天的连续课程是否在同一教室

# 查看约束分析
python show_unsatisfied_constraints.py 1
# 查看 "教室连续性分析" 部分
```

### 解决方案

#### ✅ 方案 A：提高连续性优化权重

编辑 `genetic_algorithm.py`：

```python
"classroom_continuity": 500,  # 从 300 提升到 500
```

**原理：** 更高权重使算法更努力保持同一教室

#### ✅ 方案 B：增加算法迭代次数

```powershell
python suan2.py --version 2 --population 250 --generations 400
```

#### 🔧 方案 C：手动固定教室

```sql
-- 为长期课程指定固定教室
UPDATE schedules
SET classroom_id = 'CR_FIXED_01'
WHERE course_id = 'C001'
AND version_id = 1;
```

---

## 周末/晚上排课过多问题

### 现象

- 必修课被安排在周末或晚上（11-13 节）
- 违反学生作息习惯

### 诊断步骤

```sql
-- 统计周末课程
SELECT COUNT(*) as weekend_count
FROM schedules
WHERE version_id = 1 AND week_day IN (6, 7);

-- 统计晚上课程（11-13 节）
SELECT COUNT(*) as night_count
FROM schedules
WHERE version_id = 1 AND start_slot >= 11;

-- 查看具体课程
SELECT *
FROM schedules
WHERE version_id = 1 AND (week_day IN (6,7) OR start_slot >= 11)
ORDER BY week_day, start_slot;
```

### 解决方案

#### ✅ 方案 A：增加工作日的时间槽

**问题诊断：**

- 工作日时间不足，被迫排到周末/晚上

**解决：**

1. 检查课程总时长是否超过容量
2. 增加可用教室或教师
3. 考虑分年级/专业排课

#### 🔧 方案 B：调整惩罚权重

编辑 `genetic_algorithm.py`：

```python
"weekend_penalty": -10000,         # 周末硬约束
"required_night_penalty": 500,     # 必修课晚上惩罚（从400→500）
"lecture_afternoon_preferred": 250 # 讲授课午后优先
```

#### 🔧 方案 C：设置课程时段偏好

在数据库中设置课程偏好时间：

```sql
-- 为特定课程设置不能晚上上课
UPDATE course_offerings
SET afternoon_required = 1
WHERE course_category = '必修';

-- 为某些课程设置周末禁用
UPDATE course_offerings
SET weekend_disabled = 1
WHERE course_name LIKE '%高等数学%';
```

---

## 周次冲突问题

### 现象

- 同一班级同时被安排单周和双周课程
- 显示"周次冲突"错误

### 诊断步骤

```sql
-- 检查周次配置
SELECT offering_id, week_pattern, MIN(start_week), MAX(end_week)
FROM course_offerings
GROUP BY offering_id;

-- 运行冲突分析查看周次冲突
python analyze_conflicts.py 1
```

### 解决方案

#### ✅ 方案 A：自动修复

```powershell
python analyze_conflicts.py 1
# 系统会自动避免周次冲突
```

#### 🔧 方案 B：检查数据一致性

```sql
-- 验证周次数据
SELECT ow.offering_id, COUNT(DISTINCT week_number) as week_count
FROM offering_weeks ow
GROUP BY ow.offering_id;

-- 检查是否有空的周次配置
SELECT offering_id
FROM course_offerings
WHERE week_pattern IS NULL AND offering_id NOT IN (
    SELECT DISTINCT offering_id FROM offering_weeks
);
```

---

## 运行时间过长

### 现象

- 排课需要 2+ 小时
- 想要加快速度

### 解决方案

```powershell
# 方案 A：降低参数（快速测试）
python suan2.py --version 2 --population 80 --generations 100

# 方案 B：提前停止（自动检测停滞）
python suan2.py --version 2 --max-stagnation 30

# 方案 C：多次小规模运行
# 第 1 次：快速探索
python suan2.py --version 1 --population 100 --generations 100

# 第 2 次：标准运行
python suan2.py --version 2 --population 200 --generations 300

# 第 3 次：精细优化
python analyze_conflicts.py 2
```

---

## 排码失败或无有效解

### 现象

- 排课完成但所有课程都未分配
- 冲突数极多

### 原因分析

```powershell
# 1. 检查数据是否完整
python check_data_scale.py

# 2. 查看产生的硬约束冲突
python analyze_conflicts.py 1

# 3. 检查数据库
```

**常见原因：**

- ❌ 教室严重不足
- ❌ 教师不足
- ❌ 班级课程过多
- ❌ 黑名单设置过严格
- ❌ 必需设施缺失

### 解决方案

1. **增加资源**
   - 添加教室
   - 增加可选教师

2. **放宽约束**
   - 调整黑名单规则
   - 删除不必要的设施要求

3. **分批排课**
   - 必修课 vs 选修课分开
   - 不同年级分开

4. **手动干预**
   - 手动分配 20% 的课程
   - 运行排课处理剩余课程

---

## 获取更多帮助

- **系统设计** → [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)
- **优化指南** → [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- **工具使用** → [TOOLS_USAGE.md](TOOLS_USAGE.md)
- **快速开始** → [QUICK_START.md](QUICK_START.md)
