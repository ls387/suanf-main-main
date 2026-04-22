# -*- coding: utf-8 -*-
"""
冲突修复服务

支持按类型修复：
  capacity  - 容量不足（换更大教室）
  class     - 班级时间冲突（重新分配时间槽）
  teacher   - 教师时间冲突（重新分配时间槽）
  classroom - 教室时间冲突（重新分配时间槽）

返回结构化结果，不打印、不调用 input()。
"""
import sys
import os
from collections import defaultdict
from typing import Literal

from app.database import get_db
from app.services.conflict_analyzer import analyze_conflicts, _get_weeks

# 将项目根目录加入路径，以便导入 data_models
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from data_models import get_valid_time_slots

FixType = Literal["capacity", "class", "teacher", "classroom"]

_DAY_NAMES = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]

_SCHEDULE_QUERY = """
SELECT
    sr.schedule_id,
    sr.task_id,
    sr.classroom_id,
    sr.week_day,
    sr.start_slot,
    tt.slots_count,
    tt.offering_id,
    c.course_name,
    cr.classroom_name,
    cr.capacity AS classroom_capacity,
    co.start_week,
    co.end_week,
    co.week_pattern,
    GROUP_CONCAT(DISTINCT t.teacher_name SEPARATOR ', ') AS teacher_name,
    GROUP_CONCAT(DISTINCT t.teacher_id  SEPARATOR ', ') AS teacher_ids
FROM schedules sr
JOIN teaching_tasks tt ON sr.task_id = tt.task_id
JOIN course_offerings co ON tt.offering_id = co.offering_id
JOIN courses c ON co.course_id = c.course_id
JOIN classrooms cr ON sr.classroom_id = cr.classroom_id
LEFT JOIN offering_teachers ot ON co.offering_id = ot.offering_id
LEFT JOIN teachers t ON ot.teacher_id = t.teacher_id
WHERE sr.version_id = %s
GROUP BY sr.schedule_id, sr.task_id, sr.classroom_id, sr.week_day,
         sr.start_slot, tt.slots_count, tt.offering_id, c.course_name,
         cr.classroom_name, cr.capacity, co.start_week, co.end_week, co.week_pattern
ORDER BY sr.week_day, sr.start_slot
"""


def _load_teacher_blackouts(db) -> dict:
    blackouts = defaultdict(set)
    try:
        rows = db.execute_query(
            "SELECT teacher_id, weekday, start_slot, end_slot FROM teacher_blackout_times"
        )
        for row in rows:
            for slot in range(row["start_slot"], row["end_slot"] + 1):
                blackouts[str(row["teacher_id"])].add((row["weekday"], slot))
    except Exception:
        pass
    return dict(blackouts)


def _load_classroom_features(db) -> tuple:
    classroom_features = defaultdict(set)
    offering_features = defaultdict(set)
    try:
        for row in db.execute_query("SELECT classroom_id, feature_id FROM classroom_has_features"):
            classroom_features[str(row["classroom_id"])].add(row["feature_id"])
    except Exception:
        pass
    try:
        for row in db.execute_query(
            "SELECT offering_id, feature_id FROM offering_requires_features WHERE is_mandatory = 1"
        ):
            offering_features[row["offering_id"]].add(row["feature_id"])
    except Exception:
        pass
    return dict(classroom_features), dict(offering_features)


def _load_common_data(db, version_id: int):
    """加载排课结果、周次、任务-班级关系、任务-学生数。"""
    results = db.execute_query(_SCHEDULE_QUERY, (version_id,))

    offering_weeks: dict = {}
    for row in db.execute_query("SELECT offering_id, week_number FROM offering_weeks"):
        oid = row["offering_id"]
        if oid not in offering_weeks:
            offering_weeks[oid] = set()
        offering_weeks[oid].add(row["week_number"])

    task_ids = list({r["task_id"] for r in results})
    task_classes: dict = defaultdict(list)
    task_student_count: dict = {}

    if task_ids:
        placeholders = ",".join(["%s"] * len(task_ids))
        for row in db.execute_query(
            f"""SELECT tt.task_id, cl.class_id, cl.class_name
                FROM offering_classes oc
                JOIN classes cl ON oc.class_id = cl.class_id
                JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
                WHERE tt.task_id IN ({placeholders})""",
            tuple(task_ids),
        ):
            task_classes[row["task_id"]].append(
                {"class_id": row["class_id"], "class_name": row["class_name"]}
            )

        for row in db.execute_query(
            f"""SELECT tt.task_id, SUM(cl.student_count) AS total_students
                FROM offering_classes oc
                JOIN classes cl ON oc.class_id = cl.class_id
                JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
                WHERE tt.task_id IN ({placeholders})
                GROUP BY tt.task_id""",
            tuple(task_ids),
        ):
            task_student_count[row["task_id"]] = int(row["total_students"] or 0)

    return results, offering_weeks, task_classes, task_student_count


