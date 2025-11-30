# -*- coding: utf-8 -*-
"""
课表相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class TimetableEntry(BaseModel):
    """课表条目"""
    weekday: int = Field(..., description="星期几(1-7)")
    start_slot: int = Field(..., description="开始节次(1-13)")
    end_slot: int = Field(..., description="结束节次(1-13)")
    course_id: str = Field(..., description="课程编号")
    course_name: str = Field(..., description="课程名称")
    teacher_id: str = Field(..., description="教师ID")
    teacher_name: str = Field(..., description="教师名称")
    classroom_id: str = Field(..., description="教室ID")
    classroom_name: str = Field(..., description="教室名称")
    building_name: Optional[str] = Field(None, description="教学楼名称")
    campus_id: str = Field(..., description="校区ID")
    classes: List[str] = Field([], description="上课班级列表")
    
    class Config:
        from_attributes = True


class TimetableQuery(BaseModel):
    """课表查询参数"""
    semester: str = Field(..., description="学期")
    version_id: int = Field(..., description="排课版本ID")
    week_number: Optional[int] = Field(None, ge=1, le=53, description="周次")
    teacher_id: Optional[str] = Field(None, description="教师ID")
    class_id: Optional[str] = Field(None, description="班级ID")
    classroom_id: Optional[str] = Field(None, description="教室ID")

