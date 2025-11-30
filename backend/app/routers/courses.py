# -*- coding: utf-8 -*-
"""
课程管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.database import Database, get_db
from app.schemas.course import Course, CourseCreate, CourseUpdate

router = APIRouter()


@router.get("/", response_model=List[Course])
async def get_courses(db: Database = Depends(get_db)):
    """获取所有课程"""
    query = """
        SELECT course_id, course_name, credits, total_hours, notes,
               created_at, updated_at
        FROM courses
        ORDER BY course_id
    """
    courses = db.execute_query(query)
    return courses


@router.get("/{course_id}", response_model=Course)
async def get_course(course_id: str, db: Database = Depends(get_db)):
    """获取单个课程"""
    query = """
        SELECT course_id, course_name, credits, total_hours, notes,
               created_at, updated_at
        FROM courses
        WHERE course_id = %s
    """
    result = db.execute_query(query, (course_id,))
    if not result:
        raise HTTPException(status_code=404, detail="课程不存在")
    return result[0]


@router.post("/", response_model=Course)
async def create_course(course: CourseCreate, db: Database = Depends(get_db)):
    """创建课程"""
    check_query = "SELECT course_id FROM courses WHERE course_id = %s"
    existing = db.execute_query(check_query, (course.course_id,))
    if existing:
        raise HTTPException(status_code=400, detail="课程编号已存在")
    
    insert_query = """
        INSERT INTO courses (course_id, course_name, credits, total_hours, notes)
        VALUES (%s, %s, %s, %s, %s)
    """
    db.execute_insert(
        insert_query,
        (
            course.course_id,
            course.course_name,
            course.credits,
            course.total_hours,
            course.notes,
        ),
    )
    
    return await get_course(course.course_id, db)


@router.put("/{course_id}", response_model=Course)
async def update_course(
    course_id: str, course: CourseUpdate, db: Database = Depends(get_db)
):
    """更新课程"""
    check_query = "SELECT course_id FROM courses WHERE course_id = %s"
    existing = db.execute_query(check_query, (course_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    update_fields = []
    params = []
    
    if course.course_name is not None:
        update_fields.append("course_name = %s")
        params.append(course.course_name)
    if course.credits is not None:
        update_fields.append("credits = %s")
        params.append(course.credits)
    if course.total_hours is not None:
        update_fields.append("total_hours = %s")
        params.append(course.total_hours)
    if course.notes is not None:
        update_fields.append("notes = %s")
        params.append(course.notes)
    
    if not update_fields:
        return await get_course(course_id, db)
    
    params.append(course_id)
    update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE course_id = %s"
    db.execute_update(update_query, tuple(params))
    
    return await get_course(course_id, db)


@router.delete("/{course_id}")
async def delete_course(course_id: str, db: Database = Depends(get_db)):
    """删除课程"""
    delete_query = "DELETE FROM courses WHERE course_id = %s"
    affected = db.execute_delete(delete_query, (course_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    return {"message": "删除成功", "course_id": course_id}

