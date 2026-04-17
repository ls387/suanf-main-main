<template>
  <div class="page-container">
    <!-- ══ 阶段1：选择源版本 ══ -->
    <template v-if="!workingVersionId">
      <el-card>
        <template #header><span>手动调课 — 选择源版本</span></template>
        <el-form :inline="true">
          <el-form-item label="已发布版本">
            <el-select
              v-model="sourceVersionId"
              placeholder="请选择要调整的版本"
              filterable
              style="min-width: 280px"
            >
              <el-option
                v-for="v in publishedVersions"
                :key="v.version_id"
                :label="`[${v.semester}] ${v.version_name}`"
                :value="v.version_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :disabled="!sourceVersionId"
              @click="showForkDialog = true"
            >
              基于此版本调课
            </el-button>
          </el-form-item>
        </el-form>
        <el-empty v-if="publishedVersions.length === 0" description="暂无已发布版本" />
      </el-card>
    </template>

    <!-- ══ 阶段2：拖拽调整 ══ -->
    <template v-else>
      <!-- 工具栏 -->
      <el-card class="toolbar-card">
        <div class="toolbar">
          <div class="toolbar-left">
            <span class="version-title">{{ workingVersion?.version_name }}</span>
            <el-tag type="info" size="small" style="margin-left:8px">草稿</el-tag>
            <span v-if="workingVersion?.parent_version_id" class="parent-label">
              基于版本 #{{ workingVersion.parent_version_id }}
            </span>
          </div>
          <div class="toolbar-right">
            <el-button @click="handleDiscard" :loading="discarding">放弃草稿</el-button>
            <el-button type="primary" @click="handleConfirm" :loading="confirming">
              确认发布
            </el-button>
          </div>
        </div>
        <div v-if="moveLog.length" class="move-log">
          <span v-for="(log, i) in moveLog" :key="i" class="log-item" :class="log.type">
            {{ log.msg }}
          </span>
        </div>
      </el-card>

      <!-- 拖拽课表 -->
      <el-card v-loading="scheduleLoading" style="margin-top:12px">
        <DraggableTimetableGrid
          :data="scheduleData"
          @move-success="onMoveSuccess"
          @move-error="onMoveError"
        />
      </el-card>
    </template>

    <!-- Fork 弹窗 -->
    <el-dialog v-model="showForkDialog" title="新建调课草稿" width="400px">
      <el-form :model="forkForm" label-width="100px">
        <el-form-item label="新版本名">
          <el-input v-model="forkForm.version_name" placeholder="例如：2025秋手调版" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="forkForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForkDialog = false">取消</el-button>
        <el-button type="primary" @click="handleFork" :loading="forking">创建并调课</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { versionsApi } from '@/api/versions'
import { scheduleApi } from '@/api/schedules'
import DraggableTimetableGrid from '@/components/DraggableTimetableGrid.vue'

const router = useRouter()
const route  = useRoute()

// ─── 阶段1状态 ─────────────────────────────────────────────────────────────
const publishedVersions = ref([])
const sourceVersionId   = ref(null)
const showForkDialog    = ref(false)
const forking           = ref(false)
const forkForm          = ref({ version_name: '', description: '' })

// ─── 阶段2状态 ─────────────────────────────────────────────────────────────
const workingVersionId  = ref(route.params.versionId ? Number(route.params.versionId) : null)
const workingVersion    = ref(null)
const scheduleData      = ref([])
const scheduleLoading   = ref(false)
const confirming        = ref(false)
const discarding        = ref(false)
const moveLog           = ref([])   // { msg, type: 'success'|'error' }

// ─── 初始化 ────────────────────────────────────────────────────────────────
onMounted(async () => {
  // 拉取已发布版本（阶段1 选择列表）
  const all = await versionsApi.getAll({ status: 'published' })
  publishedVersions.value = all

  // 如果 URL 里有 versionId（阶段2），直接加载
  if (workingVersionId.value) {
    await loadWorkingVersion()
    return
  }

  // 如果 URL 里有 source query（从 VersionList 跳来），预选源版本
  const sourceId = Number(route.query.source)
  if (sourceId) sourceVersionId.value = sourceId
})

async function loadWorkingVersion() {
  try {
    workingVersion.value = await versionsApi.getOne(workingVersionId.value)
  } catch {
    ElMessage.error('版本不存在')
    workingVersionId.value = null
    return
  }
  await loadSchedules()
}

async function loadSchedules() {
  scheduleLoading.value = true
  try {
    scheduleData.value = await scheduleApi.getSchedules(workingVersionId.value)
  } finally {
    scheduleLoading.value = false
  }
}

// ─── Fork ──────────────────────────────────────────────────────────────────
async function handleFork() {
  if (!forkForm.value.version_name.trim()) {
    ElMessage.warning('请输入新版本名')
    return
  }
  forking.value = true
  try {
    const newVersion = await scheduleApi.fork(sourceVersionId.value, forkForm.value)
    showForkDialog.value = false
    workingVersionId.value = newVersion.version_id
    workingVersion.value   = newVersion
    router.replace(`/scheduling/drag/${newVersion.version_id}`)
    await loadSchedules()
    ElMessage.success('草稿已创建，可以开始拖拽调课')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'fork 失败')
  } finally {
    forking.value = false
  }
}

// ─── 拖拽回调 ──────────────────────────────────────────────────────────────
async function onMoveSuccess({ scheduleId, newWeekday, newStartSlot }) {
  addLog(`✓ #${scheduleId} 已移至周${newWeekday}第${newStartSlot}节`, 'success')
  // 重新拉取确保数据一致
  await loadSchedules()
}

function onMoveError({ scheduleId, error }) {
  addLog(`✗ #${scheduleId} 移动失败：${error}`, 'error')
}

function addLog(msg, type) {
  moveLog.value.unshift({ msg, type })
  if (moveLog.value.length > 5) moveLog.value.pop()
}

// ─── 确认发布 ──────────────────────────────────────────────────────────────
async function handleConfirm() {
  await ElMessageBox.confirm('确认将此草稿发布为正式版本？', '确认发布', { type: 'warning' })
  confirming.value = true
  try {
    await versionsApi.confirm(workingVersionId.value)
    ElMessage.success('发布成功')
    router.push('/scheduling/versions')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发布失败')
  } finally {
    confirming.value = false
  }
}

// ─── 放弃草稿 ──────────────────────────────────────────────────────────────
async function handleDiscard() {
  await ElMessageBox.confirm('放弃此草稿将删除所有调整记录，确定？', '放弃草稿', { type: 'warning' })
  discarding.value = true
  try {
    await versionsApi.delete(workingVersionId.value)
    ElMessage.success('草稿已删除')
    workingVersionId.value = null
    workingVersion.value   = null
    scheduleData.value     = []
    moveLog.value          = []
    router.replace('/scheduling/drag')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  } finally {
    discarding.value = false
  }
}
</script>

<style scoped>
.page-container { width: 100%; }

.toolbar-card :deep(.el-card__body) { padding: 12px 20px; }

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; gap: 8px; }
.version-title { font-size: 16px; font-weight: 600; color: #303133; }
.parent-label  { font-size: 12px; color: #909399; }

.move-log {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 80px;
  overflow-y: auto;
}
.log-item { font-size: 12px; padding: 2px 0; }
.log-item.success { color: #67c23a; }
.log-item.error   { color: #f56c6c; }
</style>
