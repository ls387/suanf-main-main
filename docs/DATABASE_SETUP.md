# 数据库设置与操作指南

本文档提供完整的数据库准备、表结构验证和排课流程管理指南。

---

## 📋 表结构概览分类

排课系统数据库表分为 **3 大类**：

| 类别            | 用途                                         | 表数量 | 备注               |
| --------------- | -------------------------------------------- | ------ | ------------------ |
| **A. 基础数据** | 校区、部门、成员、课程、教室等静态配置       | 9 张表 | 需要预先准备       |
| **B. 学期任务** | 本学期排课任务定义（开课计划、班级、教师等） | 7 张表 | 每学期需要重新配置 |
| **C. 约束条件** | 黑名单、偏好、关系约束等                     | 3 张表 | 根据需要配置       |
| **D. 过程管理** | 排课版本控制                                 | 1 张表 | 系统自动维护       |
| **E. 结果存储** | 排课结果                                     | 1 张表 | 算法输出           |

**总计：21 张表**

---

## 🔍 详细表分类

### A. 核心基础实体（基本不变）

这些数据相对稳定，通常一个学期内不会有大的变动。

```
1. campuses          (校区表)
2. departments       (院系表)
3. majors           (专业表)
4. classes          (行政班表)
5. teachers         (教师表)
6. courses          (课程目录表)
7. classroom_features (教室设施表)
8. classrooms       (教室表)
9. classroom_has_features (教室-设施关联表)
```

**检查完整性：**

```sql
SELECT 'campuses' tbl, COUNT(*) cnt FROM campuses
UNION ALL SELECT 'departments', COUNT(*) FROM departments
UNION ALL SELECT 'teachers', COUNT(*) FROM teachers
UNION ALL SELECT 'classrooms', COUNT(*) FROM classrooms;
```

### B. 本学期排课任务定义（每学期重新准备）

这是排课工作的核心，定义了"为谁、上什么课、由谁上"。

```
1. course_offerings       (开课计划表) ← 排课的起点
2. offering_weeks         (周次详情表)
3. offering_classes       (班级关联表)
4. offering_teachers      (教师团队表)
5. teaching_groups        (教学班/小组表)
6. offering_requires_features (设施要求表)
7. teaching_tasks         (教学任务次表) ← 排课的原子单位
```

**检查完整性：**

```sql
SELECT 'course_offerings' tbl, COUNT(*) cnt FROM course_offerings WHERE semester='2025-2026-1'
UNION ALL SELECT 'teaching_tasks', COUNT(*) FROM teaching_tasks
UNION ALL SELECT 'offering_teachers', COUNT(*) FROM offering_teachers
UNION ALL SELECT 'offering_classes', COUNT(*) FROM offering_classes;
```

### C. 排课约束条件（每学期可能不同）

这些是适应度函数的主要评分依据。

```
1. teacher_blackout_times    (教师禁止时间表) ← 硬约束
2. teacher_preferences       (教师偏好表)    ← 软约束
3. task_relation_constraints (任务关系约束表) ← 软约束
```

### D. 过程管理（系统自动维护）

```
1. schedule_versions (排课方案版本表)
```

### E. 结果存储（算法输出）

```
1. schedules (排课结果表)
```

---

## 🚀 完整操作步骤

### Step 1: 环境变量配置

```powershell
# Windows PowerShell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_USER = "pk"
$env:DB_PASSWORD = "123456"
$env:DB_NAME = "paike"

# 验证连接
python -c "import pymysql; pymysql.connect(host='localhost', user='pk', password='123456', database='paike'); print('连接成功')"
```

### Step 2: 创建数据库和表

```bash
# 使用提供的建表脚本
mysql -h localhost -u pk -p123456 < new.sql
```

### Step 3: 检查基础数据完整性

```sql
-- 检查核心表是否有数据
SELECT 'campuses' tbl, COUNT(*) cnt FROM campuses
UNION ALL SELECT 'departments', COUNT(*) FROM departments
UNION ALL SELECT 'classes', COUNT(*) FROM classes
UNION ALL SELECT 'teachers', COUNT(*) FROM teachers
UNION ALL SELECT 'courses', COUNT(*) FROM courses
UNION ALL SELECT 'classrooms', COUNT(*) FROM classrooms;
```

**预期结果：** 所有表都应该有数据

