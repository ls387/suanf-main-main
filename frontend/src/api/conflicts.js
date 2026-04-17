import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const conflictsApi = {
  get: (versionId) => api.get(`/conflicts/${versionId}`).then(r => r.data),
  summary: (versionId) => api.get(`/conflicts/${versionId}/summary`).then(r => r.data),
}
