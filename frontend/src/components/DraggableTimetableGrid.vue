<template>
  <div class="timetable-wrapper">
    <!-- 表头 -->
    <div class="timetable-header">
      <div class="header-cell slot-label">节次</div>
      <div v-for="day in weekDays" :key="day.value" class="header-cell">{{ day.label }}</div>
    </div>

    <!-- 内容区 -->
    <div class="timetable-body">
      <!-- 节次列 -->
      <div class="slot-column">
        <div
          v-for="slot in 13"
          :key="slot"
          class="slot-cell"
          :class="{ 'group-separator': slot === 5 || slot === 9 }"
        >
          <span class="slot-number">第{{ slot }}节</span>
          <span v-if="slot === 1" class="slot-group-label">上午</span>
          <span v-else-if="slot === 5" class="slot-group-label">下午</span>
          <span v-else-if="slot === 9" class="slot-group-label">晚上</span>
        </div>
      </div>

      <!-- 7天网格 -->
      <div class="days-grid">
        <template v-for="slot in 13" :key="slot">
          <template v-for="day in weekDays" :key="`${day.value}-${slot}`">
            <template v-if="!isOccupied(day.value, slot)">
              <!-- 有课程：课程卡片 -->
              <div
                v-if="getCourse(day.value, slot)"
                class="grid-cell course-cell-wrapper"
                :class="{
                  'group-separator': slot === 5 || slot === 9,
                  'is-dragging': isDragging(getCourse(day.value, slot).schedule_id),
                }"
                :style="getCellStyle(day.value, slot)"
              >
                <div
                  class="course-card"
                  :style="{ backgroundColor: getCourseColor(getCourse(day.value, slot).course_name) }"
                  :draggable="!disabled"
                  @dragstart="onDragStart($event, getCourse(day.value, slot))"
                  @dragend="onDragEnd"
                >
                  <div class="course-name">{{ getCourse(day.value, slot).course_name }}</div>
                  <div class="course-info">{{ getCourse(day.value, slot).teacher_name }}</div>
                  <div class="course-info">{{ getCourse(day.value, slot).classroom_name }}</div>
                  <div v-if="getCourse(day.value, slot).classes?.length" class="course-info">
                    {{ getCourse(day.value, slot).classes.join('、') }}
                  </div>
                </div>
              </div>

              <!-- 空格子：拖放目标 -->
              <div
                v-else
                class="grid-cell empty-cell"
                :class="{
                  'group-separator': slot === 5 || slot === 9,
                  'drop-valid':   isDropHighlight(day.value, slot, true),
                  'drop-invalid': isDropHighlight(day.value, slot, false),
                }"
                @dragover.prevent="onDragOver($event, day.value, slot)"
                @dragleave="onDragLeave"
                @drop.prevent="onDrop($event, day.value, slot)"
              />
            </template>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { scheduleApi } from '@/api/schedules'

const props = defineProps({
  data: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['move-success', 'move-error'])

// ─── 常量 ────────────────────────────────────────────────────────────────────

const weekDays = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 7 },
]

const COLOR_PALETTE = [
  '#dbeafe', '#dcfce7', '#fef9c3', '#fee2e2',
  '#ede9fe', '#ffedd5', '#cffafe', '#fce7f3',
]

function hashString(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0
  return h
}
function getCourseColor(name) {
  return COLOR_PALETTE[hashString(name) % COLOR_PALETTE.length]
}

// ─── 拖拽状态 ─────────────────────────────────────────────────────────────────

/** 正在拖拽的课程信息 */
const dragging = ref(null)
// { scheduleId, span, weekday, startSlot }

/** 当前 dragover 的目标格子 */
const dropTarget = ref(null)
// { weekday, slot, valid }

// ─── 数据计算 ─────────────────────────────────────────────────────────────────

/**
 * 所有被"占用"的 (weekday, slot) 组合。
 * 连堂课的中间格（start+1 ~ end）不渲染；start 格渲染课程卡片。
 * 拖拽中排除被拖拽课程自身，让其原位置空出来（视觉上变为空格+半透明卡片）。
 */
const occupiedSet = computed(() => {
  const set = new Set()
  props.data.forEach(({ weekday, start_slot, end_slot, schedule_id }) => {
    for (let s = start_slot + 1; s <= end_slot; s++) {
      set.add(`${weekday}-${s}`)
    }
  })
  return set
})

const courseMap = computed(() => {
  const map = new Map()
  props.data.forEach(course => {
    map.set(`${course.weekday}-${course.start_slot}`, {
      ...course,
      span: course.end_slot - course.start_slot + 1,
    })
  })
  return map
})

