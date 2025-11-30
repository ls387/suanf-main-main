# -*- coding: utf-8 -*-
"""
课程相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CourseBase(BaseModel):
    """课程基础模型"""
    course_id: str = Field(..., description="课程编号")
    course_name: str = Field(..., description="课程名称")
    credits: float = Field(..., description="学分")
    total_hours: int = Field(..., description="总学时")
    notes: Optional[str] = Field(None, description="备注")


class CourseCreate(CourseBase):
    """创建课程"""
    pass


class CourseUpdate(BaseModel):
    """更新课程"""
    course_name: Optional[str] = None
    credits: Optional[float] = None
    total_hours: Optional[int] = None
    notes: Optional[str] = None


class Course(CourseBase):
    """课程完整信息"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

