<template>
  <div class="ai-page">
    <div class="page-header">
      <h2>AI 助手</h2>
      <p>通过自然语言完成 ODI 项目管理、合规咨询、报告生成等操作</p>
    </div>

    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :lg="16">
        <div class="chat-panel">
          <div class="chat-messages" ref="messagesEl">
            <a-empty v-if="!messages.length" description="开始对话吧，我可以帮您完成 ODI 相关操作" />
            <div v-for="(msg, i) in messages" :key="i" :class="['message-row', msg.role]">
              <div class="avatar">
                <RobotOutlined v-if="msg.role === 'assistant'" />
                <UserOutlined v-else />
              </div>
              <div class="message-bubble">
                <div v-if="msg.role === 'assistant' && msg.intent" class="intent-badge">
                  <a-tag :color="intentColor(msg.intent)" size="small">{{ msg.intent }}</a-tag>
                </div>
                <div class="message-content" v-html="renderContent(msg)" />
                <div v-if="msg.attachments?.length" class="attachment-preview">
                  <div v-for="att in msg.attachments" :key="att.filename" class="att-item">
                    <PaperClipOutlined /> {{ att.filename }}
                  </div>
                </div>
                <div :class="['msg-actions', msg.role]">
                  <a-tooltip title="复制">
                    <a-button type="text" size="small" class="msg-action-btn" @click="copyMessage(msg.content)">
                      <template v-if="copiedMsgId === i"><CheckOutlined /></template>
                      <template v-else><CopyOutlined /></template>
                    </a-button>
                  </a-tooltip>
                  <a-tooltip v-if="msg.role === 'user'" title="修改后重发">
                    <a-button type="text" size="small" class="msg-action-btn" @click="editMessage(msg.content)">
                      <EditOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip v-if="msg.role === 'assistant'" title="重新生成">
                    <a-button type="text" size="small" class="msg-action-btn" @click="regenerateMessage">
                      <ReloadOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip v-if="msg.role === 'assistant'" title="有帮助">
                    <a-button type="text" size="small" class="msg-action-btn" @click="submitFeedback('like')">
                      <LikeOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip v-if="msg.role === 'assistant'" title="没帮助">
                    <a-button type="text" size="small" class="msg-action-btn" @click="submitFeedback('dislike')">
                      <DislikeOutlined />
                    </a-button>
                  </a-tooltip>
                </div>
                <div v-if="msg.role === 'assistant' && msg === lastAssistantMsg" class="suggestions-bar">
                  <span class="suggestions-label">继续提问：</span>
                  <a-tag v-for="s in msg.suggestions" :key="s" class="suggestion-chip" @click="sendSuggestion(s)">{{ s }}</a-tag>
                </div>
              </div>
            </div>
            <div v-if="loading" class="message-row assistant">
              <div class="avatar"><RobotOutlined /></div>
              <div class="message-bubble"><a-spin size="small" /> 思考中...</div>
            </div>
          </div>

          <div class="chat-input-area">
            <div v-if="pendingAttachments.length" class="attachment-bar">
              <div v-for="(att, i) in pendingAttachments" :key="i" class="pending-att">
                <PaperClipOutlined /> {{ att.name }}
                <a-button type="text" size="small" @click="removeAttachment(i)">
                  <CloseCircleOutlined />
                </a-button>
              </div>
            </div>
            <div class="input-row">
              <a-upload :beforeUpload="handleFileUpload" :showUploadList="false" accept="image/*,.pdf,.doc,.docx">
                <a-button type="text"><PaperClipOutlined /></a-button>
              </a-upload>
              <a-textarea v-model:value="inputText" placeholder="输入您的问题，或描述您想完成的任务（按 Enter 发送，Shift+Enter 换行）..." :autoSize="{ minRows: 1, maxRows: 4 }" @keydown.enter.prevent="handleSend" />
              <a-button type="primary" :loading="loading" @click="handleSend" :disabled="!inputText.trim() && !pendingAttachments.length">
                <SendOutlined />
              </a-button>
            </div>
          </div>
        </div>
      </a-col>

      <a-col :xs="24" :lg="8">
        <div class="page-card">
          <div class="section-title">历史会话</div>
          <a-button type="text" block @click="startNewChat" style="margin-bottom: 8px">
            <PlusOutlined /> 新对话
          </a-button>
          <a-spin v-if="loadingSessions" />
          <div v-else>
            <div v-if="!sessions.length" style="color: var(--text-secondary); font-size: 13px; text-align: center; padding: 12px 0">暂无历史会话</div>
            <div v-for="s in sessions" :key="s.session_id" :class="['history-item', currentSessionId === s.session_id ? 'active' : '']">
              <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap" @click="loadSession(s.session_id)">
                {{ s.title || '新对话' }}
                <div style="font-size: 11px; color: var(--text-muted)">{{ formatTime(s.updated_at) }}</div>
              </div>
              <a-popconfirm title="确定删除?" @confirm="deleteSession(s.session_id)">
                <a-button type="text" size="small" danger><DeleteOutlined /></a-button>
              </a-popconfirm>
            </div>
          </div>
        </div>

        <div class="page-card" style="margin-top: 16px">
          <div class="section-title">上下文项目</div>
          <a-spin v-if="loadingProjects" />
          <a-select v-else v-model:value="selectedProjectId" placeholder="选择项目（可选）" allowClear style="width: 100%" size="small">
            <a-select-option v-for="p in projects" :key="p.project_id" :value="p.project_id">
              <div class="project-option">
                <span>{{ p.project_name || '未命名项目' }}</span>
                <a-tag :color="statusColor(p.status)" size="small">{{ statusLabel(p.status) }}</a-tag>
              </div>
            </a-select-option>
          </a-select>
        </div>

        <div class="page-card" style="margin-top: 16px">
          <div class="section-title">可用意图</div>
          <div class="intent-list">
            <a-tag v-for="intent in availableIntents" :key="intent.key" :color="intent.color" size="small">{{ intent.label }}</a-tag>
          </div>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { aiApi, uploadApi, projectsApi, conversationsApi } from '../api'
