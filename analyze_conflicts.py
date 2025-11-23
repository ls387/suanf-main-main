#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析排课结果中的冲突问题
支持导出冲突Excel和优化冲突
"""
import os
import sys
import pymysql
from collections import defaultdict
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

# 设置标准输出编码为UTF-8
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def export_conflicts_to_excel(
    class_conflicts, teacher_conflicts, classroom_conflicts, version_id
):
    """导出冲突到Excel"""
    wb = Workbook()

    # 样式定义
    header_fill = PatternFill(
        start_color="4472C4", end_color="4472C4", fill_type="solid"
    )
    header_font = Font(color="FFFFFF", bold=True, size=11)
    conflict_fill = PatternFill(
        start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"
    )

    day_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    # 班级冲突表
    if wb.active:
        ws1 = wb.active
        ws1.title = "班级冲突"
    else:
        ws1 = wb.create_sheet("班级冲突")

    ws1.append(
        [
            "冲突序号",
            "班级",
            "星期",
            "节次",
            "课程1",
            "教师1",
            "教室1",
            "课程2",
            "教师2",
            "教室2",
        ]
    )
    for col in range(1, 11):
        ws1.cell(1, col).fill = header_fill
        ws1.cell(1, col).font = header_font
        ws1.cell(1, col).alignment = Alignment(horizontal="center", vertical="center")

    for idx, conflict in enumerate(class_conflicts, 1):
        items = conflict["items"]
        ws1.append(
            [
                idx,
                conflict["class_name"],
                day_names[conflict["weekday"]],
                conflict["slot"],
                items[0]["course"],
                items[0]["teacher"],
                items[0]["classroom"],
                items[1]["course"] if len(items) > 1 else "",
                items[1]["teacher"] if len(items) > 1 else "",
                items[1]["classroom"] if len(items) > 1 else "",
            ]
        )
        for col in range(1, 11):
            ws1.cell(idx + 1, col).fill = conflict_fill

    # 调整列宽
    ws1.column_dimensions["A"].width = 10
    ws1.column_dimensions["B"].width = 20
    ws1.column_dimensions["C"].width = 8
    ws1.column_dimensions["D"].width = 8
    for col in ["E", "F", "G", "H", "I", "J"]:
        ws1.column_dimensions[col].width = 20

    # 教师冲突表
    ws2 = wb.create_sheet("教师冲突")
    ws2.append(["冲突序号", "教师", "星期", "节次", "课程1", "教室1", "课程2", "教室2"])
    for col in range(1, 9):
        ws2.cell(1, col).fill = header_fill
        ws2.cell(1, col).font = header_font
        ws2.cell(1, col).alignment = Alignment(horizontal="center", vertical="center")

    for idx, conflict in enumerate(teacher_conflicts, 1):
        items = conflict["items"]
        ws2.append(
            [
                idx,
                conflict["teacher"],
                day_names[conflict["weekday"]],
                conflict["slot"],
                items[0]["course"],
                items[0]["classroom"],
                items[1]["course"] if len(items) > 1 else "",
                items[1]["classroom"] if len(items) > 1 else "",
            ]
        )
        for col in range(1, 9):
            ws2.cell(idx + 1, col).fill = conflict_fill

    ws2.column_dimensions["A"].width = 10
    ws2.column_dimensions["B"].width = 20
    ws2.column_dimensions["C"].width = 8
    ws2.column_dimensions["D"].width = 8
    for col in ["E", "F", "G", "H"]:
        ws2.column_dimensions[col].width = 20

    # 教室冲突表
    ws3 = wb.create_sheet("教室冲突")
    ws3.append(["冲突序号", "教室", "星期", "节次", "课程1", "教师1", "课程2", "教师2"])
    for col in range(1, 9):
        ws3.cell(1, col).fill = header_fill
        ws3.cell(1, col).font = header_font
        ws3.cell(1, col).alignment = Alignment(horizontal="center", vertical="center")

    for idx, conflict in enumerate(classroom_conflicts, 1):
        items = conflict["items"]
        ws3.append(
            [
                idx,
                conflict["classroom"],
                day_names[conflict["weekday"]],
                conflict["slot"],
                items[0]["course"],
                items[0]["teacher"],
                items[1]["course"] if len(items) > 1 else "",
                items[1]["teacher"] if len(items) > 1 else "",
            ]
        )
        for col in range(1, 9):
            ws3.cell(idx + 1, col).fill = conflict_fill

    ws3.column_dimensions["A"].width = 10
    ws3.column_dimensions["B"].width = 20
    ws3.column_dimensions["C"].width = 8
    ws3.column_dimensions["D"].width = 8
    for col in ["E", "F", "G", "H"]:
        ws3.column_dimensions[col].width = 20

    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"排课冲突报告_版本{version_id}_{timestamp}.xlsx"
    wb.save(filename)
    print(f"\n✓ 冲突报告已导出到: {filename}")
    return filename


def analyze_schedule_conflicts(version_id):
    """分析指定版本的排课冲突"""

    # 连接数据库
    conn = pymysql.connect(
        host=os.getenv("DB_HOST") or "localhost",
        port=int(os.getenv("DB_PORT") or "3306"),
        user=os.getenv("DB_USER") or "root",
        password=os.getenv("DB_PASSWORD") or "123456",
        database=os.getenv("DB_NAME") or "paikew",
        charset="utf8mb4",
    )

    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 获取排课结果
        query = """
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
            GROUP_CONCAT(DISTINCT t.teacher_name SEPARATOR ', ') AS teacher_name,
            GROUP_CONCAT(DISTINCT t.teacher_id SEPARATOR ', ') AS teacher_ids
        FROM schedules sr
        JOIN teaching_tasks tt ON sr.task_id = tt.task_id
        JOIN course_offerings co ON tt.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN classrooms cr ON sr.classroom_id = cr.classroom_id
        LEFT JOIN offering_teachers ot ON co.offering_id = ot.offering_id
        LEFT JOIN teachers t ON ot.teacher_id = t.teacher_id
        WHERE sr.version_id = %s
        GROUP BY sr.schedule_id, sr.task_id, sr.classroom_id, sr.week_day, 
                 sr.start_slot, tt.slots_count, tt.offering_id, c.course_name, cr.classroom_name
        ORDER BY sr.week_day, sr.start_slot
        """

        cursor.execute(query, (version_id,))
        results = cursor.fetchall()

        # 获取任务-班级关系
        task_classes = defaultdict(list)
        for result in results:
            task_id = result["task_id"]
            class_query = """
            SELECT cl.class_id, cl.class_name
            FROM offering_classes oc
            JOIN classes cl ON oc.class_id = cl.class_id
            JOIN teaching_tasks tt ON oc.offering_id = tt.offering_id
            WHERE tt.task_id = %s
            """
            cursor.execute(class_query, (task_id,))
            classes = cursor.fetchall()
            task_classes[task_id] = classes

        print("=" * 80)
        print(f"排课版本 {version_id} 冲突分析报告")
        print("=" * 80)

        # 分析班级冲突
        print("\n【班级时间冲突分析】")
        class_schedule = defaultdict(list)
        class_conflicts_data = []  # 用于导出

        for result in results:
            task_id = result["task_id"]
            start_slot = result["start_slot"]
            end_slot = start_slot + result["slots_count"] - 1
            week_day = result["week_day"]

            for cls in task_classes[task_id]:
                class_id = cls["class_id"]
                for slot in range(start_slot, end_slot + 1):
                    time_key = (week_day, slot)
                    class_schedule[class_id].append(
                        {
                            "time": time_key,
                            "course": result["course_name"],
                            "teacher": result["teacher_name"],
                            "classroom": result["classroom_name"],
                            "class_name": cls["class_name"],
                        }
                    )

        # 检测冲突
        conflicts_found = 0
        for class_id, schedule in class_schedule.items():
            time_dict = defaultdict(list)
            for item in schedule:
                time_dict[item["time"]].append(item)

            for time, items in time_dict.items():
                if len(items) > 1:
                    conflicts_found += 1
                    week_day, slot = time
                    day_names = [
                        "",
                        "周一",
                        "周二",
                        "周三",
                        "周四",
                        "周五",
                        "周六",
                        "周日",
                    ]
                    print(f"\n冲突 #{conflicts_found}:")
                    print(f"  班级: {items[0]['class_name']}")
                    print(f"  时间: {day_names[week_day]} 第{slot}节")
                    for i, item in enumerate(items, 1):
                        print(
                            f"  课程{i}: {item['course']} - {item['teacher']} - {item['classroom']}"
                        )

                    # 记录冲突数据用于导出
                    class_conflicts_data.append(
                        {
                            "class_name": items[0]["class_name"],
                            "weekday": week_day,
                            "slot": slot,
                            "items": items,
                        }
                    )

        if conflicts_found == 0:
            print("✓ 未发现班级冲突")
        else:
            print(f"\n⚠ 共发现 {conflicts_found} 处班级冲突")

        # 分析教师冲突
        print("\n【教师时间冲突分析】")
        teacher_schedule = defaultdict(list)
        teacher_conflicts_data = []  # 用于导出

        for result in results:
            # 从 teacher_ids 字段获取教师ID列表
            teacher_ids_str = result.get("teacher_ids", "")
            if not teacher_ids_str:
                continue

            teacher_ids = teacher_ids_str.split(", ")
            start_slot = result["start_slot"]
            end_slot = start_slot + result["slots_count"] - 1
            week_day = result["week_day"]

            for teacher_id in teacher_ids:
                for slot in range(start_slot, end_slot + 1):
                    time_key = (week_day, slot)
                    teacher_schedule[teacher_id].append(
                        {
                            "time": time_key,
                            "course": result["course_name"],
                            "teacher": result["teacher_name"],
                            "classroom": result["classroom_name"],
                        }
                    )

        teacher_conflicts = 0
        for teacher_id, schedule in teacher_schedule.items():
            time_dict = defaultdict(list)
            for item in schedule:
                time_dict[item["time"]].append(item)

            for time, items in time_dict.items():
                if len(items) > 1:
                    teacher_conflicts += 1
                    week_day, slot = time
                    day_names = [
                        "",
                        "周一",
                        "周二",
                        "周三",
                        "周四",
                        "周五",
                        "周六",
                        "周日",
                    ]
                    print(f"\n冲突 #{teacher_conflicts}:")
                    print(f"  教师: {items[0]['teacher']}")
                    print(f"  时间: {day_names[week_day]} 第{slot}节")
                    for i, item in enumerate(items, 1):
                        print(f"  课程{i}: {item['course']} - {item['classroom']}")

                    # 记录冲突数据用于导出
                    teacher_conflicts_data.append(
                        {
                            "teacher": items[0]["teacher"],
                            "weekday": week_day,
                            "slot": slot,
                            "items": items,
                        }
                    )

        if teacher_conflicts == 0:
            print("✓ 未发现教师冲突")
        else:
            print(f"\n⚠ 共发现 {teacher_conflicts} 处教师冲突")

        # 分析教室冲突
        print("\n【教室时间冲突分析】")
        classroom_schedule = defaultdict(list)
        classroom_conflicts_data = []  # 用于导出

        for result in results:
            classroom_id = result["classroom_id"]
            start_slot = result["start_slot"]
            end_slot = start_slot + result["slots_count"] - 1
            week_day = result["week_day"]

            for slot in range(start_slot, end_slot + 1):
                time_key = (week_day, slot)
                classroom_schedule[classroom_id].append(
                    {
                        "time": time_key,
                        "course": result["course_name"],
                        "teacher": result["teacher_name"],
                        "classroom": result["classroom_name"],
                    }
                )

        classroom_conflicts = 0
        for classroom_id, schedule in classroom_schedule.items():
            time_dict = defaultdict(list)
            for item in schedule:
                time_dict[item["time"]].append(item)

            for time, items in time_dict.items():
                if len(items) > 1:
                    classroom_conflicts += 1
                    week_day, slot = time
                    day_names = [
                        "",
                        "周一",
                        "周二",
                        "周三",
                        "周四",
                        "周五",
                        "周六",
                        "周日",
                    ]
                    print(f"\n冲突 #{classroom_conflicts}:")
                    print(f"  教室: {items[0]['classroom']}")
                    print(f"  时间: {day_names[week_day]} 第{slot}节")
                    for i, item in enumerate(items, 1):
                        print(f"  课程{i}: {item['course']} - {item['teacher']}")

                    # 记录冲突数据用于导出
                    classroom_conflicts_data.append(
                        {
                            "classroom": items[0]["classroom"],
                            "weekday": week_day,
                            "slot": slot,
                            "items": items,
                        }
                    )

        if classroom_conflicts == 0:
            print("✓ 未发现教室冲突")
        else:
            print(f"\n⚠ 共发现 {classroom_conflicts} 处教室冲突")

        print("\n" + "=" * 80)
        print("分析完成")
        print("=" * 80)

        # 导出冲突Excel
        total_conflicts = conflicts_found + teacher_conflicts + classroom_conflicts
        if total_conflicts > 0:
            export_conflicts_to_excel(
                class_conflicts_data,
                teacher_conflicts_data,
                classroom_conflicts_data,
                version_id,
            )

            # 询问是否优化冲突
            print("\n" + "=" * 80)
            choice = input("是否尝试优化这些冲突? (y/n): ").strip().lower()
            if choice == "y":
                optimize_conflicts(
                    version_id,
                    results,
                    task_classes,
                    class_conflicts_data,
                    teacher_conflicts_data,
                    classroom_conflicts_data,
                    cursor,
                    conn,
                )

    finally:
        cursor.close()
        conn.close()


def optimize_conflicts(
    version_id,
    results,
    task_classes,
    class_conflicts_data,
    teacher_conflicts_data,
    classroom_conflicts_data,
    cursor,
    conn,
):
    """优化冲突课程 - 只调整有冲突的课程,不影响其他课程"""
    print("\n" + "=" * 80)
    print("开始优化冲突...")
    print("=" * 80)

    # 收集所有有冲突的 schedule_id
    conflict_schedule_ids = set()

    # 从班级冲突中提取
    for conflict in class_conflicts_data:
        for item in conflict["items"]:
            # 找到对应的schedule记录
            for result in results:
                if (
                    result["course_name"] == item["course"]
                    and result["classroom_name"] == item["classroom"]
                    and result["week_day"] == conflict["weekday"]
                    and result["start_slot"] == conflict["slot"]
                ):
                    conflict_schedule_ids.add(result["schedule_id"])

    # 从教师冲突中提取
    for conflict in teacher_conflicts_data:
        for item in conflict["items"]:
            for result in results:
                if (
                    result["course_name"] == item["course"]
                    and result["classroom_name"] == item["classroom"]
                    and result["week_day"] == conflict["weekday"]
                    and result["start_slot"] == conflict["slot"]
                ):
                    conflict_schedule_ids.add(result["schedule_id"])

    # 从教室冲突中提取
    for conflict in classroom_conflicts_data:
        for item in conflict["items"]:
            for result in results:
                if (
                    result["course_name"] == item["course"]
                    and result["classroom_name"] == item["classroom"]
                    and result["week_day"] == conflict["weekday"]
                    and result["start_slot"] == conflict["slot"]
                ):
                    conflict_schedule_ids.add(result["schedule_id"])

    print(f"识别到 {len(conflict_schedule_ids)} 个需要调整的课程安排")

    if len(conflict_schedule_ids) == 0:
        print("没有需要优化的冲突")
        return

    # 获取已占用的时间槽(不包括待调整的课程)
    occupied_times = defaultdict(
        lambda: defaultdict(set)
    )  # [entity_type][entity_id] = set of (weekday, slot)

    for result in results:
        if result["schedule_id"] in conflict_schedule_ids:
            continue  # 跳过冲突课程

        task_id = result["task_id"]
        start_slot = result["start_slot"]
        end_slot = start_slot + result["slots_count"] - 1
        weekday = result["week_day"]
        classroom_id = result["classroom_id"]

        # 记录教室占用
        for slot in range(start_slot, end_slot + 1):
            occupied_times["classroom"][classroom_id].add((weekday, slot))

        # 记录教师占用
        teacher_ids_str = result.get("teacher_ids", "")
        if teacher_ids_str:
            for teacher_id in teacher_ids_str.split(", "):
                for slot in range(start_slot, end_slot + 1):
                    occupied_times["teacher"][teacher_id].add((weekday, slot))

        # 记录班级占用
        for cls in task_classes[task_id]:
            class_id = cls["class_id"]
            for slot in range(start_slot, end_slot + 1):
                occupied_times["class"][class_id].add((weekday, slot))

    # 尝试为冲突课程重新安排时间
    adjustments = []

    for schedule_id in conflict_schedule_ids:
        # 找到对应的排课记录
        schedule_record = None
        for result in results:
            if result["schedule_id"] == schedule_id:
                schedule_record = result
                break

        if not schedule_record:
            continue

        task_id = schedule_record["task_id"]
        slots_count = schedule_record["slots_count"]
        classroom_id = schedule_record["classroom_id"]
        old_weekday = schedule_record["week_day"]
        old_start_slot = schedule_record["start_slot"]

        # 获取教师和班级
        teacher_ids = schedule_record.get("teacher_ids", "").split(", ")
        classes = [cls["class_id"] for cls in task_classes[task_id]]

        # 尝试找到新的时间槽
        found_slot = False
        time_slots = []

        # 生成可能的时间槽 (周一到周五, 1-13节)
        for weekday in range(1, 6):  # 周一到周五
            for start_slot in range(1, 14 - slots_count + 1):
                # 跳过周四下午
                if weekday == 4 and start_slot >= 6:
                    continue

                # 检查是否有冲突
                has_conflict = False

                # 检查教室冲突
                for slot in range(start_slot, start_slot + slots_count):
                    if (weekday, slot) in occupied_times["classroom"][classroom_id]:
                        has_conflict = True
                        break

                if has_conflict:
                    continue

                # 检查教师冲突
                for teacher_id in teacher_ids:
                    for slot in range(start_slot, start_slot + slots_count):
                        if (weekday, slot) in occupied_times["teacher"][teacher_id]:
                            has_conflict = True
                            break
                    if has_conflict:
                        break

                if has_conflict:
                    continue

                # 检查班级冲突
                for class_id in classes:
                    for slot in range(start_slot, start_slot + slots_count):
                        if (weekday, slot) in occupied_times["class"][class_id]:
                            has_conflict = True
                            break
                    if has_conflict:
                        break

                if not has_conflict:
                    time_slots.append((weekday, start_slot))

        if time_slots:
            # 选择第一个可用时间槽
            new_weekday, new_start_slot = time_slots[0]

            # 更新占用记录
            for slot in range(new_start_slot, new_start_slot + slots_count):
                occupied_times["classroom"][classroom_id].add((new_weekday, slot))
                for teacher_id in teacher_ids:
                    occupied_times["teacher"][teacher_id].add((new_weekday, slot))
                for class_id in classes:
                    occupied_times["class"][class_id].add((new_weekday, slot))

            adjustments.append(
                {
                    "schedule_id": schedule_id,
                    "course_name": schedule_record["course_name"],
                    "old_time": (old_weekday, old_start_slot),
                    "new_time": (new_weekday, new_start_slot),
                    "new_end_slot": new_start_slot + slots_count - 1,
                }
            )
        else:
            print(f"⚠ 无法为课程 {schedule_record['course_name']} 找到合适的时间槽")

    if adjustments:
        print(f"\n找到 {len(adjustments)} 个调整方案:")
        day_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for adj in adjustments:
            old_day, old_slot = adj["old_time"]
            new_day, new_slot = adj["new_time"]
            print(
                f"  {adj['course_name']}: {day_names[old_day]} 第{old_slot}节 -> {day_names[new_day]} 第{new_slot}节"
            )

        confirm = input("\n确认应用这些调整? (y/n): ").strip().lower()
        if confirm == "y":
            # 应用调整到数据库
            for adj in adjustments:
                update_query = """
                UPDATE schedules 
                SET week_day = %s, start_slot = %s, end_slot = %s
                WHERE schedule_id = %s
                """
                cursor.execute(
                    update_query,
                    (
                        adj["new_time"][0],
                        adj["new_time"][1],
                        adj["new_end_slot"],
                        adj["schedule_id"],
                    ),
                )

            conn.commit()
            print(f"\n✓ 已成功调整 {len(adjustments)} 个课程安排")
            print("建议重新运行冲突分析验证结果")
        else:
            print("\n已取消调整")
    else:
        print("\n未找到可行的调整方案")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python analyze_conflicts.py <version_id>")
        print("示例: python analyze_conflicts.py 1")
        sys.exit(1)

    version_id = int(sys.argv[1])
    analyze_schedule_conflicts(version_id)
