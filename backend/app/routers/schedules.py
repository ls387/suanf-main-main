# -*- coding: utf-8 -*-
"""
排课条目操作路由

端点（全部挂在 /api/schedules）：
  PUT /api/schedules/{schedule_id}/move   移动单条排课到新时间槽（含冲突预检）
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ScheduleMoveRequest(BaseModel):
    week_day: int = Field(..., ge=1, le=7, description="目标星期（1-7）")
    start_slot: int = Field(..., ge=1, le=13, description="目标起始节次（1-13）")
    end_slot: int = Field(..., ge=1, le=13, description="目标结束节次（1-13）")

    @model_validator(mode="after")
    def check_slots(self):
        if self.start_slot > self.end_slot:
            raise ValueError("start_slot 不能大于 end_slot")
        return self


class ScheduleMoveResponse(BaseModel):
    schedule_id: int
    version_id: int
    task_id: int
    classroom_id: str
    week_day: int
    start_slot: int
    end_slot: int


# ---------------------------------------------------------------------------
# 工具：时间段重叠判断
# new_start <= exist_end  AND  new_end >= exist_start
# ---------------------------------------------------------------------------

def _slots_overlap(new_start: int, new_end: int, exist_start: int, exist_end: int) -> bool:
    return new_start <= exist_end and new_end >= exist_start


# ---------------------------------------------------------------------------
# PUT /api/schedules/{schedule_id}/move
# ---------------------------------------------------------------------------

@router.put("/{schedule_id}/move", response_model=ScheduleMoveResponse)
async def move_schedule(schedule_id: int, body: ScheduleMoveRequest):
    """
    将一条排课记录移动到新的时间槽。

    - 只改 week_day / start_slot / end_slot，教室不变。
    - 移动前做三类冲突预检（教室 / 教师 / 班级）。
    - 有冲突返回 409，body 包含 conflict_type 和可读说明。
    - 连堂课整体移动：end_slot - start_slot 必须与原记录 span 一致。
    """
    db = get_db()

    # 1. 查原记录
    rows = db.execute_query(
        "SELECT * FROM schedules WHERE schedule_id = %s", (schedule_id,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="排课记录不存在")
    orig = rows[0]

    version_id   = orig["version_id"]
    classroom_id = orig["classroom_id"]
    task_id      = orig["task_id"]
    orig_span    = orig["end_slot"] - orig["start_slot"]
    new_span     = body.end_slot - body.start_slot

    # 2. span 一致性校验（连堂课整体移动）
    if orig_span != new_span:
        raise HTTPException(
            status_code=400,
            detail=f"连堂课必须整体移动，原 span={orig_span+1}，目标 span={new_span+1}",
        )

    # 3. 获取该 task 的 offering_id（用于后续冲突查询）
    task_rows = db.execute_query(
        "SELECT offering_id FROM teaching_tasks WHERE task_id = %s", (task_id,)
    )
    if not task_rows:
        raise HTTPException(status_code=500, detail="教学任务数据异常")
    offering_id = task_rows[0]["offering_id"]

    new_start = body.start_slot
    new_end   = body.end_slot
    new_day   = body.week_day

    # -----------------------------------------------------------------------
    # 4. 冲突预检 A：教室冲突
    # -----------------------------------------------------------------------
    classroom_conflicts = db.execute_query(
        """SELECT s.schedule_id, co2.course_name
           FROM schedules s
           JOIN teaching_tasks tt2  ON s.task_id      = tt2.task_id
           JOIN course_offerings co2 ON tt2.offering_id = co2.offering_id
           WHERE s.version_id   = %s
             AND s.classroom_id = %s
             AND s.week_day     = %s
             AND s.schedule_id != %s
             AND s.start_slot  <= %s
             AND s.end_slot    >= %s""",
        (version_id, classroom_id, new_day, schedule_id, new_end, new_start),
    )
    if classroom_conflicts:
        c = classroom_conflicts[0]
        raise HTTPException(
            status_code=409,
            detail={
                "conflict_type": "classroom",
                "message": f"教室在周{new_day}第{new_start}-{new_end}节已有课程：{c['course_name']}",
            },
        )

    # -----------------------------------------------------------------------
    # 5. 冲突预检 B：教师冲突
    # -----------------------------------------------------------------------
    teacher_conflicts = db.execute_query(
        """SELECT s.schedule_id, co2.course_name, t.teacher_name
           FROM schedules s
           JOIN teaching_tasks tt2   ON s.task_id      = tt2.task_id
           JOIN course_offerings co2  ON tt2.offering_id = co2.offering_id
           JOIN offering_teachers ot2 ON co2.offering_id = ot2.offering_id
           JOIN teachers t            ON ot2.teacher_id  = t.teacher_id
           WHERE s.version_id   = %s
             AND s.week_day     = %s
             AND s.schedule_id != %s
             AND s.start_slot  <= %s
             AND s.end_slot    >= %s
             AND ot2.teacher_id IN (
                 SELECT teacher_id FROM offering_teachers WHERE offering_id = %s
             )""",
        (version_id, new_day, schedule_id, new_end, new_start, offering_id),
    )
    if teacher_conflicts:
        c = teacher_conflicts[0]
        raise HTTPException(
            status_code=409,
            detail={
                "conflict_type": "teacher",
                "message": f"教师 {c['teacher_name']} 在周{new_day}第{new_start}-{new_end}节已有课程：{c['course_name']}",
            },
        )

    # -----------------------------------------------------------------------
    # 6. 冲突预检 C：班级冲突
    # -----------------------------------------------------------------------
    class_conflicts = db.execute_query(
        """SELECT s.schedule_id, co2.course_name, cl.class_name
           FROM schedules s
           JOIN teaching_tasks tt2   ON s.task_id      = tt2.task_id
           JOIN course_offerings co2  ON tt2.offering_id = co2.offering_id
           JOIN offering_classes oc2  ON co2.offering_id = oc2.offering_id
           JOIN classes cl            ON oc2.class_id    = cl.class_id
           WHERE s.version_id   = %s
             AND s.week_day     = %s
             AND s.schedule_id != %s
             AND s.start_slot  <= %s
             AND s.end_slot    >= %s
             AND oc2.class_id IN (
                 SELECT class_id FROM offering_classes WHERE offering_id = %s
             )""",
        (version_id, new_day, schedule_id, new_end, new_start, offering_id),
    )
    if class_conflicts:
        c = class_conflicts[0]
        raise HTTPException(
            status_code=409,
            detail={
                "conflict_type": "class",
                "message": f"班级 {c['class_name']} 在周{new_day}第{new_start}-{new_end}节已有课程：{c['course_name']}",
            },
        )

    # -----------------------------------------------------------------------
    # 7. 无冲突，执行更新
    # -----------------------------------------------------------------------
    db.execute_update(
        "UPDATE schedules SET week_day=%s, start_slot=%s, end_slot=%s WHERE schedule_id=%s",
        (new_day, new_start, new_end, schedule_id),
    )

    updated = db.execute_query(
        "SELECT * FROM schedules WHERE schedule_id=%s", (schedule_id,)
    )
    return updated[0]
