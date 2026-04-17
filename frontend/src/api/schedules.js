import request from './index'

export const scheduleApi = {
  /** 基于已发布版本 fork 出新草稿 */
  fork(versionId, data) {
    return request.post(`/versions/${versionId}/fork`, data)
  },

  /** 获取版本完整排课列表（含 schedule_id，供拖拽 UI 用） */
  getSchedules(versionId) {
    return request.get(`/versions/${versionId}/schedules`)
  },

  /** 移动单条排课到新时间槽 */
  move(scheduleId, data) {
    return request.put(`/schedules/${scheduleId}/move`, data)
  },
}
