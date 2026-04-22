import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const chatApi = {
  send: (sessionId, message) =>
    api.post('/chat', { session_id: sessionId || '', message }).then(r => r.data),

  /**
   * 流式发送，逐事件回调。
   * @param {string} sessionId
   * @param {string} message
   * @param {object} callbacks
   * @param {function} callbacks.onSession       (sessionId: string) => void
   * @param {function} callbacks.onToken         (token: string) => void
   * @param {function} callbacks.onReplace       (text: string) => void  整段替换
   * @param {function} callbacks.onReplaceStart  () => void              清空，准备第二阶段
   * @param {function} callbacks.onDownloadExcel (key: string) => void   Excel 已生成
   * @param {function} callbacks.onDone          () => void
   * @param {function} callbacks.onError         (msg: string) => void
   * @returns {AbortController}
   */
  sendStream(sessionId, message, { onSession, onToken, onReplace, onReplaceStart, onDownloadExcel, onDone, onError }) {
    const controller = new AbortController()

    fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId || '', message }),
      signal: controller.signal,
    }).then(async (res) => {
      if (!res.ok) {
        onError?.('服务异常，请稍后重试')
        return
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })

        // SSE 以 \n\n 分隔每条事件
        const parts = buf.split('\n\n')
        buf = parts.pop() // 最后一段可能不完整，留到下次

        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).trim()
          if (!raw) continue
          try {
            const evt = JSON.parse(raw)
            if (evt.type === 'session')            onSession?.(evt.session_id)
            else if (evt.type === 'token')         onToken?.(evt.content)
            else if (evt.type === 'replace')       onReplace?.(evt.content)
            else if (evt.type === 'replace_start') onReplaceStart?.()
            else if (evt.type === 'download_excel') onDownloadExcel?.(evt.excel_key)
            else if (evt.type === 'done')          onDone?.()
            else if (evt.type === 'error')         onError?.(evt.content)
          } catch {
            // 忽略解析失败的行
          }
        }
      }
    }).catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.('网络错误，请稍后重试')
      }
    })

    return controller
  },

  /**
   * 凭 excel_key 下载黑名单 Excel 文件。
   * @param {string} key
   */
  downloadBlackoutExcel(key) {
    const url = `/api/chat/blackout-excel?key=${encodeURIComponent(key)}`
    const a = document.createElement('a')
    a.href = url
    a.download = 'blackout_times.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  },
}

