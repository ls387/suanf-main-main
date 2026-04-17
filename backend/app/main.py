# -*- coding: utf-8 -*-
"""
FastAPI 主应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.routers import (
    teachers,
    courses,
    classes,
    classrooms,
    offerings,
    scheduling,
    timetables,
    versions,
    conflicts,
    chat,
)
from app.services.chat.chat_db import chat_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建立 AI 助手 DB 连接池，关闭时释放"""
    try:
        await chat_db.connect()
    except Exception as e:
        logger.warning(f"ChatDatabase 连接失败（AI 助手功能不可用）: {e}")
    yield
    await chat_db.disconnect()


# 创建 FastAPI 应用
app = FastAPI(
    title="智能排课系统 API",
    description="基于遗传算法的智能排课系统后端接口",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(teachers.router, prefix="/api/teachers", tags=["教师管理"])
app.include_router(courses.router, prefix="/api/courses", tags=["课程管理"])
app.include_router(classes.router, prefix="/api/classes", tags=["班级管理"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["教室管理"])
app.include_router(offerings.router, prefix="/api/offerings", tags=["开课计划"])
app.include_router(scheduling.router, prefix="/api/scheduling", tags=["排课调度"])
app.include_router(timetables.router, prefix="/api/timetable", tags=["课表查询"])
app.include_router(versions.router, prefix="/api/versions", tags=["版本管理"])
app.include_router(conflicts.router, prefix="/api/conflicts", tags=["冲突检测"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI 助手"])


@app.get("/")
async def pk():
    """根路径"""
    return {
        "message": "智能排课系统 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
