# 智能排课系统后端 API

基于 FastAPI 的智能排课系统后端服务。

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

复制 `.env.example` 为 `.env` 并修改数据库配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=paike2
```

### 3. 运行服务

```bash
# 开发模式（自动重载）
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口说明

### 基础数据管理

- **教师管理** `/api/teachers`
  - GET / - 获取所有教师
  - GET /{teacher_id} - 获取单个教师
  - POST / - 创建教师
  - PUT /{teacher_id} - 更新教师
  - DELETE /{teacher_id} - 删除教师

- **课程管理** `/api/courses`
  - 同上结构

- **班级管理** `/api/classes`
  - 同上结构

- **教室管理** `/api/classrooms`
  - 同上结构

### 开课计划管理

- **开课计划** `/api/offerings`
  - GET / - 获取开课计划列表（可按学期过滤）
  - GET /{offering_id} - 获取单个开课计划
  - POST / - 创建开课计划
  - PUT /{offering_id} - 更新开课计划
  - DELETE /{offering_id} - 删除开课计划

- **教师黑名单时间** `/api/offerings/blackout-times/`
  - GET / - 获取禁止时间列表
  - POST / - 创建禁止时间
  - DELETE /{blackout_id} - 删除禁止时间

- **教师偏好** `/api/offerings/preferences/`
  - GET / - 获取偏好列表
  - POST / - 创建偏好
  - DELETE /{preference_id} - 删除偏好

### 排课调度

- **运行排课** `POST /api/scheduling/run`
  
  请求体示例：
  ```json
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

### 课表查询

- **教师课表** `GET /api/timetable/teacher`
  - 参数: teacher_id, semester, version_id, week_number(可选)

- **班级课表** `GET /api/timetable/class`
  - 参数: class_id, semester, version_id, week_number(可选)

- **教室课表** `GET /api/timetable/classroom`
  - 参数: classroom_id, semester, version_id, week_number(可选)

- **周课表** `GET /api/timetable/week`
  - 参数: semester, version_id, week_number
  - 可选过滤: teacher_id, class_id, classroom_id

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── routers/             # 路由模块
│   │   ├── teachers.py
│   │   ├── courses.py
│   │   ├── classes.py
│   │   ├── classrooms.py
│   │   ├── offerings.py
│   │   ├── scheduling.py
│   │   └── timetables.py
│   ├── schemas/             # Pydantic 数据模型
│   │   ├── teacher.py
│   │   ├── course.py
│   │   ├── class_model.py
│   │   ├── classroom.py
│   │   ├── offering.py
│   │   ├── scheduling.py
│   │   └── timetable.py
│   └── services/            # 业务逻辑服务
│       └── algorithm.py     # 排课算法封装
├── requirements.txt
├── .env.example
└── README.md
```

## 开发说明

### 添加新的 API 端点

1. 在 `app/schemas/` 中定义数据模型
2. 在 `app/routers/` 中创建路由文件
3. 在 `app/main.py` 中注册路由

### 数据库操作

使用 `app.database.Database` 类进行数据库操作：

```python
from app.database import get_db

def my_function(db: Database = Depends(get_db)):
    results = db.execute_query("SELECT * FROM table")
    return results
```

## 注意事项

1. 确保 MySQL 数据库已启动并创建了 `paike2` 数据库
2. 确保已执行 `表3.txt` 中的建表 SQL
3. 可以使用 `test_data_generator.py` 生成测试数据
4. CORS 已配置，默认允许 localhost:5173 和 localhost:3000