/**
 * 所有被占用的节次（含 start 和 end 之间所有格），用于 drop 合法性检查。
 * 拖拽时排除自身。
 */
const takenSlots = computed(() => {
  const set = new Set()
  const selfId = dragging.value?.scheduleId
  props.data.forEach(({ weekday, start_slot, end_slot, schedule_id }) => {
    if (schedule_id === selfId) return
    for (let s = start_slot; s <= end_slot; s++) {
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
  if (course && course.span > 1) return { gridRow: `span ${course.span}` }
  return {}
}

function isDragging(scheduleId) {
  return dragging.value?.scheduleId === scheduleId
}

/** 判断某格子是否处于高亮范围（drop-valid 或 drop-invalid） */
function isDropHighlight(weekday, slot, expectValid) {
  if (!dropTarget.value) return false
  const { weekday: tw, slot: ts, valid, span } = dropTarget.value
  if (weekday !== tw) return false
  if (slot < ts || slot >= ts + span) return false
  return valid === expectValid
}

/** 判断 drop 到 (weekday, slot) 是否合法 */
function isValidDrop(weekday, slot) {
  if (!dragging.value) return false
  const { span } = dragging.value
  if (slot + span - 1 > 13) return false
  for (let s = slot; s < slot + span; s++) {
    if (takenSlots.value.has(`${weekday}-${s}`)) return false
  }
  return true
}

// ─── 拖拽事件处理 ─────────────────────────────────────────────────────────────

function onDragStart(e, course) {
  if (props.disabled) { e.preventDefault(); return }
  dragging.value = {
    scheduleId: course.schedule_id,
    span:       course.span,
    weekday:    course.weekday,
    startSlot:  course.start_slot,
  }
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('scheduleId', String(course.schedule_id))
}

function onDragEnd() {
  dragging.value = null
  dropTarget.value = null
}

function onDragOver(e, weekday, slot) {
  if (!dragging.value) return
  const valid = isValidDrop(weekday, slot)
  e.dataTransfer.dropEffect = valid ? 'move' : 'none'
  dropTarget.value = { weekday, slot, valid, span: dragging.value.span }
}

function onDragLeave() {
  dropTarget.value = null
}

async function onDrop(e, weekday, slot) {
  if (!dragging.value) return
  const { scheduleId, span } = dragging.value

  // 重置状态
  const savedDragging = { ...dragging.value }
  dragging.value = null
  dropTarget.value = null

  if (!isValidDrop(weekday, slot)) return

  // 与原位置相同，不请求
  if (weekday === savedDragging.weekday && slot === savedDragging.startSlot) return

  try {
    await scheduleApi.move(scheduleId, {
      week_day:   weekday,
      start_slot: slot,
      end_slot:   slot + span - 1,
    })
    emit('move-success', { scheduleId, newWeekday: weekday, newStartSlot: slot })
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'object' ? detail.message : (detail || '移动失败，请重试')
    ElMessage.error(msg)
    emit('move-error', { scheduleId, error: msg })
  }
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
.header-cell:last-child { border-right: none; }
.header-cell.slot-label { color: #909399; font-size: 12px; }

.timetable-body { display: flex; }

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
}
.slot-cell:last-child { border-bottom: none; }
.slot-cell.group-separator { border-top: 2px solid #c0c4cc; }
.slot-number { font-size: 12px; color: #606266; font-weight: 500; }
.slot-group-label { font-size: 10px; color: #909399; margin-top: 2px; }

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
  transition: background-color 0.1s;
}
.grid-cell:nth-child(7n) { border-right: none; }
.grid-cell.group-separator { border-top: 2px solid #c0c4cc; }

/* 拖拽目标高亮 */
.empty-cell.drop-valid   { background-color: #d1fae5; border: 2px dashed #10b981; }
.empty-cell.drop-invalid { background-color: #fee2e2; border: 2px dashed #ef4444; }

/* 正在被拖拽的卡片所在格子 */
.course-cell-wrapper.is-dragging { opacity: 0.4; }

.course-card {
  width: 100%;
  border-radius: 4px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  cursor: grab;
  transition: filter 0.15s, box-shadow 0.15s;
  user-select: none;
}
.course-card:hover {
  filter: brightness(0.93);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.course-card:active { cursor: grabbing; }

.course-name { font-weight: 600; color: #303133; font-size: 12px; line-height: 1.3; word-break: break-all; }
.course-info { font-size: 11px; color: #606266; line-height: 1.3; }
</style>
