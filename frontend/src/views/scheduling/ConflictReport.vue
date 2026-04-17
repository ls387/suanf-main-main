<template>
  <div class="page-container">
    <!-- 顶部：返回 + 标题 -->
    <div class="page-header">
      <el-button link @click="$router.back()">← 返回</el-button>
      <span class="page-title">冲突分析报告 · 版本 #{{ versionId }}</span>
      <el-button @click="reload" :loading="loading" size="small">刷新</el-button>
    </div>

    <!-- 四个汇总卡片 -->
    <el-row :gutter="16" style="margin: 16px 0">
      <el-col :span="6" v-for="card in summaryCards" :key="card.key">
        <div class="summary-card" :class="card.count > 0 ? 'has-conflict' : 'no-conflict'">
          <div class="card-count">{{ loading ? '-' : card.count }}</div>
          <div class="card-label">{{ card.label }}</div>
          <el-icon v-if="!loading && card.count === 0" class="ok-icon"><CircleCheckFilled /></el-icon>
        </div>
      </el-col>
    </el-row>

    <!-- 无冲突提示 -->
    <el-alert
      v-if="!loading && summary && summary.total === 0"
      title="✓ 无冲突 — 本版本排课结果完全无冲突"
      type="success"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <!-- 明细 Tabs -->
    <el-card v-loading="loading">
      <el-tabs v-model="activeTab">
        <!-- 班级冲突 -->
        <el-tab-pane :label="`班级冲突 (${data.class_conflicts?.length ?? 0})`" name="class">
          <el-table :data="data.class_conflicts" stripe empty-text="无班级冲突">
            <el-table-column prop="class_name" label="班级" width="120" />
            <el-table-column label="星期" width="80">
              <template #default="{ row }">{{ weekdayName(row.weekday) }}</template>
            </el-table-column>
            <el-table-column label="冲突节次" width="100">
              <template #default="{ row }">第 {{ row.overlap_start }}-{{ row.overlap_end }} 节</template>
            </el-table-column>
            <el-table-column label="课程 1" min-width="160">
              <template #default="{ row }">
                <div>{{ row.course1 }}</div>
                <div class="sub-text">{{ row.teacher1 }} · {{ row.classroom1 }}</div>
              </template>
            </el-table-column>
            <el-table-column label="课程 2" min-width="160">
              <template #default="{ row }">
                <div>{{ row.course2 }}</div>
                <div class="sub-text">{{ row.teacher2 }} · {{ row.classroom2 }}</div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 教师冲突 -->
        <el-tab-pane :label="`教师冲突 (${data.teacher_conflicts?.length ?? 0})`" name="teacher">
          <el-table :data="data.teacher_conflicts" stripe empty-text="无教师冲突">
            <el-table-column prop="teacher" label="教师" width="100" />
            <el-table-column label="星期" width="80">
              <template #default="{ row }">{{ weekdayName(row.weekday) }}</template>
            </el-table-column>
            <el-table-column label="冲突节次" width="100">
              <template #default="{ row }">第 {{ row.overlap_start }}-{{ row.overlap_end }} 节</template>
            </el-table-column>
            <el-table-column label="课程 1" min-width="160">
              <template #default="{ row }">
                <div>{{ row.course1 }}</div>
                <div class="sub-text">{{ row.classroom1 }}</div>
              </template>
            </el-table-column>
            <el-table-column label="课程 2" min-width="160">
              <template #default="{ row }">
                <div>{{ row.course2 }}</div>
                <div class="sub-text">{{ row.classroom2 }}</div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 教室冲突 -->
        <el-tab-pane :label="`教室冲突 (${data.classroom_conflicts?.length ?? 0})`" name="classroom">
          <el-table :data="data.classroom_conflicts" stripe empty-text="无教室冲突">
            <el-table-column prop="classroom" label="教室" width="120" />
            <el-table-column label="星期" width="80">
              <template #default="{ row }">{{ weekdayName(row.weekday) }}</template>
            </el-table-column>
            <el-table-column label="冲突节次" width="100">
              <template #default="{ row }">第 {{ row.overlap_start }}-{{ row.overlap_end }} 节</template>
            </el-table-column>
            <el-table-column label="课程 1" min-width="160">
              <template #default="{ row }">
                <div>{{ row.course1 }}</div>
                <div class="sub-text">{{ row.teacher1 }}</div>
              </template>
            </el-table-column>
            <el-table-column label="课程 2" min-width="160">
              <template #default="{ row }">
                <div>{{ row.course2 }}</div>
                <div class="sub-text">{{ row.teacher2 }}</div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 容量不足 -->
        <el-tab-pane :label="`容量不足 (${data.capacity_violations?.length ?? 0})`" name="capacity">
          <el-table :data="data.capacity_violations" stripe empty-text="无容量不足">
            <el-table-column prop="course" label="课程" min-width="160" />
            <el-table-column prop="classroom" label="教室" width="120" />
            <el-table-column label="星期" width="80">
              <template #default="{ row }">{{ weekdayName(row.weekday) }}</template>
            </el-table-column>
            <el-table-column label="节次" width="100">
              <template #default="{ row }">第 {{ row.start_slot }}-{{ row.end_slot }} 节</template>
            </el-table-column>
            <el-table-column label="容量 / 学生数" width="130">
              <template #default="{ row }">
                <el-tag type="danger">{{ row.capacity }} / {{ row.students }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="缺座" width="80">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: bold">-{{ row.shortage }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import { conflictsApi } from '@/api/conflicts'

const route = useRoute()
const versionId = Number(route.params.versionId)

const loading = ref(false)
const data = ref({})
const summary = computed(() => data.value.summary)
const activeTab = ref('class')

const WEEKDAY_NAMES = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
const weekdayName = (d) => WEEKDAY_NAMES[d] ?? `星期${d}`

const summaryCards = computed(() => [
  { key: 'class_conflicts',    label: '班级冲突',  count: summary.value?.class_conflicts    ?? 0 },
  { key: 'teacher_conflicts',  label: '教师冲突',  count: summary.value?.teacher_conflicts  ?? 0 },
  { key: 'classroom_conflicts',label: '教室冲突',  count: summary.value?.classroom_conflicts ?? 0 },
  { key: 'capacity_violations',label: '容量不足',  count: summary.value?.capacity_violations ?? 0 },
])

const reload = async () => {
  loading.value = true
  try {
    data.value = await conflictsApi.get(versionId)
  } catch (e) {
    ElMessage.error('加载冲突数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.page-container { width: 100%; }
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}
.page-title { font-size: 16px; font-weight: 600; flex: 1; }

.summary-card {
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border: 1px solid #e4e7ed;
  position: relative;
}
.summary-card.has-conflict { background: #fff0f0; border-color: #f56c6c; }
.summary-card.no-conflict  { background: #f0fff4; border-color: #67c23a; }
.card-count { font-size: 32px; font-weight: 700; line-height: 1; }
.has-conflict .card-count { color: #f56c6c; }
.no-conflict  .card-count { color: #67c23a; }
.card-label { font-size: 13px; color: #606266; margin-top: 6px; }
.ok-icon { position: absolute; top: 8px; right: 8px; color: #67c23a; font-size: 18px; }

.sub-text { font-size: 12px; color: #909399; margin-top: 2px; }
</style>
