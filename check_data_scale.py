#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据规模，为选择合适的算法参数提供建议
"""
import os
import pymysql


def check_data_scale():
    """检查数据规模"""
    print("正在连接数据库...")

    # 使用统一的配置管理
    from db_config import get_db_config

    db_config = get_db_config()

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
    except BaseException as e:
        import traceback

        traceback.print_exc()
        print(f"连接数据库失败 (BaseException): {e}")
        return

    try:
        print("[数据规模统计]")
        print("=" * 50)

        # 基础数据统计
        tables = [
            ("校区", "campuses"),
            ("院系", "departments"),
            ("专业", "majors"),
            ("班级", "classes"),
            ("教师", "teachers"),
            ("课程", "courses"),
            ("教室", "classrooms"),
        ]

        for name, table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{name:6}: {count:4} 个")

        print("-" * 50)

        # 排课相关数据统计
        cursor.execute("SELECT COUNT(*) FROM course_offerings")
        offerings_count = cursor.fetchone()[0]
        print(f"开课计划: {offerings_count:4} 个")

        cursor.execute("SELECT COUNT(*) FROM teaching_tasks")
        tasks_count = cursor.fetchone()[0]
        print(f"教学任务: {tasks_count:4} 个")

        cursor.execute("SELECT COUNT(*) FROM schedule_versions")
        versions_count = cursor.fetchone()[0]
        print(f"排课版本: {versions_count:4} 个")

        # 按学期统计
        cursor.execute(
            "SELECT semester, COUNT(*) FROM course_offerings GROUP BY semester"
        )
        print(f"\n[按学期统计]:")
        for row in cursor.fetchall():
            semester, count = row
            print(f"  {semester}: {count} 个开课计划")

        # 课程性质统计
        cursor.execute(
            "SELECT course_nature, COUNT(*) FROM course_offerings GROUP BY course_nature"
        )
        print(f"\n[按课程性质统计]:")
        for row in cursor.fetchall():
            nature, count = row
            print(f"  {nature}: {count} 门课程")

        # 课时统计
        cursor.execute(
            "SELECT slots_count, COUNT(*) FROM teaching_tasks GROUP BY slots_count ORDER BY slots_count"
        )
        print(f"\n[按课时长度统计]:")
        for row in cursor.fetchall():
            slots, count = row
            # 处理空值或无效值
            if slots is None or slots == "":
                print(f"  未设置: {count} 个任务")
            else:
                print(f"  {slots}节课: {count} 个任务")

        print("\n" + "=" * 50)

        # 推荐参数
        if tasks_count <= 20:
            print("[推荐算法参数 - 小规模]:")
            print("   python suan2.py --version 1 --population 30 --generations 50")
        elif tasks_count <= 50:
            print("[推荐算法参数 - 中等规模]:")
            print("   python suan2.py --version 1 --population 50 --generations 100")
        elif tasks_count <= 100:
            print("[推荐算法参数 - 较大规模]:")
            print("   python suan2.py --version 1 --population 100 --generations 200")
        else:
            print("[推荐算法参数 - 大规模]:")
            print("   python suan2.py --version 1 --population 150 --generations 300")

        print(f"\n[快速测试参数]:")
        print("   python suan2.py --version 1 --population 20 --generations 10")

    except Exception as e:
        print(f"检查时发生错误: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    check_data_scale()
