# -*- coding: utf-8 -*-
"""
教室相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ClassroomBase(BaseModel):
    """教室基础模型"""
    classroom_id: str = Field(..., description="教室编号")
    classroom_name: Optional[str] = Field(None, description="教室名称")
    building_name: Optional[str] = Field(None, description="教学楼名称")
    campus_id: str = Field(..., description="所在校区")
    classroom_type: Optional[str] = Field(None, description="教室类型")
    capacity: int = Field(..., description="最大容纳人数")
    is_available: bool = Field(True, description="是否可用")


class ClassroomCreate(ClassroomBase):
    """创建教室"""
    features: Optional[List[str]] = Field([], description="设施特征ID列表")


class ClassroomUpdate(BaseModel):
    """更新教室"""
    classroom_name: Optional[str] = None
    building_name: Optional[str] = None
    campus_id: Optional[str] = None
    classroom_type: Optional[str] = None
    capacity: Optional[int] = None
    is_available: Optional[bool] = None
    features: Optional[List[str]] = None


class Classroom(ClassroomBase):
    """教室完整信息"""
    features: List[str] = Field([], description="设施特征ID列表")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

