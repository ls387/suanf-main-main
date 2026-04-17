# -*- coding: utf-8 -*-
"""
排课相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict


class PenaltyScores(BaseModel):
    """约束权重配置（所有字段均可选，未传的使用算法默认值）"""
    # 硬约束罚分（负数，绝对值越大越严格）
    teacher_conflict: Optional[int] = Field(None, description="教师时间冲突罚分，默认 -50000")
    class_conflict: Optional[int] = Field(None, description="班级时间冲突罚分，默认 -80000（最高优先）")
    classroom_conflict: Optional[int] = Field(None, description="教室时间冲突罚分，默认 -50000")
    capacity_violation: Optional[int] = Field(None, description="教室容量不足罚分，默认 -60000")
    blackout_violation: Optional[int] = Field(None, description="教师禁用时段罚分，默认 -8000")
    feature_violation: Optional[int] = Field(None, description="设施不满足罚分，默认 -8000")
    thursday_afternoon: Optional[int] = Field(None, description="周四下午排课罚分，默认 -3000")
    campus_commute: Optional[int] = Field(None, description="教师跨校区通勤罚分，默认 -5000")
    weekend_penalty: Optional[int] = Field(None, description="周末排课罚分，默认 -10000")
    # 软约束强度（正数，越大越严格）
    teacher_preference: Optional[int] = Field(None, description="未满足教师偏好扣分强度，默认 100")
    classroom_continuity: Optional[int] = Field(None, description="连续课不同教室扣分强度，默认 300")
    utilization_waste: Optional[int] = Field(None, description="教室容量浪费扣分强度，默认 200")
    daily_classroom_variety: Optional[int] = Field(None, description="同天多教室扣分强度，默认 300")
    student_overload: Optional[int] = Field(None, description="学生课程过载扣分强度，默认 150")
    task_relation: Optional[int] = Field(None, description="课程关系违反扣分强度，默认 300")
    required_night_penalty: Optional[int] = Field(None, description="必修课安排晚上扣分强度，默认 400")
    required_weekend_penalty: Optional[int] = Field(None, description="必修课安排周末扣分强度，默认 300")
    elective_prime_time_penalty: Optional[int] = Field(None, description="选修课占黄金时段扣分强度，默认 30")


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
    penalty_scores: Optional[PenaltyScores] = Field(
        None, description="约束权重（可选，不传则全部使用算法默认值）"
    )


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
    average_utilization_rate: Optional[float] = Field(
        None, description="平均容量利用率(%)"
    )
    classroom_reuse_rate: Optional[float] = Field(None, description="教室复用率(0-100)")


class SchedulingJobResponse(BaseModel):
    """POST /run 立即返回的响应（异步模式）"""

    version_id: int = Field(..., description="排课版本ID")
    status: str = Field(..., description="任务状态: running / failed")
    message: str = Field(..., description="描述信息")


class ProgressEvent(BaseModel):
    """WebSocket 推送的进度事件格式（供文档参考，不作为响应模型使用）"""

    version_id: int = Field(..., description="排课版本ID")
    stage: str = Field(..., description="阶段: init / evolving / done / error")
    status: str = Field(..., description="running / completed / failed")
    percent: int = Field(..., ge=0, le=100, description="整体进度 0-100")
    generation: int = Field(0, description="当前代数")
    total_generations: int = Field(0, description="总代数")
    best_fitness: float = Field(0.0, description="当前最佳适应度")
    message: str = Field("", description="可读状态描述")
    # 完成时附带结果摘要（stage=done 时填充）
    result: Optional[Dict] = Field(None, description="排课结果摘要（完成后）")
