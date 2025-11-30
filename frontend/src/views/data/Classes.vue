<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>班级列表</span>
          <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>新增班级</el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="class_id" label="班级编号" width="120" />
        <el-table-column prop="class_name" label="班级名称" width="150" />
        <el-table-column prop="grade" label="年级" width="100" />
        <el-table-column prop="student_count" label="学生人数" width="100" />
        <el-table-column prop="major_id" label="专业编号" width="120" />
        <el-table-column prop="education_system" label="学制" width="80" />
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
        <el-form-item label="班级编号" prop="class_id">
          <el-input v-model="form.class_id" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="班级名称" prop="class_name">
          <el-input v-model="form.class_name" />
        </el-form-item>
        <el-form-item label="年级" prop="grade">
          <el-input-number v-model="form.grade" :min="2020" :max="2030" />
        </el-form-item>
        <el-form-item label="学生人数">
          <el-input-number v-model="form.student_count" :min="0" />
        </el-form-item>
        <el-form-item label="专业编号" prop="major_id">
          <el-input v-model="form.major_id" />
        </el-form-item>
        <el-form-item label="学制">
          <el-input-number v-model="form.education_system" :min="2" :max="6" />
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
import { classApi } from '@/api/classes'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增班级')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  class_id: '',
  class_name: '',
  grade: 2024,
  student_count: 0,
  major_id: '',
  education_system: 4
})

const rules = {
  class_id: [{ required: true, message: '请输入班级编号', trigger: 'blur' }],
  class_name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
  grade: [{ required: true, message: '请输入年级', trigger: 'blur' }],
  major_id: [{ required: true, message: '请输入专业编号', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    tableData.value = await classApi.getAll()
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增班级'
  form.value = { class_id: '', class_name: '', grade: 2024, student_count: 0, major_id: '', education_system: 4 }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑班级'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await classApi.update(form.value.class_id, form.value)
        ElMessage.success('更新成功')
      } else {
        await classApi.create(form.value)
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
    await ElMessageBox.confirm('确定要删除该班级吗？', '提示', { type: 'warning' })
    await classApi.delete(row.class_id)
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

