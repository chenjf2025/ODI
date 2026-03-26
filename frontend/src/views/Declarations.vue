<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>申报管理</h2>
      <p>管理对外申报记录（发改委/商务部/外汇局）</p>
    </div>

    <div class="page-card">
      <div style="margin-bottom: 16px">
        <a-space>
          <a-select v-model:value="projectFilter" placeholder="按项目筛选" style="width: 200px" allowClear @change="fetchDeclarations">
            <a-select-option v-for="p in projects" :key="p.project_id" :value="p.project_id">
              {{ p.project_name }}
            </a-select-option>
          </a-select>
          <a-select v-model:value="targetFilter" placeholder="申报主体" style="width: 150px" allowClear @change="fetchDeclarations">
            <a-select-option value="NDRC">发改委</a-select-option>
            <a-select-option value="MOFCOM">商务部</a-select-option>
            <a-select-option value="SAFE">外汇局</a-select-option>
          </a-select>
          <a-button type="primary" @click="showCreate = true">
            <template #icon><PlusOutlined /></template>
            新增申报
          </a-button>
        </a-space>
      </div>

      <a-table
        :dataSource="declarations"
        :columns="columns"
        :loading="loading"
        rowKey="record_id"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'target'">
            <a-tag :color="targetColor(record.target)">{{ targetName(record.target) }}</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusName(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleString('zh-CN') }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button v-if="record.status === 'PENDING'" type="link" size="small" @click="submitDeclaration(record)">提交</a-button>
              <a-button v-if="record.status === 'IN_PROGRESS'" type="link" size="small" @click="approveDeclaration(record)">审核通过</a-button>
              <a-button type="link" size="small" @click="editRecord(record)">编辑</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="showCreate" :title="editingId ? '编辑申报' : '新增申报'" @ok="handleSave" :confirmLoading="loading">
      <a-form :model="form" layout="vertical">
        <a-form-item label="所属项目" required>
          <a-select v-model:value="form.project_id" placeholder="选择项目" :disabled="!!editingId">
            <a-select-option v-for="p in projects" :key="p.project_id" :value="p.project_id">
              {{ p.project_name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="申报主体" required>
          <a-select v-model:value="form.target" placeholder="选择申报主体">
            <a-select-option value="NDRC">发改委</a-select-option>
            <a-select-option value="MOFCOM">商务部</a-select-option>
            <a-select-option value="SAFE">外汇局</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="form.remark" :rows="3" placeholder="请输入备注" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { declarationsApi, projectsApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const declarations = ref([])
const projects = ref([])
const projectFilter = ref(null)
const targetFilter = ref(null)
const showCreate = ref(false)
const editingId = ref(null)

const form = reactive({
  project_id: null,
  target: null,
  remark: '',
})

const columns = [
  { title: '项目名称', dataIndex: 'project_name', ellipsis: true },
  { title: '申报主体', key: 'target', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '回执号', dataIndex: 'receipt_no', ellipsis: true },
  { title: '备注', dataIndex: 'remark', ellipsis: true },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 150 },
]

onMounted(async () => {
  await fetchProjects()
  await fetchDeclarations()
})

async function fetchProjects() {
  try {
    const { data } = await projectsApi.list({ page: 1, page_size: 100 })
    projects.value = data.items || []
  } catch {}
}

async function fetchDeclarations() {
  loading.value = true
  try {
    const params = {}
    if (projectFilter.value) params.project_id = projectFilter.value
    if (targetFilter.value) params.target = targetFilter.value
    const { data } = await declarationsApi.list(params)
    declarations.value = (data || []).map(d => {
      const proj = projects.value.find(p => p.project_id === d.project_id)
      return { ...d, project_name: proj?.project_name || d.project_id }
    })
  } catch {
    message.error('获取申报记录失败')
  } finally {
    loading.value = false
  }
}

function editRecord(record) {
  editingId.value = record.record_id
  Object.assign(form, { project_id: record.project_id, target: record.target, remark: record.remark || '' })
  showCreate.value = true
}

async function handleSave() {
  if (!form.project_id || !form.target) {
    message.error('请填写必填项')
    return
  }
  loading.value = true
  try {
    if (editingId.value) {
      await declarationsApi.update(editingId.value, form)
    } else {
      await declarationsApi.create(form)
    }
    message.success('保存成功')
    showCreate.value = false
    editingId.value = null
    Object.assign(form, { project_id: null, target: null, remark: '' })
    await fetchDeclarations()
  } catch {
    message.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function submitDeclaration(record) {
  try {
    await declarationsApi.submit(record.record_id)
    message.success('提交成功（Mock模式）')
    await fetchDeclarations()
  } catch {
    message.error('提交失败')
  }
}

async function approveDeclaration(record) {
  try {
    await declarationsApi.approve(record.record_id)
    message.success('审核通过')
    await fetchDeclarations()
  } catch {
    message.error('审核失败')
  }
}

function targetName(t) {
  const map = { NDRC: '发改委', MOFCOM: '商务部', SAFE: '外汇局' }
  return map[t] || t
}
function targetColor(t) {
  const map = { NDRC: 'blue', MOFCOM: 'purple', SAFE: 'orange' }
  return map[t] || 'default'
}
function statusName(s) {
  const map = { PENDING: '待提交', IN_PROGRESS: '审核中', APPROVED: '已通过', REJECTED: '已驳回' }
  return map[s] || s
}
function statusColor(s) {
  const map = { PENDING: 'orange', IN_PROGRESS: 'blue', APPROVED: 'green', REJECTED: 'red' }
  return map[s] || 'default'
}
</script>
