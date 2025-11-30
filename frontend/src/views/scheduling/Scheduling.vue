<template>
  <div class="page-container">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>排课参数配置</span>
            </div>
          </template>
          
          <el-form :model="form" label-width="140px">
            <el-form-item label="排课版本ID" required>
              <el-input-number v-model="form.version_id" :min="1" />
              <el-text type="info" style="margin-left: 10px;">请先在数据库创建排课版本</el-text>
            </el-form-item>
            
            <el-divider content-position="left">基础参数</el-divider>
            
            <el-form-item label="种群大小">
              <el-slider v-model="form.population" :min="10" :max="500" show-input />
            </el-form-item>
            
            <el-form-item label="进化代数">
              <el-slider v-model="form.generations" :min="10" :max="1000" show-input />
            </el-form-item>
            
            <el-divider content-position="left">高级参数</el-divider>
            
            <el-form-item label="交叉率">
              <el-slider v-model="form.crossover_rate" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
            
            <el-form-item label="变异率">
              <el-slider v-model="form.mutation_rate" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
            
            <el-form-item label="锦标赛大小">
              <el-slider v-model="form.tournament_size" :min="2" :max="20" show-input />
            </el-form-item>
            
            <el-form-item label="精英个体数量">
              <el-slider v-model="form.elitism_size" :min="1" :max="50" show-input />
            </el-form-item>
            
            <el-form-item label="最大停滞代数">
              <el-slider v-model="form.max_stagnation" :min="10" :max="200" show-input />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" size="large" @click="handleRun" :loading="running">
                <el-icon><VideoPlay /></el-icon>
                开始排课
              </el-button>
              <el-button @click="loadPreset('small')">小规模预设</el-button>
              <el-button @click="loadPreset('medium')">中等规模预设</el-button>
              <el-button @click="loadPreset('large')">大规模预设</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>排课结果</span>
            </div>
          </template>
          
          <div v-if="!result" class="empty-result">
            <el-empty description="暂无排课结果" />
          </div>
          
          <div v-else class="result-info">
            <el-result
              :icon="result.success ? 'success' : 'error'"
              :title="result.success ? '排课成功' : '排课失败'"
              :sub-title="result.message"
            >
              <template #extra v-if="result.success">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="最佳适应度">
                    {{ result.best_fitness?.toFixed(2) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="覆盖率">
                    {{ result.coverage_rate?.toFixed(1) }}%
                  </el-descriptions-item>
                  <el-descriptions-item label="总任务数">
                    {{ result.total_tasks }}
                  </el-descriptions-item>
                  <el-descriptions-item label="已排任务数">
                    {{ result.scheduled_tasks }}
                  </el-descriptions-item>
                  <el-descriptions-item label="执行时间">
                    {{ result.execution_time?.toFixed(2) }} 秒
                  </el-descriptions-item>
                </el-descriptions>
                
                <div style="margin-top: 20px;" v-if="result.conflicts">
                  <el-tag type="info">教师冲突: {{ result.conflicts.teacher }}</el-tag>
                  <el-tag type="info" style="margin-left: 10px;">班级冲突: {{ result.conflicts.class }}</el-tag>
                  <el-tag type="info" style="margin-left: 10px;">教室冲突: {{ result.conflicts.classroom }}</el-tag>
                </div>
                
                <div style="margin-top: 20px;">
                  <el-button type="primary" @click="$router.push('/timetable/teacher')">
                    查看课表
                  </el-button>
                </div>
              </template>
            </el-result>
          </div>
        </el-card>
        
        <el-card style="margin-top: 20px;">
          <template #header>
            <span>参数说明</span>
          </template>
          <div class="info-text">
            <p><strong>种群大小：</strong>每代的个体数量，越大搜索范围越广</p>
            <p><strong>进化代数：</strong>算法迭代次数，越多越可能找到更优解</p>
            <p><strong>交叉率：</strong>基因交叉的概率，通常0.7-0.9</p>
            <p><strong>变异率：</strong>基因变异的概率，通常0.01-0.2</p>
            <p><strong>停滞代数：</strong>连续多少代无改进则停止</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { schedulingApi } from '@/api/scheduling'

const running = ref(false)
const result = ref(null)

const form = ref({
  version_id: 1,
  population: 100,
  generations: 200,
  crossover_rate: 0.8,
  mutation_rate: 0.1,
  tournament_size: 5,
  elitism_size: 10,
  max_stagnation: 50
})

const loadPreset = (type) => {
  if (type === 'small') {
    form.value.population = 50
    form.value.generations = 100
    ElMessage.info('已加载小规模预设参数')
  } else if (type === 'medium') {
    form.value.population = 100
    form.value.generations = 200
    ElMessage.info('已加载中等规模预设参数')
  } else if (type === 'large') {
    form.value.population = 200
    form.value.generations = 300
    ElMessage.info('已加载大规模预设参数')
  }
}

const handleRun = async () => {
  running.value = true
  result.value = null
  
  try {
    ElMessage.info('排课任务已开始，请耐心等待...')
    const res = await schedulingApi.run(form.value)
    result.value = res
    
    if (res.success) {
      ElMessage.success('排课完成！')
    } else {
      ElMessage.error('排课失败：' + res.message)
    }
  } catch (error) {
    console.error('排课失败:', error)
    result.value = {
      success: false,
      message: '排课过程中发生错误'
    }
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.page-container {
  width: 100%;
}

.card-header {
  font-weight: bold;
}

.empty-result {
  padding: 40px 0;
  text-align: center;
}

.result-info {
  padding: 20px 0;
}

.info-text p {
  margin: 10px 0;
  line-height: 1.8;
  font-size: 14px;
}
</style>

