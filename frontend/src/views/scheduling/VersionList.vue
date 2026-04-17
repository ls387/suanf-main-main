<template>
  <div class="page-container">
    <!-- 顶部操作栏 -->
    <el-card style="margin-bottom: 16px">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-select
            v-model="filterSemester"
            placeholder="全部学期"
            clearable
            style="width: 200px; margin-right: 12px"
            @change="loadVersions"
          >
            <el-option label="2025-2026-1（2025秋）" value="2025-2026-1" />
            <el-option label="2025-2026-2（2026春）" value="2025-2026-2" />
            <el-option label="2024-2025-1（2024秋）" value="2024-2025-1" />
            <el-option label="2024-2025-2（2025春）" value="2024-2025-2" />
          </el-select>
          <el-select
            v-model="filterStatus"
            placeholder="全部状态"
            clearable
            style="width: 140px"
            @change="loadVersions"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="$router.push('/scheduling/create')">
            <el-icon><Plus /></el-icon>
            新建排课版本
          </el-button>
          <el-button @click="loadVersions" :loading="loading">刷新</el-button>
        </div>
      </div>
    </el-card>

    <!-- 版本列表表格 -->
    <el-card>
      <el-table
        :data="versions"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="version_id" label="ID" width="60" />
        <el-table-column prop="semester" label="学期" width="130" />
        <el-table-column prop="version_name" label="版本名称" min-width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_by" label="创建人" width="100" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="viewTimetable(row)"
            >
              查看课表
            </el-button>

            <el-button
              size="small"
              type="info"
              link
              @click="$router.push(`/scheduling/conflicts/${row.version_id}`)"
            >
              冲突分析
            </el-button>

            <el-button
              size="small"
              type="success"
              link
              v-if="row.status === 'draft'"
              @click="runScheduling(row)"
            >
              重新排课
            </el-button>

            <el-button
              size="small"
              type="warning"
              link
              v-if="row.status === 'draft'"
              @click="confirmVersion(row)"
            >
              确认发布
            </el-button>

            <el-popconfirm
              v-if="row.status === 'draft'"
              :title="`确认删除版本 "${row.version_name}"？`"
              confirm-button-text="删除"
              cancel-button-text="取消"
              confirm-button-type="danger"
              @confirm="deleteVersion(row)"
            >
              <template #reference>
                <el-button size="small" type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="versions.length === 0 && !loading" class="empty-tip">
        <el-empty description="暂无版本，点击右上角新建" />
      </div>
    </el-card>

    <!-- 重新排课弹窗 -->
    <el-dialog v-model="runDialogVisible" title="重新排课" width="500px">
      <el-form :model="runForm" label-width="110px">
        <el-form-item label="目标版本">
          <el-text>{{ runTarget?.version_name }}（ID={{ runTarget?.version_id }}）</el-text>
        </el-form-item>
        <el-form-item label="种群大小">
          <el-slider v-model="runForm.population" :min="10" :max="500" show-input />
        </el-form-item>
        <el-form-item label="进化代数">
          <el-slider v-model="runForm.generations" :min="10" :max="1000" show-input />
        </el-form-item>
        <el-form-item label="最大停滞代">
          <el-slider v-model="runForm.max_stagnation" :min="10" :max="200" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRun" :loading="running">开始排课</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { versionsApi } from '@/api/versions'
import { schedulingApi } from '@/api/scheduling'

const router = useRouter()
const loading = ref(false)
const versions = ref([])
const filterSemester = ref('')
const filterStatus = ref('')

// 重新排课弹窗
const runDialogVisible = ref(false)
const runTarget = ref(null)
const running = ref(false)
const runForm = ref({ population: 100, generations: 200, max_stagnation: 50 })

const statusLabel = (s) => ({ draft: '草稿', published: '已发布', archived: '已归档' }[s] || s)
const statusTagType = (s) => ({ draft: 'info', published: 'success', archived: '' }[s] || 'info')

const formatDate = (dt) => {
  if (!dt) return '-'
  return dt.replace('T', ' ').slice(0, 19)
}

const loadVersions = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterSemester.value) params.semester = filterSemester.value
    if (filterStatus.value) params.status = filterStatus.value
    versions.value = await versionsApi.list(params)
  } catch {
    // axios 拦截器已提示
  } finally {
    loading.value = false
  }
}

const viewTimetable = (row) => {
  // 跳到教师课表，并把 version_id 作为 query 传递
  router.push({ path: '/timetable/teacher', query: { version_id: row.version_id } })
}

const runScheduling = (row) => {
  runTarget.value = row
  runDialogVisible.value = true
}

const submitRun = async () => {
  running.value = true
  try {
    await schedulingApi.run({
      version_id: runTarget.value.version_id,
      ...runForm.value,
      crossover_rate: 0.8,
      mutation_rate: 0.1,
      tournament_size: 5,
      elitism_size: 10,
    })
    runDialogVisible.value = false
    router.push(`/scheduling/progress/${runTarget.value.version_id}`)
  } catch {
    // 错误已处理
  } finally {
    running.value = false
  }
}

const confirmVersion = async (row) => {
  try {
    await versionsApi.confirm(row.version_id)
    ElMessage.success(`版本 "${row.version_name}" 已发布`)
    loadVersions()
  } catch {
    // 错误已处理
  }
}

const deleteVersion = async (row) => {
  try {
    await versionsApi.delete(row.version_id)
    ElMessage.success(`版本 "${row.version_name}" 已删除`)
    loadVersions()
  } catch {
    // 错误已处理
  }
}

onMounted(loadVersions)
</script>

<style scoped>
.page-container { width: 100%; }
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.toolbar-left { display: flex; align-items: center; }
.toolbar-right { display: flex; gap: 8px; }
.empty-tip { padding: 40px 0; }
</style>
