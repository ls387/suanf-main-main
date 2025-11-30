<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#409eff"><User /></el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.teachers }}</div>
              <div class="stat-label">教师数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#67c23a"><Reading /></el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.courses }}</div>
              <div class="stat-label">课程数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#e6a23c"><School /></el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.classes }}</div>
              <div class="stat-label">班级数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#f56c6c"><OfficeBuilding /></el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.classrooms }}</div>
              <div class="stat-label">教室数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速开始</span>
            </div>
          </template>
          
          <el-steps :active="1" align-center>
            <el-step title="数据录入" description="录入教师、课程、班级等基础数据" />
            <el-step title="开课计划" description="创建开课计划并配置教师偏好" />
            <el-step title="运行排课" description="设置算法参数并运行排课" />
            <el-step title="查看结果" description="查看和导出课表" />
          </el-steps>
          
          <div style="margin-top: 30px; text-align: center;">
            <el-button type="primary" @click="$router.push('/teachers')">
              开始数据录入
            </el-button>
            <el-button @click="$router.push('/scheduling')">
              前往排课控制台
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统说明</span>
            </div>
          </template>
          <div class="info-text">
            <p><strong>智能排课系统</strong>基于遗传算法，能够自动处理复杂的排课约束，包括：</p>
            <ul>
              <li>教师、班级、教室时间冲突检测</li>
              <li>教室容量和设施要求匹配</li>
              <li>教师黑名单时间和偏好时间</li>
              <li>必修课白天优先、选修课灵活安排</li>
              <li>校区通勤优化、连堂课同教室</li>
            </ul>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>使用建议</span>
            </div>
          </template>
          <div class="info-text">
            <p><strong>排课参数建议：</strong></p>
            <ul>
              <li>小规模（&lt;50任务）：种群100，代数100</li>
              <li>中等规模（50-200任务）：种群150，代数200</li>
              <li>大规模（&gt;200任务）：种群200，代数300</li>
            </ul>
            <p style="margin-top: 10px;">
              <el-text type="info">
                注意：排课过程可能需要几分钟时间，请耐心等待
              </el-text>
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { teacherApi } from '@/api/teachers'
import { courseApi } from '@/api/courses'
import { classApi } from '@/api/classes'
import { classroomApi } from '@/api/classrooms'

const stats = ref({
  teachers: 0,
  courses: 0,
  classes: 0,
  classrooms: 0
})

const loadStats = async () => {
  try {
    const [teachers, courses, classes, classrooms] = await Promise.all([
      teacherApi.getAll(),
      courseApi.getAll(),
      classApi.getAll(),
      classroomApi.getAll()
    ])
    
    stats.value = {
      teachers: teachers.length,
      courses: courses.length,
      classes: classes.length,
      classrooms: classrooms.length
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.card-header {
  font-weight: bold;
}

.info-text {
  line-height: 1.8;
}

.info-text ul {
  margin: 10px 0;
  padding-left: 20px;
}

.info-text li {
  margin: 5px 0;
}
</style>

