import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const chatApi = {
  send: (sessionId, message) =>
    api.post('/chat', { session_id: sessionId || '', message }).then(r => r.data),
}
