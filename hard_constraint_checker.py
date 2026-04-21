# -*- coding: utf-8 -*-
"""
硬约束检查模块
统一管理所有硬约束的检查和报告
"""

from typing import Dict, List, Tuple
from collections import defaultdict


class HardConstraintViolations:
    """统一硬约束违反记录类"""

    def __init__(self):
        self.violations = {
            "teacher_conflict": [],  # [(teacher_id, weekday, slot, items)]
            "class_conflict": [],  # [(class_id, weekday, slot, items)]
            "classroom_conflict": [],  # [(classroom_id, weekday, slot, items)]
            "capacity_violation": [],  # [(schedule_id, shortage)]
            "blackout_violation": [],  # [(schedule_id, teacher_id, weekday, slot)]
            "feature_violation": [],  # [(schedule_id, classroom_id, missing_features)]
            "thursday_afternoon": [],  # [(schedule_id, weekday, start_slot)]
            "campus_commute": [],  # [(teacher_id, weekday, campuses)]
            "weekend_penalty": [],  # [(schedule_id, weekday)]
        }

    def get_summary(self) -> Dict[str, int]:
        """获取总体统计"""
        return {
            constraint: len(violations)
            for constraint, violations in self.violations.items()
        }

    def get_penalty_score(self, config: Dict) -> float:
        """计算总体惩罚分"""
        total_score = 0
        for constraint, violations in self.violations.items():
            if constraint in config.get("penalty_scores", {}):
                penalty = config["penalty_scores"][constraint]
                total_score += len(violations) * penalty
        return total_score

    def add_violation(self, constraint: str, violation_data: Dict):
        """添加违反记录"""
        if constraint in self.violations:
            self.violations[constraint].append(violation_data)


def check_all_hard_constraints(
    solution: List, task_dict: Dict, data: Dict, config: Dict
) -> Tuple[HardConstraintViolations, Dict]:
    """
    完整检查所有硬约束

    Returns:
        (violations_object, summary_dict)
    """
    violations = HardConstraintViolations()

    # 1. 时间冲突检查
    _check_time_conflicts(solution, task_dict, violations)

    # 2. 容量冲突检查
    _check_capacity_violations(solution, task_dict, data, violations)

    # 3. 黑名单时间检查
    _check_blackout_violations(solution, task_dict, data, violations)

    # 4. 教室设施检查
    _check_feature_violations(solution, task_dict, data, violations)

    # 5. 周四下午检查
    _check_thursday_afternoon(solution, task_dict, violations)

    # 6. 校区通勤检查
    _check_campus_commute(solution, task_dict, data, violations)

    # 7. 周末排课检查
    _check_weekend_penalty(solution, task_dict, violations)

    # 生成统计汇总
    summary = {
        "total_violations": sum(len(v) for v in violations.violations.values()),
        "details": violations.get_summary(),
        "penalty_score": violations.get_penalty_score(config),
    }

    return violations, summary


