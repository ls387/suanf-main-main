# -*- coding: utf-8 -*-
"""
排课算法服务
封装现有遗传算法的调用
"""
import sys
import os
import time
import logging
from typing import Dict, Optional

# 添加项目根目录到路径，以便导入现有的算法模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from db_connector import DatabaseConnector, DataLoader
from genetic_algorithm import SchedulingGeneticAlgorithm

logger = logging.getLogger(__name__)


class SchedulingService:
    """排课服务"""
    
    def __init__(self, db_config: Dict):
        """初始化排课服务
        
        Args:
            db_config: 数据库配置字典
        """
        self.db_config = db_config
        self.db_connector = None
        self.data_loader = None
    
    def setup_connection(self):
        """设置数据库连接"""
        self.db_connector = DatabaseConnector(**self.db_config)
        self.db_connector.connect()
        self.data_loader = DataLoader(self.db_connector)
    
    def cleanup(self):
        """清理资源"""
        if self.db_connector:
            self.db_connector.disconnect()
    
    def run_scheduling(self, version_id: int, ga_config: Dict) -> Dict:
        """运行排课算法
        
        Args:
            version_id: 排课版本ID
            ga_config: 遗传算法配置
            
        Returns:
            排课结果字典
        """
        try:
            start_time = time.time()
            
            # 设置连接
            self.setup_connection()
            
            # 验证版本
            version_query = "SELECT * FROM schedule_versions WHERE version_id = %s"
            version_result = self.db_connector.execute_query(version_query, (version_id,))
            
            if not version_result:
                return {
                    "success": False,
                    "message": f"排课版本 {version_id} 不存在",
                }
            
            version = version_result[0]
            if version["status"] != "draft":
                return {
                    "success": False,
                    "message": f"排课版本状态为 {version['status']}，不是草案状态",
                }
            
            semester = version["semester"]
            logger.info(f"开始为学期 {semester} 版本 {version_id} 排课")
            
            # 加载数据
            data = self.data_loader.load_all_data(semester)
            
            # 验证数据完整性
            if not data["teaching_tasks"]:
                return {
                    "success": False,
                    "message": "没有找到教学任务",
                }
            
            # 初始化遗传算法
            ga = SchedulingGeneticAlgorithm(data, ga_config)
            
            # 运行算法
            logger.info("开始运行遗传算法")
            best_solution = ga.evolve()
            
            # 保存结果
            logger.info("保存排课结果")
            self.data_loader.save_schedule_results(
                version_id, best_solution, ga.task_dict
            )
            
            # 计算统计信息
            total_tasks = len(data["teaching_tasks"])
            scheduled_tasks = len(best_solution)
            coverage_rate = (scheduled_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # 检查冲突
            conflicts = self._check_conflicts(best_solution, ga.task_dict, data)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 计算适应度
            best_fitness = ga.fitness(best_solution)
            
            logger.info(f"排课完成，耗时: {execution_time:.2f} 秒")
            
            return {
                "success": True,
                "message": "排课完成",
                "best_fitness": best_fitness,
                "coverage_rate": coverage_rate,
                "total_tasks": total_tasks,
                "scheduled_tasks": scheduled_tasks,
                "execution_time": execution_time,
                "conflicts": conflicts,
            }
            
        except Exception as e:
            logger.error(f"排课过程中发生错误: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"排课失败: {str(e)}",
            }
        finally:
            self.cleanup()
    
    def _check_conflicts(self, solution, task_dict, data) -> Dict:
        """检查冲突"""
        from collections import defaultdict
        
        teacher_schedule = defaultdict(list)
        class_schedule = defaultdict(list)
        classroom_schedule = defaultdict(list)
        
        for gene in solution:
            task = task_dict[gene.task_id]
            end_slot = gene.start_slot + task.slots_count - 1
            
            for slot in range(gene.start_slot, end_slot + 1):
                time_key = (gene.week_day, slot)
                teacher_schedule[gene.teacher_id].append(time_key)
                classroom_schedule[gene.classroom_id].append(time_key)
                
                for class_id in task.classes:
                    class_schedule[class_id].append(time_key)
        
        conflicts = {
            "teacher": sum(
                1
                for times in teacher_schedule.values()
                if len(times) != len(set(times))
            ),
            "class": sum(
                1 for times in class_schedule.values() if len(times) != len(set(times))
            ),
            "classroom": sum(
                1
                for times in classroom_schedule.values()
                if len(times) != len(set(times))
            ),
        }
        
        return conflicts

