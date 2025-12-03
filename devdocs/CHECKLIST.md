# ✅ 智能排课系统 - 启动检查清单

## 📋 首次启动前的准备工作

### 1. 环境检查

- [ ] Python 3.9+ 已安装

  ```bash
  python --version
  ```

- [ ] Node.js 16+ 已安装

  ```bash
  node --version
  npm --version
  ```

- [ ] MySQL 5.7+ 已安装并运行
  ```bash
  mysql --version
  # Windows: 检查服务是否运行
  # 服务 -> MySQL
  ```

### 2. 数据库准备

- [ ] 创建数据库 `paike`

  ```sql
  CREATE DATABASE paike CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```

- [ ] 导入表结构

  ```bash
  mysql -u root -p paike < 表3.txt
  ```

- [ ] 创建排课版本

  ```sql
  USE paike;
  INSERT INTO schedule_versions (version_id, semester, version_name, status, description, created_by)
  VALUES (1, '2025-2026-1', '测试版本1', 'draft', '第一个测试版本', 'admin');
  ```

- [ ] （可选）生成测试数据
  ```bash
  python test_data_generator.py
  ```

### 3. 后端准备

- [ ] 进入后端目录

  ```bash
  cd backend
  ```

- [ ] 安装 Python 依赖

  ```bash
  pip install -r requirements.txt
  ```

- [ ] 检查数据库配置

  - 文件位置：`backend/app/config.py`
  - 默认配置：
    - Host: localhost
    - User: root
    - Password: 123456
    - Database: paike

- [ ] 启动后端服务

  ```bash
  python run.py
  ```

- [ ] 验证后端运行
  - 访问：http://localhost:8000
  - 应该看到：`{"message": "智能排课系统 API", ...}`
  - API 文档：http://localhost:8000/docs

### 4. 前端准备

- [ ] 打开新终端，进入前端目录

  ```bash
  cd frontend
  ```

- [ ] 安装 Node 依赖

  ```bash
  npm install
  ```

  如果速度慢，可以使用国内镜像：

  ```bash
  npm config set registry https://registry.npmmirror.com
  npm install
  ```

- [ ] 启动前端服务

  ```bash
  npm run dev
  ```

- [ ] 验证前端运行
  - 访问：http://localhost:5173
  - 应该看到：智能排课系统首页

---

## 🎯 第一次使用流程检查

### 步骤 1: 录入基础数据

- [ ] 添加至少 1 个教师

  - 路径：教师管理
  - 必填：教师编号、姓名、院系

- [ ] 添加至少 1 门课程

  - 路径：课程管理
  - 必填：课程编号、名称、学分、学时

- [ ] 添加至少 1 个班级

  - 路径：班级管理
  - 必填：班级编号、名称、年级、专业

- [ ] 添加至少 1 间教室
  - 路径：教室管理
  - 必填：教室编号、校区、容量

### 步骤 2: 创建开课计划

- [ ] 创建开课计划
  - 路径：开课计划
  - 必填：学期、课程、起止周
  - 注意：需要关联班级和教师

### 步骤 3: 创建教学任务

⚠️ **重要**：需要在数据库手动创建

```sql
-- 为开课计划创建教学任务
-- 例如：每周2次课，一次3节，一次2节
INSERT INTO teaching_tasks (offering_id, group_id, task_sequence, slots_count)
VALUES
  (1, NULL, 1, 3),  -- 第1次课，3节
  (1, NULL, 2, 2);  -- 第2次课，2节
```

- [ ] 已创建教学任务

### 步骤 4: 运行排课

- [ ] 进入排课控制台
- [ ] 设置版本 ID = 1
- [ ] 选择参数预设或自定义
- [ ] 点击"开始排课"
- [ ] 等待完成（可能需要几分钟）
- [ ] 检查结果：
  - [ ] 覆盖率 > 90%
  - [ ] 冲突数 = 0
  - [ ] 有适应度分数

### 步骤 5: 查看课表

- [ ] 教师课表查询成功
- [ ] 班级课表查询成功
- [ ] 教室课表查询成功
- [ ] 周课表查询成功

---

## 🔍 常见问题快速检查

### 问题：后端启动失败

- [ ] 检查 Python 版本 >= 3.9
- [ ] 检查依赖是否安装：`pip list | findstr fastapi`
- [ ] 检查 MySQL 是否运行
- [ ] 检查数据库配置是否正确
- [ ] 查看错误信息

### 问题：前端启动失败

- [ ] 检查 Node.js 版本 >= 16
- [ ] 删除 `node_modules` 重新安装
- [ ] 检查端口 5173 是否被占用
- [ ] 查看控制台错误信息

### 问题：排课失败

- [ ] 检查排课版本是否存在且状态为 draft
- [ ] 检查是否有教学任务数据
- [ ] 检查教师、教室资源是否充足
- [ ] 查看 `scheduling.log` 日志

### 问题：课表查询为空

- [ ] 检查排课是否成功完成
- [ ] 检查版本 ID、学期是否正确
- [ ] 检查数据库 `schedules` 表是否有数据
- [ ] 检查周次是否在课程起止周范围内

### 问题：API 请求失败

- [ ] 检查后端是否在 8000 端口运行
- [ ] 访问 http://localhost:8000/health 测试
- [ ] 检查浏览器控制台网络请求
- [ ] 检查 CORS 配置

---

## 📊 系统状态检查

### 后端健康检查

```bash
# 方法 1: 浏览器访问
http://localhost:8000/health

# 方法 2: curl 命令
curl http://localhost:8000/health

# 应该返回：{"status": "healthy"}
```

### 前端健康检查

```bash
# 浏览器访问
http://localhost:5173

# 应该能看到系统首页
```

### 数据库健康检查

```sql
-- 检查数据库
SHOW DATABASES LIKE 'paike';

-- 检查表
USE paike;
SHOW TABLES;

-- 检查数据
SELECT COUNT(*) FROM teachers;
SELECT COUNT(*) FROM courses;
SELECT COUNT(*) FROM teaching_tasks;
```

---

## 🎉 全部完成！

如果以上所有检查项都通过，恭喜你！系统已经可以正常使用了。

### 下一步

1. 📖 阅读 `PROJECT_GUIDE.md` 了解详细功能
2. 🎨 尝试美化界面
3. 🔧 添加新功能
4. 📝 准备项目文档和演示

### 获取帮助

- 📚 文档：`START_HERE.md`
- 🔗 API 文档：http://localhost:8000/docs
- 📋 项目总结：`SUMMARY.md`

---

**提示**：建议打印或保存此清单，每次启动系统时快速检查！
