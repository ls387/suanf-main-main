import request from './index'

export const classApi = {
  getAll() {
    return request.get('/classes/')
  },
  
  getOne(classId) {
    return request.get(`/classes/${classId}`)
  },
  
  create(data) {
    return request.post('/classes/', data)
  },
  
  update(classId, data) {
    return request.put(`/classes/${classId}`, data)
  },
  
  delete(classId) {
    return request.delete(`/classes/${classId}`)
  }
}

