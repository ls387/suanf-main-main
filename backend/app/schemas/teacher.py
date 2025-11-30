# -*- coding: utf-8 -*-
"""
教师相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TeacherBase(BaseModel):
    """教师基础模型"""
    teacher_id: str = Field(..., description="教师编号")
    teacher_name: str = Field(..., description="教师名称")
    department_id: str = Field(..., description="所属院系ID")
    gender: Optional[str] = Field("未知", description="性别")
    is_external: bool = Field(False, description="是否外聘")


class TeacherCreate(TeacherBase):
    """创建教师"""
    pass


class TeacherUpdate(BaseModel):
    """更新教师"""
    teacher_name: Optional[str] = None
    department_id: Optional[str] = None
    gender: Optional[str] = None
    is_external: Optional[bool] = None


class Teacher(TeacherBase):
    """教师完整信息"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