### Step 4: 检查学期任务数据

```sql
-- 检查本学期的开课任务
SELECT
    'course_offerings' tbl, COUNT(*) cnt
FROM course_offerings
WHERE semester='2025-2026-1'
UNION ALL
SELECT 'teaching_tasks', COUNT(*)
FROM teaching_tasks tt
JOIN course_offerings co ON tt.offering_id=co.offering_id
WHERE co.semester='2025-2026-1';
```

**预期结果：** 应该有相应数量的开课计划和教学任务

### Step 5: 创建排课版本

```sql
-- 为本次排课创建版本
INSERT INTO schedule_versions(semester, version_name, status, description, created_by)
VALUES ('2025-2026-1','2025秋第一轮草案','draft','自动算法初始版本','admin');

-- 查看生成的版本ID
SELECT * FROM schedule_versions ORDER BY version_id DESC LIMIT 1;
```

**重要：** 记录生成的 `version_id`（假设为 3）

### Step 6: 验证数据质量

```sql
-- 检查是否存在无教师的任务
SELECT t.task_id, t.offering_id
FROM teaching_tasks t
LEFT JOIN offering_teachers ot ON t.offering_id=ot.offering_id
WHERE ot.teacher_id IS NULL
LIMIT 10;

-- 检查无班级的开课
SELECT o.offering_id, o.course_id
FROM course_offerings o
LEFT JOIN offering_classes oc ON o.offering_id=oc.offering_id
WHERE o.semester='2025-2026-1'
GROUP BY o.offering_id
HAVING COUNT(oc.class_id)=0
LIMIT 10;
```

**预期结果：** 无行或很少行（表示数据完整）

### Step 7: 运行排课

```bash
# 标准配置
python suan2.py --version 3 --population 200 --generations 300

# 快速测试
python suan2.py --version 3 --population 80 --generations 100
```

### Step 8: 检查排课结果

```sql
-- 查看排课结果
SELECT * FROM schedules WHERE version_id=3 LIMIT 20;

-- 统计覆盖率
SELECT
    COUNT(DISTINCT task_id) 已排课程数,
    (SELECT COUNT(*) FROM teaching_tasks tt
     JOIN course_offerings co ON tt.offering_id=co.offering_id
     WHERE co.semester='2025-2026-1') 总课程数
FROM schedules WHERE version_id=3;
```

### Step 9: 检测冲突（理论上应无）

```sql
-- 教师同一时间重复（班级冲突）
SELECT s.week_day, s.start_slot, oc.class_id, COUNT(*) cnt
FROM schedules s
JOIN teaching_tasks tt ON s.task_id=tt.task_id
JOIN offering_classes oc ON tt.offering_id=oc.offering_id
WHERE s.version_id=3
GROUP BY s.week_day, s.start_slot, oc.class_id
HAVING cnt>1;

-- 教室冲突
SELECT s.week_day, s.start_slot, s.classroom_id, COUNT(*) cnt
FROM schedules s
WHERE s.version_id=3
GROUP BY s.week_day, s.start_slot, s.classroom_id
HAVING cnt>1;
```

**预期结果：** 无行（无冲突）

### Step 10: 分析排课质量

```sql
-- 教室利用率分析
SELECT
    s.classroom_id,
    cr.classroom_name,
    cr.capacity,
    COUNT(DISTINCT s.task_id) 课程数,
    ROUND(100.0 * SUM(t.student_count) / (cr.capacity * COUNT(DISTINCT CONCAT(s.week_day, s.start_slot))), 1) 平均利用率
FROM schedules s
JOIN classrooms cr ON s.classroom_id=cr.classroom_id
JOIN teaching_tasks t ON s.task_id=t.task_id
WHERE s.version_id=3
GROUP BY s.classroom_id
ORDER BY 平均利用率;

-- 教师课程负荷分析
SELECT
    t.teacher_id,
    t.teacher_name,
    COUNT(DISTINCT co.offering_id) 课程数,
    SUM(tt.slots_count) 总课时
FROM teachers t
LEFT JOIN offering_teachers ot ON t.teacher_id=ot.teacher_id
LEFT JOIN course_offerings co ON ot.offering_id=co.offering_id
LEFT JOIN teaching_tasks tt ON co.offering_id=tt.offering_id
WHERE co.semester='2025-2026-1'
GROUP BY t.teacher_id
ORDER BY 总课时 DESC;
```

