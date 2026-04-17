# -*- coding: utf-8 -*-
"""
排课版本管理路由

端点（全部挂在 /api/versions）：
  POST   /api/versions                创建版本（学期 + 方案名 + 描述）
  GET    /api/versions                版本列表（可按学期筛选）
  GET    /api/versions/{id}           版本详情（含排课统计）
  POST   /api/versions/{id}/confirm   确认版本（draft → published）
  DELETE /api/versions/{id}           删除草稿版本

注：schedule_versions 表 status 枚举为 draft / published / archived
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Schemas（局部定义，只在 versions 使用）
# ---------------------------------------------------------------------------

class VersionCreateRequest(BaseModel):
    semester: str = Field(..., description="学期，格式如 2024-2025-1", examples=["2024-2025-1"])
    version_name: str = Field(..., description="方案名称，如 '第一轮草案'")
    description: Optional[str] = Field(None, description="版本描述")
    created_by: Optional[str] = Field(None, description="创建人")


class VersionResponse(BaseModel):
    version_id: int
    semester: str
    version_name: str
    status: str
    description: Optional[str]
    created_by: Optional[str]
    parent_version_id: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


class VersionDetailResponse(VersionResponse):
    """版本详情，附带排课统计"""
    schedule_count: int = Field(0, description="已排课条目数")


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _row_to_version(row: dict) -> dict:
    return {
        "version_id": row["version_id"],
        "semester": row["semester"],
        "version_name": row["version_name"],
        "status": row["status"],
        "description": row.get("description"),
        "created_by": row.get("created_by"),
        "parent_version_id": row.get("parent_version_id"),
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
        "updated_at": str(row["updated_at"]) if row.get("updated_at") else None,
    }


def _get_version_or_404(db, version_id: int) -> dict:
    rows = db.execute_query(
        "SELECT * FROM schedule_versions WHERE version_id = %s",
        (version_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"版本 {version_id} 不存在")
    return rows[0]


# ---------------------------------------------------------------------------
# POST /api/versions — 创建版本
# ---------------------------------------------------------------------------

@router.post("", response_model=VersionResponse, status_code=201)
async def create_version(body: VersionCreateRequest):
    """
    创建新的排课版本（初始状态为 draft）。

    同一学期下 version_name 不可重复（数据库唯一约束）。
    """
    db = get_db()
    try:
        new_id = db.execute_insert(
            "INSERT INTO schedule_versions (semester, version_name, description, created_by) "
            "VALUES (%s, %s, %s, %s)",
            (body.semester, body.version_name, body.description, body.created_by),
        )
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=409,
                detail=f"学期 {body.semester} 下已存在同名版本 '{body.version_name}'",
            )
        logger.error(f"创建版本失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建版本失败")

    row = _get_version_or_404(db, new_id)
    return _row_to_version(row)


# ---------------------------------------------------------------------------
# GET /api/versions — 版本列表
# ---------------------------------------------------------------------------

@router.get("", response_model=list[VersionResponse])
async def list_versions(
    semester: Optional[str] = Query(None, description="按学期筛选，如 2024-2025-1"),
    status: Optional[str] = Query(None, description="按状态筛选：draft / published / archived"),
):
    """返回所有版本，按创建时间倒序。可用 semester / status 参数过滤。"""
    db = get_db()
    sql = "SELECT * FROM schedule_versions WHERE 1=1"
    params: list = []

    if semester:
        sql += " AND semester = %s"
        params.append(semester)
    if status:
        sql += " AND status = %s"
        params.append(status)

    sql += " ORDER BY created_at DESC"
    rows = db.execute_query(sql, tuple(params) if params else None)
    return [_row_to_version(r) for r in rows]


# ---------------------------------------------------------------------------
# GET /api/versions/{id} — 版本详情
# ---------------------------------------------------------------------------

@router.get("/{version_id}", response_model=VersionDetailResponse)
async def get_version(version_id: int):
    """返回版本详情，附带该版本已排课条目数。"""
    db = get_db()
    row = _get_version_or_404(db, version_id)

    # 查排课数量
    count_rows = db.execute_query(
        "SELECT COUNT(*) AS cnt FROM schedules WHERE version_id = %s",
        (version_id,),
    )
    schedule_count = count_rows[0]["cnt"] if count_rows else 0

    result = _row_to_version(row)
    result["schedule_count"] = schedule_count
    return result


# ---------------------------------------------------------------------------
# POST /api/versions/{id}/confirm — 确认版本（draft → published）
# ---------------------------------------------------------------------------

@router.post("/{version_id}/confirm", response_model=VersionResponse)
async def confirm_version(version_id: int):
    """
    确认版本，将 status 从 draft 改为 published。

    已 published 或 archived 的版本不可再次确认。
    """
    db = get_db()
    row = _get_version_or_404(db, version_id)

    if row["status"] != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"只有草稿版本可以确认，当前状态为 {row['status']}",
        )

    # 检查该版本是否有排课结果
    count_rows = db.execute_query(
        "SELECT COUNT(*) AS cnt FROM schedules WHERE version_id = %s",
        (version_id,),
    )
    schedule_count = count_rows[0]["cnt"] if count_rows else 0
    if schedule_count == 0:
        raise HTTPException(
            status_code=400,
            detail="版本没有排课结果，请先完成排课再确认",
        )

    db.execute_update(
        "UPDATE schedule_versions SET status = 'published' WHERE version_id = %s",
        (version_id,),
    )

    updated = _get_version_or_404(db, version_id)
    return _row_to_version(updated)


# ---------------------------------------------------------------------------
# DELETE /api/versions/{id} — 删除草稿版本
# ---------------------------------------------------------------------------

@router.delete("/{version_id}", status_code=204)
async def delete_version(version_id: int):
    """
    删除草稿版本（连同其排课结果，级联删除）。

    已发布（published）或已归档（archived）的版本不可删除。
    """
    db = get_db()
    row = _get_version_or_404(db, version_id)

    if row["status"] != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"只有草稿版本可以删除，当前状态为 {row['status']}",
        )

    try:
        db.execute_delete(
            "DELETE FROM schedule_versions WHERE version_id = %s",
            (version_id,),
        )
    except Exception as e:
        logger.error(f"删除版本 {version_id} 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除失败")

    # 204 No Content，不返回 body
    return None


# ---------------------------------------------------------------------------
# POST /api/versions/{id}/fork — Fork 版本（复制排课结果到新草稿）
# ---------------------------------------------------------------------------

class ForkVersionRequest(BaseModel):
    version_name: str = Field(..., description="新版本名称")
    description: Optional[str] = Field(None, description="新版本描述")


@router.post("/{version_id}/fork", response_model=VersionResponse, status_code=201)
async def fork_version(version_id: int, body: ForkVersionRequest):
    """
    基于一个已发布（published）版本复制排课结果，生成新草稿。

    新版本的 parent_version_id 指向源版本，便于追溯。
    """
    db = get_db()
    row = _get_version_or_404(db, version_id)

    if row["status"] != "published":
        raise HTTPException(
            status_code=400,
            detail=f"只能从已发布版本 fork，当前状态为 {row['status']}",
        )

    # 创建新版本
    try:
        new_id = db.execute_insert(
            """INSERT INTO schedule_versions
               (semester, version_name, description, created_by, parent_version_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (row["semester"], body.version_name, body.description,
             row.get("created_by"), version_id),
        )
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=409,
                detail=f"学期 {row['semester']} 下已存在同名版本 '{body.version_name}'",
            )
        logger.error(f"fork 版本失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="fork 版本失败")

    # 批量复制 schedules（排除 schedule_id 和 created_at，让数据库自动生成）
    db.execute_insert(
        """INSERT INTO schedules (version_id, task_id, classroom_id, week_day, start_slot, end_slot)
           SELECT %s, task_id, classroom_id, week_day, start_slot, end_slot
           FROM schedules WHERE version_id = %s""",
        (new_id, version_id),
    )

    new_row = _get_version_or_404(db, new_id)
    return _row_to_version(new_row)


# ---------------------------------------------------------------------------
# GET /api/versions/{id}/schedules — 获取版本完整排课列表（供拖拽 UI 用）
# ---------------------------------------------------------------------------

class ScheduleEntry(BaseModel):
    """拖拽调课用的排课条目（含 schedule_id）"""
    schedule_id: int
    weekday: int
    start_slot: int
    end_slot: int
    course_id: str
    course_name: str
    teacher_id: str
    teacher_name: str
    classroom_id: str
    classroom_name: str
    building_name: Optional[str]
    campus_id: str
    classes: List[str] = []


@router.get("/{version_id}/schedules", response_model=List[ScheduleEntry])
async def get_version_schedules(version_id: int):
    """
    返回该版本所有排课条目，字段完整展开。
    含 schedule_id，供前端拖拽调课时标识每条记录。
    """
    db = get_db()
    _get_version_or_404(db, version_id)

    rows = db.execute_query(
        """SELECT
               s.schedule_id,
               s.week_day   AS weekday,
               s.start_slot,
               s.end_slot,
               s.task_id,
               co.course_id,
               co.course_nature,
               c.course_name,
               t.teacher_id,
               t.teacher_name,
               cr.classroom_id,
               cr.classroom_name,
               cr.building_name,
               cr.campus_id
           FROM schedules s
           JOIN teaching_tasks tt  ON s.task_id      = tt.task_id
           JOIN course_offerings co ON tt.offering_id = co.offering_id
           JOIN courses c           ON co.course_id   = c.course_id
           JOIN offering_teachers ot ON co.offering_id = ot.offering_id
           JOIN teachers t          ON ot.teacher_id  = t.teacher_id
           JOIN classrooms cr       ON s.classroom_id = cr.classroom_id
           WHERE s.version_id = %s
           ORDER BY s.week_day, s.start_slot""",
        (version_id,),
    )

    # 按 schedule_id 去重（多教师场景可能重复），取第一条
    seen: set = set()
    deduped = []
    for r in rows:
        if r["schedule_id"] not in seen:
            seen.add(r["schedule_id"])
            deduped.append(r)

    # 补充班级信息
    for entry in deduped:
        cls_rows = db.execute_query(
            """SELECT cl.class_name
               FROM offering_classes oc
               JOIN classes cl ON oc.class_id = cl.class_id
               WHERE oc.offering_id = (
                   SELECT offering_id FROM teaching_tasks WHERE task_id = %s
               )""",
            (entry["task_id"],),
        )
        entry["classes"] = [r["class_name"] for r in cls_rows]

    return deduped
