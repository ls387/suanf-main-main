<template>
  <div class="timetable-grid">
    <el-table :data="gridData" border style="width: 100%">
      <el-table-column prop="slot" label="节次" width="80" fixed />
      <el-table-column
        v-for="day in weekDays"
        :key="day.value"
        :label="day.label"
        :prop="`day${day.value}`"
      >
        <template #default="{ row }">
          <div v-if="row[`day${day.value}`]" class="course-cell">
            <div class="course-name">{{ row[`day${day.value}`].course_name }}</div>
            <div class="course-info">{{ row[`day${day.value}`].teacher_name }}</div>
            <div class="course-info">{{ row[`day${day.value}`].classroom_name }}</div>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const weekDays = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 7 }
]

const gridData = computed(() => {
  const grid = []
  
  // 初始化13节课的网格
  for (let slot = 1; slot <= 13; slot++) {
    const row = { slot: `第${slot}节` }
    for (let day = 1; day <= 7; day++) {
      row[`day${day}`] = null
    }
    grid.push(row)
  }
  
  // 填充课程数据
  props.data.forEach(course => {
    const { weekday, start_slot, end_slot } = course
    
    // 对于跨多节的课程，只在第一节显示
    if (grid[start_slot - 1]) {
      grid[start_slot - 1][`day${weekday}`] = {
        ...course,
        span: end_slot - start_slot + 1
      }
    }
  })
  
  return grid
})
</script>

<style scoped>
.timetable-grid {
  width: 100%;
}

.course-cell {
  padding: 8px;
  background-color: #ecf5ff;
  border-radius: 4px;
  min-height: 60px;
}

.course-name {
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.course-info {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}
</style>