# ---------------------------------------------------------------------------
# 容量不足修复
# ---------------------------------------------------------------------------

def fix_capacity(version_id: int) -> dict:
    """为容量不足的排课找到更大的空闲教室并更新数据库。"""
    db = get_db()
    results, offering_weeks, task_classes, task_student_count = _load_common_data(db, version_id)
    classroom_features, offering_features = _load_classroom_features(db)

    all_classrooms = db.execute_query(
        "SELECT classroom_id, classroom_name, capacity, campus_id FROM classrooms ORDER BY capacity"
    )

    adjustments = []
    failed = []
    batch_allocated: dict = defaultdict(set)  # (weekday, slot) -> set of classroom_id

    for r in results:
        student_count = task_student_count.get(r["task_id"], 0)
        capacity = int(r.get("classroom_capacity") or 0)
        if capacity >= student_count:
            continue

        schedule_id = r["schedule_id"]
        current_classroom_id = r["classroom_id"]
        weekday = r["week_day"]
        start_slot = r["start_slot"]
        slots_count = r["slots_count"]
        end_slot = start_slot + slots_count - 1

        # 查该时间段已占用的教室
        occupied_rows = db.execute_query(
            """SELECT DISTINCT sr2.classroom_id
               FROM schedules sr2
               JOIN teaching_tasks tt2 ON sr2.task_id = tt2.task_id
               WHERE sr2.version_id = %s
                 AND sr2.week_day = %s
                 AND sr2.schedule_id != %s
                 AND sr2.start_slot <= %s
                 AND sr2.start_slot + tt2.slots_count - 1 >= %s""",
            (version_id, weekday, schedule_id, end_slot, start_slot),
        )
        occupied = {row["classroom_id"] for row in occupied_rows}
        for slot in range(start_slot, end_slot + 1):
            occupied.update(batch_allocated[(weekday, slot)])

        offering_id = r.get("offering_id")
        required_feats = offering_features.get(offering_id, set()) if offering_id else set()

        suitable = [
            room for room in all_classrooms
            if room["capacity"] >= student_count
            and room["classroom_id"] not in occupied
            and room["classroom_id"] != current_classroom_id
            and required_feats.issubset(classroom_features.get(str(room["classroom_id"]), set()))
        ]

        if suitable:
            best = min(suitable, key=lambda rm: rm["capacity"])
            adjustments.append({
                "schedule_id": schedule_id,
                "course": r["course_name"],
                "time": f"{_DAY_NAMES[weekday]} 第{start_slot}-{end_slot}节",
                "old_classroom": r["classroom_name"],
                "old_capacity": capacity,
                "new_classroom_id": best["classroom_id"],
                "new_classroom": best["classroom_name"],
                "new_capacity": best["capacity"],
                "students": student_count,
            })
            for slot in range(start_slot, end_slot + 1):
                batch_allocated[(weekday, slot)].add(best["classroom_id"])
        else:
            failed.append({
                "course": r["course_name"],
                "time": f"{_DAY_NAMES[weekday]} 第{start_slot}-{end_slot}节",
                "reason": "该时间段无容量足够的空闲教室",
            })

    # 写库
    for adj in adjustments:
        db.execute_update(
            "UPDATE schedules SET classroom_id = %s WHERE schedule_id = %s",
            (adj["new_classroom_id"], adj["schedule_id"]),
        )

    return {
        "fix_type": "capacity",
        "applied": len(adjustments),
        "failed": len(failed),
        "adjustments": adjustments,
        "failures": failed,
    }


# ---------------------------------------------------------------------------
# 时间冲突修复（班级 / 教师 / 教室 共用一套逻辑）
# ---------------------------------------------------------------------------

