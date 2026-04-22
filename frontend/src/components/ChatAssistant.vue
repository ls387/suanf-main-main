<template>
  <!-- 悬浮按钮 -->
  <div class="chat-fab" @click="toggle" :title="open ? '收起助手' : '打开AI教务助手'">
    <el-icon v-if="!open" class="fab-icon"><ChatDotRound /></el-icon>
    <el-icon v-else class="fab-icon"><Close /></el-icon>
  </div>

  <!-- 聊天面板 -->
  <transition name="chat-slide">
    <div v-if="open" class="chat-panel">
      <!-- 顶部标题栏 -->
      <div class="chat-header">
        <span class="chat-title">
          <el-icon><Cpu /></el-icon>
          教务智能助手
        </span>
        <el-button link size="small" @click="clearSession" title="清空对话">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesRef">
        <!-- 欢迎语 -->
        <div v-if="messages.length === 0" class="welcome-msg">
          <el-icon style="font-size:28px;color:#409eff"><Cpu /></el-icon>
          <p>你好！我是教务智能助手，可以帮你查询课程安排、教室占用、教师信息等。</p>
          <div class="quick-hints">
            <el-tag
              v-for="hint in hints"
              :key="hint"
              class="hint-tag"
              @click="sendHint(hint)"
            >{{ hint }}</el-tag>
          </div>
        </div>

        <!-- 消息气泡 -->
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="msg-row"
          :class="msg.role"
        >
          <div class="bubble">
            <span class="bubble-text" v-html="formatText(msg.content)"></span>
            <div v-if="msg.excelKey" class="excel-download">
              <el-button
                type="success"
                size="small"
                @click="downloadExcel(msg.excelKey)"
              >
                <el-icon><Download /></el-icon>
                下载 Excel 导入表
              </el-button>
            </div>
          </div>
        </div>

        <!-- 思考中 -->
        <div v-if="loading" class="msg-row assistant">
          <div class="bubble thinking">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="chat-input-area">
        <el-input
          v-model="input"
          placeholder="输入问题，按 Enter 发送..."
          :disabled="loading"
          @keydown.enter.prevent="send"
          size="default"
          :rows="2"
          type="textarea"
          resize="none"
        />
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!input.trim()"
          @click="send"
          class="send-btn"
        >
          发送
        </el-button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Close, Cpu, Delete, Download } from '@element-plus/icons-vue'
import { chatApi } from '@/api/chat'

const SESSION_KEY = 'chat_session_id'

const open = ref(false)
const input = ref('')
const loading = ref(false)
const messages = ref([])
const messagesRef = ref(null)

const hints = [
  '周一上午有哪些课？',
  '张老师这学期教哪些课？',
  '哪些教室现在空着？',
  '查看已发布版本的排课结果',
]

const toggle = () => { open.value = !open.value }

const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const formatText = (text) => {
  return text.replace(/\n/g, '<br>')
}

const send = async () => {
  const msg = input.value.trim()
  if (!msg || loading.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  await scrollToBottom()

  loading.value = true

  // 占位气泡，流式 token 会不断追加到这里
  const assistantMsg = { role: 'assistant', content: '' }
  let bubblePushed = false

  const sessionId = localStorage.getItem(SESSION_KEY) || ''

  chatApi.sendStream(sessionId, msg, {
    onSession(id) {
      localStorage.setItem(SESSION_KEY, id)
    },
    onToken(token) {
      if (!bubblePushed) {
        messages.value.push(assistantMsg)
        bubblePushed = true
        loading.value = false
      }
      assistantMsg.content += token
      scrollToBottom()
    },
    onReplaceStart() {
      assistantMsg.content = ''
    },
    onReplace(text) {
      if (!bubblePushed) {
        messages.value.push(assistantMsg)
        bubblePushed = true
        loading.value = false
      }
      assistantMsg.content = text
      scrollToBottom()
    },
    onDownloadExcel(key) {
      if (!bubblePushed) {
        messages.value.push(assistantMsg)
        bubblePushed = true
        loading.value = false
      }
      assistantMsg.excelKey = key
      scrollToBottom()
    },
    onDone() {
      loading.value = false
    },
    onError(errMsg) {
      loading.value = false
      if (!bubblePushed) {
        messages.value.push({ role: 'assistant', content: errMsg })
      } else {
        assistantMsg.content = errMsg
      }
      ElMessage.error('助手暂时无法回应，请稍后重试')
      scrollToBottom()
    },
  })
}

const sendHint = (hint) => {
  input.value = hint
  send()
}

const clearSession = () => {
  localStorage.removeItem(SESSION_KEY)
  messages.value = []
  ElMessage.success('对话已清空，开始新会话')
}

const downloadExcel = (key) => {
  chatApi.downloadBlackoutExcel(key)
}
</script>

<style scoped>
/* 悬浮按钮 */
.chat-fab {
  position: fixed;
  right: 28px;
  bottom: 28px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(64,158,255,0.45);
  z-index: 1000;
  transition: background 0.2s, transform 0.15s;
}
.chat-fab:hover { background: #337ecc; transform: scale(1.08); }
.fab-icon { font-size: 24px; }

/* 聊天面板 */
.chat-panel {
  position: fixed;
  right: 28px;
  bottom: 92px;
  width: 380px;
  height: 560px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18);
  display: flex;
  flex-direction: column;
  z-index: 999;
  overflow: hidden;
}

/* 过渡动画 */
.chat-slide-enter-active, .chat-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.chat-slide-enter-from, .chat-slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.97);
}

/* 标题栏 */
.chat-header {
  background: #409eff;
  color: #fff;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.chat-title {
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
:deep(.chat-header .el-button) { color: rgba(255,255,255,0.85); }
:deep(.chat-header .el-button:hover) { color: #fff; }

/* 消息区 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 欢迎 */
.welcome-msg {
  text-align: center;
  color: #606266;
  font-size: 14px;
  padding: 20px 8px 8px;
}
.welcome-msg p { margin: 10px 0 14px; line-height: 1.6; }
.quick-hints { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
.hint-tag { cursor: pointer; }
.hint-tag:hover { background: #ecf5ff; }

/* 气泡 */
.msg-row { display: flex; }
.msg-row.user { justify-content: flex-end; }
.msg-row.assistant { justify-content: flex-start; }

.bubble {
  max-width: 80%;
  padding: 9px 13px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.msg-row.user .bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg-row.assistant .bubble {
  background: #f4f4f5;
  color: #303133;
  border-bottom-left-radius: 4px;
}

/* 思考动画 */
.thinking {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 12px 16px;
}
.dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #909399;
  display: inline-block;
  animation: blink 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* 输入区 */
.chat-input-area {
  padding: 10px 12px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 8px;
  align-items: flex-end;
  flex-shrink: 0;
}
:deep(.chat-input-area .el-textarea__inner) {
  font-size: 14px;
  border-radius: 10px;
  resize: none;
}
.send-btn { flex-shrink: 0; align-self: flex-end; }

/* Excel 下载按钮 */
.excel-download {
  margin-top: 8px;
}
</style>
