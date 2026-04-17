# -*- coding: utf-8 -*-
"""
冲突检测服务

从数据库查询排课结果，检测四类冲突：
- 班级冲突：同班级同时段多门课（含周次重叠判断）
- 教师冲突：同教师同时段多门课
- 教室冲突：同教室同时段多门课
- 容量不足：学生数超过教室容量
"""
from collections import defaultdict
from app.database import get_db

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
    GROUP_CONCAT(DISTINCT t.teacher_id SEPARATOR ', ')   AS teacher_ids
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

_STUDENT_COUNT_QUERY = """
SELECT SUM(cl.student_count) AS total_students
FROM offering_classes oc
JOIN classes cl ON oc.class_id = cl.class_id
JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
WHERE tt.task_id = %s
"""

_TASK_CLASSES_QUERY = """
SELECT cl.class_id, cl.class_name
FROM offering_classes oc
JOIN classes cl ON oc.class_id = cl.class_id
JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
WHERE tt.task_id = %s
"""

_OFFERING_WEEKS_QUERY = "SELECT offering_id, week_number FROM offering_weeks"


def _has_week_overlap(weeks1, weeks2) -> bool:
    if not weeks1 or not weeks2:
        return True
    return len(weeks1 & weeks2) > 0


def _get_weeks(result, offering_weeks: dict) -> set:
    offering_id = result["offering_id"]
    if offering_id in offering_weeks:
        return offering_weeks[offering_id]
    start_week = result.get("start_week") or 1
    end_week = result.get("end_week") or 17
    week_pattern = result.get("week_pattern") or "CONTINUOUS"
    if week_pattern == "SINGLE":
        return set(w for w in range(start_week, end_week + 1) if w % 2 == 1)
    elif week_pattern == "DOUBLE":
        return set(w for w in range(start_week, end_week + 1) if w % 2 == 0)
    return set(range(start_week, end_week + 1))


def _detect_pairwise_conflicts(schedules_by_key: dict, entity_key: str) -> list:
    """通用二维冲突检测（班级/教师/教室共用）"""
    conflicts = []
    for entity_id, schedules in schedules_by_key.items():
        seen_pairs = set()
        for i in range(len(schedules)):
            for j in range(i + 1, len(schedules)):
                s1, s2 = schedules[i], schedules[j]
                if s1["weekday"] != s2["weekday"]:
                    continue
                if s1["end_slot"] < s2["start_slot"] or s2["end_slot"] < s1["start_slot"]:
                    continue
                if not _has_week_overlap(s1["weeks"], s2["weeks"]):
                    continue
                pair_key = tuple(sorted([s1["schedule_id"], s2["schedule_id"]]))
                if (entity_id, pair_key) in seen_pairs:
                    continue
                seen_pairs.add((entity_id, pair_key))
                overlap_start = max(s1["start_slot"], s2["start_slot"])
                overlap_end = min(s1["end_slot"], s2["end_slot"])
                conflicts.append({
                    entity_key: s1[entity_key],
                    "weekday": s1["weekday"],
                    "overlap_start": overlap_start,
                    "overlap_end": overlap_end,
                    "course1": s1["course"],
                    "teacher1": s1.get("teacher", ""),
                    "classroom1": s1["classroom"],
                    "course2": s2["course"],
                    "teacher2": s2.get("teacher", ""),
                    "classroom2": s2["classroom"],
                })
    return conflicts


