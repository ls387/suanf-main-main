# -*- coding: utf-8 -*-
"""
AI 助手专用 aiomysql 异步连接池
（从 neiqian-agent/database.py 迁移，改用 app.config.settings）
"""
import asyncio
import aiomysql
from typing import List, Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ChatDatabase:
    """AI 助手专用异步 MySQL 连接池（只做 SELECT 查询）"""

    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
            autocommit=True,
            charset="utf8mb4",
            cursorclass=aiomysql.DictCursor,
            minsize=1,
            maxsize=5,
        )
        logger.info("ChatDatabase (aiomysql) 连接池已建立")

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("ChatDatabase (aiomysql) 连接池已关闭")

    async def execute_query(self, query: str) -> Optional[List[Dict[str, Any]]]:
        if not self.pool:
            raise RuntimeError("ChatDatabase 未连接，请先调用 connect()")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 去除尾部分号，避免拼接 LIMIT 时出错
                query = query.strip().rstrip(";")

                # 未指定 LIMIT 时默认加 LIMIT 100，防止返回过多数据
                if "limit " not in query.lower():
                    query = f"{query} LIMIT 100"

                await asyncio.wait_for(
                    cur.execute(query),
                    timeout=settings.SQL_TIMEOUT,
                )
                return await cur.fetchall()


# 全局单例，由 main.py lifespan 管理生命周期
chat_db = ChatDatabase()
