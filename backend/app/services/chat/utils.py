# -*- coding: utf-8 -*-
"""
工具函数：时间、学期推断、SQL 提取与安全检查
（从 neiqian-agent/utils.py 迁移，无外部依赖）
"""
import re
from datetime import datetime


def get_current_time_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_term() -> str:
    now = datetime.now()
    year = now.year
    month = now.month
    if 2 <= month <= 7:
        return f"{year-1}-{year}-2"
    elif month >= 8:
        return f"{year}-{year+1}-1"
    else:
        return f"{year-1}-{year}-1"


def extract_sql(text: str) -> str | None:
    match = re.search(r"<sql>\s*(.*?)\s*</sql>", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return False
    dangerous_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "SLEEP", "BENCHMARK", "INTO",
    ]
    for keyword in dangerous_keywords:
        if re.search(r"\b" + keyword + r"\b", sql_upper):
            return False
    return True
