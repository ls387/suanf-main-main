# -*- coding: utf-8 -*-
"""
班级相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClassBase(BaseModel):
    """班级基础模型"""
    class_id: str = Field(..., description="行政班编号")
    class_name: str = Field(..., description="行政班名称")
    grade: int = Field(..., description="年级")
    student_count: Optional[int] = Field(None, description="班级人数")
    major_id: str = Field(..., description="专业编号")
    education_system: Optional[int] = Field(None, description="学制")


class ClassCreate(ClassBase):
    """创建班级"""
    pass


class ClassUpdate(BaseModel):
    """更新班级"""
    class_name: Optional[str] = None
    grade: Optional[int] = None
    student_count: Optional[int] = None
    major_id: Optional[str] = None
    education_system: Optional[int] = None


class Class(ClassBase):
    """班级完整信息"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

