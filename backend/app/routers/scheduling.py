# -*- coding: utf-8 -*-
"""
排课调度路由

端点：
  POST /api/scheduling/run            提交排课任务（立即返回，后台运行）
  WS   /api/scheduling/ws/{version_id} WebSocket 进度订阅
  GET  /api/scheduling/status/{version_id} 查询当前状态（HTTP 轮询降级）
"""
import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.config import settings
from app.schemas.scheduling import (
    SchedulingRequest,
    SchedulingResponse,
    SchedulingJobResponse,
)
from app.services.algorithm import SchedulingService
from app.core.ws_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_db_config() -> dict:
    return {
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "database": settings.DB_NAME,
        "charset": settings.DB_CHARSET,
    }


def _build_ga_config(request: SchedulingRequest) -> dict:
    config = {
        "population_size": request.population,
        "generations": request.generations,
        "crossover_rate": request.crossover_rate,
        "mutation_rate": request.mutation_rate,
        "tournament_size": request.tournament_size,
        "elitism_size": request.elitism_size,
        "max_stagnation": request.max_stagnation,
    }
    if request.penalty_scores:
        # 过滤掉 None 值，只传用户明确设置的权重（算法层做深合并）
        ps = {k: v for k, v in request.penalty_scores.model_dump().items() if v is not None}
        if ps:
            config["penalty_scores"] = ps
    return config


async def _run_scheduling_background(
    version_id: int,
    ga_config: dict,
    db_config: dict,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """
    后台任务：在线程池中运行排课算法，通过 ws_manager 推送进度。
    整个函数在 asyncio 协程中运行，算法本身被丢进 run_in_executor。
    """
    service = SchedulingService(db_config)

    # 构造线程安全进度回调：在 worker 线程里调用，消息回到主循环推送给 WS
    progress_callback = manager.make_thread_safe_callback(version_id, loop)

    try:
        result = await service.run_scheduling_async(
            version_id, ga_config, progress_callback
        )

        if result.get("success"):
            # 推送完成消息（包含结果摘要）
            await manager.send_progress(version_id, {
                "version_id": version_id,
                "stage": "done",
                "status": "completed",
                "percent": 100,
                "generation": ga_config.get("generations", 0),
                "total_generations": ga_config.get("generations", 0),
                "best_fitness": result.get("best_fitness", 0.0),
                "message": "排课完成",
                "result": {
                    "coverage_rate": result.get("coverage_rate"),
                    "total_tasks": result.get("total_tasks"),
                    "scheduled_tasks": result.get("scheduled_tasks"),
                    "execution_time": result.get("execution_time"),
                    "conflicts": result.get("conflicts"),
                    "average_utilization_rate": result.get("average_utilization_rate"),
                    "classroom_reuse_rate": result.get("classroom_reuse_rate"),
                },
            })
        else:
            await manager.send_error(version_id, result.get("message", "排课失败"))

    except Exception as e:
        logger.error(f"后台排课任务异常 version_id={version_id}: {e}", exc_info=True)
        await manager.send_error(version_id, f"排课异常: {str(e)}")


# ---------------------------------------------------------------------------
# 端点 1：提交排课任务（立即返回）
# ---------------------------------------------------------------------------

@router.post("/run", response_model=SchedulingJobResponse)
async def run_scheduling(request: SchedulingRequest):
    """
    提交排课任务。

    立即返回 version_id + status=running，排课在后台异步执行。
    进度通过 WS /api/scheduling/ws/{version_id} 推送。
    """
    db_config = _build_db_config()
    ga_config = _build_ga_config(request)
    version_id = request.version_id
    loop = asyncio.get_event_loop()

    # 启动后台协程（不等待完成）
    asyncio.create_task(
        _run_scheduling_background(version_id, ga_config, db_config, loop)
    )

    logger.info(f"排课任务已启动，version_id={version_id}")
    return SchedulingJobResponse(
        version_id=version_id,
        status="running",
        message=f"排课已启动，请连接 WS /api/scheduling/ws/{version_id} 订阅进度",
    )


# ---------------------------------------------------------------------------
# 端点 2：WebSocket 进度订阅
# ---------------------------------------------------------------------------

@router.websocket("/ws/{version_id}")
async def ws_progress(version_id: int, ws: WebSocket):
    """
    WebSocket 进度订阅。

    客户端连接后接收实时进度推送。
    客户端可定期发送任意文本（如 "ping"）作为心跳，服务端不做响应。
    排课完成后服务端推送 stage=done，客户端可自行关闭连接。
    """
    await manager.connect(version_id, ws)
    try:
        while True:
            # 阻塞等待客户端消息（心跳 ping），维持连接
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(version_id)


# ---------------------------------------------------------------------------
# 端点 3：HTTP 轮询降级（重连后查询状态）
# ---------------------------------------------------------------------------

@router.get("/status/{version_id}")
async def get_scheduling_status(version_id: int):
    """
    查询排课版本当前状态。

    供前端在 WebSocket 断线后重连前先查询状态，
    判断任务是否仍在运行，决定是否重连 WS。
    """
    from app.database import get_db

    db = get_db()
    rows = db.execute_query(
        "SELECT version_id, status, semester, description, created_at "
        "FROM schedule_versions WHERE version_id = %s",
        (version_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"版本 {version_id} 不存在")

    row = rows[0]

    # 是否有活跃 WS 连接
    is_connected = version_id in manager._connections

    return {
        "version_id": row["version_id"],
        "status": row["status"],
        "semester": row["semester"],
        "description": row.get("description"),
        "created_at": str(row.get("created_at", "")),
        "ws_connected": is_connected,
    }
