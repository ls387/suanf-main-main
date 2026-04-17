import aiomysql
from typing import List, Dict, Any, Optional
from config import config
import asyncio


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            db=config.DB_NAME,
            autocommit=True,
            charset="utf8mb4",
            cursorclass=aiomysql.DictCursor,
        )

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute_query(self, query: str) -> Optional[List[Dict[str, Any]]]:
        if not self.pool:
            raise Exception("Database not connected")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 去除结尾分号避免拼接 LIMIT 报错
                query = query.strip()
                if query.endswith(";"):
                    query = query[:-1]

                # 限制返回行数，提升安全性
                if "limit " not in query.lower():
                    query = f"{query} LIMIT 100"

                # 使用 asyncio.wait_for 实现超时控制
                await asyncio.wait_for(cur.execute(query), timeout=config.SQL_TIMEOUT)
                result = await cur.fetchall()
                return result


db = Database()