import {
  RobotOutlined, UserOutlined, SendOutlined, PaperClipOutlined,
  ClearOutlined, CloseCircleOutlined, CopyOutlined, CheckOutlined,
  ReloadOutlined, LikeOutlined, DislikeOutlined, PlusOutlined, DeleteOutlined,
  EditOutlined
} from '@ant-design/icons-vue'

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const pendingAttachments = ref([])
const messagesEl = ref(null)
const projects = ref([])
const loadingProjects = ref(false)
const selectedProjectId = ref(null)
const sessions = ref([])
const loadingSessions = ref(false)
const currentSessionId = ref(null)
const copiedMsgId = ref(null)

const STATUS_MAP = {
  PRE_REVIEW: { label: '智能预审', color: 'orange' },
  DATA_COLLECTION: { label: '材料准备', color: 'blue' },
  NDRC_FILING_PENDING: { label: '发改委待备案', color: 'purple' },
  NDRC_APPROVED: { label: '发改委通过', color: 'green' },
  MOFCOM_FILING_PENDING: { label: '商务部待备案', color: 'purple' },
  MOFCOM_APPROVED: { label: '商务部通过', color: 'green' },
  BANK_REG_PENDING: { label: '银行登记', color: 'cyan' },
  FUNDS_REMITTED: { label: '资金汇出', color: 'green' },
  POST_INVESTMENT: { label: '投后管理', color: 'default' },
}

const availableIntents = [
  { key: 'create_project', label: '创建项目', color: 'green' },
  { key: 'query_project', label: '查询项目', color: 'blue' },
  { key: 'pre_review', label: '智能预审', color: 'orange' },
  { key: 'generate_report', label: '生成报告', color: 'purple' },
  { key: 'export_ndrc', label: '导出发改委', color: 'cyan' },
  { key: 'export_mofcom', label: '导出商务部', color: 'cyan' },
  { key: 'query_entity', label: '查询主体', color: 'geekblue' },
  { key: 'query_rules', label: '合规规则', color: 'magenta' },
  { key: 'knowledge_qa', label: '知识库问答', color: 'default' },
]