---

## 📊 关键表结构说明

### teaching_tasks（教学任务表） - 最重要

这是**排课算法的原子单位**。每一条记录代表一次具体的上课安排。

```sql
CREATE TABLE teaching_tasks (
    task_id INT PRIMARY KEY AUTO_INCREMENT,
    offering_id INT NOT NULL,        -- 关联的开课计划
    group_id INT DEFAULT 1,          -- 小组编号（如果有分班）
    sequence INT,                    -- 序号（同课多次时用）
    slots_count INT NOT NULL,        -- 这次课上几节（2或3）

    FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id)
);
```

**重要：**

- `slots_count` 通常只用 2 或 3（一节课 2 时段，一节课 3 时段）
- 每次排课前必须确保该表有足够的记录

### schedules（排课结果表） - 最终输出

```sql
CREATE TABLE schedules (
    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
    version_id INT NOT NULL,
    task_id INT NOT NULL,
    teacher_id INT NOT NULL,
    classroom_id VARCHAR(20) NOT NULL,
    week_day INT NOT NULL,           -- 1-7 代表周一到周日
    start_slot INT NOT NULL,         -- 1-13 代表第几节课

    UNIQUE KEY uk_version_time_space (version_id, classroom_id, week_day, start_slot),

    FOREIGN KEY (version_id) REFERENCES schedule_versions(version_id),
    FOREIGN KEY (task_id) REFERENCES teaching_tasks(task_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(classroom_id)
);
```

**重要：**

- 约束 `uk_version_time_space` 保证同一教室在同一时间只有一个安排
- 这是防止教室多重分配的关键

---

## 💡 常见问题

### Q: 排课前需要准备哪些表？

**A:** 最少这些：

```
必须：
- campuses, departments, classes, teachers, courses, classrooms
- course_offerings, teaching_tasks
- offering_classes, offering_teachers

可选但推荐：
- teacher_blackout_times (教师禁止时间)
- teacher_preferences (教师偏好)
- task_relation_constraints (任务关系)
```

### Q: teaching_tasks 的 slots_count 应该怎么设置？

**A:**

- 大多数课程：2 或 3（一次上课占用的时段数）
- **不应该** 用 1、4、5 等其他数字
- 一般规则：
  - 2 的课：45 分钟课
  - 3 的课：90 分钟课

### Q: 排课前检查数据完整性的最快方法？

**A:** 运行：

```bash
python check_data_scale.py
```

这个工具会自动检查数据规模并给出推荐参数。

### Q: 排课结果保存在哪里？

**A:**

- 数据库：`schedules` 表，关联到相应的 `version_id`
- Excel 导出：运行 `python view_schedule.py <version_id>`

### Q: 如何重新排课？

**A:**

```bash
# 创建新版本
INSERT INTO schedule_versions(semester, version_name, status)
VALUES ('2025-2026-1', '第二轮', 'draft');

# 运行排课（用新的 version_id）
python suan2.py --version 4 --population 250 --generations 400
```

---

## 📈 性能优化建议

### 1. 索引优化

```sql
-- 添加查询索引
CREATE INDEX idx_offering_semester ON course_offerings(semester);
CREATE INDEX idx_teaching_tasks_offering ON teaching_tasks(offering_id);
CREATE INDEX idx_schedules_version ON schedules(version_id);
CREATE INDEX idx_schedules_task ON schedules(task_id);
```

### 2. 大数据量处理

如果课程数 > 200：

```bash
# 增加参数
python suan2.py --version 5 --population 300 --generations 500
```

### 3. 备份策略

```bash
# 排课前备份
mysqldump -u pk -p123456 paike > paike_backup_$(date +%Y%m%d).sql

# 恢复备份
mysql -u pk -p123456 paike < paike_backup_20251125.sql
```

---

## 🎓 参考链接

- **快速开始**: [docs/QUICK_START.md](../docs/QUICK_START.md)
- **工具使用**: [docs/TOOLS_USAGE.md](../docs/TOOLS_USAGE.md)
- **排课工具**: [docs/TOOLS_USAGE.md#排课工具](../docs/TOOLS_USAGE.md)
- **参数调优**: [docs/PARAMETER_TUNING.md](../docs/PARAMETER_TUNING.md)

---

**最后更新**: 2026-04-12
