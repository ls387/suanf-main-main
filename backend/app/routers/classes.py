# -*- coding: utf-8 -*-
"""
班级管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.database import Database, get_db
from app.schemas.class_model import Class, ClassCreate, ClassUpdate

router = APIRouter()


@router.get("/", response_model=List[Class])
async def get_classes(db: Database = Depends(get_db)):
    """获取所有班级"""
    query = """
        SELECT class_id, class_name, grade, student_count, major_id, education_system,
               created_at, updated_at
        FROM classes
        ORDER BY grade DESC, class_id
    """
    classes = db.execute_query(query)
    return classes


@router.get("/{class_id}", response_model=Class)
async def get_class(class_id: str, db: Database = Depends(get_db)):
    """获取单个班级"""
    query = """
        SELECT class_id, class_name, grade, student_count, major_id, education_system,
               created_at, updated_at
        FROM classes
        WHERE class_id = %s
    """
    result = db.execute_query(query, (class_id,))
    if not result:
        raise HTTPException(status_code=404, detail="班级不存在")
    return result[0]


@router.post("/", response_model=Class)
async def create_class(class_data: ClassCreate, db: Database = Depends(get_db)):
    """创建班级"""
    check_query = "SELECT class_id FROM classes WHERE class_id = %s"
    existing = db.execute_query(check_query, (class_data.class_id,))
    if existing:
        raise HTTPException(status_code=400, detail="班级编号已存在")
    
    insert_query = """
        INSERT INTO classes (class_id, class_name, grade, student_count, major_id, education_system)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    db.execute_insert(
        insert_query,
        (
            class_data.class_id,
            class_data.class_name,
            class_data.grade,
            class_data.student_count,
            class_data.major_id,
            class_data.education_system,
        ),
    )
    
    return await get_class(class_data.class_id, db)


@router.put("/{class_id}", response_model=Class)
async def update_class(
    class_id: str, class_data: ClassUpdate, db: Database = Depends(get_db)
):
    """更新班级"""
    check_query = "SELECT class_id FROM classes WHERE class_id = %s"
    existing = db.execute_query(check_query, (class_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    update_fields = []
    params = []
    
    if class_data.class_name is not None:
        update_fields.append("class_name = %s")
        params.append(class_data.class_name)
    if class_data.grade is not None:
        update_fields.append("grade = %s")
        params.append(class_data.grade)
    if class_data.student_count is not None:
        update_fields.append("student_count = %s")
        params.append(class_data.student_count)
    if class_data.major_id is not None:
        update_fields.append("major_id = %s")
        params.append(class_data.major_id)
    if class_data.education_system is not None:
        update_fields.append("education_system = %s")
        params.append(class_data.education_system)
    
    if not update_fields:
        return await get_class(class_id, db)
    
    params.append(class_id)
    update_query = f"UPDATE classes SET {', '.join(update_fields)} WHERE class_id = %s"
    db.execute_update(update_query, tuple(params))
    
    return await get_class(class_id, db)


@router.delete("/{class_id}")
async def delete_class(class_id: str, db: Database = Depends(get_db)):
    """删除班级"""
    delete_query = "DELETE FROM classes WHERE class_id = %s"
    affected = db.execute_delete(delete_query, (class_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    return {"message": "删除成功", "class_id": class_id}

