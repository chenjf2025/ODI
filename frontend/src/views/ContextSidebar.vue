<template>
  <div class="context-sidebar">
    <div class="sidebar-header">
      <span>上下文</span>
      <a-button v-if="selectedProjectId" type="link" size="small" @click="clearSelection">清除</a-button>
    </div>

    <div class="sidebar-section">
      <div class="section-title">当前项目</div>
      <a-spin v-if="loadingProjects" />
      <a-select
        v-else
        v-model:value="selectedProjectId"
        placeholder="选择项目（可选）"
        allowClear
        style="width: 100%"
        size="small"
        @change="$emit('project-change', selectedProjectId)"
      >
        <a-select-option v-for="p in projects" :key="p.project_id" :value="p.project_id">
          <div class="project-option">
            <span>{{ p.project_name || '未命名项目' }}</span>
            <a-tag :color="statusColor(p.status)" size="small">{{ statusLabel(p.status) }}</a-tag>
          </div>
        </a-select-option>
      </a-select>
    </div>

    <div class="sidebar-section">
      <div class="section-title">快捷项目</div>
      <a-list v-if="recentProjects.length" size="small" :data-source="recentProjects" :loading="loadingProjects">
        <template #renderItem="{ item }">
          <a-list-item class="project-list-item" @click="selectProject(item.project_id)">
            <div class="project-item">
              <div class="project-name">{{ item.project_name || '未命名项目' }}</div>
              <div class="project-meta">{{ statusLabel(item.status) }}</div>
            </div>
          </a-list-item>
        </template>
      </a-list>
      <a-empty v-else description="暂无项目" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
    </div>

    <div class="sidebar-section">
      <div class="section-title">可用意图</div>
      <div class="intent-list">
        <a-tag v-for="intent in availableIntents" :key="intent.key" :color="intent.color" size="small">
          {{ intent.label }}
        </a-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Empty } from 'ant-design-vue'
import { projectsApi } from '../api'

const emit = defineEmits(['project-change'])

const selectedProjectId = ref(null)
const projects = ref([])
const loadingProjects = ref(false)

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
]

const recentProjects = ref([])

onMounted(async () => {
  loadingProjects.value = true
  try {
    const { data } = await projectsApi.list({ page: 1, page_size: 50 })
    projects.value = data.items || []
    recentProjects.value = projects.value.slice(0, 5)
  } catch {}
  finally { loadingProjects.value = false }
})

function selectProject(id) {
  selectedProjectId.value = id
  emit('project-change', id)
}

function clearSelection() {
  selectedProjectId.value = null
  emit('project-change', null)
}

function statusLabel(status) {
  return STATUS_MAP[status]?.label || status
}

function statusColor(status) {
  return STATUS_MAP[status]?.color || 'default'
}
</script>

<style scoped>
.context-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-section {
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
}

.section-title {
  font-size: 11px;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.project-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.project-list-item {
  cursor: pointer;
  padding: 6px 4px;
}

.project-list-item:hover {
  background: var(--page-bg);
  border-radius: 4px;
}

.project-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.project-name {
  font-size: 13px;
  font-weight: 500;
}

.project-meta {
  font-size: 11px;
  color: var(--text-secondary);
}

.intent-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
