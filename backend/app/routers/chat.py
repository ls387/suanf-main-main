# -*- coding: utf-8 -*-
"""
AI 助手聊天路由

POST /api/chat    多轮对话入口
"""
import traceback
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat.session import (
    get_or_create_session,
    get_session_history,
    add_message_to_session,
)
from app.services.chat.utils import extract_sql, is_safe_sql
from app.services.chat.llm import call_llm, call_llm_with_sql_result
from app.services.chat.chat_db import chat_db

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = ""
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    requires_sql: bool = False


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    AI 教务助手多轮对话接口。

    - 发送 message，可选传 session_id（为空则自动创建新会话）
    - 返回 reply（自然语言回答）和 session_id（前端需保存以维持多轮上下文）
    """
    try:
        # 1. 获取或创建会话
        session_id = get_or_create_session(request.session_id)

        # 2. 保存用户消息
        add_message_to_session(session_id, "user", request.message)

        # 3. 读取带历史的消息列表
        history = get_session_history(session_id)

        # 4. 首次调用 LLM（生成直接回复，或生成 <sql>...</sql>）
        llm_reply = await call_llm(history)

        # 5. 提取 SQL（如果有）
        sql = extract_sql(llm_reply)
        final_reply: str

        if sql:
            if not is_safe_sql(sql):
                final_reply = "抱歉，由于安全限制，我无法执行该查询请求。"
            else:
                try:
                    sql_result = await chat_db.execute_query(sql)
                    final_reply = await call_llm_with_sql_result(history, sql, sql_result)
                except Exception:
                    logger.error(f"SQL 执行失败: {sql}\n{traceback.format_exc()}")
                    final_reply = "数据库查询过程中发生错误，可能由于 SQL 语法或超时导致，请稍后再试或换个问法。"
        else:
            final_reply = llm_reply

        # 6. 保存助手回复
        add_message_to_session(session_id, "assistant", final_reply)

        return ChatResponse(
            session_id=session_id,
            reply=final_reply,
            requires_sql=bool(sql),
        )

    except Exception:
        logger.error(f"chat_endpoint 未预期异常:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="AI 助手服务异常，请稍后重试")
