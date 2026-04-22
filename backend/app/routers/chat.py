# -*- coding: utf-8 -*-
"""
AI 助手聊天路由

POST /api/chat                  多轮对话入口（非流式）
POST /api/chat/stream           多轮对话入口（SSE 流式）
GET  /api/chat/blackout-excel   下载已生成的黑名单 Excel
"""
import json
import traceback
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from app.services.chat.session import (
    get_or_create_session,
    get_session_history,
    add_message_to_session,
)
from app.services.chat.utils import extract_sql, is_safe_sql
from app.services.chat.llm import (
    call_llm,
    call_llm_with_sql_result,
    stream_llm_first,
    stream_llm_with_sql_result,
)
from app.services.chat.chat_db import chat_db
from app.services.chat.blackout_collector import (
    is_blackout_intent,
    get_blackout_session,
    process_blackout_turn,
    pop_excel,
)

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


@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    AI 教务助手流式对话接口（SSE）。

    事件类型：
      session        首条，告知 session_id
      token          逐字输出
      replace_start  清空气泡，进入第二阶段（SQL 结果翻译）
      replace        整段替换气泡内容
      download_excel Excel 已生成，携带 excel_key 供前端下载
      done           结束
      error          出错
    """
    session_id = get_or_create_session(request.session_id)
    add_message_to_session(session_id, "user", request.message)

    async def event_stream():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        full_reply = ""
        try:
            # ── 黑名单收集模式 ──────────────────────────────────────────────
            # 如果当前 session 已处于黑名单收集流程，或本轮触发了意图，走状态机
            in_blackout = get_blackout_session(session_id) is not None
            if in_blackout or is_blackout_intent(request.message):
                result = process_blackout_turn(session_id, request.message)
                full_reply = result["reply"]
                # 逐字符模拟流式（体验一致）
                for ch in full_reply:
                    yield f"data: {json.dumps({'type': 'token', 'content': ch}, ensure_ascii=False)}\n\n"
                if result.get("excel_key"):
                    yield f"data: {json.dumps({'type': 'download_excel', 'excel_key': result['excel_key']}, ensure_ascii=False)}\n\n"
                add_message_to_session(session_id, "assistant", full_reply)
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                return

            # ── 普通 Text-to-SQL 模式 ───────────────────────────────────────
            history = get_session_history(session_id)

            async for token in stream_llm_first(history):
                full_reply += token
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

            sql = extract_sql(full_reply)

            if sql:
                if not is_safe_sql(sql):
                    final_text = "抱歉，由于安全限制，我无法执行该查询请求。"
                    yield f"data: {json.dumps({'type': 'replace', 'content': final_text}, ensure_ascii=False)}\n\n"
                    full_reply = final_text
                else:
                    try:
                        sql_result = await chat_db.execute_query(sql)
                        yield f"data: {json.dumps({'type': 'replace_start'}, ensure_ascii=False)}\n\n"
                        full_reply = ""
                        async for token in stream_llm_with_sql_result(history, sql, sql_result):
                            full_reply += token
                            yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                    except Exception:
                        logger.error(f"SQL 执行失败: {sql}\n{traceback.format_exc()}")
                        final_text = "数据库查询过程中发生错误，请稍后再试或换个问法。"
                        yield f"data: {json.dumps({'type': 'replace', 'content': final_text}, ensure_ascii=False)}\n\n"
                        full_reply = final_text

            add_message_to_session(session_id, "assistant", full_reply)
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

        except Exception:
            logger.error(f"chat_stream_endpoint 异常:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'AI 助手服务异常，请稍后重试'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/blackout-excel")
async def download_blackout_excel(key: str):
    """凭 excel_key 下载黑名单 Excel 文件（一次性，下载后 key 失效）。"""
    data = pop_excel(key)
    if data is None:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=\"blackout_times.xlsx\""},
    )
