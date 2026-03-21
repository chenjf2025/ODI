<template>
  <div class="fade-in-up">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><h2>LLM 模型配置</h2><p>管理 AI 大模型提供商的 API 配置</p></div>
      <a-button type="primary" @click="showModal = true"><PlusOutlined /> 添加配置</a-button>
    </div>
    <div class="page-card">
      <a-table :dataSource="configs" :columns="columns" :loading="loading" rowKey="config_id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'provider_name'">
            <a-tag :color="providerColor(record.provider_name)">{{ record.provider_name }}</a-tag>
          </template>
          <template v-if="column.key === 'is_enabled'"><a-switch :checked="!!record.is_enabled" @change="toggleEnabled(record)" size="small" /></template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="startEdit(record)">编辑</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.config_id)"><a-button type="link" danger size="small">删除</a-button></a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
    <a-modal v-model:open="showModal" :title="editId ? '编辑配置' : '添加配置'" @ok="handleSubmit" :confirmLoading="submitting" :width="600">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="提供商" required><a-select v-model:value="form.provider_name"><a-select-option value="deepseek">DeepSeek</a-select-option><a-select-option value="kimi">Kimi</a-select-option><a-select-option value="minimax">MiniMax</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="显示名称"><a-input v-model:value="form.display_name" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="优先级"><a-input-number v-model:value="form.priority" style="width:100%" :min="0" /></a-form-item></a-col>
        </a-row>
        <a-form-item label="API Key" required><a-input-password v-model:value="form.api_key" /></a-form-item>
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="Base URL" required><a-input v-model:value="form.base_url" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="模型版本" required><a-input v-model:value="form.model_version" /></a-form-item></a-col>
        </a-row>
        <a-form-item label="备注"><a-textarea v-model:value="form.description" :rows="2" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const configs = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const editId = ref(null)
const form = reactive({ provider_name: 'deepseek', display_name: '', api_key: '', base_url: '', model_version: '', priority: 0, description: '' })

const columns = [
  { title: '提供商', key: 'provider_name', width: 120 },
  { title: '显示名称', dataIndex: 'display_name', width: 150 },
  { title: 'Base URL', dataIndex: 'base_url', ellipsis: true },
  { title: '模型版本', dataIndex: 'model_version', width: 160 },
  { title: '优先级', dataIndex: 'priority', width: 80 },
  { title: '启用', key: 'is_enabled', width: 80 },
  { title: '操作', key: 'actions', width: 140 },
]

onMounted(fetch)
async function fetch() {
  loading.value = true
  try { const { data } = await adminApi.listLLMConfigs(); configs.value = data } catch {} finally { loading.value = false }
}

function startEdit(r) {
  editId.value = r.config_id
  Object.assign(form, { provider_name: r.provider_name, display_name: r.display_name || '', api_key: '', base_url: r.base_url, model_version: r.model_version, priority: r.priority, description: r.description || '' })
  showModal.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    const payload = { ...form }
    if (editId.value && !payload.api_key) delete payload.api_key
    if (editId.value) { await adminApi.updateLLMConfig(editId.value, payload); message.success('更新成功') }
    else { await adminApi.createLLMConfig(payload); message.success('创建成功') }
    showModal.value = false; editId.value = null; await fetch()
  } catch (e) { message.error('操作失败') } finally { submitting.value = false }
}

async function toggleEnabled(r) {
  try { await adminApi.updateLLMConfig(r.config_id, { is_enabled: r.is_enabled ? 0 : 1 }); await fetch() } catch { message.error('切换失败') }
}

async function handleDelete(id) {
  try { await adminApi.deleteLLMConfig(id); message.success('已删除'); await fetch() } catch { message.error('删除失败') }
}

function providerColor(p) {
  const map = { deepseek: 'blue', kimi: 'purple', minimax: 'cyan' }
  return map[p] || 'default'
}
</script>
