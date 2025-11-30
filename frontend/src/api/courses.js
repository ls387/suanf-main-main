import request from './index'

export const courseApi = {
  getAll() {
    return request.get('/courses/')
  },
  
  getOne(courseId) {
    return request.get(`/courses/${courseId}`)
  },
  
  create(data) {
    return request.post('/courses/', data)
  },
  
  update(courseId, data) {
    return request.put(`/courses/${courseId}`, data)
  },
  
  delete(courseId) {
    return request.delete(`/courses/${courseId}`)
  }
}