def _check_time_conflicts(
    solution: List, task_dict: Dict, violations: HardConstraintViolations
):
    """检查教师/班级/教室时间冲突"""
    teacher_schedule = defaultdict(list)  # [entity_id][(weekday, slot)] = [task_ids]
    class_schedule = defaultdict(list)
    classroom_schedule = defaultdict(list)

    # 构建时间占用表（只记录起始位置，避免重复）
    for gene in solution:
        task = task_dict.get(gene.task_id)
        if not task:
            continue

        # 记录课程的时间段信息（weekday, start_slot, end_slot, task_id, weeks）
        time_segment = {
            "weekday": gene.week_day,
            "start_slot": gene.start_slot,
            "end_slot": gene.start_slot + task.slots_count - 1,
            "task_id": gene.task_id,
            "weeks": getattr(task, "weeks", None),  # 周次信息
        }

        # 记录所有教师的时间占用
        for teacher_id in task.teachers:
            teacher_schedule[teacher_id].append(time_segment)

        # 记录班级和教室
        for class_id in task.classes:
            class_schedule[class_id].append(time_segment)

        classroom_schedule[gene.classroom_id].append(time_segment)

    # 统计冲突
    def count_and_record_conflicts(schedule_dict, conflict_type):
        count = 0
        for entity_id, segments_list in schedule_dict.items():
            # 检查每对课程是否有时间段重叠
            for i in range(len(segments_list)):
                for j in range(i + 1, len(segments_list)):
                    seg1, seg2 = segments_list[i], segments_list[j]

                    # 检查周几是否相同
                    if seg1["weekday"] != seg2["weekday"]:
                        continue

                    # 检查时间段是否重叠
                    if (
                        seg1["end_slot"] < seg2["start_slot"]
                        or seg2["end_slot"] < seg1["start_slot"]
                    ):
                        continue

                    # 检查周次是否重叠（如果有周次信息）
                    weeks1 = seg1.get("weeks")
                    weeks2 = seg2.get("weeks")
                    if weeks1 is not None and weeks2 is not None:
                        # 如果都有周次信息，检查是否重叠
                        if not (weeks1 & weeks2):  # 没有交集
                            continue

                    # 确认冲突
                    violations.add_violation(
                        conflict_type,
                        {
                            "entity_id": entity_id,
                            "weekday": seg1["weekday"],
                            "start_slot": max(seg1["start_slot"], seg2["start_slot"]),
                            "end_slot": min(seg1["end_slot"], seg2["end_slot"]),
                            "task_ids": (seg1["task_id"], seg2["task_id"]),
                        },
                    )
                    count += 1
        return count

    count_and_record_conflicts(teacher_schedule, "teacher_conflict")
    count_and_record_conflicts(class_schedule, "class_conflict")
    count_and_record_conflicts(classroom_schedule, "classroom_conflict")


def _check_capacity_violations(
    solution: List, task_dict: Dict, data: Dict, violations: HardConstraintViolations
):
    """检查教室容量不足"""
    classrooms = data.get("classrooms", {})

    for gene in solution:
        task = task_dict.get(gene.task_id)
        if not task:
            continue

        classroom = classrooms.get(gene.classroom_id)
        if not classroom:
            continue

        if classroom.capacity < task.student_count:
            violations.add_violation(
                "capacity_violation",
                {
                    "task_id": gene.task_id,
                    "classroom_id": gene.classroom_id,
                    "capacity": classroom.capacity,
                    "students": task.student_count,
                    "shortage": task.student_count - classroom.capacity,
                },
            )


def _check_blackout_violations(
    solution: List, task_dict: Dict, data: Dict, violations: HardConstraintViolations
):
    """检查教师黑名单时间违反"""
    teacher_blackouts = defaultdict(set)

    # 构建黑名单映射
    for blackout in data.get("teacher_blackout_times", []):
        for slot in range(blackout.start_slot, blackout.end_slot + 1):
            teacher_blackouts[blackout.teacher_id].add((blackout.weekday, slot))

    for gene in solution:
        task = task_dict.get(gene.task_id)
        if not task:
            continue

        for slot in range(gene.start_slot, gene.start_slot + task.slots_count):
            time_key = (gene.week_day, slot)

            for teacher_id in task.teachers:
                if time_key in teacher_blackouts[teacher_id]:
                    violations.add_violation(
                        "blackout_violation",
                        {
                            "task_id": gene.task_id,
                            "teacher_id": teacher_id,
                            "weekday": gene.week_day,
                            "slot": slot,
                        },
                    )


def _check_feature_violations(
    solution: List, task_dict: Dict, data: Dict, violations: HardConstraintViolations
):
    """检查教室设施不符要求"""
    classrooms = data.get("classrooms", {})

    for gene in solution:
        task = task_dict.get(gene.task_id)
        if not task:
            continue

        classroom = classrooms.get(gene.classroom_id)
        if not classroom:
            continue

        # 检查必需特征
        missing_features = task.required_features - classroom.features

        if missing_features:
            violations.add_violation(
                "feature_violation",
                {
                    "task_id": gene.task_id,
                    "classroom_id": gene.classroom_id,
                    "missing_features": list(missing_features),
                },
            )


