import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const conflictsApi = {
  get: (versionId) => api.get(`/conflicts/${versionId}`).then(r => r.data),
  summary: (versionId) => api.get(`/conflicts/${versionId}/summary`).then(r => r.data),
  fix: (versionId, fixType) =>
    api.post(`/conflicts/${versionId}/fix`, { fix_type: fixType }).then(r => r.data),
  exportUrl: (versionId) => `/api/conflicts/${versionId}/export`,
}
