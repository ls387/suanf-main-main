<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>教师偏好与黑名单时间管理</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="教师黑名单时间" name="blackout">
          <div style="margin-bottom: 15px;">
            <el-button type="primary" @click="handleAddBlackout">
              <el-icon><Plus /></el-icon>新增黑名单时间
            </el-button>
          </div>
          <el-table :data="blackoutData" v-loading="loading" border stripe>
            <el-table-column prop="teacher_id" label="教师ID" width="120" />
            <el-table-column prop="semester" label="学期" width="120" />
            <el-table-column prop="weekday" label="星期" width="80" />
            <el-table-column prop="start_slot" label="开始节次" width="100" />
            <el-table-column prop="end_slot" label="结束节次" width="100" />
            <el-table-column prop="reason" label="原因" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="handleDeleteBlackout(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="教师偏好时间" name="preference">
          <div style="margin-bottom: 15px;">
            <el-button type="primary" @click="handleAddPreference">
              <el-icon><Plus /></el-icon>新增偏好时间
            </el-button>
          </div>
          <el-table :data="preferenceData" v-loading="loading" border stripe>
            <el-table-column prop="teacher_id" label="教师ID" width="120" />
            <el-table-column prop="offering_id" label="开课计划ID" width="120" />
            <el-table-column prop="preference_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.preference_type === 'PREFERRED' ? 'success' : 'warning'">
                  {{ row.preference_type === 'PREFERRED' ? '偏好' : '避免' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="weekday" label="星期" width="80" />
            <el-table-column prop="start_slot" label="开始节次" width="100" />
            <el-table-column prop="end_slot" label="结束节次" width="100" />
            <el-table-column prop="penalty_score" label="惩罚分数" width="100" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="handleDeletePreference(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 黑名单对话框 -->
    <el-dialog v-model="blackoutDialogVisible" title="新增黑名单时间" width="500px">
      <el-form :model="blackoutForm" ref="blackoutFormRef" label-width="100px">
        <el-form-item label="教师ID" required>
          <el-input v-model="blackoutForm.teacher_id" />
        </el-form-item>
        <el-form-item label="学期" required>
          <el-input v-model="blackoutForm.semester" placeholder="例如: 2025-2026-1" />
        </el-form-item>
        <el-form-item label="星期" required>
          <el-input-number v-model="blackoutForm.weekday" :min="1" :max="7" />
        </el-form-item>
        <el-form-item label="开始节次" required>
          <el-input-number v-model="blackoutForm.start_slot" :min="1" :max="13" />
        </el-form-item>
        <el-form-item label="结束节次" required>
          <el-input-number v-model="blackoutForm.end_slot" :min="1" :max="13" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="blackoutForm.reason" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="blackoutDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBlackout">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 偏好对话框 -->
    <el-dialog v-model="preferenceDialogVisible" title="新增偏好时间" width="500px">
      <el-form :model="preferenceForm" ref="preferenceFormRef" label-width="100px">
        <el-form-item label="教师ID" required>
          <el-input v-model="preferenceForm.teacher_id" />
        </el-form-item>
        <el-form-item label="开课计划ID" required>
          <el-input-number v-model="preferenceForm.offering_id" :min="1" />
        </el-form-item>
        <el-form-item label="偏好类型" required>
          <el-select v-model="preferenceForm.preference_type">
            <el-option label="偏好" value="PREFERRED" />
            <el-option label="避免" value="AVOIDED" />
          </el-select>
        </el-form-item>
        <el-form-item label="星期">
          <el-input-number v-model="preferenceForm.weekday" :min="1" :max="7" />
        </el-form-item>
        <el-form-item label="开始节次">
          <el-input-number v-model="preferenceForm.start_slot" :min="1" :max="13" />
        </el-form-item>
        <el-form-item label="结束节次">
          <el-input-number v-model="preferenceForm.end_slot" :min="1" :max="13" />
        </el-form-item>
        <el-form-item label="惩罚分数">
          <el-input-number v-model="preferenceForm.penalty_score" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="preferenceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPreference">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { offeringApi } from '@/api/offerings'

const loading = ref(false)
const activeTab = ref('blackout')
const blackoutData = ref([])
const preferenceData = ref([])
const blackoutDialogVisible = ref(false)
const preferenceDialogVisible = ref(false)

const blackoutForm = ref({
  teacher_id: '',
  semester: '2025-2026-1',
  weekday: 1,
  start_slot: 1,
  end_slot: 5,
  reason: ''
})

const preferenceForm = ref({
  teacher_id: '',
  offering_id: 1,
  preference_type: 'PREFERRED',
  weekday: 1,
  start_slot: 1,
  end_slot: 5,
  penalty_score: 100
})

const loadBlackoutData = async () => {
  loading.value = true
  try {
    blackoutData.value = await offeringApi.getBlackoutTimes()
  } finally {
    loading.value = false
  }
}

const loadPreferenceData = async () => {
  loading.value = true
  try {
    preferenceData.value = await offeringApi.getPreferences()
  } finally {
    loading.value = false
  }
}

const handleAddBlackout = () => {
  blackoutForm.value = {
    teacher_id: '',
    semester: '2025-2026-1',
    weekday: 1,
    start_slot: 1,
    end_slot: 5,
    reason: ''
  }
  blackoutDialogVisible.value = true
}

const submitBlackout = async () => {
  try {
    await offeringApi.createBlackoutTime(blackoutForm.value)
    ElMessage.success('创建成功')
    blackoutDialogVisible.value = false
    loadBlackoutData()
  } catch (error) {
    console.error('创建失败:', error)
  }
}

const handleDeleteBlackout = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除吗？', '提示', { type: 'warning' })
    await offeringApi.deleteBlackoutTime(row.blackout_id)
    ElMessage.success('删除成功')
    loadBlackoutData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

const handleAddPreference = () => {
  preferenceForm.value = {
    teacher_id: '',
    offering_id: 1,
    preference_type: 'PREFERRED',
    weekday: 1,
    start_slot: 1,
    end_slot: 5,
    penalty_score: 100
  }
  preferenceDialogVisible.value = true
}

const submitPreference = async () => {
  try {
    await offeringApi.createPreference(preferenceForm.value)
    ElMessage.success('创建成功')
    preferenceDialogVisible.value = false
    loadPreferenceData()
  } catch (error) {
    console.error('创建失败:', error)
  }
}

const handleDeletePreference = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除吗？', '提示', { type: 'warning' })
    await offeringApi.deletePreference(row.preference_id)
    ElMessage.success('删除成功')
    loadPreferenceData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

watch(activeTab, (val) => {
  if (val === 'blackout') {
    loadBlackoutData()
  } else {
    loadPreferenceData()
  }
})

onMounted(() => {
  loadBlackoutData()
})
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

