# -*- coding: utf-8 -*-
"""
教师管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.database import Database, get_db
from app.schemas.teacher import Teacher, TeacherCreate, TeacherUpdate

router = APIRouter()


@router.get("/", response_model=List[Teacher])
async def get_teachers(db: Database = Depends(get_db)):
    """获取所有教师"""
    query = """
        SELECT teacher_id, teacher_name, department_id, gender, is_external, 
               created_at, updated_at
        FROM teachers
        ORDER BY teacher_id
    """
    teachers = db.execute_query(query)
    return teachers


@router.get("/{teacher_id}", response_model=Teacher)
async def get_teacher(teacher_id: str, db: Database = Depends(get_db)):
    """获取单个教师"""
    query = """
        SELECT teacher_id, teacher_name, department_id, gender, is_external,
               created_at, updated_at
        FROM teachers
        WHERE teacher_id = %s
    """
    result = db.execute_query(query, (teacher_id,))
    if not result:
        raise HTTPException(status_code=404, detail="教师不存在")
    return result[0]


@router.post("/", response_model=Teacher)
async def create_teacher(teacher: TeacherCreate, db: Database = Depends(get_db)):
    """创建教师"""
    # 检查是否已存在
    check_query = "SELECT teacher_id FROM teachers WHERE teacher_id = %s"
    existing = db.execute_query(check_query, (teacher.teacher_id,))
    if existing:
        raise HTTPException(status_code=400, detail="教师编号已存在")
    
    # 插入
    insert_query = """
        INSERT INTO teachers (teacher_id, teacher_name, department_id, gender, is_external)
        VALUES (%s, %s, %s, %s, %s)
    """
    db.execute_insert(
        insert_query,
        (
            teacher.teacher_id,
            teacher.teacher_name,
            teacher.department_id,
            teacher.gender,
            teacher.is_external,
        ),
    )
    
    # 返回创建的教师
    return await get_teacher(teacher.teacher_id, db)


@router.put("/{teacher_id}", response_model=Teacher)
async def update_teacher(
    teacher_id: str, teacher: TeacherUpdate, db: Database = Depends(get_db)
):
    """更新教师"""
    # 检查是否存在
    check_query = "SELECT teacher_id FROM teachers WHERE teacher_id = %s"
    existing = db.execute_query(check_query, (teacher_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if teacher.teacher_name is not None:
        update_fields.append("teacher_name = %s")
        params.append(teacher.teacher_name)
    if teacher.department_id is not None:
        update_fields.append("department_id = %s")
        params.append(teacher.department_id)
    if teacher.gender is not None:
        update_fields.append("gender = %s")
        params.append(teacher.gender)
    if teacher.is_external is not None:
        update_fields.append("is_external = %s")
        params.append(teacher.is_external)
    
    if not update_fields:
        return await get_teacher(teacher_id, db)
    
    params.append(teacher_id)
    update_query = f"UPDATE teachers SET {', '.join(update_fields)} WHERE teacher_id = %s"
    db.execute_update(update_query, tuple(params))
    
    return await get_teacher(teacher_id, db)


@router.delete("/{teacher_id}")
async def delete_teacher(teacher_id: str, db: Database = Depends(get_db)):
    """删除教师"""
    delete_query = "DELETE FROM teachers WHERE teacher_id = %s"
    affected = db.execute_delete(delete_query, (teacher_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    return {"message": "删除成功", "teacher_id": teacher_id}

