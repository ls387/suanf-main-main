# -*- coding: utf-8 -*-
"""
开课计划管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.database import Database, get_db
from app.schemas.offering import (
    Offering,
    OfferingCreate,
    OfferingUpdate,
    TeacherBlackoutTime,
    TeacherBlackoutTimeCreate,
    TeacherPreference,
    TeacherPreferenceCreate,
)

router = APIRouter()


@router.get("/", response_model=List[Offering])
async def get_offerings(semester: str = None, db: Database = Depends(get_db)):
    """获取开课计划列表"""
    if semester:
        query = """
            SELECT offering_id, semester, course_id, course_nature, student_count_estimate,
                   start_week, end_week, week_pattern, created_at, updated_at
            FROM course_offerings
            WHERE semester = %s
            ORDER BY offering_id DESC
        """
        offerings = db.execute_query(query, (semester,))
    else:
        query = """
            SELECT offering_id, semester, course_id, course_nature, student_count_estimate,
                   start_week, end_week, week_pattern, created_at, updated_at
            FROM course_offerings
            ORDER BY offering_id DESC
        """
        offerings = db.execute_query(query)
    
    # 获取关联数据
    for offering in offerings:
        offering_id = offering["offering_id"]
        
        # 获取班级
        class_query = "SELECT class_id FROM offering_classes WHERE offering_id = %s"
        classes = db.execute_query(class_query, (offering_id,))
        offering["class_ids"] = [c["class_id"] for c in classes]
        
        # 获取教师
        teacher_query = "SELECT teacher_id FROM offering_teachers WHERE offering_id = %s"
        teachers = db.execute_query(teacher_query, (offering_id,))
        offering["teacher_ids"] = [t["teacher_id"] for t in teachers]
        
        # 获取设施要求
        feature_query = "SELECT feature_id FROM offering_requires_features WHERE offering_id = %s"
        features = db.execute_query(feature_query, (offering_id,))
        offering["feature_ids"] = [f["feature_id"] for f in features]
    
    return offerings


@router.get("/{offering_id}", response_model=Offering)
async def get_offering(offering_id: int, db: Database = Depends(get_db)):
    """获取单个开课计划"""
    query = """
        SELECT offering_id, semester, course_id, course_nature, student_count_estimate,
               start_week, end_week, week_pattern, created_at, updated_at
        FROM course_offerings
        WHERE offering_id = %s
    """
    result = db.execute_query(query, (offering_id,))
    if not result:
        raise HTTPException(status_code=404, detail="开课计划不存在")
    
    offering = result[0]
    
    # 获取班级
    class_query = "SELECT class_id FROM offering_classes WHERE offering_id = %s"
    classes = db.execute_query(class_query, (offering_id,))
    offering["class_ids"] = [c["class_id"] for c in classes]
    
    # 获取教师
    teacher_query = "SELECT teacher_id FROM offering_teachers WHERE offering_id = %s"
    teachers = db.execute_query(teacher_query, (offering_id,))
    offering["teacher_ids"] = [t["teacher_id"] for t in teachers]
    
    # 获取设施要求
    feature_query = "SELECT feature_id FROM offering_requires_features WHERE offering_id = %s"
    features = db.execute_query(feature_query, (offering_id,))
    offering["feature_ids"] = [f["feature_id"] for f in features]
    
    return offering


@router.post("/", response_model=Offering)
async def create_offering(offering: OfferingCreate, db: Database = Depends(get_db)):
    """创建开课计划"""
    insert_query = """
        INSERT INTO course_offerings 
        (semester, course_id, course_nature, student_count_estimate, start_week, end_week, week_pattern)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    offering_id = db.execute_insert(
        insert_query,
        (
            offering.semester,
            offering.course_id,
            offering.course_nature,
            offering.student_count_estimate,
            offering.start_week,
            offering.end_week,
            offering.week_pattern,
        ),
    )
    
    # 插入班级关联
    if offering.class_ids:
        class_insert = "INSERT INTO offering_classes (offering_id, class_id) VALUES (%s, %s)"
        for class_id in offering.class_ids:
            db.execute_insert(class_insert, (offering_id, class_id))
    
    # 插入教师关联
    if offering.teacher_ids:
        teacher_insert = """
            INSERT INTO offering_teachers (offering_id, teacher_id, role)
            VALUES (%s, %s, %s)
        """
        for teacher_id in offering.teacher_ids:
            db.execute_insert(teacher_insert, (offering_id, teacher_id, "主讲"))
    
    # 插入设施要求
    if offering.feature_ids:
        feature_insert = """
            INSERT INTO offering_requires_features (offering_id, feature_id, is_mandatory)
            VALUES (%s, %s, %s)
        """
        for feature_id in offering.feature_ids:
            db.execute_insert(feature_insert, (offering_id, feature_id, True))
    
    return await get_offering(offering_id, db)


