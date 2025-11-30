import request from './index'

export const offeringApi = {
  getAll(semester) {
    return request.get('/offerings/', { params: { semester } })
  },
  
  getOne(offeringId) {
    return request.get(`/offerings/${offeringId}`)
  },
  
  create(data) {
    return request.post('/offerings/', data)
  },
  
  update(offeringId, data) {
    return request.put(`/offerings/${offeringId}`, data)
  },
  
  delete(offeringId) {
    return request.delete(`/offerings/${offeringId}`)
  },
  
  // 教师黑名单时间
  getBlackoutTimes(params) {
    return request.get('/offerings/blackout-times/', { params })
  },
  
  createBlackoutTime(data) {
    return request.post('/offerings/blackout-times/', data)
  },
  
  deleteBlackoutTime(blackoutId) {
    return request.delete(`/offerings/blackout-times/${blackoutId}`)
  },
  
  // 教师偏好
  getPreferences(params) {
    return request.get('/offerings/preferences/', { params })
  },
  
  createPreference(data) {
    return request.post('/offerings/preferences/', data)
  },
  
  deletePreference(preferenceId) {
    return request.delete(`/offerings/preferences/${preferenceId}`)
  }
}

