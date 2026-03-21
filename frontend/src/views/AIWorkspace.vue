<template>
  <div class="ai-workspace">
    <div class="chat-header">
      <div class="chat-title">
        <RobotOutlined />
        <span>AI 智能助手</span>
      </div>
      <div class="chat-actions">
        <a-tag v-if="contextProjectId" color="blue">
          项目: {{ contextProjectId.slice(0, 8) }}...
        </a-tag>
        <a-button type="text" size="small" @click="clearChat">
          <ClearOutlined /> 新对话
        </a-button>
      </div>
    </div>

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
          <div class="message-content" v-html="msg.role === 'user' ? escapeHtml(msg.content) : marked.parse(msg.content)" />
          <div v-if="msg.attachments?.length" class="attachment-preview">
            <div v-for="att in msg.attachments" :key="att.filename" class="att-item">
              <PaperClipOutlined /> {{ att.filename }}
            </div>
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
        <a-upload
          :beforeUpload="handleFileUpload"
          :showUploadList="false"
          accept="image/*,.pdf,.doc,.docx"
        >
          <a-button type="text"><PaperClipOutlined /></a-button>
        </a-upload>
        <a-input-textarea
          v-model:value="inputText"
          placeholder="输入您的问题，或描述您想完成的任务..."
          :autoSize="{ minRows: 1, maxRows: 4 }"
          @pressEnter="handleSend"
          @keydown.enter.prevent
        />
        <a-button type="primary" :loading="loading" @click="handleSend" :disabled="!inputText.trim() && !pendingAttachments.length">
          <SendOutlined />
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { aiApi, uploadApi } from '../api'
import {
  RobotOutlined, UserOutlined, SendOutlined, PaperClipOutlined,
  ClearOutlined, CloseCircleOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  contextProjectId: { type: String, default: null }
})

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const pendingAttachments = ref([])
const messagesEl = ref(null)

async function handleSend() {
  const text = inputText.value.trim()
  if (!text && !pendingAttachments.length) return

  const attachments = await Promise.all(
    pendingAttachments.value.map(async (file) => {
      try {
        const { data } = await uploadApi.uploadFile(file.originFileObj)
        return { filename: file.name, url: data.url || data.path || '', content_type: file.type }
      } catch {
        return null
      }
    })
  )
  const validAttachments = attachments.filter(Boolean)

  const userMsg = {
    role: 'user',
    content: text,
    attachments: validAttachments.length ? validAttachments : undefined
  }
  messages.value.push(userMsg)
  inputText.value = ''
  pendingAttachments.value = []
  loading.value = true
  scrollBottom()

  try {
    const history = messages.value
      .filter(m => !m.loading)
      .map(({ role, content }) => ({ role, content }))

    const { data } = await aiApi.chat({
      messages: history,
      context_project_id: props.contextProjectId,
      attachments: validAttachments.length ? validAttachments : null
    })

    messages.value.push({
      role: 'assistant',
      content: data.content,
      intent: data.intent,
      confidence: data.confidence
    })
  } catch (e) {
    message.error('AI 服务请求失败')
    messages.value.push({
      role: 'assistant',
      content: '抱歉，AI 服务暂时不可用，请稍后重试。',
      intent: 'error'
    })
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function handleFileUpload(file) {
  pendingAttachments.value.push(file)
  return false
}

function removeAttachment(index) {
  pendingAttachments.value.splice(index, 1)
}

function clearChat() {
  messages.value = []
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

function intentColor(intent) {
  const map = {
    create_project: 'green',
    query_project: 'blue',
    pre_review: 'orange',
    generate_report: 'purple',
    export_ndrc: 'cyan',
    export_mofcom: 'cyan',
    query_entity: 'geekblue',
    query_rules: 'magenta',
    knowledge_qa: 'default',
    general_chat: 'default',
    clarify: 'warning',
    error: 'red'
  }
  return map[intent] || 'default'
}
</script>

<style scoped>
.ai-workspace {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  background: var(--card-bg);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--page-bg);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.message-row.user {
  flex-direction: row-reverse;
}

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

.message-row.assistant .avatar {
  background: #e6f4ff;
  color: #1677ff;
}

.message-row.user .avatar {
  background: #fff7e6;
  color: #fa8c16;
}

.message-bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.message-row.assistant .message-bubble {
  background: var(--page-bg);
  border: 1px solid var(--border-color);
}

.message-row.user .message-bubble {
  background: #1677ff;
  color: #fff;
}

.message-content {
  word-break: break-word;
}

.message-row.user .message-content {
  white-space: pre-wrap;
}

.intent-badge {
  margin-bottom: 4px;
}

.attachment-preview {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.att-item {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(0,0,0,0.06);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.message-row.user .att-item {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

.chat-input-area {
  border-top: 1px solid var(--border-color);
  padding: 12px 16px;
}

.attachment-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.pending-att {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--page-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
</style>
