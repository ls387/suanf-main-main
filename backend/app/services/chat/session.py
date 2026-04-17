# -*- coding: utf-8 -*-
"""
多轮对话会话管理（内存存储）
（从 neiqian-agent/session.py 迁移，改用 app.config.settings）
"""
import uuid
from typing import List, Dict
from app.config import settings

# 简单内存会话存储（生产环境建议使用 Redis）
sessions: Dict[str, List[Dict[str, str]]] = {}


def get_or_create_session(session_id: str) -> str:
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    return session_id


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    return sessions.get(session_id, [])


def add_message_to_session(session_id: str, role: str, content: str):
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append({"role": role, "content": content})

    # 保持最近 N 轮对话（一问一答算一轮 = 2 条消息）
    max_msgs = settings.MAX_SESSION_HISTORY * 2
    if len(sessions[session_id]) > max_msgs:
        sessions[session_id] = sessions[session_id][-max_msgs:]
