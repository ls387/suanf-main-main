import request from './index'

export const versionsApi = {
  // 创建版本
  create(data) {
    return request.post('/versions', data)
  },

  // 版本列表（可按 semester / status 筛选）
  list(params) {
    return request.get('/versions', { params })
  },

  // 版本详情
  get(versionId) {
    return request.get(`/versions/${versionId}`)
  },

  // 确认版本（draft → published）
  confirm(versionId) {
    return request.post(`/versions/${versionId}/confirm`)
  },

  // 删除草稿版本
  delete(versionId) {
    return request.delete(`/versions/${versionId}`)
  },

  // 查询排课状态（供 WebSocket 断线重连用）
  getSchedulingStatus(versionId) {
    return request.get(`/scheduling/status/${versionId}`)
  }
}
