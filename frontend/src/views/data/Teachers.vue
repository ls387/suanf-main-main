<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>教师列表</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增教师
          </el-button>
        </div>
      </template>
      
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="teacher_id" label="教师编号" width="120" />
        <el-table-column prop="teacher_name" label="教师姓名" width="120" />
        <el-table-column prop="department_id" label="院系编号" width="120" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="is_external" label="是否外聘" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_external ? 'warning' : 'success'">
              {{ row.is_external ? '是' : '否' }}
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
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="教师编号" prop="teacher_id">
          <el-input v-model="form.teacher_id" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="教师姓名" prop="teacher_name">
          <el-input v-model="form.teacher_name" />
        </el-form-item>
        <el-form-item label="院系编号" prop="department_id">
          <el-input v-model="form.department_id" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="form.gender" placeholder="请选择">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否外聘" prop="is_external">
          <el-switch v-model="form.is_external" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { teacherApi } from '@/api/teachers'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增教师')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  teacher_id: '',
  teacher_name: '',
  department_id: '',
  gender: '未知',
  is_external: false
})

const rules = {
  teacher_id: [{ required: true, message: '请输入教师编号', trigger: 'blur' }],
  teacher_name: [{ required: true, message: '请输入教师姓名', trigger: 'blur' }],
  department_id: [{ required: true, message: '请输入院系编号', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    tableData.value = await teacherApi.getAll()
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增教师'
  form.value = {
    teacher_id: '',
    teacher_name: '',
    department_id: '',
    gender: '未知',
    is_external: false
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑教师'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value) {
        await teacherApi.update(form.value.teacher_id, form.value)
        ElMessage.success('更新成功')
      } else {
        await teacherApi.create(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadData()
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该教师吗？', '提示', {
      type: 'warning'
    })
    
    await teacherApi.delete(row.teacher_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-container {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

