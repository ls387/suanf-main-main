# 高校教务智能助手 (Agent) 说明书

## 1. 产品概述

高校教务智能助手是一款基于大语言模型（LLM）驱动的自然语言问答内嵌组件。它能够在理解用户教务查阅意图后，自动将自然语言转化为安全的只读 SQL 查询，实时拉取 MySQL 系统中的排课、教师、教室、班级等数据，并最终以友好的方式生成自然语言回复。

---

## 2. 功能说明书

### 2.1 核心功能特性

- **自然语言查询 (Text-to-SQL)**：用户无需熟悉任何后台页面操作，直接输入问题（如“查一下张老师周二的课”），系统自动提取关键词转换为数据库条件，查出结果。
- **支持的数据业务域**：
  - **基础信息**：校区、院系、班级、人员（教师）的基础资料及状态确认。
  - **教学计划与任务**：课程开设信息、教学任务详情、预期学生数等。
  - **教室约束与借用**：教室实时容量、设施类型和可用状态查询。
  - **排课结果追踪**：实时追踪正式排课结果（发布版）与预排课结果（草案草稿版）。
- **多轮对话上下文记忆**：基于 `Session ID` 原理追踪当前对话历史，使得多轮追问成为可能。例如，第一轮问“李老师教什么课”，第二轮直接问“这门课有多少学生”，系统无需重复指明老师姓名。
- **数据安全防御机制**：
  - 内置安全拦截，凡是不以 `SELECT` 开头的语句（如包含 `DELETE`, `UPDATE`, `DROP` 等危险关键词）将被直接强制拦截。
  - 全局 SQL 查询上限限制（隐式增加 `LIMIT`）。
- **主动反问机制**：当用户的提问模糊、缺少必要查询维度（如：“这门课安排在什么时间？”，但没指明是哪个学期的这门课）时，助手不会瞎猜，而是能聪明地反问提示用户以补全条件。

---

## 3. 使用说明书

### 3.1 适用对象

本助手供该校学生、教师及辅导员或教务管理人员，在日常教务系统协同平台查阅数据时使用。

### 3.2 使用场景与示例指令

在右下角的智能助手小组件中，直接输入您的需求，按“发送”即可。由于助手具有一定的推理能力，您不需要使用死板的关键字，可采用如常人交流的口吻提问：

1. **查教师课表**
   - _“李圣炎老师这学期教几门课？”_
   - _“他周三上午有课吗？”_（上下文追问）
2. **查教室资源**
   - _“帮我查一下主校区有哪些容量超过100人的空闲教室？”_
   - _“理科楼有带多媒体设施的房间吗？”_
3. **查排课情况与草稿方案**
   - _“目前计算机专业的排课结果出了吗？”_
   - _“查一下目前未确定的草稿版本的排课表里，高数安排在周几？”_

### 3.3 注意事项

- 本助手为**单纯的数据检索类助手**，不具备“帮我排一节课”、“把张老师的课调到周五”等修改数据库的权限。如发送修改指令，助手会自动拒绝。
- 若助手回答“抱歉，由于安全限制，我无法执行该查询请求”，通常是因为触发了关键字防注入系统；如果提示“查询发生错误”，可能是您的表述方式让模型生成的底层查询过于复杂而超时，建议换种简单直接的问法。

---

## 4. 网站内嵌开发说明书

本节面向**前端/全栈开发人员**，说明如何将此智能助手以“组件”形式集成至您的既有教务门户网站中。

### 4.1 部署架构概述

- **服务端（FastAPI 后端）**：接收并处理请求、调用大模型与 MySQL 数据库交互。默认暴露在 `127.0.0.1:8000`（或您的服务器域名）。
- **前端集成**：在现有的门户系统前端（如 Vue / React / 原生 JS 页面），加入一个悬浮挂件，通过 Ajax/Fetch 请求后端的 RESTful API。

### 4.2 API 接口协议

- **请求路径**：`POST http://<你的服务器IP>:8000/chat`
- **Content-Type**：`application/json`
- **接受参数 (Request Body)**：

  ```json
  {
    "session_id": "用户唯一标识符或随机生成的对话ID",
    "message": "用户在输入框打的字"
  }
  ```

  _(注：`session_id` 必须由前端传入并保持在一整个聊天生命周期内不变，否则后端无法关联历史对话。如果用户刷新页面想重新开始对话，前端重新生成一个 session_id 即可。)_

- **返回参数 (Response Body)**：
  ```json
  {
    "session_id": "该对话绑定的ID",
    "reply": "助手回复的文本内容，前端直接渲染到对话框里",
    "requires_sql": true // 仅作调试参考：表示这轮对话是否触发了数据库查询
  }
  ```

### 4.3 前端集成代码规范示例 (Vanilla JS & HTML)

在前端系统底层新建一个公用组件，关键交互示例如下：

```html
<!-- 这是一个示例聊天小程序的骨架，具体样式请由贵司 UI 进行调整 -->
<div id="ai-chatbot-widget">
  <div class="chat-messages" id="chat-box"></div>
  <div class="chat-input">
    <input type="text" id="chat-input-field" />
    <button onclick="sendMessage()">发送</button>
  </div>
</div>

<script>
  // 1. 初始化对话 session ID (存在内在中或 session_storage 中)
  const sessionId = "session_" + Math.random().toString(36).substr(2, 9);

  async function sendMessage() {
    const inputField = document.getElementById("chat-input-field");
    const msg = inputField.value;
    if (!msg) return;

    // 2. 清空输入框，把用户的字挂载到屏幕上
    //    (此处省略渲染逻辑代码...)

    // 3. 开始调用你的后端接口
    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: msg,
        }),
      });
      const result = await response.json();

      // 4. 将 result.reply 以机器人的样式挂载到屏幕上
      //    (此处省略渲染逻辑代码...)
    } catch (error) {
      console.error("请求失败: ", error);
    }
  }
</script>
```

### 4.4 针对后端的额外配置核验

当你们把应用部署于生产环境之后，请务必核验 FastAPI 后端的 `CORS（跨域资源共享）` 配置是否正常运作。在 `main.py` 中已经内置了 CORS 支持：

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中为了安全，请把 "*" 改为你们真实的门户网站域名，如 "https://jw.school.edu.cn"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