const lastAssistantMsg = computed(() => [...messages.value].reverse().find(m => m.role === 'assistant'))

onMounted(async () => {
  loadingSessions.value = true
  try {
    const { data } = await conversationsApi.list()
    sessions.value = data || []
  } catch {}
  finally { loadingSessions.value = false }

  loadingProjects.value = true
  try {
    const { data } = await projectsApi.list({ page: 1, page_size: 100 })
    projects.value = data.items || []
  } catch {}
  finally { loadingProjects.value = false }
})

async function handleSend() {
  const text = inputText.value.trim()
  if (!text && !pendingAttachments.length) return

  const attachments = await Promise.all(
    pendingAttachments.value.map(async (file) => {
      try {
        const { data } = await uploadApi.uploadFile(file.originFileObj)
        return { filename: file.name, url: data.url || data.path || '', content_type: file.type }
      } catch { return null }
    })
  )
  const validAttachments = attachments.filter(Boolean)

  const userMsg = {
    role: 'user',
    content: text,
    attachments: validAttachments.length ? validAttachments : undefined,
    suggestions: [],
  }
  messages.value.push(userMsg)
  inputText.value = ''
  pendingAttachments.value = []
  loading.value = true
  scrollBottom()

  const assistantMsg = {
    role: 'assistant',
    content: '',
    intent: 'knowledge_qa',
    confidence: 0,
    suggestions: [],
  }
  messages.value.push(assistantMsg)

  try {
    const history = messages.value
      .filter(m => !m.loading && m.role === 'user')
      .map(({ role, content }) => ({ role, content }))

    await aiApi.chatStream({
      messages: history,
      context_project_id: selectedProjectId.value,
      attachments: validAttachments.length ? validAttachments : null,
      session_id: currentSessionId.value,
    }, {
      onChunk: (chunk) => {
        assistantMsg.content += chunk
        scrollBottom()
      },
      onDone: () => {
        if (assistantMsg.content && currentSessionId.value) {
          try {
            conversationsApi.list().then(({ data }) => {
              sessions.value = data || []
            })
          } catch {}
        }
        loading.value = false
        scrollBottom()
      },
      onError: (err) => {
        console.error('AI chat error:', err)
        assistantMsg.content = '抱歉，AI 服务暂时不可用，请稍后重试。 (' + err + ')'
        assistantMsg.intent = 'error'
        loading.value = false
        scrollBottom()
      }
    })
  } catch (e) {
    console.error('AI chat error:', e?.response?.data || e?.message || e)
    message.error('AI 服务请求失败')
    assistantMsg.content = '抱歉，AI 服务暂时不可用，请稍后重试。' + (e?.response?.data?.detail ? ' (' + e.response.data.detail + ')' : '')
    assistantMsg.intent = 'error'
    loading.value = false
    scrollBottom()
  }
}

async function loadSession(sessionId) {
  try {
    const { data } = await conversationsApi.get(sessionId)
    currentSessionId.value = sessionId
    messages.value = (data.messages || []).map(m => ({
      role: m.role,
      content: m.content,
      intent: m.intent,
      suggestions: [],
    }))
    scrollBottom()
  } catch {
    message.error('加载会话失败')
  }
}

function startNewChat() {
  messages.value = []
  currentSessionId.value = null
  suggestions.value = []
}

async function deleteSession(sessionId) {
  try {
    await conversationsApi.delete(sessionId)
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    if (currentSessionId.value === sessionId) {
      startNewChat()
    }
    message.success('会话已删除')
  } catch {
    message.error('删除失败')
  }
}

async function regenerateMessage() {
  const msgs = messages.value.filter(m => m.role !== 'loading')
  const lastUserIdx = msgs.map(m => m.role).lastIndexOf('user')
  const trimmed = msgs.slice(0, lastUserIdx + 1)
  messages.value = trimmed
  await handleSend()
}