def analyze_conflicts(version_id: int) -> dict:
    """
    检测指定版本的四类冲突，返回结构化 dict。
    不打印、不导出 Excel。
    """
    db = get_db()

    # 1. 查询所有排课结果
    results = db.execute_query(_SCHEDULE_QUERY, (version_id,))

    if not results:
        return {
            "version_id": version_id,
            "summary": {
                "class_conflicts": 0,
                "teacher_conflicts": 0,
                "classroom_conflicts": 0,
                "capacity_violations": 0,
                "total": 0,
            },
            "class_conflicts": [],
            "teacher_conflicts": [],
            "classroom_conflicts": [],
            "capacity_violations": [],
        }

    # 2. 加载所有 offering_weeks（一次性，避免 N+1）
    offering_weeks: dict = {}
    for row in db.execute_query(_OFFERING_WEEKS_QUERY):
        oid = row["offering_id"]
        if oid not in offering_weeks:
            offering_weeks[oid] = set()
        offering_weeks[oid].add(row["week_number"])

    # 3. 加载每个 task 对应的班级（一次性批量，避免 N+1）
    task_ids = list({r["task_id"] for r in results})
    task_classes: dict = defaultdict(list)
    if task_ids:
        placeholders = ",".join(["%s"] * len(task_ids))
        rows = db.execute_query(
            f"""
            SELECT tt.task_id, cl.class_id, cl.class_name
            FROM offering_classes oc
            JOIN classes cl ON oc.class_id = cl.class_id
            JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
            WHERE tt.task_id IN ({placeholders})
            """,
            tuple(task_ids),
        )
        for row in rows:
            task_classes[row["task_id"]].append(
                {"class_id": row["class_id"], "class_name": row["class_name"]}
            )

    # 4. 批量查询每个 task 的学生人数
    task_student_count: dict = {}
    if task_ids:
        rows = db.execute_query(
            f"""
            SELECT tt.task_id, SUM(cl.student_count) AS total_students
            FROM offering_classes oc
            JOIN classes cl ON oc.class_id = cl.class_id
            JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
            WHERE tt.task_id IN ({placeholders})
            GROUP BY tt.task_id
            """,
            tuple(task_ids),
        )
        for row in rows:
            task_student_count[row["task_id"]] = int(row["total_students"] or 0)

    # 5. 容量不足检测
    capacity_violations = []
    for r in results:
        student_count = task_student_count.get(r["task_id"], 0)
        capacity = int(r.get("classroom_capacity") or 0)
        if capacity < student_count:
            capacity_violations.append({
                "course": r["course_name"],
                "classroom": r["classroom_name"],
                "capacity": capacity,
                "students": student_count,
                "shortage": student_count - capacity,
                "weekday": r["week_day"],
                "start_slot": r["start_slot"],
                "end_slot": r["start_slot"] + r["slots_count"] - 1,
            })

    # 6. 构建各维度的 schedule 列表
    class_schedules: dict = defaultdict(list)
    teacher_schedules: dict = defaultdict(list)
    classroom_schedules: dict = defaultdict(list)

    for r in results:
        weeks = _get_weeks(r, offering_weeks)
        base = {
            "schedule_id": r["schedule_id"],
            "weekday": r["week_day"],
            "start_slot": r["start_slot"],
            "end_slot": r["start_slot"] + r["slots_count"] - 1,
            "course": r["course_name"],
            "teacher": r["teacher_name"] or "",
            "classroom": r["classroom_name"],
            "weeks": weeks,
        }

        # 班级维度（一个 task 可能对应多个班级）
        for cls in task_classes.get(r["task_id"], []):
            entry = dict(base)
            entry["class_name"] = cls["class_name"]
            class_schedules[cls["class_id"]].append(entry)

        # 教师维度
        teacher_ids_str = r.get("teacher_ids", "") or ""
        for tid in (tid.strip() for tid in teacher_ids_str.split(",") if tid.strip()):
            teacher_schedules[tid].append(base)

        # 教室维度
        classroom_schedules[r["classroom_id"]].append(base)

    # 7. 执行冲突检测
    class_conflicts = _detect_pairwise_conflicts(class_schedules, "class_name")
    teacher_conflicts = _detect_pairwise_conflicts(teacher_schedules, "teacher")
    classroom_conflicts = _detect_pairwise_conflicts(classroom_schedules, "classroom")

    total = (
        len(class_conflicts)
        + len(teacher_conflicts)
        + len(classroom_conflicts)
        + len(capacity_violations)
    )

    return {
        "version_id": version_id,
        "summary": {
            "class_conflicts": len(class_conflicts),
            "teacher_conflicts": len(teacher_conflicts),
            "classroom_conflicts": len(classroom_conflicts),
            "capacity_violations": len(capacity_violations),
            "total": total,
        },
        "class_conflicts": class_conflicts,
        "teacher_conflicts": teacher_conflicts,
        "classroom_conflicts": classroom_conflicts,
        "capacity_violations": capacity_violations,
    }
