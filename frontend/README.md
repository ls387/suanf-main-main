# 智能排课系统前端

基于 Vue 3 + Vite + Element Plus 的智能排课系统前端界面。

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

## 功能模块

### 数据管理
- **教师管理** - 教师信息的增删改查
- **课程管理** - 课程信息的增删改查
- **班级管理** - 班级信息的增删改查
- **教室管理** - 教室信息的增删改查
- **开课计划** - 开课计划的创建和管理
- **教师偏好** - 教师黑名单时间和偏好时间管理

### 排课调度
- **排课控制台** - 配置算法参数并运行排课
- 支持小/中/大规模预设参数
- 实时显示排课结果和统计信息

### 课表查询
- **教师课表** - 按教师查询课表
- **班级课表** - 按班级查询课表
- **教室课表** - 按教室查询课表
- **周课表** - 查询某周的全部课表

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Vue Router** - 官方路由管理器
- **Pinia** - Vue 状态管理库
- **Element Plus** - Vue 3 UI 组件库
- **Axios** - HTTP 客户端

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API 接口封装
│   │   ├── index.js
│   │   ├── teachers.js
│   │   ├── courses.js
│   │   ├── classes.js
│   │   ├── classrooms.js
│   │   ├── offerings.js
│   │   ├── scheduling.js
│   │   └── timetable.js
│   ├── components/     # 公共组件
│   │   └── TimetableGrid.vue
│   ├── layouts/        # 布局组件
│   │   └── MainLayout.vue
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── views/          # 页面组件
│   │   ├── Dashboard.vue
│   │   ├── data/       # 数据管理页面
│   │   ├── scheduling/ # 排课页面
│   │   └── timetable/  # 课表查询页面
│   ├── App.vue
│   └── main.js
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## 开发说明

### API 代理配置

开发环境下，API 请求会自动代理到后端服务（http://localhost:8000）。

配置位置：`vite.config.js`

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### 添加新页面

1. 在 `src/views/` 下创建页面组件
2. 在 `src/router/index.js` 中添加路由
3. 在 `src/layouts/MainLayout.vue` 中添加菜单项

### 调用 API

```javascript
import { teacherApi } from '@/api/teachers'

// 获取所有教师
const teachers = await teacherApi.getAll()

// 创建教师
await teacherApi.create(data)
```

## 注意事项

1. 确保后端服务已启动（默认端口 8000）
2. 首次运行需要先录入基础数据（教师、课程、班级等）
3. 排课前需要在数据库中创建排课版本记录
4. 课表查询需要先完成排课操作

## 常见问题

### 1. 端口冲突

如果 5173 端口被占用，可以修改 `vite.config.js` 中的端口配置。

### 2. API 请求失败

检查后端服务是否正常运行，查看浏览器控制台的网络请求详情。

### 3. 页面空白

检查浏览器控制台是否有错误信息，确认路由配置是否正确。

