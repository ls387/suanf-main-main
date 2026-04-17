# -*- coding: utf-8 -*-
"""
WebSocket 连接管理器

按 version_id 维护 WebSocket 连接池，支持：
  - connect / disconnect
  - 从异步上下文向指定 version 推送进度消息
  - 跨线程安全推送（供 run_in_executor 的 worker 线程调用）

用法示例（路由层）：

    from app.core.ws_manager import manager

    # WebSocket 端点
    @router.websocket("/ws/{version_id}")
    async def ws_endpoint(version_id: int, ws: WebSocket):
        await manager.connect(version_id, ws)
        try:
            while True:
                await ws.receive_text()   # 保持连接，接收心跳 ping
        except WebSocketDisconnect:
            manager.disconnect(version_id)

    # 在后台任务中构造线程安全回调
    loop = asyncio.get_event_loop()
    def make_callback(version_id, loop):
        def callback(data: dict):
            # 此函数在 worker 线程中执行，不能直接 await
            asyncio.run_coroutine_threadsafe(
                manager.send_progress(version_id, data), loop
            )
        return callback
"""

import asyncio
import logging
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """按 version_id 管理 WebSocket 连接"""

    def __init__(self):
        # version_id -> WebSocket
        self._connections: Dict[int, WebSocket] = {}

    async def connect(self, version_id: int, ws: WebSocket) -> None:
        """接受连接并注册"""
        await ws.accept()
        self._connections[version_id] = ws
        logger.info(f"[WS] version_id={version_id} 已连接，当前连接数={len(self._connections)}")

    def disconnect(self, version_id: int) -> None:
        """注销连接（不 close，FastAPI 断开时调用）"""
        self._connections.pop(version_id, None)
        logger.info(f"[WS] version_id={version_id} 已断开，剩余连接数={len(self._connections)}")

    async def send_progress(self, version_id: int, data: dict) -> None:
        """向指定 version 推送进度数据（在 asyncio 事件循环内调用）"""
        ws = self._connections.get(version_id)
        if ws is None:
            return  # 客户端已断开，静默忽略
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.warning(f"[WS] version_id={version_id} 发送失败: {e}")
            self.disconnect(version_id)

    async def send_error(self, version_id: int, message: str) -> None:
        """推送错误消息"""
        await self.send_progress(version_id, {
            "stage": "error",
            "status": "failed",
            "percent": 0,
            "message": message,
        })

    def make_thread_safe_callback(self, version_id: int, loop: asyncio.AbstractEventLoop):
        """
        生成一个线程安全的进度回调函数。

        在 run_in_executor 的 worker 线程里调用此回调，
        它会用 run_coroutine_threadsafe 把消息调度回主事件循环。

        Args:
            version_id: 目标版本
            loop: 主 asyncio 事件循环（在路由层用 asyncio.get_event_loop() 获取）

        Returns:
            callable: 接受一个 dict 参数的同步函数
        """
        manager = self

        def callback(data: dict) -> None:
            # 给前端格式加上 version_id，方便前端路由
            payload = {"version_id": version_id, **data}
            asyncio.run_coroutine_threadsafe(
                manager.send_progress(version_id, payload), loop
            )

        return callback


# 全局单例，整个应用共享
manager = ConnectionManager()
