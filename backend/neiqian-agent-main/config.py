import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "edu_db")

    OPENAI_API_KEY = os.getenv("LLM_API_KEY", "your-api-key")
    OPENAI_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

    MAX_SESSION_HISTORY = int(os.getenv("MAX_SESSION_HISTORY", 5))
    SQL_TIMEOUT = int(os.getenv("SQL_TIMEOUT", 10))


config = Config()