function copyMessage(content) {
  navigator.clipboard.writeText(content)
  message.success('已复制')
}

function editMessage(content) {
  inputText.value = content
}

async function submitFeedback(rating) {
  if (!currentSessionId.value) {
    message.warning('请先开始一次对话再提交反馈')
    return
  }
  try {
    await conversationsApi.submitFeedback(currentSessionId.value, { rating })
    message.success('感谢您的反馈！')
  } catch {
    message.error('反馈提交失败')
  }
}

function sendSuggestion(text) {
  inputText.value = text
  handleSend()
}

function handleFileUpload(file) {
  pendingAttachments.value.push(file)
  return false
}

function removeAttachment(index) {
  pendingAttachments.value.splice(index, 1)
}

function scrollBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>')
}

function renderContent(msg) {
  if (msg.role === 'user') {
    return escapeHtml(msg.content)
  }
  const raw = msg.content || ''
  try {
    const result = marked.parse(raw)
    if (result instanceof Promise) {
      return escapeHtml(raw)
    }
    return result
  } catch {
    return escapeHtml(raw)
  }
}

function intentColor(intent) {
  const map = {
    create_project: 'green', query_project: 'blue', pre_review: 'orange',
    generate_report: 'purple', export_ndrc: 'cyan', export_mofcom: 'cyan',
    query_entity: 'geekblue', query_rules: 'magenta', knowledge_qa: 'default',
    general_chat: 'default', clarify: 'warning', error: 'red'
  }
  return map[intent] || 'default'
}

function statusLabel(status) { return STATUS_MAP[status]?.label || status }
function statusColor(status) { return STATUS_MAP[status]?.color || 'default' }

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.ai-page { padding: 0; }
.chat-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 220px);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  background: var(--card-bg);
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.message-row { display: flex; gap: 10px; align-items: flex-start; }
.message-row.user { flex-direction: row-reverse; }
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
}
.message-row.assistant .avatar { background: #e6f4ff; color: #1677ff; }
.message-row.user .avatar { background: #fff7e6; color: #fa8c16; }
.message-bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  position: relative;
}
.message-row.assistant .message-bubble { background: var(--page-bg); border: 1px solid var(--border-color); }
.message-row.user .message-bubble { background: #1677ff; color: #fff; }
.message-content { word-break: break-word; }
.message-row.user .message-content { white-space: pre-wrap; }
.intent-badge { margin-bottom: 4px; }
.attachment-preview { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.att-item { font-size: 12px; padding: 2px 8px; background: rgba(0,0,0,0.06); border-radius: 4px; display: flex; align-items: center; gap: 4px; }
.message-row.user .att-item { background: rgba(255,255,255,0.2); color: #fff; }
.chat-input-area { border-top: 1px solid var(--border-color); padding: 12px 16px; }
.attachment-bar { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.pending-att { display: flex; align-items: center; gap: 4px; padding: 2px 8px; background: var(--page-bg); border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; }
.input-row { display: flex; align-items: flex-end; gap: 8px; }
.section-title { font-size: 11px; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 8px; letter-spacing: 0.5px; }
.project-option { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.intent-list { display: flex; flex-wrap: wrap; gap: 4px; }
.msg-actions { display: none; gap: 4px; margin-top: 6px; }
.message-bubble:hover .msg-actions { display: flex; }
.msg-action-btn { font-size: 12px; padding: 0 4px; color: var(--text-secondary); }
.msg-action-btn:hover { color: var(--primary-color); }
.message-row.user .msg-action-btn { color: rgba(255,255,255,0.7); }
.message-row.user .msg-action-btn:hover { color: #fff; }
.suggestions-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border-color); }
.suggestions-label { font-size: 12px; color: var(--text-secondary); }
.suggestion-chip { cursor: pointer; font-size: 12px; }
.suggestion-chip:hover { opacity: 0.8; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 4px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.history-item:hover { background: var(--page-bg); }
.history-item.active { background: var(--bg-secondary); color: var(--primary-color); }
</style>
