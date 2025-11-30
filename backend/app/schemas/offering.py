# -*- coding: utf-8 -*-
"""
开课计划相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OfferingBase(BaseModel):
    """开课计划基础模型"""
    semester: str = Field(..., description="学年学期")
    course_id: str = Field(..., description="课程编号")
    course_nature: str = Field("必修", description="课程性质")
    student_count_estimate: Optional[int] = Field(None, description="预估总上课人数")
    start_week: int = Field(..., description="起始周")
    end_week: int = Field(..., description="结束周")
    week_pattern: str = Field("CONTINUOUS", description="周次模式")


class OfferingCreate(OfferingBase):
    """创建开课计划"""
    class_ids: List[str] = Field([], description="关联的班级ID列表")
    teacher_ids: List[str] = Field([], description="授课教师ID列表")
    feature_ids: List[str] = Field([], description="设施要求ID列表")


class OfferingUpdate(BaseModel):
    """更新开课计划"""
    semester: Optional[str] = None
    course_id: Optional[str] = None
    course_nature: Optional[str] = None
    student_count_estimate: Optional[int] = None
    start_week: Optional[int] = None
    end_week: Optional[int] = None
    week_pattern: Optional[str] = None
    class_ids: Optional[List[str]] = None
    teacher_ids: Optional[List[str]] = None
    feature_ids: Optional[List[str]] = None


class Offering(OfferingBase):
    """开课计划完整信息"""
    offering_id: int
    class_ids: List[str] = []
    teacher_ids: List[str] = []
    feature_ids: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TeacherBlackoutTimeBase(BaseModel):
    """教师禁止时间基础模型"""
    teacher_id: str = Field(..., description="教师ID")
    semester: str = Field(..., description="学期")
    weekday: int = Field(..., ge=1, le=7, description="星期几(1-7)")
    start_slot: int = Field(..., ge=1, le=13, description="开始节次(1-13)")
    end_slot: int = Field(..., ge=1, le=13, description="结束节次(1-13)")
    reason: Optional[str] = Field(None, description="原因")


class TeacherBlackoutTimeCreate(TeacherBlackoutTimeBase):
    """创建教师禁止时间"""
    pass


class TeacherBlackoutTime(TeacherBlackoutTimeBase):
    """教师禁止时间完整信息"""
    blackout_id: int
    
    class Config:
        from_attributes = True


class TeacherPreferenceBase(BaseModel):
    """教师偏好基础模型"""
    offering_id: int = Field(..., description="开课计划ID")
    teacher_id: str = Field(..., description="教师ID")
    preference_type: str = Field(..., description="偏好类型: PREFERRED/AVOIDED")
    weekday: Optional[int] = Field(None, ge=1, le=7, description="星期几(1-7)")
    start_slot: Optional[int] = Field(None, ge=1, le=13, description="开始节次(1-13)")
    end_slot: Optional[int] = Field(None, ge=1, le=13, description="结束节次(1-13)")
    penalty_score: int = Field(100, description="惩罚分数")


class TeacherPreferenceCreate(TeacherPreferenceBase):
    """创建教师偏好"""
    pass


class TeacherPreference(TeacherPreferenceBase):
    """教师偏好完整信息"""
    preference_id: int
    
    class Config:
        from_attributes = True

