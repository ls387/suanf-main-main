# -*- coding: utf-8 -*-
"""
智能排课系统主程序
使用遗传算法解决复杂的排课优化问题
"""

import argparse
import logging
import os
import sys
import time
from typing import Dict, List

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_connector import DatabaseConnector, DataLoader
from genetic_algorithm import SchedulingGeneticAlgorithm
from data_models import Gene, ScheduleVersion
from hard_constraint_checker import (
    check_all_hard_constraints,
    generate_hard_constraint_report,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scheduling.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class SchedulingSystem:
    """排课系统主类"""

    # === 配置常量 ===
    # 容量浪费阈值配置
    WASTE_RATIO_SMALL_CLASS = 0.5  # 小班(<30人)允许50%浪费
    WASTE_RATIO_MID_CLASS = 0.4  # 中班(30-60人)允许40%
    WASTE_RATIO_LARGE_CLASS = 0.3  # 大班(>60人)允许30%

    SMALL_CLASS_THRESHOLD = 30  # 小班阈值
    MID_CLASS_THRESHOLD = 60  # 中班阈值

    # 显示配置
    MAX_DISPLAY_CONFLICTS = 5  # 冲突详情最多显示数量
    MAX_DISPLAY_VIOLATIONS = 5  # 容量违规最多显示数量
    MAX_DISPLAY_WASTE = 10  # 容量浪费最多显示数量
    MAX_DISPLAY_PREFERENCES = 10  # 偏好未满足最多显示数量

    # 利用率阈值
    LOW_UTILIZATION_THRESHOLD = 0.5  # 利用率过低阈值

    def __init__(self):
        self.db_connector = None
        self.data_loader = None

    def setup_database_connection(self):
        """设置数据库连接"""
        from db_config import get_db_config

        db_config = get_db_config()
        logger.info(
            f"连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        self.db_connector = DatabaseConnector(**db_config)
        self.db_connector.connect()
        self.data_loader = DataLoader(self.db_connector)

    def validate_version(self, version_id: int) -> bool:
        """验证排课版本是否存在且状态正确，不存在则自动创建"""
        query = "SELECT * FROM schedule_versions WHERE version_id = %s"
        result = self.db_connector.execute_query(query, (version_id,))

        if not result:
            logger.error(f"排课版本 {version_id} 不存在")
            return False

        version = result[0]
        if version["status"] != "draft":
            logger.error(
                f"排课版本 {version_id} 状态为 {version['status']}，不是草案状态"
            )
            return False

        logger.info(f"验证版本成功: {version['version_name']} ({version['semester']})")
        return True

    def validate_data_integrity(self, data: Dict) -> bool:
        """验证数据完整性"""
        logger.info("开始验证数据完整性")

        issues = []

        # 检查是否有教学任务
        if not data["teaching_tasks"]:
            issues.append("没有找到教学任务")

        # 检查任务是否有教师
        tasks_without_teachers = [
            task for task in data["teaching_tasks"] if not task.teachers
        ]
        if tasks_without_teachers:
            issues.append(f"有 {len(tasks_without_teachers)} 个任务没有分配教师")

        # 检查任务是否有班级
        tasks_without_classes = [
            task for task in data["teaching_tasks"] if not task.classes
        ]
        if tasks_without_classes:
            issues.append(f"有 {len(tasks_without_classes)} 个任务没有分配班级")

        # 检查是否有可用教室
        if not data["classrooms"]:
            issues.append("没有可用教室")

        # 检查slots_count的有效性
        invalid_slots = [
            task for task in data["teaching_tasks"] if task.slots_count not in [2, 3, 4]
        ]
        if invalid_slots:
            issues.append(f"有 {len(invalid_slots)} 个任务的节数不在有效范围(2,3,4)内")

        # 输出问题
        if issues:
            logger.error("数据完整性检查失败:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        logger.info("数据完整性检查通过")
        logger.info(f"  - 教学任务: {len(data['teaching_tasks'])} 个")
        logger.info(f"  - 教师: {len(data['teachers'])} 人")
        logger.info(f"  - 教室: {len(data['classrooms'])} 间")
        logger.info(f"  - 班级: {len(data['classes'])} 个")

        return True

    def run_scheduling(
        self, version_id: int, grades: List[int] = None, ga_config: Dict = None
    ) -> bool:
        """运行排课算法"""
        try:
            start_time = time.time()

            # 验证版本
            if not self.validate_version(version_id):
                return False

            # 获取学期信息
            version_query = (
                "SELECT semester FROM schedule_versions WHERE version_id = %s"
            )
            version_result = self.db_connector.execute_query(
                version_query, (version_id,)
            )
            semester = version_result[0]["semester"]

            # 加载数据
            logger.info(f"开始加载学期 {semester} 的数据")
            if grades:
                logger.info(f"限制年级范围: {grades}")
            data = self.data_loader.load_all_data(semester, grades)

            # 验证数据完整性
            if not self.validate_data_integrity(data):
                return False

            # 初始化遗传算法（添加进度回调）
            logger.info("初始化遗传算法")

            # 定义进度回调函数
            def progress_callback(event: dict):
                """进度回调：接收事件字典"""
                stage = event.get("stage", "")
                generation = event.get("generation", 0)
                total_generations = event.get(
                    "total_generations", ga_config.get("generations", 200)
                )
                best_fitness = event.get("best_fitness", 0.0)
                percent = event.get("percent", 0)

                if stage == "evolving" and (
                    generation % 10 == 0 or generation == total_generations - 1
                ):
                    logger.info(
                        f"[进化进度] {percent}% | 第 {generation}/{total_generations} 代 | "
                        f"最佳适应度: {best_fitness:.2f}"
                    )

            # 将回调函数添加到配置
            if ga_config is None:
                ga_config = {}
            ga_config["progress_callback"] = progress_callback

            ga = SchedulingGeneticAlgorithm(data, ga_config)

            # 运行算法
            logger.info("开始运行遗传算法")
            best_solution = ga.evolve()

            # 保存结果
            logger.info("保存排课结果")
            self.data_loader.save_schedule_results(
                version_id, best_solution, ga.task_dict
            )

            # 生成统计报告
            self._generate_report(
                version_id, best_solution, ga.task_dict, data, ga.config
            )

            end_time = time.time()
            logger.info(f"排课完成，总耗时: {end_time - start_time:.2f} 秒")

            return True

        except Exception as e:
            logger.error(f"排课过程中发生错误: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def _generate_report(
        self,
        version_id: int,
        solution: List[Gene],
        task_dict: Dict,
        data: Dict,
        config: Dict = None,
    ):
        """生成排课统计报告"""
        logger.info("生成排课统计报告")

        if config is None:
            config = {}

        total_tasks = len(data["teaching_tasks"])
        scheduled_tasks = len(solution)
        coverage_rate = (scheduled_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        logger.info(
            f"排课覆盖率: {coverage_rate:.1f}% ({scheduled_tasks}/{total_tasks})"
        )

        # ============ 新增：完整硬约束检查系统 ============
        logger.info("\n" + "=" * 70)
        logger.info("执行完整硬约束检查")
        logger.info("=" * 70)

        violations, summary = check_all_hard_constraints(
            solution, task_dict, data, config
        )

        # 输出详细报告
        report_text = generate_hard_constraint_report(violations, config, logger)
        logger.info(report_text)

        # 输出总体评估
        total_violations = summary["total_violations"]
        if total_violations == 0:
            logger.info("✓ 优秀：没有发现任何硬约束违反！")
        else:
            logger.warning(
                f"⚠ 警告：发现 {total_violations} 处硬约束违反，总惩罚分数: {int(summary['penalty_score']):,}"
            )

        # ============ 继续其他分析 ============

        # 教室利用率统计
        self._analyze_classroom_utilization(solution, task_dict, data)

        # 个性化要求满足情况分析
        self._analyze_preference_satisfaction(solution, task_dict, data)

    def _print_conflict_details(
        self, conflict_details: List[Dict], entity_type: str, data: Dict
    ):
        """打印冲突详细信息（显示所有冲突）"""
        day_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, conflict in enumerate(conflict_details, 1):
            entity_id = conflict["entity_id"]
            weekday = conflict["weekday"]
            slot = conflict["slot"]

            # 使用辅助方法获取实体名称
            entity_name_str = self._get_entity_name(entity_id, entity_type, data)

            logger.warning(
                f"    [{i}] {entity_type}: {entity_name_str}, "
                f"时间: {day_names[weekday]} 第{slot}节"
            )

            for j, task_info in enumerate(conflict["tasks"], 1):
                # 使用辅助方法获取名称
                teacher_str = self._get_entity_name(
                    task_info["teacher_id"], "教师", data
                )
                classroom_str = self._get_entity_name(
                    task_info["classroom_id"], "教室", data
                )

                logger.warning(
                    f"        课程{j}: {task_info['course_name']} | "
                    f"教师: {teacher_str} | "
                    f"教室: {classroom_str} | "
                    f"时间: {task_info['start_slot']}-"
                    f"{task_info['start_slot']+task_info['slots_count']-1}节"
                )

        logger.warning(f"【共计 {len(conflict_details)} 处{entity_type}冲突】")

    def _check_conflicts(
        self, solution: List[Gene], task_dict: Dict, data: Dict
    ) -> Dict:
        """检查冲突并返回详细信息"""
        from collections import defaultdict

        teacher_schedule = defaultdict(list)
        class_schedule = defaultdict(list)
        classroom_schedule = defaultdict(list)

        # 用于存储基因信息，方便后续查找
        gene_map = {}

        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                logger.warning(f"任务 {gene.task_id} 不存在，跳过")
                continue

            # 预先计算时间slots（性能优化）
            time_slots = [
                (gene.week_day, slot)
                for slot in range(gene.start_slot, gene.start_slot + task.slots_count)
            ]

            gene_map[gene.task_id] = gene

            # 批量添加（性能优化）
            for time_key in time_slots:
                # 修复: 检查任务的所有教师
                for teacher_id in task.teachers:
                    teacher_schedule[teacher_id].append((time_key, gene.task_id))
                classroom_schedule[gene.classroom_id].append((time_key, gene.task_id))
                for class_id in task.classes:
                    class_schedule[class_id].append((time_key, gene.task_id))

        # 检测冲突并记录详细信息
        def find_conflicts(schedule_dict, entity_type):
            """查找冲突详情"""
            conflict_count = 0
            conflict_details = []

            for entity_id, time_list in schedule_dict.items():
                # 按时间分组
                time_dict = defaultdict(list)
                for time_key, task_id in time_list:
                    time_dict[time_key].append(task_id)

                # 找出有冲突的时间点
                for time_key, task_ids in time_dict.items():
                    if len(task_ids) > 1:
                        conflict_count += 1
                        weekday, slot = time_key

                        # 获取冲突任务的详细信息
                        conflict_info = {
                            "entity_id": entity_id,
                            "weekday": weekday,
                            "slot": slot,
                            "tasks": [],
                        }

                        for task_id in task_ids:
                            gene = gene_map.get(task_id)
                            task = task_dict.get(task_id)

                            if not gene or not task:
                                logger.warning(f"冲突分析: 任务 {task_id} 数据缺失")
                                continue

                            # 使用辅助方法获取课程名称
                            course_name_str = self._get_course_name(task, data)

                            conflict_info["tasks"].append(
                                {
                                    "task_id": task_id,
                                    "course_name": course_name_str,
                                    "teacher_id": gene.teacher_id,
                                    "classroom_id": gene.classroom_id,
                                    "start_slot": gene.start_slot,
                                    "slots_count": task.slots_count,
                                }
                            )

                        conflict_details.append(conflict_info)

            return conflict_count, conflict_details

        teacher_count, teacher_details = find_conflicts(teacher_schedule, "teacher")
        class_count, class_details = find_conflicts(class_schedule, "class")
        classroom_count, classroom_details = find_conflicts(
            classroom_schedule, "classroom"
        )

        return {
            "teacher_count": teacher_count,
            "teacher_details": teacher_details,
            "class_count": class_count,
            "class_details": class_details,
            "classroom_count": classroom_count,
            "classroom_details": classroom_details,
        }

    def _check_capacity_violations(
        self, solution: List[Gene], task_dict: Dict, data: Dict
    ) -> List[Dict]:
        """检查容量不足冲突（硬约束）"""
        capacity_violations = []

        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                logger.warning(f"容量检查: 任务 {gene.task_id} 不存在，跳过")
                continue

            classroom = data["classrooms"].get(gene.classroom_id)
            if not classroom:
                logger.warning(f"容量检查: 教室 {gene.classroom_id} 不存在，跳过")
                continue

            # 检查容量是否足够（添加类型验证）
            if (
                classroom.capacity is not None
                and task.student_count is not None
                and classroom.capacity < task.student_count
            ):

                # 使用辅助方法获取课程名称
                course_name = self._get_course_name(task, data)

                capacity_violations.append(
                    {
                        "course": course_name,
                        "classroom": classroom.classroom_name or gene.classroom_id,
                        "capacity": classroom.capacity,
                        "students": task.student_count,
                        "shortage": task.student_count - classroom.capacity,
                    }
                )

        return capacity_violations

    def _check_advanced_hard_constraints(
        self, solution: List[Gene], task_dict: Dict, data: Dict
    ) -> Dict:
        """检查高级硬约束违规（周末、跨校区、禁排时间、设施、黑名单）"""
        from collections import defaultdict

        day_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        violations = {
            "weekend_violations": [],
            "weekend_count": 0,
            "campus_commute_violations": [],
            "campus_commute_count": 0,
            "thursday_afternoon_violations": [],
            "thursday_afternoon_count": 0,
            "feature_violations": [],
            "feature_violation_count": 0,
            "blackout_violations": [],
            "blackout_count": 0,
        }

        # 1. 检查周末排课
        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                continue

            if gene.week_day in [6, 7]:  # 周六/周日
                teacher_name = "未知"
                if hasattr(gene, "teacher_id"):
                    teacher_name = self._get_entity_name(gene.teacher_id, "教师", data)

                violations["weekend_violations"].append(
                    {
                        "course": self._get_course_name(task, data),
                        "day_name": day_names[gene.week_day],
                        "slot": gene.start_slot,
                        "end_slot": gene.start_slot + task.slots_count - 1,
                        "teacher": teacher_name,
                        "class": ", ".join(
                            [
                                self._get_entity_name(c, "班级", data)
                                for c in task.classes
                            ]
                        ),
                    }
                )
                violations["weekend_count"] += 1

        # 2. 检查教师一天跨校区
        teacher_daily_campuses = defaultdict(lambda: defaultdict(set))
        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                continue
            classroom = data["classrooms"].get(gene.classroom_id)
            if not classroom:
                continue

            for teacher_id in task.teachers:
                campus_id = getattr(classroom, "campus_id", None)
                if campus_id:
                    teacher_daily_campuses[teacher_id][gene.week_day].add(campus_id)

        for teacher_id, daily_campuses in teacher_daily_campuses.items():
            for weekday, campuses in daily_campuses.items():
                if len(campuses) > 1:
                    campus_names = []
                    for campus_id in campuses:
                        campus_names.append(str(campus_id))
                    violations["campus_commute_violations"].append(
                        {
                            "teacher": self._get_entity_name(teacher_id, "教师", data),
                            "day_name": day_names[weekday],
                            "campuses": campus_names,
                        }
                    )
                    violations["campus_commute_count"] += 1

        # 3. 检查周四下午（6-10节）禁排
        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                continue

            if gene.week_day == 4 and 6 <= gene.start_slot <= 10:
                teacher_name = "未知"
                if hasattr(gene, "teacher_id"):
                    teacher_name = self._get_entity_name(gene.teacher_id, "教师", data)

                violations["thursday_afternoon_violations"].append(
                    {
                        "course": self._get_course_name(task, data),
                        "start_slot": gene.start_slot,
                        "end_slot": gene.start_slot + task.slots_count - 1,
                        "teacher": teacher_name,
                        "class": ", ".join(
                            [
                                self._get_entity_name(c, "班级", data)
                                for c in task.classes
                            ]
                        ),
                    }
                )
                violations["thursday_afternoon_count"] += 1

        # 4. 检查教室设施不符
        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                continue
            classroom = data["classrooms"].get(gene.classroom_id)
            if not classroom:
                continue

            classroom_features = getattr(classroom, "features", set())
            if isinstance(classroom_features, set):
                if not task.required_features.issubset(classroom_features):
                    missing_features = task.required_features - classroom_features
                    violations["feature_violations"].append(
                        {
                            "course": self._get_course_name(task, data),
                            "classroom": classroom.classroom_name or gene.classroom_id,
                            "required": list(missing_features),
                        }
                    )
                    violations["feature_violation_count"] += 1

        # 5. 检查教师黑名单时间
        teacher_blackouts = data.get("teacher_blackout_times", [])
        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                continue

            for teacher_id in task.teachers:
                # 检查课程是否在黑名单时间内
                for blackout in teacher_blackouts:
                    # 黑名单时间可能是对象或字典，兼容两种形式
                    blackout_teacher = (
                        blackout.teacher_id
                        if hasattr(blackout, "teacher_id")
                        else blackout.get("teacher_id")
                    )
                    blackout_weekday = (
                        blackout.weekday
                        if hasattr(blackout, "weekday")
                        else blackout.get("weekday")
                    )
                    blackout_start = (
                        blackout.start_slot
                        if hasattr(blackout, "start_slot")
                        else blackout.get("start_slot")
                    )
                    blackout_end = (
                        blackout.end_slot
                        if hasattr(blackout, "end_slot")
                        else blackout.get("end_slot")
                    )

                    if (
                        blackout_teacher == teacher_id
                        and blackout_weekday == gene.week_day
                    ):
                        # 检查课程是否与黑名单时间重叠
                        course_slots = set(
                            range(gene.start_slot, gene.start_slot + task.slots_count)
                        )
                        blackout_slots = set(range(blackout_start, blackout_end + 1))
                        if course_slots & blackout_slots:  # 有重叠
                            overlapping_slots = course_slots & blackout_slots
                            for slot in sorted(overlapping_slots):
                                violations["blackout_violations"].append(
                                    {
                                        "teacher": self._get_entity_name(
                                            teacher_id, "教师", data
                                        ),
                                        "day_name": day_names[gene.week_day],
                                        "slot": slot,
                                        "course": self._get_course_name(task, data),
                                    }
                                )
                                violations["blackout_count"] += 1
                            break

        return violations

    def _analyze_classroom_utilization(
        self, solution: List[Gene], task_dict: Dict, data: Dict
    ):
        """分析教室利用率和容量浪费（软约束优化）"""
        from collections import defaultdict

        classroom_usage = defaultdict(list)
        high_waste = []
        total_waste_seats = 0

        for gene in solution:
            task = task_dict.get(gene.task_id)
            classroom = data["classrooms"].get(gene.classroom_id)

            if not task or not classroom:
                continue

            utilization = (
                task.student_count / classroom.capacity
                if classroom.capacity and classroom.capacity > 0
                else 0
            )
            classroom_usage[gene.classroom_id].append(utilization)

            # 检查容量浪费
            if classroom.capacity and classroom.capacity > 0:
                waste_seats = classroom.capacity - task.student_count
                total_waste_seats += waste_seats
                waste_ratio = waste_seats / classroom.capacity

                # 使用辅助方法获取最大浪费率
                max_waste_ratio = self._get_max_waste_ratio(task.student_count)

                if waste_ratio > max_waste_ratio:
                    # 使用辅助方法获取课程名称
                    course_name = self._get_course_name(task, data)

                    high_waste.append(
                        {
                            "course": course_name,
                            "classroom": classroom.classroom_name or gene.classroom_id,
                            "capacity": classroom.capacity,
                            "students": task.student_count,
                            "waste_seats": waste_seats,
                            "waste_ratio": waste_ratio,
                            "utilization": utilization,
                        }
                    )

        # 计算平均利用率
        total_utilization = 0
        used_classrooms = 0

        for classroom_id, utilizations in classroom_usage.items():
            avg_util = sum(utilizations) / len(utilizations)
            total_utilization += avg_util
            used_classrooms += 1

        if used_classrooms > 0:
            overall_utilization = total_utilization / used_classrooms
            logger.info(f"\n【教室利用率分析】")
            logger.info(f"教室平均利用率: {overall_utilization:.1%}")
            logger.info(f"总计浪费座位数: {total_waste_seats} 个")
            logger.info(
                f"平均每节课浪费: {total_waste_seats / len(solution):.1f} 个座位"
            )

        # 找出利用率过低的教室（使用常量）
        low_utilization_classrooms = [
            (classroom_id, sum(utils) / len(utils))
            for classroom_id, utils in classroom_usage.items()
            if sum(utils) / len(utils) < self.LOW_UTILIZATION_THRESHOLD
        ]

        if low_utilization_classrooms:
            logger.warning(
                f"发现 {len(low_utilization_classrooms)} 间教室利用率过低"
                f"(<{self.LOW_UTILIZATION_THRESHOLD:.0%})"
            )

        # 报告容量浪费情况（使用常量）
        if high_waste:
            logger.warning(f"\n【容量浪费检测】")
            logger.warning(f"⚠ 发现 {len(high_waste)} 个教室容量浪费严重的课程:")
            high_waste.sort(key=lambda x: x["waste_ratio"], reverse=True)
            for i, item in enumerate(high_waste[: self.MAX_DISPLAY_WASTE], 1):
                logger.warning(
                    f"  [{i}] {item['course']}: 教室 {item['classroom']} "
                    f"(容量{item['capacity']}) > 学生数{item['students']}, "
                    f"浪费 {item['waste_seats']} 个座位 "
                    f"(浪费率{item['waste_ratio']:.1%}, 利用率{item['utilization']:.1%})"
                )
            if len(high_waste) > self.MAX_DISPLAY_WASTE:
                logger.warning(
                    f"  ... 还有 {len(high_waste) - self.MAX_DISPLAY_WASTE} "
                    f"个浪费严重的课程"
                )
        else:
            logger.info("\n【容量浪费检测】")
            logger.info("✓ 教室容量分配合理，无严重浪费")

    def _analyze_preference_satisfaction(
        self, solution: List[Gene], task_dict: Dict, data: Dict
    ):
        """分析个性化要求满足情况"""
        from collections import defaultdict
        from data_models import PreferenceType

        logger.info("\n【个性化要求满足情况分析】")

        total_preferences = len(data["teacher_preferences"])
        if total_preferences == 0:
            logger.info("✓ 没有设置个性化要求")
            return

        logger.info(f"总共有 {total_preferences} 条个性化要求")

        # 按教师分组个性化要求
        teacher_prefs = defaultdict(lambda: {"preferred": [], "avoided": []})
        for pref in data["teacher_preferences"]:
            if pref.preference_type == PreferenceType.PREFERRED:
                teacher_prefs[pref.teacher_id]["preferred"].append(pref)
            else:
                teacher_prefs[pref.teacher_id]["avoided"].append(pref)

        # 构建教师实际排课时间
        teacher_schedules = defaultdict(list)
        for gene in solution:
            task = task_dict.get(gene.task_id)
            if not task:
                continue

            # 注意：一个任务可能有多个教师
            for teacher_id in task.teachers:
                start_slot = gene.start_slot
                end_slot = start_slot + task.slots_count - 1

                # 使用辅助方法获取课程名称
                course_name = self._get_course_name(task, data)

                teacher_schedules[teacher_id].append(
                    {
                        "weekday": gene.week_day,
                        "start_slot": start_slot,
                        "end_slot": end_slot,
                        "course_name": course_name,
                        "task_id": gene.task_id,
                    }
                )

        # 分析每个教师的个性化要求满足情况
        violated_preferred = []
        violated_avoided = []

        for teacher_id, prefs in teacher_prefs.items():
            # 使用辅助方法获取教师名称
            teacher_name_str = self._get_entity_name(teacher_id, "教师", data)
            schedule = teacher_schedules.get(teacher_id, [])

            # 检查偏好时间（PREFERRED）
            for pref in prefs["preferred"]:
                if pref.weekday and pref.start_slot and pref.end_slot:
                    found = False
                    for sch in schedule:
                        if sch["weekday"] == pref.weekday:
                            if not (
                                sch["end_slot"] < pref.start_slot
                                or sch["start_slot"] > pref.end_slot
                            ):
                                found = True
                                break

                    if not found:
                        violated_preferred.append(
                            {
                                "teacher_id": teacher_id,
                                "teacher_name": teacher_name_str,
                                "weekday": pref.weekday,
                                "start_slot": pref.start_slot,
                                "end_slot": pref.end_slot,
                                "penalty_score": pref.penalty_score,
                            }
                        )

            # 检查避免时间（AVOIDED）
            for pref in prefs["avoided"]:
                if pref.weekday and pref.start_slot and pref.end_slot:
                    for sch in schedule:
                        if sch["weekday"] == pref.weekday:
                            if not (
                                sch["end_slot"] < pref.start_slot
                                or sch["start_slot"] > pref.end_slot
                            ):
                                violated_avoided.append(
                                    {
                                        "teacher_id": teacher_id,
                                        "teacher_name": teacher_name_str,
                                        "weekday": pref.weekday,
                                        "start_slot": pref.start_slot,
                                        "end_slot": pref.end_slot,
                                        "course_name": sch["course_name"],
                                        "course_time": f"{sch['start_slot']}-{sch['end_slot']}节",
                                        "penalty_score": pref.penalty_score,
                                    }
                                )
                                break

        # 输出分析结果（使用常量）
        day_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        if violated_preferred:
            logger.warning(f"\n⚠ 发现 {len(violated_preferred)} 条偏好时间未被满足:")
            for i, item in enumerate(
                violated_preferred[: self.MAX_DISPLAY_PREFERENCES], 1
            ):
                logger.warning(
                    f"  [{i}] 教师: {item['teacher_name']}, "
                    f"偏好时间: {day_names[item['weekday']]} "
                    f"{item['start_slot']}-{item['end_slot']}节, "
                    f"惩罚分数: {item['penalty_score']}"
                )
            if len(violated_preferred) > self.MAX_DISPLAY_PREFERENCES:
                logger.warning(
                    f"  ... 还有 "
                    f"{len(violated_preferred) - self.MAX_DISPLAY_PREFERENCES} "
                    f"条偏好时间未满足"
                )
        else:
            logger.info("✓ 所有偏好时间都已满足")

        if violated_avoided:
            logger.warning(f"\n⚠ 发现 {len(violated_avoided)} 条避免时间被违反:")
            for i, item in enumerate(
                violated_avoided[: self.MAX_DISPLAY_PREFERENCES], 1
            ):
                logger.warning(
                    f"  [{i}] 教师: {item['teacher_name']}, "
                    f"避免时间: {day_names[item['weekday']]} "
                    f"{item['start_slot']}-{item['end_slot']}节, "
                    f"实际课程: {item['course_name']} ({item['course_time']}), "
                    f"惩罚分数: {item['penalty_score']}"
                )
            if len(violated_avoided) > self.MAX_DISPLAY_PREFERENCES:
                logger.warning(
                    f"  ... 还有 "
                    f"{len(violated_avoided) - self.MAX_DISPLAY_PREFERENCES} "
                    f"条避免时间被违反"
                )
        else:
            logger.info("✓ 所有避免时间都已遵守")

        # 计算总体满足率
        total_prefs_count = sum(
            len(p["preferred"]) + len(p["avoided"]) for p in teacher_prefs.values()
        )
        satisfied_count = (
            total_prefs_count - len(violated_preferred) - len(violated_avoided)
        )
        satisfaction_rate = (
            (satisfied_count / total_prefs_count * 100)
            if total_prefs_count > 0
            else 100
        )

        logger.info(
            f"\n个性化要求总体满足率: {satisfaction_rate:.1f}% "
            f"({satisfied_count}/{total_prefs_count})"
        )

    # === 辅助方法 ===
    def _get_course_name(self, task, data: Dict) -> str:
        """获取课程名称（避免重复代码）"""
        if not task.offering:
            return "未知课程"
        course = data["courses"].get(task.offering.course_id)
        return course.course_name if course else "未知课程"

    def _get_entity_name(self, entity_id: str, entity_type: str, data: Dict) -> str:
        """获取实体名称（教师/班级/教室）"""
        if entity_type == "教师":
            entity = data["teachers"].get(entity_id)
            return entity.teacher_name if entity else entity_id
        elif entity_type == "班级":
            entity = data["classes"].get(entity_id)
            return entity.class_name if entity else entity_id
        else:  # 教室
            entity = data["classrooms"].get(entity_id)
            return entity.classroom_name if entity else entity_id

    def _get_max_waste_ratio(self, student_count: int) -> float:
        """根据班级规模获取最大容量浪费率"""
        if student_count < self.SMALL_CLASS_THRESHOLD:
            return self.WASTE_RATIO_SMALL_CLASS
        elif student_count < self.MID_CLASS_THRESHOLD:
            return self.WASTE_RATIO_MID_CLASS
        else:
            return self.WASTE_RATIO_LARGE_CLASS

    def cleanup(self):
        """清理资源"""
        if self.db_connector:
            self.db_connector.disconnect()


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="智能排课系统")

    parser.add_argument("--version", type=int, required=True, help="排课版本ID")
    parser.add_argument("--semester", type=str, help="学期（如果不指定则从版本中获取）")
    parser.add_argument(
        "--population", type=int, default=100, help="种群大小 (默认: 100)"
    )
    parser.add_argument(
        "--generations", type=int, default=200, help="进化代数 (默认: 200)"
    )
    parser.add_argument(
        "--crossover-rate", type=float, default=0.8, help="交叉率 (默认: 0.8)"
    )
    parser.add_argument(
        "--mutation-rate", type=float, default=0.1, help="变异率 (默认: 0.1)"
    )
    parser.add_argument(
        "--tournament-size", type=int, default=5, help="锦标赛大小 (默认: 5)"
    )
    parser.add_argument(
        "--elitism-size", type=int, default=10, help="精英个体数量 (默认: 10)"
    )
    parser.add_argument(
        "--max-stagnation", type=int, default=50, help="最大停滞代数 (默认: 50)"
    )
    parser.add_argument(
        "--grades",
        type=str,
        default=None,
        help="年级范围（格式：1,2,3 或 all；默认加载所有年级）",
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 解析年级参数
    grades = None
    if args.grades and args.grades != "all":
        try:
            grades = [int(g.strip()) for g in args.grades.split(",")]
        except ValueError:
            logger.error(f"年级参数格式错误: {args.grades}")
            sys.exit(1)

    # 构建遗传算法配置
    ga_config = {
        "population_size": args.population,
        "generations": args.generations,
        "crossover_rate": args.crossover_rate,
        "mutation_rate": args.mutation_rate,
        "tournament_size": args.tournament_size,
        "elitism_size": args.elitism_size,
        "max_stagnation": args.max_stagnation,
    }

    logger.info("=" * 60)
    logger.info("智能排课系统启动")
    logger.info("=" * 60)
    logger.info(f"版本ID: {args.version}")
    if grades:
        logger.info(f"年级范围: {grades}")
    logger.info(f"遗传算法配置: {ga_config}")

    # 初始化系统
    system = SchedulingSystem()

    try:
        # 设置数据库连接
        system.setup_database_connection()

        # 运行排课
        success = system.run_scheduling(args.version, grades, ga_config)

        if success:
            logger.info("排课任务完成成功！")
            sys.exit(0)
        else:
            logger.error("排课任务执行失败！")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(1)
    except Exception as e:
        logger.error(f"系统异常: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        system.cleanup()


if __name__ == "__main__":
    main()
