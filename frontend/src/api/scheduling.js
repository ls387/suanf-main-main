import request from './index'

export const schedulingApi = {
  // 提交排课任务（立即返回，后台运行）
  run(data) {
    return request.post('/scheduling/run', data)
  },

  // 查询排课状态（WebSocket 断线重连前的降级查询）
  getStatus(versionId) {
    return request.get(`/scheduling/status/${versionId}`)
  }
}

/**
 * 创建 WebSocket 进度订阅连接
 *
 * @param {number} versionId  排课版本ID
 * @returns {WebSocket}        原生 WebSocket 实例
 */
export function createSchedulingWs(versionId) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location.host  // vite dev proxy 会转发 ws 连接
  return new WebSocket(`${protocol}//${host}/api/scheduling/ws/${versionId}`)
}
