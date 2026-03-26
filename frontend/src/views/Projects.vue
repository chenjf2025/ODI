<template>
  <div class="fade-in-up">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start">
      <div>
        <h2>项目管理</h2>
        <p>管理所有 ODI 境外投资项目</p>
      </div>
      <a-button type="primary" size="large" @click="showCreate = true">
        <template #icon><PlusOutlined /></template>
        新建项目
      </a-button>
    </div>

    <!-- 筛选 -->
    <div class="page-card" style="margin-bottom: 16px">
      <a-space>
        <a-select v-model:value="statusFilter" placeholder="按状态筛选" style="width: 200px" allowClear @change="fetchProjects">
          <a-select-option v-for="s in dicts.project_status" :key="s.dict_value" :value="s.dict_value">{{ s.dict_label }}</a-select-option>
        </a-select>
        <a-button @click="statusFilter = null; fetchProjects()">重置</a-button>
      </a-space>
    </div>

    <!-- 列表 -->
    <div class="page-card">
      <a-table :dataSource="projects" :columns="columns" :loading="loading" rowKey="project_id"
        :pagination="{ current: page, pageSize: 20, total, onChange: (p) => { page = p; fetchProjects() } }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusName(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'investment_amount'">
            {{ record.investment_amount ? `${Number(record.investment_amount).toLocaleString()} ${record.currency}` : '-' }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleDateString('zh-CN') }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="$router.push(`/projects/${record.project_id}`)">详情</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.project_id)" v-if="userStore.isAdmin">
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 新建弹窗 -->
    <a-modal v-model:open="showCreate" title="新建 ODI 项目" :width="640" @ok="handleCreate" :confirmLoading="creating">
      <a-form :model="createForm" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="境内主体">
              <a-select v-model:value="createForm.domestic_entity_id" placeholder="选择境内主体" allowClear>
                <a-select-option v-for="e in domesticEntities" :key="e.entity_id" :value="e.entity_id">
                  {{ e.company_name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="境外标的">
              <a-select v-model:value="createForm.overseas_entity_id" placeholder="选择境外标的" allowClear>
                <a-select-option v-for="e in overseasEntities" :key="e.entity_id" :value="e.entity_id">
                  {{ e.overseas_name_cn }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="项目名称（留空自动生成）">
          <a-input v-model:value="createForm.project_name" placeholder="[境内主体]在[国家]新设[境外企业]项目" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="投资金额">
              <a-input-number v-model:value="createForm.investment_amount" style="width: 100%" :min="0" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="币种">
              <a-select v-model:value="createForm.currency">
                <a-select-option v-for="c in dicts.currency" :key="c.dict_value" :value="c.dict_value">{{ c.dict_label }} ({{ c.dict_value }})</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="投资架构">
              <a-select v-model:value="createForm.investment_path">
                <a-select-option v-for="p in dicts.investment_path" :key="p.dict_value" :value="p.dict_value">{{ p.dict_label }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="投资必要性说明">
          <a-textarea v-model:value="createForm.purpose_description" :rows="3" placeholder="请描述投资背景和目的，AI可基于此扩写…" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { projectsApi, entitiesApi, dictionariesApi } from '../api'
import { useUserStore } from '../stores/user'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const userStore = useUserStore()
const projects = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const statusFilter = ref(null)
const showCreate = ref(false)
const creating = ref(false)
const domesticEntities = ref([])
const overseasEntities = ref([])
const dicts = ref({
  currency: [],
  investment_path: [],
  project_status: [],
})

const STATUS_LIST = [
  'PRE_REVIEW', 'DATA_COLLECTION', 'NDRC_FILING_PENDING', 'NDRC_APPROVED',
  'MOFCOM_FILING_PENDING', 'MOFCOM_APPROVED', 'BANK_REG_PENDING', 'FUNDS_REMITTED', 'POST_INVESTMENT'
]

const createForm = reactive({
  domestic_entity_id: null, overseas_entity_id: null, project_name: '',
  investment_amount: null, currency: 'USD', investment_path: 'DIRECT', purpose_description: ''
})

const columns = [
  { title: '项目名称', dataIndex: 'project_name', key: 'project_name', ellipsis: true, width: 280 },
  { title: '状态', key: 'status', width: 120 },
  { title: '投资金额', key: 'investment_amount', width: 180 },
  { title: '创建日期', key: 'created_at', width: 120 },
  { title: '操作', key: 'actions', width: 140 },
]

onMounted(async () => {
  await fetchProjects()
  try {
    const [d, o, currencies, paths, statuses] = await Promise.all([
      entitiesApi.listDomestic(),
      entitiesApi.listOverseas(),
      dictionariesApi.list({ dict_type: 'currency' }),
      dictionariesApi.list({ dict_type: 'investment_path' }),
      dictionariesApi.list({ dict_type: 'project_status' }),
    ])
    domesticEntities.value = d.data
    overseasEntities.value = o.data
    dicts.value.currency = currencies.data || []
    dicts.value.investment_path = paths.data || []
    dicts.value.project_status = statuses.data || []
  } catch (e) {
    console.error('获取初始化数据失败', e)
  }
})

async function fetchProjects() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await projectsApi.list(params)
    projects.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    message.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  creating.value = true
  try {
    await projectsApi.create(createForm)
    message.success('项目创建成功')
    showCreate.value = false
    Object.assign(createForm, { domestic_entity_id: null, overseas_entity_id: null, project_name: '', investment_amount: null, purpose_description: '' })
    await fetchProjects()
    await userStore.fetchUser()
  } catch (e) {
    message.error(e.response?.data?.detail?.message || e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(id) {
  try {
    await projectsApi.delete(id)
    message.success('项目已删除')
    await fetchProjects()
  } catch (e) {
    message.error('删除失败')
  }
}

function statusName(s) {
  const map = {
    PRE_REVIEW: '智能预审', DATA_COLLECTION: '材料准备', NDRC_FILING_PENDING: '发改委备案',
    NDRC_APPROVED: '发改委通过', MOFCOM_FILING_PENDING: '商务部备案', MOFCOM_APPROVED: '商务部通过',
    BANK_REG_PENDING: '银行登记', FUNDS_REMITTED: '资金汇出', POST_INVESTMENT: '投后管理',
  }
  return map[s] || s
}
function statusColor(s) {
  const map = {
    PRE_REVIEW: 'blue', DATA_COLLECTION: 'cyan', NDRC_FILING_PENDING: 'purple',
    NDRC_APPROVED: 'green', MOFCOM_FILING_PENDING: 'orange', MOFCOM_APPROVED: 'green',
    BANK_REG_PENDING: 'geekblue', FUNDS_REMITTED: 'green', POST_INVESTMENT: 'default',
  }
  return map[s] || 'default'
}
</script>
