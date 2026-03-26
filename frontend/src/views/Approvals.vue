<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>审批流程</h2>
      <p>管理项目审批流程</p>
    </div>

    <div class="page-card">
      <a-tabs v-model:activeKey="activeTab" @change="fetchFlows">
        <a-tab-pane key="pending" tab="待办审批" />
        <a-tab-pane key="all" tab="全部流程" />
      </a-tabs>

      <a-table
        :dataSource="flows"
        :columns="columns"
        :loading="loading"
        rowKey="flow_id"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusName(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'current_level'">
            {{ levelName(record.current_level) }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleString('zh-CN') }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="showDetail(record)">详情</a-button>
              <a-button v-if="record.status === 'PENDING' && activeTab === 'pending'" type="link" size="small" @click="showApproveModal(record)">审批</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="showDetailModal" title="审批详情" width="640" :footer="null">
      <a-descriptions bordered :column="2" v-if="currentFlow">
        <a-descriptions-item label="流程ID">{{ currentFlow.flow_id }}</a-descriptions-item>
        <a-descriptions-item label="当前级别">{{ levelName(currentFlow.current_level) }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColor(currentFlow.status)">{{ statusName(currentFlow.status) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ new Date(currentFlow.created_at).toLocaleString('zh-CN') }}</a-descriptions-item>
      </a-descriptions>
      <a-divider>审批历史</a-divider>
      <a-timeline v-if="flowLogs.length">
        <a-timeline-item v-for="log in flowLogs" :key="log.log_id" :color="log.action === 'APPROVED' ? 'green' : 'red'">
          <p><strong>{{ levelName(log.level) }} - {{ log.action === 'APPROVED' ? '通过' : '驳回' }}</strong></p>
          <p v-if="log.opinion">意见: {{ log.opinion }}</p>
          <p style="font-size: 12px; color: #999">{{ new Date(log.created_at).toLocaleString('zh-CN') }}</p>
        </a-timeline-item>
      </a-timeline>
      <a-empty v-else description="暂无审批历史" />
    </a-modal>

    <a-modal v-model:open="showApprove" title="审批" @ok="handleApprove" :confirmLoading="loading">
      <a-form layout="vertical">
        <a-form-item label="审批意见">
          <a-textarea v-model:value="approveForm.opinion" :rows="3" placeholder="请输入审批意见" />
        </a-form-item>
      </a-form>
      <div style="margin-top: 16px; text-align: center">
        <a-space>
          <a-button type="primary" @click="handleApproveAction('APPROVED')" :loading="loading">通过</a-button>
          <a-button danger @click="handleApproveAction('REJECTED')" :loading="loading">驳回</a-button>
        </a-space>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { approvalsApi, projectsApi } from '../api'
import { message } from 'ant-design-vue'

const loading = ref(false)
const activeTab = ref('pending')
const flows = ref([])
const currentFlow = ref(null)
const flowLogs = ref([])
const showDetailModal = ref(false)
const showApprove = ref(false)
const projects = ref([])

const approveForm = reactive({ opinion: '' })

const columns = [
  { title: '项目名称', dataIndex: 'project_name', ellipsis: true },
  { title: '当前级别', key: 'current_level', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 120 },
]

onMounted(async () => {
  await fetchProjects()
  await fetchFlows()
})

async function fetchProjects() {
  try {
    const { data } = await projectsApi.list({ page: 1, page_size: 100 })
    projects.value = data.items || []
  } catch {}
}

async function fetchFlows() {
  loading.value = true
  try {
    let { data } = activeTab.value === 'pending'
      ? await approvalsApi.listPending()
      : await approvalsApi.listFlows({})
    flows.value = data || []
    flows.value = flows.value.map(f => {
      const proj = projects.value.find(p => p.project_id === f.project_id)
      return { ...f, project_name: proj?.project_name || f.project_id }
    })
  } catch {
    message.error('获取审批流程失败')
  } finally {
    loading.value = false
  }
}

async function showDetail(record) {
  try {
    const { data } = await approvalsApi.getFlow(record.flow_id)
    currentFlow.value = data.flow
    flowLogs.value = data.logs || []
    showDetailModal.value = true
  } catch {
    message.error('获取详情失败')
  }
}

function showApproveModal(record) {
  currentFlow.value = record
  approveForm.opinion = ''
  showApprove.value = true
}

async function handleApproveAction(action) {
  if (!currentFlow.value) return
  loading.value = true
  try {
    if (action === 'APPROVED') {
      await approvalsApi.approve(currentFlow.value.flow_id, { opinion: approveForm.opinion })
      message.success('审批通过')
    } else {
      await approvalsApi.reject(currentFlow.value.flow_id, { opinion: approveForm.opinion })
      message.success('已驳回')
    }
    showApprove.value = false
    await fetchFlows()
  } catch {
    message.error('操作失败')
  } finally {
    loading.value = false
  }
}

async function handleApprove() {}

function statusName(s) {
  const map = { PENDING: '待审批', APPROVED: '已通过', REJECTED: '已驳回', WITHDRAWN: '已撤回' }
  return map[s] || s
}
function statusColor(s) {
  const map = { PENDING: 'blue', APPROVED: 'green', REJECTED: 'red', WITHDRAWN: 'orange' }
  return map[s] || 'default'
}
function levelName(l) {
  const map = { FIRST: '一级', REVIEW: '复核', FINAL: '终审' }
  return map[l] || l
}
</script>
