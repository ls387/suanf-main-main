# task_relation_constraints 任务关系约束使用说明

## ✅ 功能状态：已实现并启用

`task_relation_constraints` 功能已经完整实现，可以控制同一门课程的不同任务次之间的时间安排关系。

---

## 📋 功能说明

该约束用于定义**同一开课计划（同一门课）的不同任务次之间的时间关系**，属于**软约束**。

### 支持的三种约束类型

| 约束类型       | 数据库值                 | 说明                         | 示例场景                |
| -------------- | ------------------------ | ---------------------------- | ----------------------- |
| **同一天**     | `REQUIRE_SAME_DAY`       | 要求两个任务必须安排在同一天 | 上下午连贯的实验课      |
| **避免连续天** | `AVOID_CONSECUTIVE_DAYS` | 避免两个任务在连续的两天上课 | 一周 2 次的理论课       |
| **最小间隔**   | `MIN_DAYS_APART`         | 要求两个任务至少间隔 N 天    | 理论课与实验课间隔 2 天 |

---

## 📊 数据表结构

```sql
CREATE TABLE task_relation_constraints (
    constraint_id INT AUTO_INCREMENT PRIMARY KEY,
    offering_id INT NOT NULL,              -- 开课计划ID
    task_sequence_a INT NOT NULL,          -- 任务次A的序号
    task_sequence_b INT NOT NULL,          -- 任务次B的序号
    constraint_type ENUM(
        'AVOID_CONSECUTIVE_DAYS',
        'REQUIRE_SAME_DAY',
        'MIN_DAYS_APART'
    ) NOT NULL,
    constraint_value INT,                  -- 约束值（仅MIN_DAYS_APART需要）
    penalty_score INT DEFAULT 200,         -- 违反时的惩罚分数

    FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id)
);
```

---

## ✍️ 填写示例

### 示例 1：理论课一周 2 次，避免连续天

**场景**：《高等数学》每周上 2 次课，希望分散安排，避免周一周二连续上。

```sql
-- 假设 offering_id = 100，有两个teaching_tasks:
-- task_sequence = 1 (第一次课)
-- task_sequence = 2 (第二次课)

INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(100, 1, 2, 'AVOID_CONSECUTIVE_DAYS', NULL, 200);
```

### 示例 2：理论课和实验课至少间隔 2 天

**场景**：《计算机网络》理论课在前，实验课在后，希望至少间隔 2 天让学生消化理论知识。

```sql
-- offering_id = 200
-- task_sequence = 1 (理论课)
-- task_sequence = 2 (实验课)

INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(200, 1, 2, 'MIN_DAYS_APART', 2, 300);
```

### 示例 3：上下午实验课必须同一天

**场景**：《化学实验》需要连续进行，上午和下午必须安排在同一天。

```sql
-- offering_id = 300
-- task_sequence = 1 (上午实验，3节)
-- task_sequence = 2 (下午实验，3节)

INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(300, 1, 2, 'REQUIRE_SAME_DAY', NULL, 500);
```

### 示例 4：一周 3 次课，每次至少间隔 1 天

**场景**：《英语》每周 3 次课，任意两次都要间隔至少 1 天。

```sql
-- offering_id = 400
-- 需要添加3条约束，形成两两约束

-- 第1次和第2次至少间隔1天
INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(400, 1, 2, 'MIN_DAYS_APART', 1, 200);

-- 第2次和第3次至少间隔1天
INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(400, 2, 3, 'MIN_DAYS_APART', 1, 200);

-- 第1次和第3次至少间隔2天（可选，确保更分散）
INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(400, 1, 3, 'MIN_DAYS_APART', 2, 150);
```

---

## ⚙️ 配置参数

在遗传算法配置中：

```python
"penalty_scores": {
    "task_relation": 300,  # 默认惩罚分数
    # 如果数据库中设置了penalty_score，会使用数据库的值
}
```

---

## 🔍 约束检查逻辑

### 实现位置

- **文件**: `genetic_algorithm.py`
- **方法**: `_check_task_relations()`
- **调用**: 在 `calculate_fitness_penalty()` 中自动调用

### 检查流程

