import request from './index'

export const classroomApi = {
  getAll() {
    return request.get('/classrooms/')
  },
  
  getOne(classroomId) {
    return request.get(`/classrooms/${classroomId}`)
  },
  
  create(data) {
    return request.post('/classrooms/', data)
  },
  
  update(classroomId, data) {
    return request.put(`/classrooms/${classroomId}`, data)
  },
  
  delete(classroomId) {
    return request.delete(`/classrooms/${classroomId}`)
  }
}

