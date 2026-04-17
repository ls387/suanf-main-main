from openai import AsyncOpenAI
import json
from config import config
from prompts import get_system_prompt

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)


async def call_llm(messages: list) -> str:
    """第一次调用，生成对话回复或生成 <sql> 语句"""
    system_prompt = get_system_prompt()
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=full_messages,
        temperature=0.1,  # 较低的准确度，有助于稳定生成 SQL 或者反问
    )

    return response.choices[0].message.content


async def call_llm_with_sql_result(
    messages: list, sql: str, sql_result: list | dict | str
) -> str:
    """当 SQL 执行完成后，将结果交给 LLM 生成易读的自然语言总结"""
    # 构建结果的系统提升语
    result_context = (
        f"你在上一步决定查询数据库，执行的 SQL 为：\n{sql}\n\n"
        f"数据库返回的查询结果为：\n{json.dumps(sql_result, ensure_ascii=False, default=str)}\n\n"
        f"请根据上述查询结果，结合之前的对话历史，直接用自然语言回答用户刚刚的问题。"
        f"如果查询结果为空，请如实告知未找到相关信息。"
        f"要求：回答应友好、亲切，切勿暴露底层使用的 SQL。"
    )

    # 重新拼接消息给大模型做最后一代（这属于一次独立的分支调用）
    temp_messages = messages.copy()
    temp_messages.append({"role": "system", "content": result_context})

    response = await client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=temp_messages,
        temperature=0.5,
    )

    return response.choices[0].message.content
