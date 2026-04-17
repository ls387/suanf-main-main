<template>
  <div class="page-container">
    <el-row :gutter="20">
      <!-- 主进度区 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>排课进度 · 版本 #{{ versionId }}</span>
              <el-tag :type="statusTagType" size="large">{{ statusLabel }}</el-tag>
            </div>
          </template>

          <!-- 进度条 -->
          <div class="progress-section">
            <el-progress
              :percentage="percent"
              :status="progressStatus"
              :stroke-width="18"
              striped
              striped-flow
              :duration="10"
            />
            <div class="progress-meta">
              <span v-if="stage === 'init'">初始化种群...</span>
              <span v-else-if="stage === 'evolving'">
                第 {{ generation }} / {{ totalGenerations }} 代 &nbsp;·&nbsp;
                最佳适应度：{{ bestFitness.toFixed(0) }}
              </span>
              <span v-else-if="stage === 'done'">排课完成！</span>
              <span v-else-if="stage === 'error'" class="error-text">{{ errorMessage }}</span>
              <span v-else>等待排课开始...</span>
            </div>
          </div>

          <!-- 实时数据卡片 -->
          <el-row :gutter="12" style="margin-top: 24px" v-if="stage === 'evolving' || stage === 'done'">
            <el-col :span="8">
              <div class="stat-card">
                <div class="stat-value">{{ generation }}</div>
                <div class="stat-label">当前代数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-card">
                <div class="stat-value">{{ bestFitness.toFixed(0) }}</div>
                <div class="stat-label">最佳适应度</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-card">
                <div class="stat-value">{{ elapsedTime }}</div>
                <div class="stat-label">已用时</div>
              </div>
            </el-col>
          </el-row>

          <!-- 完成结果展示 -->
          <div v-if="stage === 'done' && result" class="result-section">
            <el-divider>排课结果摘要</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="覆盖率">
                <el-tag :type="result.coverage_rate >= 95 ? 'success' : 'warning'">
                  {{ result.coverage_rate?.toFixed(1) }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="已排 / 总任务">
                {{ result.scheduled_tasks }} / {{ result.total_tasks }}
              </el-descriptions-item>
              <el-descriptions-item label="执行时间">
                {{ result.execution_time?.toFixed(1) }} 秒
              </el-descriptions-item>
              <el-descriptions-item label="平均利用率">
                {{ result.average_utilization_rate?.toFixed(1) ?? '-' }}%
              </el-descriptions-item>
              <el-descriptions-item label="冲突情况" :span="2">
                <el-space>
                  <el-tag :type="result.conflicts?.teacher > 0 ? 'danger' : 'success'">
                    教师冲突 {{ result.conflicts?.teacher ?? '-' }}
                  </el-tag>
                  <el-tag :type="result.conflicts?.class > 0 ? 'danger' : 'success'">
                    班级冲突 {{ result.conflicts?.class ?? '-' }}
                  </el-tag>
                  <el-tag :type="result.conflicts?.classroom > 0 ? 'danger' : 'success'">
                    教室冲突 {{ result.conflicts?.classroom ?? '-' }}
                  </el-tag>
                </el-space>
              </el-descriptions-item>
            </el-descriptions>

            <div style="margin-top: 20px; display: flex; gap: 12px">
              <el-button type="primary" @click="$router.push('/timetable/teacher')">
                查看课表
              </el-button>
              <el-button type="warning" @click="$router.push(`/scheduling/conflicts/${versionId}`)">
                冲突分析
              </el-button>
              <el-button @click="confirmVersion" :loading="confirming" v-if="versionStatus === 'draft'">
                确认此版本
              </el-button>
              <el-button @click="$router.push('/scheduling/versions')">
                返回版本列表
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：连接状态 + 日志 -->
      <el-col :span="8">
        <el-card>
          <template #header><span>连接状态</span></template>
          <div class="ws-status">
            <el-badge :type="wsConnected ? 'success' : 'danger'" is-dot>
              <span>{{ wsConnected ? 'WebSocket 已连接' : 'WebSocket 已断开' }}</span>
            </el-badge>
            <el-button
              v-if="!wsConnected && stage !== 'done'"
              size="small"
              style="margin-top: 8px"
              @click="reconnect"
            >
              手动重连
            </el-button>
          </div>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header><span>进度日志</span></template>
          <div class="log-container" ref="logContainer">
            <div v-for="(log, i) in logs" :key="i" class="log-item" :class="log.type">
              <span class="log-time">{{ log.time }}</span>
              {{ log.message }}
            </div>
            <div v-if="logs.length === 0" class="empty-log">等待进度推送...</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createSchedulingWs } from '@/api/scheduling'
import { versionsApi } from '@/api/versions'

const route = useRoute()
const router = useRouter()

const versionId = computed(() => Number(route.params.versionId))

// 进度状态
const percent = ref(0)
const stage = ref('')        // init | evolving | done | error
const generation = ref(0)
const totalGenerations = ref(0)
const bestFitness = ref(0)
const errorMessage = ref('')
const result = ref(null)
const versionStatus = ref('draft')

