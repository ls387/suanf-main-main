# -*- coding: utf-8 -*-
"""
数据库连接管理模块
"""
import pymysql
from typing import Optional, Dict, List
import logging
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """数据库连接管理器"""

    def __init__(self):
        self.connection_config = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "database": settings.DB_NAME,
            "charset": settings.DB_CHARSET,
            "cursorclass": pymysql.cursors.DictCursor,
        }
        self._connection: Optional[pymysql.Connection] = None

    def connect(self):
        """建立数据库连接"""
        try:
            self._connection = pymysql.connect(**self.connection_config)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def disconnect(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            logger.info("数据库连接已关闭")

    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        if not self._connection or not self._connection.open:
            self.connect()

        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询语句"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """执行插入语句，返回插入的 ID"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新语句，返回影响的行数"""
        with self.get_cursor() as cursor:
            affected_rows = cursor.execute(query, params)
            return affected_rows

    def execute_delete(self, query: str, params: tuple = None) -> int:
        """执行删除语句，返回影响的行数"""
        with self.get_cursor() as cursor:
            affected_rows = cursor.execute(query, params)
            return affected_rows


# 全局数据库实例
db = Database()


def get_db() -> Database:
    """获取数据库实例（用于依赖注入）"""
    return db
