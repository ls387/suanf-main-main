# -*- coding: utf-8 -*-
"""
排课调度路由
"""
from fastapi import APIRouter, Depends
from app.config import settings
from app.schemas.scheduling import SchedulingRequest, SchedulingResponse
from app.services.algorithm import SchedulingService

router = APIRouter()


@router.post("/run", response_model=SchedulingResponse)
async def run_scheduling(request: SchedulingRequest):
    """运行排课算法"""
    # 构建数据库配置
    db_config = {
        "host": settings.DB_HOST,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "database": settings.DB_NAME,
        "charset": settings.DB_CHARSET,
    }
    
    # 构建遗传算法配置
    ga_config = {
        "population_size": request.population,
        "generations": request.generations,
        "crossover_rate": request.crossover_rate,
        "mutation_rate": request.mutation_rate,
        "tournament_size": request.tournament_size,
        "elitism_size": request.elitism_size,
        "max_stagnation": request.max_stagnation,
    }
    
    # 创建排课服务并运行
    service = SchedulingService(db_config)
    result = service.run_scheduling(request.version_id, ga_config)
    
    return SchedulingResponse(**result)

