import request from './index'

export const schedulingApi = {
  // 运行排课
  run(data) {
    return request.post('/scheduling/run', data)
  }
}

