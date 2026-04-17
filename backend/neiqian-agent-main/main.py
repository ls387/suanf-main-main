from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import traceback

from config import config
from database import db
from session import get_or_create_session, get_session_history, add_message_to_session
from utils import extract_sql, is_safe_sql
from llm import call_llm, call_llm_with_sql_result


from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时初始化数据库连接
    try:
        await db.connect()
        print("Database connected successfully.")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
    # 提供应用上下文
    yield
    # 应用关闭时断开数据库连接
    await db.disconnect()
    print("Database disconnected.")


app = FastAPI(title="高校教务智能问答助手", lifespan=lifespan)

# 允许跨域（前端 HTML 页面可能是在别的端口或者由浏览器直接双击打开）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str = ""
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    requires_sql: bool = False


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. 获取或创建会话
        session_id = get_or_create_session(request.session_id)

        # 2. 保存用户消息
        add_message_to_session(session_id, "user", request.message)

        # 3. 提取带有历史的多轮回答
        history = get_session_history(session_id)

        # 4. 首次调用 LLM（如果需要查询，会生成 <sql>...<sql>，否则生成直接回复）
        llm_reply = await call_llm(history)

        # 5. 分析是否生成了 SQL 标签
        sql = extract_sql(llm_reply)

        if sql:
            # 安全性检查：仅支持 SELECT 语法，且无危险关键字
            if not is_safe_sql(sql):
                final_reply = "抱歉，由于安全限制，我无法执行该查询请求。"
            else:
                try:
                    # 执行 SQL
                    sql_result = await db.execute_query(sql)

                    # 再次调用 LLM 来将查询到的结构化数据转为自然语言回复
                    final_reply = await call_llm_with_sql_result(
                        history, sql, sql_result
                    )

                except Exception as db_err:
                    print(
                        f"Database explicit error executing SQL: {sql}\n{traceback.format_exc()}"
                    )
                    final_reply = "数据库查询过程中发生错误，可能由于 SQL 语法或超时导致，请稍后再试或换个问法。"
        else:
            # LLM 没有生成 SQL，说明在反问或回答非数据库范畴的话题
            final_reply = llm_reply

        # 6. 保存助手最终回复到会话记录
        add_message_to_session(session_id, "assistant", final_reply)

        return ChatResponse(
            session_id=session_id, reply=final_reply, requires_sql=bool(sql)
        )

    except Exception as e:
        print(f"Unexpected application error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    import uvicorn

    # 本地开发服务器启动
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
