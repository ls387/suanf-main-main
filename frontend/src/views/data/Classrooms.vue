<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>教室列表</span>
          <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>新增教室</el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="classroom_id" label="教室编号" width="120" />
        <el-table-column prop="classroom_name" label="教室名称" width="120" />
        <el-table-column prop="building_name" label="教学楼" width="120" />
        <el-table-column prop="campus_id" label="校区" width="100" />
        <el-table-column prop="classroom_type" label="类型" width="120" />
        <el-table-column prop="capacity" label="容量" width="80" />
        <el-table-column prop="is_available" label="可用" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_available ? 'success' : 'danger'">
              {{ row.is_available ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="教室编号" prop="classroom_id">
          <el-input v-model="form.classroom_id" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="教室名称">
          <el-input v-model="form.classroom_name" />
        </el-form-item>
        <el-form-item label="教学楼">
          <el-input v-model="form.building_name" />
        </el-form-item>
        <el-form-item label="校区" prop="campus_id">
          <el-input v-model="form.campus_id" />
        </el-form-item>
        <el-form-item label="类型">
          <el-input v-model="form.classroom_type" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="form.capacity" :min="0" />
        </el-form-item>
        <el-form-item label="是否可用">
          <el-switch v-model="form.is_available" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { classroomApi } from '@/api/classrooms'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增教室')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  classroom_id: '',
  classroom_name: '',
  building_name: '',
  campus_id: '',
  classroom_type: '',
  capacity: 0,
  is_available: true,
  features: []
})

const rules = {
  classroom_id: [{ required: true, message: '请输入教室编号', trigger: 'blur' }],
  campus_id: [{ required: true, message: '请输入校区', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    tableData.value = await classroomApi.getAll()
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增教室'
  form.value = { classroom_id: '', classroom_name: '', building_name: '', campus_id: '', classroom_type: '', capacity: 0, is_available: true, features: [] }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑教室'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await classroomApi.update(form.value.classroom_id, form.value)
        ElMessage.success('更新成功')
      } else {
        await classroomApi.create(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadData()
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该教室吗？', '提示', { type: 'warning' })
    await classroomApi.delete(row.classroom_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

