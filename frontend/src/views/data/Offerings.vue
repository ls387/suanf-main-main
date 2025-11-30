<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>开课计划列表</span>
          <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>新增开课计划</el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="offering_id" label="ID" width="80" />
        <el-table-column prop="semester" label="学期" width="120" />
        <el-table-column prop="course_id" label="课程编号" width="120" />
        <el-table-column prop="course_nature" label="课程性质" width="100" />
        <el-table-column prop="student_count_estimate" label="预估人数" width="100" />
        <el-table-column prop="start_week" label="起始周" width="80" />
        <el-table-column prop="end_week" label="结束周" width="80" />
        <el-table-column prop="week_pattern" label="周次模式" width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="学期" prop="semester">
          <el-input v-model="form.semester" placeholder="例如: 2025-2026-1" />
        </el-form-item>
        <el-form-item label="课程" prop="course_id">
          <el-select
            v-model="form.course_id"
            placeholder="请选择课程"
            filterable
            style="width: 100%;"
          >
            <el-option
              v-for="c in courseOptions"
              :key="c.course_id"
              :label="`${c.course_id} - ${c.course_name}`"
              :value="c.course_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="课程性质" prop="course_nature">
          <el-select v-model="form.course_nature">
            <el-option label="必修" value="必修" />
            <el-option label="选修" value="选修" />
            <el-option label="通识" value="通识" />
          </el-select>
        </el-form-item>
        <el-form-item label="预估人数">
          <el-input-number v-model="form.student_count_estimate" :min="0" />
        </el-form-item>
        <el-form-item label="授课教师">
          <el-select
            v-model="form.teacher_ids"
            multiple
            filterable
            placeholder="请选择教师"
            style="width: 100%;"
          >
            <el-option
              v-for="t in teacherOptions"
              :key="t.teacher_id"
              :label="`${t.teacher_id} - ${t.teacher_name}`"
              :value="t.teacher_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="上课班级">
          <el-select
            v-model="form.class_ids"
            multiple
            filterable
            placeholder="请选择班级"
            style="width: 100%;"
          >
            <el-option
              v-for="cls in classOptions"
              :key="cls.class_id"
              :label="`${cls.class_id} - ${cls.class_name}`"
              :value="cls.class_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="起始周" prop="start_week">
          <el-input-number v-model="form.start_week" :min="1" :max="53" />
        </el-form-item>
        <el-form-item label="结束周" prop="end_week">
          <el-input-number v-model="form.end_week" :min="1" :max="53" />
        </el-form-item>
        <el-form-item label="周次模式" prop="week_pattern">
          <el-select v-model="form.week_pattern">
            <el-option label="连续周" value="CONTINUOUS" />
            <el-option label="单周" value="SINGLE" />
            <el-option label="双周" value="DOUBLE" />
          </el-select>
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
import { offeringApi } from '@/api/offerings'
import { courseApi } from '@/api/courses'
import { teacherApi } from '@/api/teachers'
import { classApi } from '@/api/classes'

const loading = ref(false)
const tableData = ref([])
const courseOptions = ref([])
const teacherOptions = ref([])
const classOptions = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增开课计划')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  semester: '2025-2026-1',
  course_id: '',
  course_nature: '必修',
  student_count_estimate: 0,
  start_week: 1,
  end_week: 16,
  week_pattern: 'CONTINUOUS',
  class_ids: [],
  teacher_ids: [],
  feature_ids: []
})

const rules = {
  semester: [{ required: true, message: '请输入学期', trigger: 'blur' }],
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  start_week: [{ required: true, message: '请输入起始周', trigger: 'blur' }],
  end_week: [{ required: true, message: '请输入结束周', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    tableData.value = await offeringApi.getAll()
  } finally {
    loading.value = false
  }
}

const loadOptions = async () => {
  try {
    const [courses, teachers, classes] = await Promise.all([
      courseApi.getAll(),
      teacherApi.getAll(),
      classApi.getAll()
    ])
    courseOptions.value = courses
    teacherOptions.value = teachers
    classOptions.value = classes
  } catch (e) {
    console.error('加载选项失败:', e)
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增开课计划'
  form.value = {
    semester: '2025-2026-1',
    course_id: '',
    course_nature: '必修',
    student_count_estimate: 0,
    start_week: 1,
    end_week: 16,
    week_pattern: 'CONTINUOUS',
    class_ids: [],
    teacher_ids: [],
    feature_ids: []
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑开课计划'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await offeringApi.update(form.value.offering_id, form.value)
        ElMessage.success('更新成功')
      } else {
        await offeringApi.create(form.value)
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
    await ElMessageBox.confirm('确定要删除该开课计划吗？', '提示', { type: 'warning' })
    await offeringApi.delete(row.offering_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

onMounted(() => {
  loadData()
  loadOptions()
})
</script>

<style scoped>
.page-container { width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

