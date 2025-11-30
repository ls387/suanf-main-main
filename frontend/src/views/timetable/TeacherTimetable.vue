<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>教师课表查询</span>
        </div>
      </template>
      
      <el-form :inline="true" :model="query">
        <el-form-item label="教师">
          <el-select
            v-model="query.teacher_id"
            placeholder="请选择教师"
            filterable
            style="min-width: 220px;"
          >
            <el-option
              v-for="t in teacherOptions"
              :key="t.teacher_id"
              :label="`${t.teacher_id} - ${t.teacher_name}`"
              :value="t.teacher_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-input v-model="query.semester" placeholder="例如: 2025-2026-1" />
        </el-form-item>
        <el-form-item label="版本ID">
          <el-input-number v-model="query.version_id" :min="1" />
        </el-form-item>
        <el-form-item label="周次">
          <el-input-number v-model="query.week_number" :min="1" :max="53" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
        </el-form-item>
      </el-form>
      
      <el-divider />
      
      <div v-loading="loading">
        <TimetableGrid v-if="timetableData.length > 0" :data="timetableData" />
        <el-empty v-else description="暂无课表数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { timetableApi } from '@/api/timetable'
import { teacherApi } from '@/api/teachers'
import TimetableGrid from '@/components/TimetableGrid.vue'

const loading = ref(false)
const timetableData = ref([])
const teacherOptions = ref([])

const query = ref({
  teacher_id: '',
  semester: '2025-2026-1',
  version_id: 1,
  week_number: 1
})

const loadTeachers = async () => {
  try {
    teacherOptions.value = await teacherApi.getAll()
  } catch (e) {
    console.error('加载教师列表失败:', e)
  }
}

const handleQuery = async () => {
  if (!query.value.teacher_id) {
    ElMessage.warning('请选择教师')
    return
  }
  
  loading.value = true
  try {
    timetableData.value = await timetableApi.getTeacherTimetable(query.value)
    if (timetableData.value.length === 0) {
      ElMessage.info('该教师暂无课表')
    }
  } catch (error) {
    console.error('查询失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTeachers()
})
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { font-weight: bold; }
</style>

