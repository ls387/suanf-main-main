<template>
  <div class="page-container">
    <el-row :gutter="20">
      <!-- 左侧：版本创建表单 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>创建排课版本</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="120px"
            @submit.prevent
          >
            <!-- 基本信息 -->
            <el-divider content-position="left">基本信息</el-divider>

            <el-form-item label="学期" prop="semester">
              <el-select v-model="form.semester" placeholder="选择或输入学期" allow-create filterable style="width: 220px">
                <el-option label="2025-2026-1（2025秋）" value="2025-2026-1" />
                <el-option label="2025-2026-2（2026春）" value="2025-2026-2" />
                <el-option label="2024-2025-1（2024秋）" value="2024-2025-1" />
                <el-option label="2024-2025-2（2025春）" value="2024-2025-2" />
              </el-select>
              <el-text type="info" style="margin-left: 10px; font-size: 12px">
                格式：YYYY-YYYY-N（1=秋，2=春）
              </el-text>
            </el-form-item>

            <el-form-item label="版本名称" prop="version_name">
              <el-input v-model="form.version_name" placeholder="如：第一轮草案" style="width: 280px" />
            </el-form-item>

            <el-form-item label="版本描述">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="2"
                placeholder="可选，简要描述版本目标或特点"
                style="width: 400px"
              />
            </el-form-item>

            <!-- GA 参数 -->
            <el-divider content-position="left">遗传算法参数</el-divider>

            <el-form-item label="种群大小">
              <el-slider v-model="form.population" :min="10" :max="500" show-input style="width: 360px" />
            </el-form-item>

            <el-form-item label="进化代数">
              <el-slider v-model="form.generations" :min="10" :max="1000" show-input style="width: 360px" />
            </el-form-item>

            <el-form-item label="交叉率">
              <el-slider v-model="form.crossover_rate" :min="0" :max="1" :step="0.05" show-input style="width: 360px" />
            </el-form-item>

            <el-form-item label="变异率">
              <el-slider v-model="form.mutation_rate" :min="0" :max="0.5" :step="0.01" show-input style="width: 360px" />
            </el-form-item>

            <el-form-item label="锦标赛大小">
              <el-slider v-model="form.tournament_size" :min="2" :max="20" show-input style="width: 360px" />
            </el-form-item>

            <el-form-item label="精英数量">
              <el-slider v-model="form.elitism_size" :min="1" :max="50" show-input style="width: 360px" />
            </el-form-item>

            <el-form-item label="最大停滞代">
              <el-slider v-model="form.max_stagnation" :min="10" :max="200" show-input style="width: 360px" />
            </el-form-item>

            <!-- 预设 -->
            <el-form-item label="快速预设">
              <el-button-group>
                <el-button @click="loadPreset('small')">小规模</el-button>
                <el-button @click="loadPreset('medium')">中等</el-button>
                <el-button @click="loadPreset('large')">大规模</el-button>
              </el-button-group>
            </el-form-item>

            <!-- 约束权重（高级，默认折叠） -->
            <el-divider content-position="left">
              约束权重
              <el-text type="info" style="font-size: 12px; margin-left: 8px">（高级，不懂可不改）</el-text>
            </el-divider>

            <el-collapse v-model="penaltyCollapse" style="margin-bottom: 16px; border: none">
              <el-collapse-item name="penalty">
                <template #title>
                  <el-text type="primary" style="font-size: 13px">
                    展开约束权重配置
                    <el-tag v-if="penaltyModified" type="warning" size="small" style="margin-left: 8px">已修改</el-tag>
                  </el-text>
                </template>

                <div class="penalty-section">
                  <div class="penalty-group-title">
                    硬约束罚分
                    <el-text type="info" size="small">（负数，绝对值越大 = 该约束越不可违反）</el-text>
                  </div>
                  <el-row :gutter="12">
                    <el-col :span="12" v-for="item in hardConstraints" :key="item.key">
                      <div class="penalty-item">
                        <el-tooltip :content="item.tip" placement="top">
                          <span class="penalty-label">{{ item.label }}</span>
                        </el-tooltip>
                        <el-input-number
                          v-model="penalty[item.key]"
                          :min="-99999" :max="-1"
                          :step="1000"
                          size="small"
                          style="width: 140px"
                          :placeholder="String(item.default)"
                        />
                        <el-text type="info" size="small" style="margin-left: 4px">默认 {{ item.default }}</el-text>
                      </div>
                    </el-col>
                  </el-row>

                  <div class="penalty-group-title" style="margin-top: 16px">
                    软约束强度
                    <el-text type="info" size="small">（正数，越大 = 违反该软约束扣分越多）</el-text>
                  </div>
                  <el-row :gutter="12">
                    <el-col :span="12" v-for="item in softConstraints" :key="item.key">
                      <div class="penalty-item">
                        <el-tooltip :content="item.tip" placement="top">
                          <span class="penalty-label">{{ item.label }}</span>
                        </el-tooltip>
                        <el-input-number
                          v-model="penalty[item.key]"
                          :min="0" :max="10000"
                          :step="50"
                          size="small"
                          style="width: 140px"
                          :placeholder="String(item.default)"
                        />
                        <el-text type="info" size="small" style="margin-left: 4px">默认 {{ item.default }}</el-text>
                      </div>
                    </el-col>
                  </el-row>

                  <div style="margin-top: 12px">
                    <el-button size="small" @click="resetPenalty">恢复全部默认值</el-button>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="submitting"
                @click="handleSubmit"
              >
                <el-icon><VideoPlay /></el-icon>
                创建版本并开始排课
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：说明 + 最近版本 -->
      <el-col :span="10">
        <el-card>
          <template #header><span>参数说明</span></template>
          <div class="info-text">
            <p><strong>种群大小：</strong>每代个体数，越大搜索越广，越慢</p>
            <p><strong>进化代数：</strong>算法迭代次数</p>
            <p><strong>交叉率：</strong>基因交叉概率，推荐 0.7–0.9</p>
            <p><strong>变异率：</strong>基因变异概率，推荐 0.05–0.15</p>
            <p><strong>停滞代数：</strong>连续无改进则提前停止</p>
          </div>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <span>最近版本</span>
              <el-button link @click="$router.push('/scheduling/versions')">查看全部</el-button>
            </div>
          </template>
          <div v-if="recentVersions.length === 0" class="empty-tip">
            <el-text type="info">暂无版本</el-text>
          </div>
          <div v-else>
            <div v-for="v in recentVersions" :key="v.version_id" class="version-item">
              <div class="version-name">{{ v.version_name }}</div>
              <div class="version-meta">
                {{ v.semester }} &nbsp;|&nbsp;
                <el-tag :type="statusTagType(v.status)" size="small">{{ statusLabel(v.status) }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import { versionsApi } from '@/api/versions'
import { schedulingApi } from '@/api/scheduling'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const recentVersions = ref([])
const penaltyCollapse = ref([])  // 默认收起

const form = ref({
  semester: '',
  version_name: '',
  description: '',
  population: 100,
  generations: 200,
  crossover_rate: 0.8,
  mutation_rate: 0.1,
  tournament_size: 5,
  elitism_size: 10,
  max_stagnation: 50,
})

// ---- 约束权重 ----
// null 表示"使用后端默认值"，用户改过的键才传给后端
const penalty = ref({
  teacher_conflict: null,
  class_conflict: null,
  classroom_conflict: null,
  capacity_violation: null,
  blackout_violation: null,
  feature_violation: null,
  thursday_afternoon: null,
  campus_commute: null,
  weekend_penalty: null,
  teacher_preference: null,
  classroom_continuity: null,
  utilization_waste: null,
  daily_classroom_variety: null,
  student_overload: null,
  task_relation: null,
  required_night_penalty: null,
  elective_prime_time_penalty: null,
})

const hardConstraints = [
  { key: 'teacher_conflict',   label: '教师时间冲突',   default: -50000, tip: '同一教师在同一时段被安排多门课' },
  { key: 'class_conflict',     label: '班级时间冲突',   default: -80000, tip: '同一班级在同一时段被安排多门课（最高优先级）' },
  { key: 'classroom_conflict', label: '教室时间冲突',   default: -50000, tip: '同一教室在同一时段被安排多门课' },
  { key: 'capacity_violation', label: '教室容量不足',   default: -60000, tip: '学生人数超过教室容量' },
  { key: 'blackout_violation', label: '教师禁用时段',   default: -8000,  tip: '违反教师设置的不可排课时段' },
  { key: 'feature_violation',  label: '设施不满足',     default: -8000,  tip: '课程所需设施（实验室等）教室不具备' },
  { key: 'thursday_afternoon', label: '周四下午禁排',   default: -3000,  tip: '周四第6-10节禁止安排课程' },
  { key: 'campus_commute',     label: '跨校区通勤',     default: -5000,  tip: '同一教师同一天在不同校区上课' },
  { key: 'weekend_penalty',    label: '周末排课',       default: -10000, tip: '任何课程安排在周六/周日' },
]

const softConstraints = [
  { key: 'teacher_preference',          label: '教师偏好未满足', default: 100,  tip: '未安排在教师偏好的时间段，每次违反扣此分' },
  { key: 'classroom_continuity',        label: '连续课换教室',   default: 300,  tip: '同一课程连续课次未在同一教室' },
  { key: 'utilization_waste',           label: '教室容量浪费',   default: 200,  tip: '教室容量远大于实际学生数' },
  { key: 'daily_classroom_variety',     label: '同天多教室',     default: 300,  tip: '同一教师同一天在多个教室上课' },
  { key: 'student_overload',            label: '学生课程过载',   default: 150,  tip: '学生单日课时过多' },
  { key: 'task_relation',               label: '课程关系违反',   default: 300,  tip: '有前后依赖关系的课程排课顺序不当' },
  { key: 'required_night_penalty',      label: '必修课安排晚上', default: 400,  tip: '必修课被安排在晚上时段' },
  { key: 'elective_prime_time_penalty', label: '选修占黄金时段', default: 30,   tip: '选修课占用上午/下午前半段黄金时间' },
]

// 是否有任何权重被修改过（非 null）
const penaltyModified = computed(() =>
  Object.values(penalty.value).some(v => v !== null)
)

const resetPenalty = () => {
  Object.keys(penalty.value).forEach(k => { penalty.value[k] = null })
  ElMessage.info('已恢复所有约束权重为默认值')
}

// ---- 其他逻辑 ----
const rules = {
  semester: [{ required: true, message: '请选择或输入学期', trigger: 'blur' }],
  version_name: [{ required: true, message: '请输入版本名称', trigger: 'blur' }],
}

const loadPreset = (type) => {
  const presets = {
    small:  { population: 50,  generations: 100, max_stagnation: 30 },
    medium: { population: 100, generations: 200, max_stagnation: 50 },
    large:  { population: 200, generations: 300, max_stagnation: 80 },
  }
  Object.assign(form.value, presets[type])
  ElMessage.info(`已加载${type === 'small' ? '小规模' : type === 'medium' ? '中等' : '大规模'}预设参数`)
}

const statusLabel = (s) => ({ draft: '草稿', published: '已发布', archived: '已归档' }[s] || s)
const statusTagType = (s) => ({ draft: 'info', published: 'success', archived: '' }[s] || 'info')

const loadRecentVersions = async () => {
  try {
    recentVersions.value = (await versionsApi.list()).slice(0, 5)
  } catch {
    // 静默失败
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true

  try {
    // 1. 创建版本
    const version = await versionsApi.create({
      semester: form.value.semester,
      version_name: form.value.version_name,
      description: form.value.description || undefined,
    })

    ElMessage.success(`版本 "${version.version_name}" 已创建（ID=${version.version_id}）`)

    // 2. 组装排课请求（只传用户改过的权重）
    const payload = {
      version_id: version.version_id,
      population: form.value.population,
      generations: form.value.generations,
      crossover_rate: form.value.crossover_rate,
      mutation_rate: form.value.mutation_rate,
      tournament_size: form.value.tournament_size,
      elitism_size: form.value.elitism_size,
      max_stagnation: form.value.max_stagnation,
    }

    // 过滤掉 null，只附带用户明确修改的权重
    const customPenalty = Object.fromEntries(
      Object.entries(penalty.value).filter(([, v]) => v !== null)
    )
    if (Object.keys(customPenalty).length > 0) {
      payload.penalty_scores = customPenalty
    }

    // 3. 提交排课任务
    await schedulingApi.run(payload)

    // 4. 跳转到进度页
    router.push(`/scheduling/progress/${version.version_id}`)
  } catch (err) {
    console.error('创建/提交排课失败:', err)
  } finally {
    submitting.value = false
  }
}

onMounted(loadRecentVersions)
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
.info-text p { margin: 8px 0; line-height: 1.8; font-size: 14px; }
.empty-tip { padding: 20px 0; text-align: center; }
.version-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.version-item:last-child { border-bottom: none; }
.version-name { font-size: 14px; font-weight: 500; }
.version-meta { font-size: 12px; color: #909399; margin-top: 4px; }

.penalty-section { padding: 4px 8px 8px; }
.penalty-group-title { font-size: 13px; font-weight: 600; color: #303133; margin-bottom: 10px; }
.penalty-item { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.penalty-label {
  width: 100px;
  font-size: 13px;
  color: #606266;
  cursor: default;
  border-bottom: 1px dashed #c0c4cc;
  flex-shrink: 0;
}
</style>
