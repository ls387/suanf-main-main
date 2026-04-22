# -*- coding: utf-8 -*-
"""
LLM 调用（OpenAI 兼容接口，当前用阿里云 qwen-max）
（从 neiqian-agent/llm.py 迁移，改用 app.config.settings）
"""
import json
from typing import AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings
from app.services.chat.prompts import get_system_prompt

client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)


async def call_llm(messages: list) -> str:
    """首次调用：生成对话回复，或生成 <sql>...</sql> 语句"""
    system_prompt = get_system_prompt()
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=0.1,
    )
    return response.choices[0].message.content


async def call_llm_with_sql_result(
    messages: list, sql: str, sql_result: list | dict | str
) -> str:
    """SQL 执行完成后，将结果交给 LLM 转成自然语言回复"""
    result_context = (
        f"你在上一步决定查询数据库，执行的 SQL 为：\n{sql}\n\n"
        f"数据库返回的查询结果为：\n{json.dumps(sql_result, ensure_ascii=False, default=str)}\n\n"
        f"请根据上述查询结果，结合之前的对话历史，直接用自然语言回答用户刚刚的问题。"
        f"如果查询结果为空，请如实告知未找到相关信息。"
        f"要求：回答应友好、亲切，切勿暴露底层使用的 SQL。"
    )

    temp_messages = messages.copy()
    temp_messages.append({"role": "system", "content": result_context})

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=temp_messages,
        temperature=0.5,
    )
    return response.choices[0].message.content


async def stream_llm_first(messages: list) -> AsyncGenerator[str, None]:
    """流式首次调用：逐 token yield，调用方负责收集完整文本以提取 SQL"""
    system_prompt = get_system_prompt()
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    stream = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=0.1,
        stream=True,
    )
    async for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


async def stream_llm_with_sql_result(
    messages: list, sql: str, sql_result: list | dict | str
) -> AsyncGenerator[str, None]:
    """SQL 结果已知后，流式生成最终自然语言回复"""
    result_context = (
        f"你在上一步决定查询数据库，执行的 SQL 为：\n{sql}\n\n"
        f"数据库返回的查询结果为：\n{json.dumps(sql_result, ensure_ascii=False, default=str)}\n\n"
        f"请根据上述查询结果，结合之前的对话历史，直接用自然语言回答用户刚刚的问题。"
        f"如果查询结果为空，请如实告知未找到相关信息。"
        f"要求：回答应友好、亲切，切勿暴露底层使用的 SQL。"
    )

    temp_messages = messages.copy()
    temp_messages.append({"role": "system", "content": result_context})

    stream = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=temp_messages,
        temperature=0.5,
        stream=True,
    )
    async for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token
