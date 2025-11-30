import request from './index'

export const teacherApi = {
  // 获取所有教师
  getAll() {
    return request.get('/teachers/')
  },
  
  // 获取单个教师
  getOne(teacherId) {
    return request.get(`/teachers/${teacherId}`)
  },
  
  // 创建教师
  create(data) {
    return request.post('/teachers/', data)
  },
  
  // 更新教师
  update(teacherId, data) {
    return request.put(`/teachers/${teacherId}`, data)
  },
  
  // 删除教师
  delete(teacherId) {
    return request.delete(`/teachers/${teacherId}`)
  }
}

