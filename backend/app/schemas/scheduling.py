# -*- coding: utf-8 -*-
"""
排课相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class SchedulingRequest(BaseModel):
    """排课请求"""
    version_id: int = Field(..., description="排课版本ID")
    population: int = Field(100, ge=10, le=500, description="种群大小")
    generations: int = Field(200, ge=10, le=1000, description="进化代数")
    crossover_rate: float = Field(0.8, ge=0.0, le=1.0, description="交叉率")
    mutation_rate: float = Field(0.1, ge=0.0, le=1.0, description="变异率")
    tournament_size: int = Field(5, ge=2, le=20, description="锦标赛大小")
    elitism_size: int = Field(10, ge=1, le=50, description="精英个体数量")
    max_stagnation: int = Field(50, ge=10, le=200, description="最大停滞代数")


class SchedulingResponse(BaseModel):
    """排课响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    best_fitness: Optional[float] = Field(None, description="最佳适应度")
    coverage_rate: Optional[float] = Field(None, description="排课覆盖率(%)")
    total_tasks: Optional[int] = Field(None, description="总任务数")
    scheduled_tasks: Optional[int] = Field(None, description="已排课任务数")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")
    conflicts: Optional[dict] = Field(None, description="冲突统计")

