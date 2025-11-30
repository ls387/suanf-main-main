# 智能排课系统 - 完整开发指南

## 项目概述

这是一个基于遗传算法的智能排课系统，包含完整的前后端实现。

### 技术栈
- **后端**: FastAPI + PyMySQL + 遗传算法
- **前端**: Vue 3 + Vite + Element Plus
- **数据库**: MySQL

## 快速启动

### 1. 数据库准备

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE paike2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 导入表结构
mysql -u root -p paike2 < 表3.txt

# 生成测试数据（可选）
python test_data_generator.py
```

### 2. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置数据库（修改 .env 文件或使用默认配置）
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=root
# DB_NAME=paike2

# 启动服务
python run.py

# 或使用
python -m app.main
```

后端将在 http://localhost:8000 启动
- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 启动

## 使用流程

### 第一步：数据录入

1. **教师管理** (`/teachers`)
   - 添加教师基本信息
   - 字段：教师编号、姓名、院系、性别、是否外聘

2. **课程管理** (`/courses`)
   - 添加课程信息
   - 字段：课程编号、名称、学分、总学时

3. **班级管理** (`/classes`)
   - 添加班级信息
   - 字段：班级编号、名称、年级、人数、专业

4. **教室管理** (`/classrooms`)
   - 添加教室信息
   - 字段：教室编号、名称、楼栋、校区、容量、类型

### 第二步：开课计划

1. **创建开课计划** (`/offerings`)
   - 选择学期、课程、课程性质（必修/选修/通识）
   - 设置起止周、周次模式（连续/单周/双周）
   - 关联班级、教师、设施要求

2. **配置教师偏好** (`/preferences`)
   - **黑名单时间**：教师不可上课的时间段（硬约束）
   - **偏好时间**：教师希望/避免的时间段（软约束）

### 第三步：运行排课

1. 进入**排课控制台** (`/scheduling`)

2. 配置参数：
   - **版本ID**：需要先在数据库创建排课版本
   - **种群大小**：建议 100-200
   - **进化代数**：建议 200-300
   - 可使用预设参数（小/中/大规模）

3. 点击"开始排课"，等待算法完成

4. 查看结果：
   - 最佳适应度
   - 覆盖率
   - 冲突统计
   - 执行时间

### 第四步：查看课表

选择任一视角查询课表：

1. **教师课表** (`/timetable/teacher`)
   - 输入教师ID、学期、版本ID、周次
   - 查看该教师的周课表

2. **班级课表** (`/timetable/class`)
   - 输入班级ID查看学生课表

3. **教室课表** (`/timetable/classroom`)
   - 输入教室ID查看教室使用情况

4. **周课表** (`/timetable/week`)
   - 查看某周的全部课程安排

## API 接口说明

### 基础数据管理

所有基础数据接口都遵循 RESTful 风格：

```
GET    /api/{resource}/          # 获取列表
GET    /api/{resource}/{id}      # 获取单个
POST   /api/{resource}/          # 创建
PUT    /api/{resource}/{id}      # 更新
DELETE /api/{resource}/{id}      # 删除
```

资源列表：`teachers`, `courses`, `classes`, `classrooms`, `offerings`

### 排课接口

```
POST /api/scheduling/run
{
  "version_id": 1,
  "population": 100,
  "generations": 200,
  "crossover_rate": 0.8,
  "mutation_rate": 0.1,
  "tournament_size": 5,
  "elitism_size": 10,
  "max_stagnation": 50
}
```

### 课表查询接口

```
GET /api/timetable/teacher?teacher_id=T001&semester=2025-2026-1&version_id=1&week_number=1
GET /api/timetable/class?class_id=CLS001&semester=2025-2026-1&version_id=1&week_number=1
GET /api/timetable/classroom?classroom_id=CR001&semester=2025-2026-1&version_id=1&week_number=1
GET /api/timetable/week?semester=2025-2026-1&version_id=1&week_number=1
```

## 排课算法说明

### 约束类型

**硬约束**（必须满足）：
- 教师/班级/教室时间不冲突
- 教室容量满足要求
- 教室设施满足要求
- 教师黑名单时间不排课
- 周四下午不排课

**软约束**（尽量满足）：
- 教师偏好时间
- 必修课白天优先
- 连堂课同教室
- 校区通勤优化
- 教室利用率优化

### 参数建议

| 数据规模 | 种群大小 | 进化代数 | 预计时间 |
|---------|---------|---------|---------|
| 小（<50任务） | 50-100 | 100-150 | <1分钟 |
| 中（50-200任务） | 100-150 | 200-250 | 1-3分钟 |
| 大（>200任务） | 150-200 | 250-300 | 3-10分钟 |

## 常见问题

### 1. 排课失败

**可能原因**：
- 排课版本不存在或状态不是 draft
- 没有教学任务数据
- 教室/教师资源不足
- 约束条件过于严格

**解决方法**：
- 检查数据库 `schedule_versions` 表
- 确认 `teaching_tasks` 表有数据
- 增加教室或放宽约束条件

### 2. 课表查询为空

**可能原因**：
- 排课未完成或失败
- 查询参数错误（版本ID、学期等）
- 周次不在课程起止周范围内

**解决方法**：
- 确认排课已成功完成
- 检查 `schedules` 表是否有数据
- 核对查询参数

### 3. 前端无法连接后端

**可能原因**：
- 后端服务未启动
- 端口冲突
- CORS 配置问题

**解决方法**：
- 确认后端在 8000 端口运行
- 检查 `backend/app/config.py` 中的 CORS 配置
- 查看浏览器控制台网络请求

## 下一步扩展

### AI 助手集成（Dify）

可以添加 AI 助手功能，支持自然语言查询：

1. 在后端添加专用 API：
```python
@router.get("/ai/teacher_day_schedule")
async def get_teacher_day_schedule(teacher_id: str, date: str):
    # 返回教师某天的课表摘要
    pass
```

2. 在 Dify 中创建工作流：
   - 解析用户意图
   - 调用 API 获取数据
   - 生成自然语言回答

3. 前端添加 AI 助手入口

### 其他功能建议

- 课表导出（Excel/PDF）
- 调课功能
- 冲突自动检测和提示
- 排课历史记录
- 多版本对比

## 项目结构

```
srtp/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 数据库连接
│   │   ├── routers/        # 路由
│   │   ├── schemas/        # 数据模型
│   │   └── services/       # 业务逻辑
│   ├── requirements.txt
│   └── run.py
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── api/            # API 封装
│   │   ├── components/     # 组件
│   │   ├── layouts/        # 布局
│   │   ├── router/         # 路由
│   │   ├── views/          # 页面
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── data_models.py           # 算法数据模型
├── db_connector.py          # 算法数据库连接
├── genetic_algorithm.py     # 遗传算法核心
├── suan2.py                # 算法主程序
├── test_data_generator.py  # 测试数据生成
├── 表3.txt                 # 数据库表结构
└── PROJECT_GUIDE.md        # 本文件
```

## 联系与支持

如有问题，请查看：
1. 后端 API 文档：http://localhost:8000/docs
2. 项目 README 文件
3. 代码注释

祝使用愉快！