def _build_occupied_times(results, task_classes, exclude_ids: set) -> dict:
    """构建所有非冲突课程的时间占用表。"""
    occupied = {
        "classroom": defaultdict(set),
        "teacher": defaultdict(set),
        "class": defaultdict(set),
    }
    for r in results:
        if r["schedule_id"] in exclude_ids:
            continue
        start_slot = r["start_slot"]
        slots_count = r["slots_count"]
        weekday = r["week_day"]
        classroom_id = r["classroom_id"]
        teacher_ids_str = r.get("teacher_ids", "") or ""
        classes = [cls["class_id"] for cls in task_classes.get(r["task_id"], [])]

        for slot in range(start_slot, start_slot + slots_count):
            occupied["classroom"][classroom_id].add((weekday, slot))
            for tid in (t.strip() for t in teacher_ids_str.split(",") if t.strip()):
                occupied["teacher"][tid].add((weekday, slot))
            for cid in classes:
                occupied["class"][cid].add((weekday, slot))
    return occupied


def _find_new_slot(
    slots_count, classroom_id, teacher_ids, class_ids,
    old_weekday, old_start_slot, occupied, teacher_blackouts
):
    """在周一~周五的合法时间块里找第一个无冲突的新时间槽。"""
    for weekday in range(1, 6):
        for start_slot, _ in get_valid_time_slots(slots_count):
            if weekday == old_weekday and start_slot == old_start_slot:
                continue
            # 周四下午禁排
            if weekday == 4 and 6 <= start_slot <= 10:
                continue
            # 教师禁止时间
            blocked = False
            for tid in teacher_ids:
                for slot in range(start_slot, start_slot + slots_count):
                    if (weekday, slot) in teacher_blackouts.get(tid, set()):
                        blocked = True
                        break
                if blocked:
                    break
            if blocked:
                continue
            # 检查占用
            conflict = False
            for slot in range(start_slot, start_slot + slots_count):
                tk = (weekday, slot)
                if tk in occupied["classroom"][classroom_id]:
                    conflict = True
                    break
                for tid in teacher_ids:
                    if tk in occupied["teacher"][tid]:
                        conflict = True
                        break
                if conflict:
                    break
                for cid in class_ids:
                    if tk in occupied["class"][cid]:
                        conflict = True
                        break
                if conflict:
                    break
            if not conflict:
                return weekday, start_slot
    return None, None


def _fix_time_conflicts(version_id: int, conflict_schedule_ids: set, fix_type: str) -> dict:
    db = get_db()
    results, offering_weeks, task_classes, _ = _load_common_data(db, version_id)
    teacher_blackouts = _load_teacher_blackouts(db)

    occupied = _build_occupied_times(results, task_classes, conflict_schedule_ids)

    adjustments = []
    failed = []

    for schedule_id in conflict_schedule_ids:
        r = next((x for x in results if x["schedule_id"] == schedule_id), None)
        if not r:
            continue

        task_id = r["task_id"]
        slots_count = r["slots_count"]
        classroom_id = r["classroom_id"]
        old_weekday = r["week_day"]
        old_start_slot = r["start_slot"]
        teacher_ids = [t.strip() for t in (r.get("teacher_ids") or "").split(",") if t.strip()]
        class_ids = [cls["class_id"] for cls in task_classes.get(task_id, [])]

        new_weekday, new_start_slot = _find_new_slot(
            slots_count, classroom_id, teacher_ids, class_ids,
            old_weekday, old_start_slot, occupied, teacher_blackouts
        )

        if new_weekday is not None:
            # 更新占用表（避免后续课程选同一时间）
            for slot in range(new_start_slot, new_start_slot + slots_count):
                occupied["classroom"][classroom_id].add((new_weekday, slot))
                for tid in teacher_ids:
                    occupied["teacher"][tid].add((new_weekday, slot))
                for cid in class_ids:
                    occupied["class"][cid].add((new_weekday, slot))

            adjustments.append({
                "schedule_id": schedule_id,
                "course": r["course_name"],
                "old_time": f"{_DAY_NAMES[old_weekday]} 第{old_start_slot}-{old_start_slot + slots_count - 1}节",
                "new_time": f"{_DAY_NAMES[new_weekday]} 第{new_start_slot}-{new_start_slot + slots_count - 1}节",
                "new_weekday": new_weekday,
                "new_start_slot": new_start_slot,
                "new_end_slot": new_start_slot + slots_count - 1,
            })
        else:
            failed.append({
                "course": r["course_name"],
                "current_time": f"{_DAY_NAMES[old_weekday]} 第{old_start_slot}节",
                "reason": "无法找到无冲突的空闲时间槽",
            })

    # 写库
    for adj in adjustments:
        db.execute_update(
            "UPDATE schedules SET week_day = %s, start_slot = %s, end_slot = %s WHERE schedule_id = %s",
            (adj["new_weekday"], adj["new_start_slot"], adj["new_end_slot"], adj["schedule_id"]),
        )

    return {
        "fix_type": fix_type,
        "applied": len(adjustments),
        "failed": len(failed),
        "adjustments": [
            {"course": a["course"], "old_time": a["old_time"], "new_time": a["new_time"]}
            for a in adjustments
        ],
        "failures": failed,
    }


