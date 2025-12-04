# -*- coding: utf-8 -*-
"""
配置管理模块
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_USER: str = "pk"
    # 你的 MySQL 密码，当前统一改为 pk，如需修改请同步改动其它脚本
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "paike"
    DB_CHARSET: str = "utf8mb4"

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
