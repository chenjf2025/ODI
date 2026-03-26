<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>付汇登记</h2>
      <p>管理境外投资付汇记录</p>
    </div>

    <div class="page-card">
      <div style="margin-bottom: 16px">
        <a-space>
          <a-select v-model:value="projectFilter" placeholder="按项目筛选" style="width: 200px" allowClear @change="fetchRemittances">
            <a-select-option v-for="p in projects" :key="p.project_id" :value="p.project_id">
              {{ p.project_name }}
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="showCreate = true">
            <template #icon><PlusOutlined /></template>
            新增付汇
          </a-button>
        </a-space>
      </div>

      <a-table
        :dataSource="remittances"
        :columns="columns"
        :loading="loading"
        rowKey="record_id"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'remittance_amount'">
            {{ Number(record.remittance_amount).toLocaleString() }} {{ record.currency }}
          </template>
          <template v-if="column.key === 'remittance_date'">
            {{ record.remittance_date ? new Date(record.remittance_date).toLocaleDateString('zh-CN') : '-' }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleString('zh-CN') }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="editRecord(record)">编辑</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.record_id)">
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="showCreate" :title="editingId ? '编辑付汇' : '新增付汇'" @ok="handleSave" :confirmLoading="loading" width="640">
      <a-form :model="form" layout="vertical">
        <a-form-item label="所属项目" required>
          <a-select v-model:value="form.project_id" placeholder="选择项目" :disabled="!!editingId">
            <a-select-option v-for="p in projects" :key="p.project_id" :value="p.project_id">
              {{ p.project_name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="付汇金额" required>
              <a-input-number v-model:value="form.remittance_amount" style="width: 100%" :min="0" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="币种" required>
              <a-select v-model:value="form.currency">
                <a-select-option value="USD">USD</a-select-option>
                <a-select-option value="CNY">CNY</a-select-option>
                <a-select-option value="HKD">HKD</a-select-option>
                <a-select-option value="EUR">EUR</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="收款账户名">
          <a-input v-model:value="form.receiver_account_name" placeholder="请输入收款账户名" />
        </a-form-item>
        <a-form-item label="收款银行">
          <a-input v-model:value="form.receiver_bank_name" placeholder="请输入收款银行" />
        </a-form-item>
        <a-form-item label="收款账号">
          <a-input v-model:value="form.receiver_account_no" placeholder="请输入收款账号" />
        </a-form-item>
        <a-form-item label="付汇日期">
          <a-date-picker v-model:value="form.remittance_date" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { remittancesApi, projectsApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const remittances = ref([])
const projects = ref([])
const projectFilter = ref(null)
const showCreate = ref(false)
const editingId = ref(null)

const form = reactive({
  project_id: null,
  remittance_amount: null,
  currency: 'USD',
  receiver_account_name: '',
  receiver_bank_name: '',
  receiver_account_no: '',
  remittance_date: null,
})

const columns = [
  { title: '项目名称', dataIndex: 'project_name', ellipsis: true },
  { title: '付汇金额', key: 'remittance_amount', width: 150 },
  { title: '收款账户', dataIndex: 'receiver_account_name', ellipsis: true },
  { title: '收款银行', dataIndex: 'receiver_bank_name', ellipsis: true },
  { title: '付汇日期', key: 'remittance_date', width: 120 },
  { title: '登记时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 120 },
]

onMounted(async () => {
  await fetchProjects()
  await fetchRemittances()
})

async function fetchProjects() {
  try {
    const { data } = await projectsApi.list({ page: 1, page_size: 100 })
    projects.value = data.items || []
  } catch {}
}

async function fetchRemittances() {
  loading.value = true
  try {
    const params = {}
    if (projectFilter.value) params.project_id = projectFilter.value
    const { data } = await remittancesApi.list(params)
    remittances.value = (data || []).map(r => {
      const proj = projects.value.find(p => p.project_id === r.project_id)
      return { ...r, project_name: proj?.project_name || r.project_id }
    })
  } catch {
    message.error('获取付汇记录失败')
  } finally {
    loading.value = false
  }
}

function editRecord(record) {
  editingId.value = record.record_id
  Object.assign(form, {
    project_id: record.project_id,
    remittance_amount: record.remittance_amount,
    currency: record.currency,
    receiver_account_name: record.receiver_account_name,
    receiver_bank_name: record.receiver_bank_name,
    receiver_account_no: record.receiver_account_no,
    remittance_date: record.remittance_date ? new Date(record.remittance_date) : null,
  })
  showCreate.value = true
}

async function handleSave() {
  if (!form.project_id || !form.remittance_amount) {
    message.error('请填写必填项')
    return
  }
  loading.value = true
  try {
    const payload = { ...form }
    if (form.remittance_date) payload.remittance_date = form.remittance_date.format('YYYY-MM-DD')
    if (editingId.value) {
      await remittancesApi.update(editingId.value, payload)
    } else {
      await remittancesApi.create(payload)
    }
    message.success('保存成功')
    showCreate.value = false
    editingId.value = null
    Object.assign(form, { project_id: null, remittance_amount: null, currency: 'USD', receiver_account_name: '', receiver_bank_name: '', receiver_account_no: '', remittance_date: null })
    await fetchRemittances()
  } catch {
    message.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  try {
    await remittancesApi.delete(id)
    message.success('删除成功')
    await fetchRemittances()
  } catch {
    message.error('删除失败')
  }
}
</script>
