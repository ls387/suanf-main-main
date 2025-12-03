# 🚀 智能排课系统 - 快速开始

## 📋 系统已完成功能

### ✅ 后端 API（FastAPI）

- [x] 教师/课程/班级/教室基础数据管理 CRUD
- [x] 开课计划管理
- [x] 教师黑名单时间和偏好管理
- [x] 排课算法调用接口
- [x] 四视角课表查询（教师/班级/教室/周）
- [x] 完整的 API 文档（Swagger）

### ✅ 前端界面（Vue 3）

- [x] 响应式主布局和导航
- [x] 数据管理页面（6 个模块）
- [x] 排课控制台（参数配置+结果展示）
- [x] 课表查询（4 个视角）
- [x] 统计首页

### ⏳ 待扩展功能

- [ ] AI 助手（Dify 集成）
- [ ] 课表导出（Excel/PDF）
- [ ] 调课功能
- [ ] 排课历史记录

---

## 🎯 第一次使用 - 完整流程

### 步骤 1: 准备数据库

```bash
# 1. 创建数据库
mysql -u root -p
CREATE DATABASE paike CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE paike;

# 2. 导入表结构
source 表3.txt;
# 或者
mysql -u root -p paike < 表3.txt

# 3. 创建排课版本（必需！）
INSERT INTO schedule_versions (version_id, semester, version_name, status, description, created_by)
VALUES (1, '2025-2026-1', '测试版本1', 'draft', '第一个测试版本', 'admin');

# 4. 生成测试数据（可选，如果没有真实数据）
exit
python test_data_generator.py
```

### 步骤 2: 启动后端

```bash
# 进入后端目录
cd backend

# 安装依赖（首次运行）
pip install -r requirements.txt

# 启动服务
python run.py
```

✅ 后端启动成功后，访问：

- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 步骤 3: 启动前端

**新开一个终端窗口**

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

✅ 前端启动成功后，访问：http://localhost:5173

---

## 📝 使用系统的正确顺序

### 1️⃣ 数据录入（必须按顺序）

访问前端系统，依次录入以下数据：

#### a) 基础数据（可以任意顺序）

- **教师管理** → 添加教师（教师编号、姓名、院系等）
- **课程管理** → 添加课程（课程编号、名称、学分、学时）
- **班级管理** → 添加班级（班级编号、名称、年级、人数）
- **教室管理** → 添加教室（教室编号、楼栋、校区、容量）

#### b) 开课计划（依赖基础数据）

- **开课计划** → 创建开课计划
  - 选择学期：2025-2026-1
  - 选择课程
  - 设置课程性质（必修/选修/通识）
  - 设置起止周（例如 1-16 周）
  - 关联班级和教师

#### c) 教学任务（需要手动在数据库创建）

```sql
-- 为每个开课计划创建教学任务
-- 例如：数据结构课程，每周2次课，一次3节，一次2节
INSERT INTO teaching_tasks (offering_id, group_id, task_sequence, slots_count)
VALUES
  (1, NULL, 1, 3),  -- 第1次课，3节连堂
  (1, NULL, 2, 2);  -- 第2次课，2节连堂
```

#### d) 教师偏好（可选）

- **教师偏好** → 设置黑名单时间和偏好时间

### 2️⃣ 运行排课

进入 **排课控制台**：

1. **设置参数**：
   - 版本 ID：1（刚才创建的）
   - 使用预设参数或自定义
2. **点击"开始排课"**

   - 等待算法运行（可能需要几分钟）
   - 查看结果统计

3. **检查结果**：
   - 覆盖率应该接近 100%
   - 冲突数应该为 0
   - 适应度分数越高越好

### 3️⃣ 查看课表

选择任一视角查询：

- **教师课表**：输入教师 ID（例如 T001）
- **班级课表**：输入班级 ID（例如 CLS001）
- **教室课表**：输入教室 ID（例如 CR001）
- **周课表**：查看某周的全部课程

---

## 🔧 常见问题排查

### 问题 1: 后端启动失败

**症状**：`ModuleNotFoundError` 或数据库连接失败

**解决**：

```bash
# 确认依赖已安装
pip list | grep fastapi
pip list | grep pymysql

# 检查数据库配置
# 编辑 backend/.env 文件（如果存在）
# 或检查 backend/app/config.py 中的默认配置
```

### 问题 2: 前端启动失败

**症状**：`npm install` 报错

**解决**：

```bash
# 清理缓存重试
rm -rf node_modules package-lock.json
npm install

# 或使用 cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

### 问题 3: 排课失败

**症状**：提示"排课版本不存在"或"没有教学任务"

**解决**：

```sql
-- 检查排课版本
SELECT * FROM schedule_versions WHERE version_id = 1;

-- 检查教学任务
SELECT COUNT(*) FROM teaching_tasks tt
JOIN course_offerings co ON tt.offering_id = co.offering_id
WHERE co.semester = '2025-2026-1';

-- 如果教学任务为0，需要手动创建
```

### 问题 4: 课表查询为空

**症状**：查询后显示"暂无课表数据"

**解决**：

1. 确认排课已成功完成
2. 检查查询参数（版本 ID、学期）是否正确
3. 查看数据库：

```sql
SELECT COUNT(*) FROM schedules WHERE version_id = 1;
```

### 问题 5: 前端无法连接后端

**症状**：API 请求失败，控制台显示网络错误

**解决**：

1. 确认后端在 8000 端口运行
2. 访问 http://localhost:8000/health 检查后端状态
3. 检查浏览器控制台的具体错误信息

---

## 📚 更多文档

- **后端 API 文档**：`backend/README.md`
- **前端说明**：`frontend/README.md`
- **完整开发指南**：`PROJECT_GUIDE.md`
- **算法说明**：`README.md`（项目根目录）

---

## 🎓 学习建议

### 对于负责后端的同学

1. 先理解 FastAPI 的基本用法
2. 查看 `backend/app/routers/` 下的路由实现
3. 学习如何调用现有的遗传算法
4. 尝试添加新的 API 端点

### 对于负责前端的同学

1. 先理解 Vue 3 Composition API
2. 查看 `frontend/src/views/data/Teachers.vue` 作为模板
3. 学习如何使用 Element Plus 组件
4. 尝试美化现有页面或添加新功能

### 对于负责算法的同学

1. 查看 `genetic_algorithm.py` 的实现
2. 理解硬约束和软约束的区别
3. 尝试调整惩罚分数或添加新约束
4. 优化算法性能

---

## ✨ 下一步建议

### 短期（1-2 周）

1. 熟悉整个系统的使用流程
2. 用真实数据测试排课效果
3. 修复发现的 bug
4. 美化界面样式

### 中期（3-4 周）

1. 添加课表导出功能
2. 实现调课功能
3. 添加数据验证和错误提示
4. 优化算法参数

### 长期（选做）

1. 集成 Dify AI 助手
2. 添加移动端适配
3. 实现权限管理
4. 部署到服务器

---

## 🎉 恭喜！

你现在拥有一个完整的智能排课系统！

如果遇到问题，请：

1. 查看相关文档
2. 检查浏览器控制台和后端日志
3. 查看 `scheduling.log` 文件
4. 访问 http://localhost:8000/docs 查看 API 文档

祝你的 SRTP 项目顺利！🚀
