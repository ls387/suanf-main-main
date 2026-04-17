import re
from datetime import datetime


def get_current_time_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_term() -> str:
    # 动态计算当前学期的简单逻辑
    # 假设 2-7 月是春季学期（-2），8-1 月是秋季学期（-1）
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

    # 必须以 SELECT 开头
    if not sql_upper.startswith("SELECT"):
        return False

    # 禁止潜在的危险关键字或函数
    dangerous_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "SLEEP",
        "BENCHMARK",
        "INTO",
    ]

    for keyword in dangerous_keywords:
        # 使用正则匹配独立单词，防止匹配到类似 "SELECTION" 这样的合法词段
        if re.search(r"\b" + keyword + r"\b", sql_upper):
            return False

    return True