def fix_class_conflicts(version_id: int) -> dict:
    """修复班级时间冲突。"""
    report = analyze_conflicts(version_id)
    conflict_ids = set()
    for c in report["class_conflicts"]:
        for item in c.get("items", []):
            if "schedule_id" in item:
                conflict_ids.add(item["schedule_id"])
    # analyze_conflicts 返回的冲突里没有 schedule_id，需要重新从 DB 抓
    # 直接用冲突的 course1/course2 + weekday + overlap_start 定位 schedule_id
    if not conflict_ids:
        conflict_ids = _extract_conflict_ids_from_report(version_id, report["class_conflicts"], "class")
    if not conflict_ids:
        return {"fix_type": "class", "applied": 0, "failed": 0, "adjustments": [], "failures": []}
    return _fix_time_conflicts(version_id, conflict_ids, "class")


def fix_teacher_conflicts(version_id: int) -> dict:
    """修复教师时间冲突。"""
    report = analyze_conflicts(version_id)
    conflict_ids = _extract_conflict_ids_from_report(version_id, report["teacher_conflicts"], "teacher")
    if not conflict_ids:
        return {"fix_type": "teacher", "applied": 0, "failed": 0, "adjustments": [], "failures": []}
    return _fix_time_conflicts(version_id, conflict_ids, "teacher")


def fix_classroom_conflicts(version_id: int) -> dict:
    """修复教室时间冲突。"""
    report = analyze_conflicts(version_id)
    conflict_ids = _extract_conflict_ids_from_report(version_id, report["classroom_conflicts"], "classroom")
    if not conflict_ids:
        return {"fix_type": "classroom", "applied": 0, "failed": 0, "adjustments": [], "failures": []}
    return _fix_time_conflicts(version_id, conflict_ids, "classroom")


def _extract_conflict_ids_from_report(version_id: int, conflicts: list, conflict_type: str) -> set:
    """
    conflict_analyzer 返回的冲突数据中没有 schedule_id，
    通过 course_name + weekday + overlap_start 从 DB 查出对应 schedule_id。
    """
    if not conflicts:
        return set()

    db = get_db()
    conflict_ids = set()

    for c in conflicts:
        weekday = c["weekday"]
        overlap_start = c["overlap_start"]
        for course_key in ("course1", "course2"):
            course_name = c.get(course_key, "")
            if not course_name:
                continue
            rows = db.execute_query(
                """SELECT sr.schedule_id, sr.start_slot, tt.slots_count
                   FROM schedules sr
                   JOIN teaching_tasks tt ON sr.task_id = tt.task_id
                   JOIN course_offerings co ON tt.offering_id = co.offering_id
                   JOIN courses c ON co.course_id = c.course_id
                   WHERE sr.version_id = %s
                     AND sr.week_day = %s
                     AND c.course_name = %s
                     AND sr.start_slot <= %s
                     AND sr.start_slot + tt.slots_count - 1 >= %s""",
                (version_id, weekday, course_name, overlap_start, overlap_start),
            )
            for row in rows:
                conflict_ids.add(row["schedule_id"])

    return conflict_ids


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------

def fix_conflicts(version_id: int, fix_type: FixType) -> dict:
    if fix_type == "capacity":
        return fix_capacity(version_id)
    elif fix_type == "class":
        return fix_class_conflicts(version_id)
    elif fix_type == "teacher":
        return fix_teacher_conflicts(version_id)
    elif fix_type == "classroom":
        return fix_classroom_conflicts(version_id)
    else:
        raise ValueError(f"未知的修复类型: {fix_type}")