// WS 状态
const wsConnected = ref(false)
let ws = null
let reconnectTimer = null
let heartbeatTimer = null

// 计时器
const startTime = ref(null)
const elapsedTime = ref('0s')
let elapsedTimer = null

// 日志
const logs = ref([])
const logContainer = ref(null)
const confirming = ref(false)

// ---- 计算属性 ----
const statusLabel = computed(() => ({
  '': '等待中',
  init: '初始化',
  evolving: '运行中',
  done: '已完成',
  error: '出错',
}[stage.value] || stage.value))

const statusTagType = computed(() => ({
  '': 'info', init: 'warning', evolving: '', done: 'success', error: 'danger',
}[stage.value] || 'info'))

const progressStatus = computed(() => {
  if (stage.value === 'done') return 'success'
  if (stage.value === 'error') return 'exception'
  return ''
})

// ---- WebSocket ----
const addLog = (message, type = 'info') => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.push({ time, message, type })
  if (logs.value.length > 200) logs.value.shift()
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const startElapsedTimer = () => {
  startTime.value = Date.now()
  elapsedTimer = setInterval(() => {
    const sec = Math.floor((Date.now() - startTime.value) / 1000)
    if (sec < 60) elapsedTime.value = `${sec}s`
    else elapsedTime.value = `${Math.floor(sec / 60)}m${sec % 60}s`
  }, 1000)
}

const handleMessage = (data) => {
  percent.value = data.percent ?? percent.value
  stage.value = data.stage ?? stage.value
  generation.value = data.generation ?? generation.value
  totalGenerations.value = data.total_generations ?? totalGenerations.value
  bestFitness.value = data.best_fitness ?? bestFitness.value

  if (data.stage === 'init' && !startTime.value) {
    startElapsedTimer()
  }

  if (data.stage === 'done') {
    result.value = data.result ?? null
    clearInterval(elapsedTimer)
    addLog(`排课完成！覆盖率 ${data.result?.coverage_rate?.toFixed(1)}%`, 'success')
    stopWs()
  } else if (data.stage === 'error') {
    errorMessage.value = data.message
    addLog(`错误：${data.message}`, 'error')
    clearInterval(elapsedTimer)
    stopWs()
  } else {
    if (data.message) addLog(data.message)
  }
}

const connect = () => {
  if (ws) stopWs()

  ws = createSchedulingWs(versionId.value)

  ws.onopen = () => {
    wsConnected.value = true
    addLog('WebSocket 已连接')
    // 心跳：每 20s 发一次 ping，防止连接超时
    heartbeatTimer = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) ws.send('ping')
    }, 20000)
  }

  ws.onmessage = (e) => {
    try {
      handleMessage(JSON.parse(e.data))
    } catch {
      addLog(`收到消息: ${e.data}`)
    }
  }

  ws.onclose = () => {
    wsConnected.value = false
    clearInterval(heartbeatTimer)
    // 排课未完成时自动重连
    if (stage.value !== 'done' && stage.value !== 'error') {
      addLog('连接断开，5s 后重连...', 'warn')
      reconnectTimer = setTimeout(connect, 5000)
    } else {
      addLog('连接已关闭')
    }
  }

  ws.onerror = () => {
    addLog('WebSocket 连接出错', 'error')
  }
}

const stopWs = () => {
  clearInterval(heartbeatTimer)
  clearTimeout(reconnectTimer)
  ws?.close()
  ws = null
}

const reconnect = () => {
  addLog('手动重连...')
  connect()
}

// ---- 确认版本 ----
const confirmVersion = async () => {
  confirming.value = true
  try {
    await versionsApi.confirm(versionId.value)
    versionStatus.value = 'published'
    ElMessage.success('版本已确认发布')
  } catch {
    // 错误已由 axios 拦截器处理
  } finally {
    confirming.value = false
  }
}

// ---- 生命周期 ----
onMounted(async () => {
  // 先查一下当前状态（可能是断线重连场景）
  try {
    const status = await versionsApi.getSchedulingStatus(versionId.value)
    versionStatus.value = status.status
    if (status.status === 'published' || status.status === 'archived') {
      // 已完成，不需要 WS，直接显示状态
      stage.value = 'done'
      percent.value = 100
      addLog('版本已完成排课，已加载历史状态')
      return
    }
  } catch {
    // 查询失败也继续连 WS
  }

  connect()
})

onUnmounted(() => {
  stopWs()
  clearInterval(elapsedTimer)
})
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }

.progress-section { padding: 8px 0; }
.progress-meta { margin-top: 10px; color: #606266; font-size: 14px; text-align: center; }
.error-text { color: #f56c6c; }

.stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.stat-value { font-size: 28px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }

.result-section { margin-top: 24px; }

.ws-status { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; }

.log-container {
  height: 320px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 4px;
  padding: 8px;
}
.log-item { padding: 2px 0; line-height: 1.6; }
.log-item.success { color: #89d185; }
.log-item.error { color: #f48771; }
.log-item.warn { color: #d7ba7d; }
.log-time { color: #858585; margin-right: 6px; }
.empty-log { color: #555; text-align: center; padding: 20px 0; }
</style>
