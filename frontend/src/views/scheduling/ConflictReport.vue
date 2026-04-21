<template>
  <div class="page-container">
    <!-- 顶部：返回 + 标题 + 导出 -->
    <div class="page-header">
      <el-button link @click="$router.back()">← 返回</el-button>
      <span class="page-title">冲突分析报告 · 版本 #{{ versionId }}</span>
      <el-button @click="reload" :loading="loading" size="small">刷新</el-button>
      <el-button @click="handleExport" size="small" type="success" :disabled="loading">
        导出 Excel
      </el-button>
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
          <div class="tab-toolbar">
            <el-button
              type="warning" size="small"
              :disabled="!data.class_conflicts?.length || fixing.class"
              :loading="fixing.class"
              @click="openFixDialog('class')"
            >修复班级冲突</el-button>
          </div>
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
          <div class="tab-toolbar">
            <el-button
              type="warning" size="small"
              :disabled="!data.teacher_conflicts?.length || fixing.teacher"
              :loading="fixing.teacher"
              @click="openFixDialog('teacher')"
            >修复教师冲突</el-button>
          </div>
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
          <div class="tab-toolbar">
            <el-button
              type="warning" size="small"
              :disabled="!data.classroom_conflicts?.length || fixing.classroom"
              :loading="fixing.classroom"
              @click="openFixDialog('classroom')"
            >修复教室冲突</el-button>
          </div>
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
          <div class="tab-toolbar">
            <el-button
              type="warning" size="small"
              :disabled="!data.capacity_violations?.length || fixing.capacity"
              :loading="fixing.capacity"
              @click="openFixDialog('capacity')"
            >修复容量不足</el-button>
          </div>
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

    <!-- 修复确认弹窗 -->
    <el-dialog v-model="fixDialog.visible" :title="fixDialog.title" width="420px">
      <p>{{ fixDialog.desc }}</p>
      <p style="color: #e6a23c; font-size: 13px; margin-top: 8px">
        ⚠ 此操作将直接修改排课数据，建议先导出 Excel 留存当前记录。
      </p>
      <template #footer>
        <el-button @click="fixDialog.visible = false">取消</el-button>
        <el-button type="danger" @click="confirmFix" :loading="fixing[fixDialog.type]">
          确认修复
        </el-button>
      </template>
    </el-dialog>

    <!-- 修复结果弹窗 -->
    <el-dialog v-model="resultDialog.visible" title="修复结果" width="500px">
      <el-alert
        :title="`成功调整 ${resultDialog.applied} 处，${resultDialog.failed} 处无法自动修复`"
        :type="resultDialog.failed > 0 ? 'warning' : 'success'"
        :closable="false"
        style="margin-bottom: 12px"
      />
      <div v-if="resultDialog.adjustments?.length">
        <div style="font-weight: 600; margin-bottom: 6px">已调整：</div>
        <el-table :data="resultDialog.adjustments" size="small" max-height="200">
          <el-table-column prop="course" label="课程" min-width="120" />
          <el-table-column prop="old_classroom" label="原教室" min-width="100"
            v-if="resultDialog.type === 'capacity'" />
          <el-table-column prop="new_classroom" label="新教室" min-width="100"
            v-if="resultDialog.type === 'capacity'" />
          <el-table-column prop="old_time" label="原时间" min-width="130"
            v-if="resultDialog.type !== 'capacity'" />
          <el-table-column prop="new_time" label="新时间" min-width="130"
            v-if="resultDialog.type !== 'capacity'" />
        </el-table>
      </div>
      <div v-if="resultDialog.failures?.length" style="margin-top: 12px">
        <div style="font-weight: 600; color: #e6a23c; margin-bottom: 6px">未能修复：</div>
        <el-table :data="resultDialog.failures" size="small" max-height="160">
          <el-table-column prop="course" label="课程" min-width="120" />
          <el-table-column prop="reason" label="原因" min-width="160" />
        </el-table>
      </div>
      <template #footer>
        <el-button type="primary" @click="resultDialog.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
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

const fixing = reactive({ class: false, teacher: false, classroom: false, capacity: false })

const fixDialog = reactive({ visible: false, type: '', title: '', desc: '' })
const resultDialog = reactive({
  visible: false, type: '', applied: 0, failed: 0, adjustments: [], failures: []
})

const FIX_LABELS = {
  class: '班级冲突',
  teacher: '教师冲突',
  classroom: '教室冲突',
  capacity: '容量不足',
}

const FIX_DESCS = {
  class: '将为有时间冲突的班级课程自动寻找新的无冲突时间槽并调整排课。',
  teacher: '将为有时间冲突的教师课程自动寻找新的无冲突时间槽并调整排课。',
  classroom: '将为有时间冲突的教室课程自动寻找新的无冲突时间槽并调整排课。',
  capacity: '将为学生数超过教室容量的课程自动更换为容量更大的空闲教室。',
}

const WEEKDAY_NAMES = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
const weekdayName = (d) => WEEKDAY_NAMES[d] ?? `星期${d}`

const summaryCards = computed(() => [
  { key: 'class_conflicts',     label: '班级冲突',  count: summary.value?.class_conflicts    ?? 0 },
  { key: 'teacher_conflicts',   label: '教师冲突',  count: summary.value?.teacher_conflicts  ?? 0 },
  { key: 'classroom_conflicts', label: '教室冲突',  count: summary.value?.classroom_conflicts ?? 0 },
  { key: 'capacity_violations', label: '容量不足',  count: summary.value?.capacity_violations ?? 0 },
])

const reload = async () => {
  loading.value = true
  try {
    data.value = await conflictsApi.get(versionId)
  } catch {
    ElMessage.error('加载冲突数据失败')
  } finally {
    loading.value = false
  }
}

const handleExport = () => {
  window.open(conflictsApi.exportUrl(versionId), '_blank')
}

const openFixDialog = (type) => {
  fixDialog.type = type
  fixDialog.title = `修复${FIX_LABELS[type]}`
  fixDialog.desc = FIX_DESCS[type]
  fixDialog.visible = true
}

const confirmFix = async () => {
  const type = fixDialog.type
  fixDialog.visible = false
  fixing[type] = true
  try {
    const res = await conflictsApi.fix(versionId, type)
    resultDialog.type = type
    resultDialog.applied = res.applied
    resultDialog.failed = res.failed
    resultDialog.adjustments = res.adjustments ?? []
    resultDialog.failures = res.failures ?? []
    resultDialog.visible = true
    await reload()
  } catch (e) {
    ElMessage.error('修复失败：' + (e?.response?.data?.detail ?? e.message))
  } finally {
    fixing[type] = false
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

.tab-toolbar { margin-bottom: 12px; }
.sub-text { font-size: 12px; color: #909399; margin-top: 2px; }
</style>
