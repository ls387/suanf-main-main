# db_config.py（根目录新建）
# -*- coding: utf-8 -*-
"""
数据库配置管理模块（用于根目录脚本）
"""
import os
from typing import Dict


def get_db_config() -> Dict[str, any]:
    """
    获取数据库配置

    从环境变量读取配置，如果未设置则使用默认值

    Returns:
        Dict: 包含数据库连接参数的字典
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "pk"),
        "password": os.getenv("DB_PASSWORD", "123456"),
        "database": os.getenv("DB_NAME", "paike"),
        "charset": "utf8mb4",
    }


if __name__ == "__main__":
    config = get_db_config()
    print("数据库配置:")
    # 隐藏密码
    safe_config = {k: ("****" if k == "password" else v) for k, v in config.items()}
    for key, value in safe_config.items():
        print(f"  {key}: {value}")
