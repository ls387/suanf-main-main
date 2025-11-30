# -*- coding: utf-8 -*-
"""
教室管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.database import Database, get_db
from app.schemas.classroom import Classroom, ClassroomCreate, ClassroomUpdate

router = APIRouter()


@router.get("/", response_model=List[Classroom])
async def get_classrooms(db: Database = Depends(get_db)):
    """获取所有教室"""
    query = """
        SELECT c.classroom_id, c.classroom_name, c.building_name, c.campus_id,
               c.classroom_type, c.capacity, c.is_available, c.created_at, c.updated_at
        FROM classrooms c
        ORDER BY c.campus_id, c.building_name, c.classroom_name
    """
    classrooms = db.execute_query(query)
    
    # 获取每个教室的设施
    for classroom in classrooms:
        feature_query = """
            SELECT feature_id FROM classroom_has_features
            WHERE classroom_id = %s
        """
        features = db.execute_query(feature_query, (classroom["classroom_id"],))
        classroom["features"] = [f["feature_id"] for f in features]
    
    return classrooms


@router.get("/{classroom_id}", response_model=Classroom)
async def get_classroom(classroom_id: str, db: Database = Depends(get_db)):
    """获取单个教室"""
    query = """
        SELECT classroom_id, classroom_name, building_name, campus_id,
               classroom_type, capacity, is_available, created_at, updated_at
        FROM classrooms
        WHERE classroom_id = %s
    """
    result = db.execute_query(query, (classroom_id,))
    if not result:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    classroom = result[0]
    
    # 获取设施
    feature_query = """
        SELECT feature_id FROM classroom_has_features
        WHERE classroom_id = %s
    """
    features = db.execute_query(feature_query, (classroom_id,))
    classroom["features"] = [f["feature_id"] for f in features]
    
    return classroom


@router.post("/", response_model=Classroom)
async def create_classroom(classroom: ClassroomCreate, db: Database = Depends(get_db)):
    """创建教室"""
    check_query = "SELECT classroom_id FROM classrooms WHERE classroom_id = %s"
    existing = db.execute_query(check_query, (classroom.classroom_id,))
    if existing:
        raise HTTPException(status_code=400, detail="教室编号已存在")
    
    insert_query = """
        INSERT INTO classrooms (classroom_id, classroom_name, building_name, campus_id,
                               classroom_type, capacity, is_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    db.execute_insert(
        insert_query,
        (
            classroom.classroom_id,
            classroom.classroom_name,
            classroom.building_name,
            classroom.campus_id,
            classroom.classroom_type,
            classroom.capacity,
            classroom.is_available,
        ),
    )
    
    # 插入设施关联
    if classroom.features:
        feature_insert = """
            INSERT INTO classroom_has_features (classroom_id, feature_id)
            VALUES (%s, %s)
        """
        for feature_id in classroom.features:
            db.execute_insert(feature_insert, (classroom.classroom_id, feature_id))
    
    return await get_classroom(classroom.classroom_id, db)


@router.put("/{classroom_id}", response_model=Classroom)
async def update_classroom(
    classroom_id: str, classroom: ClassroomUpdate, db: Database = Depends(get_db)
):
    """更新教室"""
    check_query = "SELECT classroom_id FROM classrooms WHERE classroom_id = %s"
    existing = db.execute_query(check_query, (classroom_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    update_fields = []
    params = []
    
    if classroom.classroom_name is not None:
        update_fields.append("classroom_name = %s")
        params.append(classroom.classroom_name)
    if classroom.building_name is not None:
        update_fields.append("building_name = %s")
        params.append(classroom.building_name)
    if classroom.campus_id is not None:
        update_fields.append("campus_id = %s")
        params.append(classroom.campus_id)
    if classroom.classroom_type is not None:
        update_fields.append("classroom_type = %s")
        params.append(classroom.classroom_type)
    if classroom.capacity is not None:
        update_fields.append("capacity = %s")
        params.append(classroom.capacity)
    if classroom.is_available is not None:
        update_fields.append("is_available = %s")
        params.append(classroom.is_available)
    
    if update_fields:
        params.append(classroom_id)
        update_query = f"UPDATE classrooms SET {', '.join(update_fields)} WHERE classroom_id = %s"
        db.execute_update(update_query, tuple(params))
    
    # 更新设施关联
    if classroom.features is not None:
        # 删除旧的关联
        delete_features = "DELETE FROM classroom_has_features WHERE classroom_id = %s"
        db.execute_delete(delete_features, (classroom_id,))
        
        # 插入新的关联
        if classroom.features:
            feature_insert = """
                INSERT INTO classroom_has_features (classroom_id, feature_id)
                VALUES (%s, %s)
            """
            for feature_id in classroom.features:
                db.execute_insert(feature_insert, (classroom_id, feature_id))
    
    return await get_classroom(classroom_id, db)


@router.delete("/{classroom_id}")
async def delete_classroom(classroom_id: str, db: Database = Depends(get_db)):
    """删除教室"""
    delete_query = "DELETE FROM classrooms WHERE classroom_id = %s"
    affected = db.execute_delete(delete_query, (classroom_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    return {"message": "删除成功", "classroom_id": classroom_id}

