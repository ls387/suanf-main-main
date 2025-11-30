<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>周课表查询</span>
        </div>
      </template>
      
      <el-form :inline="true" :model="query">
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
import { ref } from 'vue'
import { timetableApi } from '@/api/timetable'
import TimetableGrid from '@/components/TimetableGrid.vue'

const loading = ref(false)
const timetableData = ref([])

const query = ref({
  semester: '2025-2026-1',
  version_id: 1,
  week_number: 1
})

const handleQuery = async () => {
  loading.value = true
  try {
    timetableData.value = await timetableApi.getWeekTimetable(query.value)
  } catch (error) {
    console.error('查询失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { font-weight: bold; }
</style>