1. **构建映射**：遍历种群中的每个基因，建立 task_id 到基因的映射
2. **检查约束**：对每个有关系约束的任务对，检查是否满足约束
3. **计算惩罚**：
   - 违反约束时，累加惩罚分数
   - 优先使用数据库中的 `penalty_score`
   - 若未设置，使用配置中的 `task_relation`

### 示例日志输出

```
任务关系约束违反: 任务123和124应至少间隔2天，但实际只间隔1天
任务关系约束违反: 任务456和457应在同一天，但实际分别在周2和周4
```

---

## 💡 使用建议

### 1. 适度使用

- 不要为所有课程都设置约束
- 只为有明确时间关系需求的课程设置

### 2. 合理设置惩罚分数

- **100-200**：一般偏好，可以不满足
- **300-400**：强烈偏好，尽量满足
- **500+**：非常重要，接近硬约束

### 3. 避免冲突

- 不要设置互相矛盾的约束
- 例如：不要既要求"同一天"又要求"间隔 2 天"

### 4. 考虑任务数量

- 一周 2 次课：设置 1 条约束即可
- 一周 3 次课：可设置 2-3 条约束
- 一周 4 次以上：谨慎使用，避免过度约束

### 5. 测试和调整

1. 先添加少量约束
2. 运行排课算法
3. 查看日志中的违反情况
4. 根据实际效果调整惩罚分数

---

## 📈 效果验证

### 查看约束违反情况

运行排课后，查看日志中是否有类似信息：

```
任务关系约束违反: ...
```

### 分析排课结果

可以使用 `analyze_conflicts.py` 或查询数据库验证：

```sql
-- 查看某个课程的任务安排情况
SELECT
    tt.task_sequence,
    s.week_day,
    s.start_slot,
    s.end_slot,
    cr.classroom_name
FROM schedules s
JOIN teaching_tasks tt ON s.task_id = tt.task_id
JOIN classrooms cr ON s.classroom_id = cr.classroom_id
WHERE tt.offering_id = 100  -- 替换为你的offering_id
ORDER BY tt.task_sequence;
```

---

## 🛠️ 故障排查

### 问题 1：约束不生效

**可能原因**：

- offering_id 或 task_sequence 填写错误
- 数据库中没有对应的 teaching_tasks

**解决方法**：

```sql
-- 检查teaching_tasks是否存在
SELECT tt.task_id, tt.task_sequence, co.offering_id
FROM teaching_tasks tt
JOIN course_offerings co ON tt.offering_id = co.offering_id
WHERE co.offering_id = 100;
```

### 问题 2：约束总是被违反

**可能原因**：

- 惩罚分数太低，算法认为违反代价不大
- 其他硬约束冲突，无法满足

**解决方法**：

1. 提高 `penalty_score` 值
2. 检查是否有其他约束冲突
3. 增加遗传算法的代数和种群大小

### 问题 3：查看已加载的约束

在运行排课时，查看日志：

```
加载了 15 条任务关系约束
构建了 10 个任务的关系约束
```

---

## 📝 完整示例脚本

```sql
-- 为《数据结构》课程设置约束
-- offering_id = 500, 有2次课（理论+实验）

-- 1. 查看该课程的teaching_tasks
SELECT task_id, task_sequence, slots_count
FROM teaching_tasks
WHERE offering_id = 500;

-- 2. 添加约束：理论课和实验课至少间隔1天
INSERT INTO task_relation_constraints
(offering_id, task_sequence_a, task_sequence_b, constraint_type, constraint_value, penalty_score)
VALUES
(500, 1, 2, 'MIN_DAYS_APART', 1, 250);

-- 3. 查看添加的约束
SELECT * FROM task_relation_constraints WHERE offering_id = 500;
```

---

## 🎯 总结

`task_relation_constraints` 功能已完整实现，可以有效控制同一课程不同任务次的时间安排关系，提高排课质量和灵活性。合理使用该功能可以：

✅ 避免课程安排过于集中
✅ 确保理论与实践的合理间隔
✅ 满足特殊课程的连贯性要求
✅ 提升学生的学习体验

建议从简单场景开始尝试，逐步扩展到更复杂的约束组合。
