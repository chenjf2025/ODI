<template>
  <div class="fade-in-up">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><h2>合规规则管理</h2><p>配置国家和行业合规风险规则</p></div>
      <a-button type="primary" @click="showModal = true" v-if="userStore.isAdmin"><PlusOutlined /> 新增规则</a-button>
    </div>
    <div class="page-card" style="margin-bottom: 16px">
      <a-space>
        <a-select v-model:value="typeFilter" placeholder="规则类型" style="width: 150px" allowClear @change="fetch">
          <a-select-option value="COUNTRY">国家规则</a-select-option>
          <a-select-option value="INDUSTRY">行业规则</a-select-option>
        </a-select>
      </a-space>
    </div>
    <div class="page-card">
      <a-table :dataSource="rules" :columns="columns" :loading="loading" rowKey="rule_id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'rule_type'"><a-tag :color="record.rule_type === 'COUNTRY' ? 'blue' : 'purple'">{{ record.rule_type === 'COUNTRY' ? '国家' : '行业' }}</a-tag></template>
          <template v-if="column.key === 'risk_level'"><a-tag :color="{ HIGH: 'red', MEDIUM: 'orange', LOW: 'green' }[record.risk_level]">{{ { HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[record.risk_level] }}</a-tag></template>
          <template v-if="column.key === 'is_active'"><a-tag :color="record.is_active ? 'green' : 'default'">{{ record.is_active ? '已启用' : '已禁用' }}</a-tag></template>
          <template v-if="column.key === 'actions'">
            <a-space v-if="userStore.isAdmin">
              <a-button type="link" size="small" @click="startEdit(record)">编辑</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.rule_id)"><a-button type="link" danger size="small">删除</a-button></a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
    <a-modal v-model:open="showModal" :title="editId ? '编辑规则' : '新增规则'" @ok="handleSubmit" :confirmLoading="submitting" :width="600">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="规则类型" required><a-select v-model:value="form.rule_type"><a-select-option value="COUNTRY">国家</a-select-option><a-select-option value="INDUSTRY">行业</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="目标值" required><a-input v-model:value="form.target_value" placeholder="如 HK, Vietnam" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="风险等级" required><a-select v-model:value="form.risk_level"><a-select-option value="HIGH">高风险</a-select-option><a-select-option value="MEDIUM">中风险</a-select-option><a-select-option value="LOW">低风险</a-select-option></a-select></a-form-item></a-col>
        </a-row>
        <a-form-item label="规则名称"><a-input v-model:value="form.rule_name" /></a-form-item>
        <a-form-item label="描述"><a-textarea v-model:value="form.description" :rows="2" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { rulesApi } from '../api'
import { useUserStore } from '../stores/user'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const userStore = useUserStore()
const rules = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const editId = ref(null)
const typeFilter = ref(null)
const form = reactive({ rule_type: 'COUNTRY', target_value: '', risk_level: 'MEDIUM', rule_name: '', description: '' })

const columns = [
  { title: '类型', key: 'rule_type', width: 100 },
  { title: '目标值', dataIndex: 'target_value', width: 120 },
  { title: '规则名称', dataIndex: 'rule_name', width: 200 },
  { title: '风险等级', key: 'risk_level', width: 100 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '操作', key: 'actions', width: 140 },
]

onMounted(fetch)
async function fetch() {
  loading.value = true
  try { const { data } = await rulesApi.list({ rule_type: typeFilter.value }); rules.value = data } catch {} finally { loading.value = false }
}

function startEdit(r) {
  editId.value = r.rule_id
  Object.assign(form, { rule_type: r.rule_type, target_value: r.target_value, risk_level: r.risk_level, rule_name: r.rule_name || '', description: r.description || '' })
  showModal.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editId.value) { await rulesApi.update(editId.value, form); message.success('更新成功') }
    else { await rulesApi.create(form); message.success('创建成功') }
    showModal.value = false; editId.value = null; await fetch()
  } catch (e) { message.error('操作失败') } finally { submitting.value = false }
}

async function handleDelete(id) {
  try { await rulesApi.delete(id); message.success('已删除'); await fetch() } catch { message.error('删除失败') }
}
</script>
