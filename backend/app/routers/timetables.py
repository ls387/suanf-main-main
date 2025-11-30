# -*- coding: utf-8 -*-
"""
课表查询路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from app.database import Database, get_db
from app.schemas.timetable import TimetableEntry

router = APIRouter()


@router.get("/teacher", response_model=List[TimetableEntry])
async def get_teacher_timetable(
    teacher_id: str = Query(..., description="教师ID"),
    semester: str = Query(..., description="学期"),
    version_id: int = Query(..., description="排课版本ID"),
    week_number: Optional[int] = Query(None, description="周次"),
    db: Database = Depends(get_db),
):
    """查询教师课表"""
    query = """
        SELECT 
            s.week_day as weekday,
            s.start_slot,
            s.end_slot,
            c.course_id,
            c.course_name,
            t.teacher_id,
            t.teacher_name,
            cr.classroom_id,
            cr.classroom_name,
            cr.building_name,
            cr.campus_id
        FROM schedules s
        JOIN teaching_tasks tt ON s.task_id = tt.task_id
        JOIN course_offerings co ON tt.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN offering_teachers ot ON co.offering_id = ot.offering_id
        JOIN teachers t ON ot.teacher_id = t.teacher_id
        JOIN classrooms cr ON s.classroom_id = cr.classroom_id
        WHERE s.version_id = %s
          AND co.semester = %s
          AND t.teacher_id = %s
    """
    params = [version_id, semester, teacher_id]
    
    # 如果指定了周次，添加周次过滤
    if week_number is not None:
        query += """
            AND %s BETWEEN co.start_week AND co.end_week
            AND (
                co.week_pattern = 'CONTINUOUS'
                OR (co.week_pattern = 'SINGLE' AND %s %% 2 = 1)
                OR (co.week_pattern = 'DOUBLE' AND %s %% 2 = 0)
            )
        """
        params.extend([week_number, week_number, week_number])
    
    query += " ORDER BY s.week_day, s.start_slot"
    
    results = db.execute_query(query, tuple(params))
    
    # 为每个课程添加班级信息
    for entry in results:
        # 查询该课程的班级
        class_query = """
            SELECT c.class_name
            FROM offering_classes oc
            JOIN classes c ON oc.class_id = c.class_id
            JOIN course_offerings co ON oc.offering_id = co.offering_id
            WHERE co.course_id = %s AND co.semester = %s
        """
        classes = db.execute_query(class_query, (entry["course_id"], semester))
        entry["classes"] = [cls["class_name"] for cls in classes]
    
    return results


@router.get("/class", response_model=List[TimetableEntry])
async def get_class_timetable(
    class_id: str = Query(..., description="班级ID"),
    semester: str = Query(..., description="学期"),
    version_id: int = Query(..., description="排课版本ID"),
    week_number: Optional[int] = Query(None, description="周次"),
    db: Database = Depends(get_db),
):
    """查询班级课表"""
    query = """
        SELECT 
            s.week_day as weekday,
            s.start_slot,
            s.end_slot,
            c.course_id,
            c.course_name,
            t.teacher_id,
            t.teacher_name,
            cr.classroom_id,
            cr.classroom_name,
            cr.building_name,
            cr.campus_id
        FROM schedules s
        JOIN teaching_tasks tt ON s.task_id = tt.task_id
        JOIN course_offerings co ON tt.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN offering_classes oc ON co.offering_id = oc.offering_id
        JOIN offering_teachers ot ON co.offering_id = ot.offering_id
        JOIN teachers t ON ot.teacher_id = t.teacher_id
        JOIN classrooms cr ON s.classroom_id = cr.classroom_id
        WHERE s.version_id = %s
          AND co.semester = %s
          AND oc.class_id = %s
    """
    params = [version_id, semester, class_id]
    
    if week_number is not None:
        query += """
            AND %s BETWEEN co.start_week AND co.end_week
            AND (
                co.week_pattern = 'CONTINUOUS'
                OR (co.week_pattern = 'SINGLE' AND %s %% 2 = 1)
                OR (co.week_pattern = 'DOUBLE' AND %s %% 2 = 0)
            )
        """
        params.extend([week_number, week_number, week_number])
    
    query += " ORDER BY s.week_day, s.start_slot"
    
    results = db.execute_query(query, tuple(params))
    
    # 为每个课程添加班级信息
    for entry in results:
        class_query = """
            SELECT c.class_name
            FROM offering_classes oc
            JOIN classes c ON oc.class_id = c.class_id
            JOIN course_offerings co ON oc.offering_id = co.offering_id
            WHERE co.course_id = %s AND co.semester = %s
        """
        classes = db.execute_query(class_query, (entry["course_id"], semester))
        entry["classes"] = [cls["class_name"] for cls in classes]
    
    return results


@router.get("/classroom", response_model=List[TimetableEntry])
async def get_classroom_timetable(
    classroom_id: str = Query(..., description="教室ID"),
    semester: str = Query(..., description="学期"),
    version_id: int = Query(..., description="排课版本ID"),
    week_number: Optional[int] = Query(None, description="周次"),
    db: Database = Depends(get_db),
):
    """查询教室课表"""
    query = """
        SELECT 
            s.week_day as weekday,
            s.start_slot,
            s.end_slot,
            c.course_id,
            c.course_name,
            t.teacher_id,
            t.teacher_name,
            cr.classroom_id,
            cr.classroom_name,
            cr.building_name,
            cr.campus_id
        FROM schedules s
        JOIN teaching_tasks tt ON s.task_id = tt.task_id
        JOIN course_offerings co ON tt.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN offering_teachers ot ON co.offering_id = ot.offering_id
        JOIN teachers t ON ot.teacher_id = t.teacher_id
        JOIN classrooms cr ON s.classroom_id = cr.classroom_id
        WHERE s.version_id = %s
          AND co.semester = %s
          AND s.classroom_id = %s
    """
    params = [version_id, semester, classroom_id]
    
    if week_number is not None:
        query += """
            AND %s BETWEEN co.start_week AND co.end_week
            AND (
                co.week_pattern = 'CONTINUOUS'
                OR (co.week_pattern = 'SINGLE' AND %s %% 2 = 1)
                OR (co.week_pattern = 'DOUBLE' AND %s %% 2 = 0)
            )
        """
        params.extend([week_number, week_number, week_number])
    
    query += " ORDER BY s.week_day, s.start_slot"
    
    results = db.execute_query(query, tuple(params))
    
    # 为每个课程添加班级信息
    for entry in results:
        class_query = """
            SELECT c.class_name
            FROM offering_classes oc
            JOIN classes c ON oc.class_id = c.class_id
            JOIN course_offerings co ON oc.offering_id = co.offering_id
            WHERE co.course_id = %s AND co.semester = %s
        """
        classes = db.execute_query(class_query, (entry["course_id"], semester))
        entry["classes"] = [cls["class_name"] for cls in classes]
    
    return results


@router.get("/week", response_model=List[TimetableEntry])
async def get_week_timetable(
    semester: str = Query(..., description="学期"),
    version_id: int = Query(..., description="排课版本ID"),
    week_number: int = Query(..., description="周次"),
    teacher_id: Optional[str] = Query(None, description="教师ID过滤"),
    class_id: Optional[str] = Query(None, description="班级ID过滤"),
    classroom_id: Optional[str] = Query(None, description="教室ID过滤"),
    db: Database = Depends(get_db),
):
    """查询某周的全部课表（支持过滤）"""
    query = """
        SELECT 
            s.week_day as weekday,
            s.start_slot,
            s.end_slot,
            c.course_id,
            c.course_name,
            t.teacher_id,
            t.teacher_name,
            cr.classroom_id,
            cr.classroom_name,
            cr.building_name,
            cr.campus_id
        FROM schedules s
        JOIN teaching_tasks tt ON s.task_id = tt.task_id
        JOIN course_offerings co ON tt.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN offering_teachers ot ON co.offering_id = ot.offering_id
        JOIN teachers t ON ot.teacher_id = t.teacher_id
        JOIN classrooms cr ON s.classroom_id = cr.classroom_id
        WHERE s.version_id = %s
          AND co.semester = %s
          AND %s BETWEEN co.start_week AND co.end_week
          AND (
              co.week_pattern = 'CONTINUOUS'
              OR (co.week_pattern = 'SINGLE' AND %s %% 2 = 1)
              OR (co.week_pattern = 'DOUBLE' AND %s %% 2 = 0)
          )
    """
    params = [version_id, semester, week_number, week_number, week_number]
    
    # 添加过滤条件
    if teacher_id:
        query += " AND t.teacher_id = %s"
        params.append(teacher_id)
    
    if class_id:
        query += " AND EXISTS (SELECT 1 FROM offering_classes oc WHERE oc.offering_id = co.offering_id AND oc.class_id = %s)"
        params.append(class_id)
    
    if classroom_id:
        query += " AND s.classroom_id = %s"
        params.append(classroom_id)
    
    query += " ORDER BY s.week_day, s.start_slot"
    
    results = db.execute_query(query, tuple(params))
    
    # 为每个课程添加班级信息
    for entry in results:
        class_query = """
            SELECT c.class_name
            FROM offering_classes oc
            JOIN classes c ON oc.class_id = c.class_id
            JOIN course_offerings co ON oc.offering_id = co.offering_id
            WHERE co.course_id = %s AND co.semester = %s
        """
        classes = db.execute_query(class_query, (entry["course_id"], semester))
        entry["classes"] = [cls["class_name"] for cls in classes]
    
    return results