@router.put("/{offering_id}", response_model=Offering)
async def update_offering(
    offering_id: int, offering: OfferingUpdate, db: Database = Depends(get_db)
):
    """更新开课计划"""
    check_query = "SELECT offering_id FROM course_offerings WHERE offering_id = %s"
    existing = db.execute_query(check_query, (offering_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="开课计划不存在")
    
    update_fields = []
    params = []
    
    if offering.semester is not None:
        update_fields.append("semester = %s")
        params.append(offering.semester)
    if offering.course_id is not None:
        update_fields.append("course_id = %s")
        params.append(offering.course_id)
    if offering.course_nature is not None:
        update_fields.append("course_nature = %s")
        params.append(offering.course_nature)
    if offering.student_count_estimate is not None:
        update_fields.append("student_count_estimate = %s")
        params.append(offering.student_count_estimate)
    if offering.start_week is not None:
        update_fields.append("start_week = %s")
        params.append(offering.start_week)
    if offering.end_week is not None:
        update_fields.append("end_week = %s")
        params.append(offering.end_week)
    if offering.week_pattern is not None:
        update_fields.append("week_pattern = %s")
        params.append(offering.week_pattern)
    
    if update_fields:
        params.append(offering_id)
        update_query = f"UPDATE course_offerings SET {', '.join(update_fields)} WHERE offering_id = %s"
        db.execute_update(update_query, tuple(params))
    
    # 更新班级关联
    if offering.class_ids is not None:
        db.execute_delete("DELETE FROM offering_classes WHERE offering_id = %s", (offering_id,))
        if offering.class_ids:
            class_insert = "INSERT INTO offering_classes (offering_id, class_id) VALUES (%s, %s)"
            for class_id in offering.class_ids:
                db.execute_insert(class_insert, (offering_id, class_id))
    
    # 更新教师关联
    if offering.teacher_ids is not None:
        db.execute_delete("DELETE FROM offering_teachers WHERE offering_id = %s", (offering_id,))
        if offering.teacher_ids:
            teacher_insert = """
                INSERT INTO offering_teachers (offering_id, teacher_id, role)
                VALUES (%s, %s, %s)
            """
            for teacher_id in offering.teacher_ids:
                db.execute_insert(teacher_insert, (offering_id, teacher_id, "主讲"))
    
    # 更新设施要求
    if offering.feature_ids is not None:
        db.execute_delete("DELETE FROM offering_requires_features WHERE offering_id = %s", (offering_id,))
        if offering.feature_ids:
            feature_insert = """
                INSERT INTO offering_requires_features (offering_id, feature_id, is_mandatory)
                VALUES (%s, %s, %s)
            """
            for feature_id in offering.feature_ids:
                db.execute_insert(feature_insert, (offering_id, feature_id, True))
    
    return await get_offering(offering_id, db)


@router.delete("/{offering_id}")
async def delete_offering(offering_id: int, db: Database = Depends(get_db)):
    """删除开课计划"""
    delete_query = "DELETE FROM course_offerings WHERE offering_id = %s"
    affected = db.execute_delete(delete_query, (offering_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="开课计划不存在")
    
    return {"message": "删除成功", "offering_id": offering_id}


# 教师黑名单时间管理
@router.get("/blackout-times/", response_model=List[TeacherBlackoutTime])
async def get_blackout_times(
    teacher_id: str = None, semester: str = None, db: Database = Depends(get_db)
):
    """获取教师禁止时间列表"""
    query = """
        SELECT blackout_id, teacher_id, semester, weekday, start_slot, end_slot, reason
        FROM teacher_blackout_times
        WHERE 1=1
    """
    params = []
    
    if teacher_id:
        query += " AND teacher_id = %s"
        params.append(teacher_id)
    if semester:
        query += " AND semester = %s"
        params.append(semester)
    
    query += " ORDER BY teacher_id, weekday, start_slot"
    
    return db.execute_query(query, tuple(params) if params else None)


@router.post("/blackout-times/", response_model=TeacherBlackoutTime)
async def create_blackout_time(
    blackout: TeacherBlackoutTimeCreate, db: Database = Depends(get_db)
):
    """创建教师禁止时间"""
    insert_query = """
        INSERT INTO teacher_blackout_times 
        (teacher_id, semester, weekday, start_slot, end_slot, reason)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    blackout_id = db.execute_insert(
        insert_query,
        (
            blackout.teacher_id,
            blackout.semester,
            blackout.weekday,
            blackout.start_slot,
            blackout.end_slot,
            blackout.reason,
        ),
    )
    
    # 返回创建的记录
    query = "SELECT * FROM teacher_blackout_times WHERE blackout_id = %s"
    result = db.execute_query(query, (blackout_id,))
    return result[0]


@router.delete("/blackout-times/{blackout_id}")
async def delete_blackout_time(blackout_id: int, db: Database = Depends(get_db)):
    """删除教师禁止时间"""
    delete_query = "DELETE FROM teacher_blackout_times WHERE blackout_id = %s"
    affected = db.execute_delete(delete_query, (blackout_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="禁止时间不存在")
    
    return {"message": "删除成功", "blackout_id": blackout_id}


# 教师偏好管理
@router.get("/preferences/", response_model=List[TeacherPreference])
async def get_preferences(
    teacher_id: str = None, offering_id: int = None, db: Database = Depends(get_db)
):
    """获取教师偏好列表"""
    query = """
        SELECT preference_id, offering_id, teacher_id, preference_type,
               weekday, start_slot, end_slot, penalty_score
        FROM teacher_preferences
        WHERE 1=1
    """
    params = []
    
    if teacher_id:
        query += " AND teacher_id = %s"
        params.append(teacher_id)
    if offering_id:
        query += " AND offering_id = %s"
        params.append(offering_id)
    
    query += " ORDER BY teacher_id, offering_id"
    
    return db.execute_query(query, tuple(params) if params else None)


@router.post("/preferences/", response_model=TeacherPreference)
async def create_preference(
    preference: TeacherPreferenceCreate, db: Database = Depends(get_db)
):
    """创建教师偏好"""
    insert_query = """
        INSERT INTO teacher_preferences 
        (offering_id, teacher_id, preference_type, weekday, start_slot, end_slot, penalty_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    preference_id = db.execute_insert(
        insert_query,
        (
            preference.offering_id,
            preference.teacher_id,
            preference.preference_type,
            preference.weekday,
            preference.start_slot,
            preference.end_slot,
            preference.penalty_score,
        ),
    )
    
    # 返回创建的记录
    query = "SELECT * FROM teacher_preferences WHERE preference_id = %s"
    result = db.execute_query(query, (preference_id,))
    return result[0]


@router.delete("/preferences/{preference_id}")
async def delete_preference(preference_id: int, db: Database = Depends(get_db)):
    """删除教师偏好"""
    delete_query = "DELETE FROM teacher_preferences WHERE preference_id = %s"
    affected = db.execute_delete(delete_query, (preference_id,))
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="偏好不存在")
    
    return {"message": "删除成功", "preference_id": preference_id}

