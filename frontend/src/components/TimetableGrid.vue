<template>
  <div class="timetable-wrapper">
    <!-- 表头 -->
    <div class="timetable-header">
      <div class="header-cell slot-label">节次</div>
      <div v-for="day in weekDays" :key="day.value" class="header-cell">{{ day.label }}</div>
    </div>

    <!-- 内容区 -->
    <div class="timetable-body">
      <!-- 左侧节次列 -->
      <div class="slot-column">
        <template v-for="slot in 13" :key="slot">
          <div
            class="slot-cell"
            :class="{
              'group-separator': slot === 5 || slot === 9
            }"
          >
            <span class="slot-number">第{{ slot }}节</span>
            <span v-if="slot === 1" class="slot-group-label">上午</span>
            <span v-else-if="slot === 5" class="slot-group-label">下午</span>
            <span v-else-if="slot === 9" class="slot-group-label">晚上</span>
          </div>
        </template>
      </div>

      <!-- 7天课表网格 -->
      <div class="days-grid">
        <template v-for="slot in 13" :key="slot">
          <template v-for="day in weekDays" :key="`${day.value}-${slot}`">
            <!-- 被连堂覆盖的格子跳过不渲染 -->
            <template v-if="!isOccupied(day.value, slot)">
              <div
                class="grid-cell"
                :class="{ 'group-separator': slot === 5 || slot === 9 }"
                :style="getCellStyle(day.value, slot)"
              >
                <div
                  v-if="getCourse(day.value, slot)"
                  class="course-card"
                  :style="{ backgroundColor: getCourseColor(getCourse(day.value, slot).course_name) }"
                >
                  <div class="course-name">{{ getCourse(day.value, slot).course_name }}</div>
                  <div class="course-info">{{ getCourse(day.value, slot).teacher_name }}</div>
                  <div class="course-info">{{ getCourse(day.value, slot).classroom_name }}</div>
                  <div v-if="getCourse(day.value, slot).classes?.length" class="course-info">
                    {{ getCourse(day.value, slot).classes.join('、') }}
                  </div>
                </div>
              </div>
            </template>
          </template>
        </template>
      </div>
    </div>
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

const COLOR_PALETTE = [
  '#dbeafe', // 蓝
  '#dcfce7', // 绿
  '#fef9c3', // 黄
  '#fee2e2', // 红
  '#ede9fe', // 紫
  '#ffedd5', // 橙
  '#cffafe', // 青
  '#fce7f3', // 粉
]

function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) >>> 0
  }
  return hash
}

function getCourseColor(courseName) {
  return COLOR_PALETTE[hashString(courseName) % COLOR_PALETTE.length]
}

// courseMap: (weekday, start_slot) => course entry（含 span）
const courseMap = computed(() => {
  const map = new Map()
  props.data.forEach(course => {
    const { weekday, start_slot, end_slot } = course
    const key = `${weekday}-${start_slot}`
    map.set(key, {
      ...course,
      span: end_slot - start_slot + 1
    })
  })
  return map
})

// occupiedSet: 被连堂覆盖的中间格子（不含 start_slot 本身）
const occupiedSet = computed(() => {
  const set = new Set()
  props.data.forEach(({ weekday, start_slot, end_slot }) => {
    for (let s = start_slot + 1; s <= end_slot; s++) {
      set.add(`${weekday}-${s}`)
    }
  })
  return set
})

function isOccupied(weekday, slot) {
  return occupiedSet.value.has(`${weekday}-${slot}`)
}

function getCourse(weekday, slot) {
  return courseMap.value.get(`${weekday}-${slot}`) || null
}

function getCellStyle(weekday, slot) {
  const course = getCourse(weekday, slot)
  if (course && course.span > 1) {
    return { gridRow: `span ${course.span}` }
  }
  return {}
}
</script>

<style scoped>
.timetable-wrapper {
  width: 100%;
  font-size: 13px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

/* 表头 */
.timetable-header {
  display: grid;
  grid-template-columns: 60px repeat(7, 1fr);
  background-color: #f5f7fa;
  border-bottom: 2px solid #e4e7ed;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-cell {
  padding: 10px 4px;
  text-align: center;
  font-weight: 600;
  color: #303133;
  border-right: 1px solid #e4e7ed;
}

.header-cell:last-child {
  border-right: none;
}

.header-cell.slot-label {
  color: #909399;
  font-size: 12px;
}

/* 内容区：节次列 + 课表网格并排 */
.timetable-body {
  display: flex;
}

/* 左侧节次列 */
.slot-column {
  width: 60px;
  flex-shrink: 0;
  border-right: 1px solid #e4e7ed;
}

.slot-cell {
  height: 72px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #e4e7ed;
  background-color: #f5f7fa;
  position: relative;
}

.slot-cell:last-child {
  border-bottom: none;
}

.slot-cell.group-separator {
  border-top: 2px solid #c0c4cc;
}

.slot-number {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.slot-group-label {
  font-size: 10px;
  color: #909399;
  margin-top: 2px;
}

/* 7天课表网格 */
.days-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(13, 72px);
  grid-auto-flow: row;
}

.grid-cell {
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  padding: 4px;
  display: flex;
  align-items: stretch;
  min-height: 72px;
}

/* 第7列去掉右边框 */
.grid-cell:nth-child(7n) {
  border-right: none;
}

.grid-cell.group-separator {
  border-top: 2px solid #c0c4cc;
}

/* 课程卡片 */
.course-card {
  width: 100%;
  border-radius: 4px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  cursor: default;
  transition: filter 0.15s;
}

.course-card:hover {
  filter: brightness(0.95);
}

.course-name {
  font-weight: 600;
  color: #303133;
  font-size: 12px;
  line-height: 1.3;
  word-break: break-all;
}

.course-info {
  font-size: 11px;
  color: #606266;
  line-height: 1.3;
}
</style>