def _check_thursday_afternoon(
    solution: List, task_dict: Dict, violations: HardConstraintViolations
):
    """检查周四下午（第6-10节）禁排"""
    for gene in solution:
        task = task_dict.get(gene.task_id)
        if not task:
            continue

        # 周四 = 4，禁排时间段：第6-10节
        # 检查课程是否与禁排时间有任何重叠
        end_slot = gene.start_slot + task.slots_count - 1

        if gene.week_day == 4:
            # 检查课程时间段[start_slot, end_slot]是否与禁排时间[6, 10]有重叠
            # 重叠条件：end_slot >= 6 AND start_slot <= 10
            if end_slot >= 6 and gene.start_slot <= 10:
                violations.add_violation(
                    "thursday_afternoon",
                    {
                        "task_id": gene.task_id,
                        "weekday": gene.week_day,
                        "start_slot": gene.start_slot,
                        "end_slot": end_slot,
                        "overlap_with_forbidden": (
                            max(6, gene.start_slot),
                            min(10, end_slot),
                        ),
                    },
                )


def _check_campus_commute(
    solution: List, task_dict: Dict, data: Dict, violations: HardConstraintViolations
):
    """检查教师一天跨多个校区"""
    classrooms = data.get("classrooms", {})
    teacher_daily_campuses = defaultdict(lambda: defaultdict(set))

    for gene in solution:
        task = task_dict.get(gene.task_id)
        if not task:
            continue

        classroom = classrooms.get(gene.classroom_id)
        if not classroom:
            continue

        for teacher_id in task.teachers:
            teacher_daily_campuses[teacher_id][gene.week_day].add(classroom.campus_id)

    for teacher_id, daily_campuses in teacher_daily_campuses.items():
        for weekday, campuses in daily_campuses.items():
            if len(campuses) > 1:
                violations.add_violation(
                    "campus_commute",
                    {
                        "teacher_id": teacher_id,
                        "weekday": weekday,
                        "campuses": list(campuses),
                        "campus_count": len(campuses),
                    },
                )


def _check_weekend_penalty(
    solution: List, task_dict: Dict, violations: HardConstraintViolations
):
    """检查周末排课"""
    for gene in solution:
        # 周六 = 6, 周日 = 7
        if gene.week_day in [6, 7]:
            violations.add_violation(
                "weekend_penalty",
                {"task_id": gene.task_id, "weekday": gene.week_day},
            )


def generate_hard_constraint_report(
    violations: HardConstraintViolations, config: Dict, logger
) -> str:
    """生成格式化的硬约束报告"""
    report_lines = [
        "\n【硬约束完整检查报告】",
        "=" * 70,
        "",
        "硬约束违反统计：",
        "-" * 70,
    ]

    summary = violations.get_summary()
    total_violations = 0
    total_penalty = 0

    # 按优先级排序显示
    constraint_order = [
        "class_conflict",
        "teacher_conflict",
        "classroom_conflict",
        "capacity_violation",
        "blackout_violation",
        "feature_violation",
        "thursday_afternoon",
        "campus_commute",
        "weekend_penalty",
    ]

    for constraint in constraint_order:
        if constraint not in summary:
            continue

        count = summary[constraint]
        penalty = config.get("penalty_scores", {}).get(constraint, 0)
        total_penalty_for_constraint = count * penalty if count > 0 else 0

        constraint_name = {
            "teacher_conflict": "教师时间冲突",
            "class_conflict": "班级时间冲突",
            "classroom_conflict": "教室时间冲突",
            "capacity_violation": "教室容量不足",
            "blackout_violation": "教师黑名单时间违反",
            "feature_violation": "教室设施不符",
            "thursday_afternoon": "周四下午禁排违反",
            "campus_commute": "教师校区通勤冲突",
            "weekend_penalty": "周末排课违反",
        }.get(constraint, constraint)

        if count > 0:
            report_lines.append(
                f"{constraint_name:20} : {count:5} 处  |  "
                f"单次惩罚: {penalty:8} | 总惩罚: {total_penalty_for_constraint:10}"
            )
            total_violations += count
            total_penalty += total_penalty_for_constraint
        else:
            report_lines.append(f"{constraint_name:20} : {count:5} 处  |  ✓ 满足")

    report_lines.extend(
        [
            "-" * 70,
            f"总硬约束违反数：{total_violations} 处",
            f"总惩罚分数：{int(total_penalty):,}",
            "=" * 70,
            "",
        ]
    )

    return "\n".join(report_lines)
