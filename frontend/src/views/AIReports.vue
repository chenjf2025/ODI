<template>
  <div class="fade-in-up">
    <div class="page-header"><h2>AI 报告中心</h2><p>选择项目，使用 AI 生成预审报告、可研报告、尽调报告</p></div>

    <a-row :gutter="16">
      <a-col :xs="24" :lg="8">
        <div class="page-card">
          <h3 style="margin-bottom: 16px; font-weight: 600">选择项目</h3>
          <a-select v-model:value="selectedProjectId" placeholder="搜索或选择项目" style="width: 100%" show-search
            :filter-option="(input, option) => option.label.toLowerCase().includes(input.toLowerCase())"
            :options="projects.map(p => ({ value: p.project_id, label: p.project_name }))" @change="loadProject" />

          <div v-if="selectedProject" style="margin-top: 16px">
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="项目名称">{{ selectedProject.project_name }}</a-descriptions-item>
              <a-descriptions-item label="状态"><a-tag>{{ statusName(selectedProject.status) }}</a-tag></a-descriptions-item>
              <a-descriptions-item label="投资金额">{{ selectedProject.investment_amount }} {{ selectedProject.currency }}</a-descriptions-item>
            </a-descriptions>
          </div>

          <a-divider />
          <h4 style="margin-bottom: 12px">AI 操作</h4>
          <a-space direction="vertical" style="width: 100%">
            <a-button type="primary" block :disabled="!selectedProjectId" :loading="loading" @click="runAI('pre_review')">🔍 智能预审</a-button>
            <a-button block :disabled="!selectedProjectId" :loading="loading" @click="runAI('feasibility')">📋 生成可研报告</a-button>
            <a-button block :disabled="!selectedProjectId" :loading="loading" @click="runAI('due_diligence')">📑 生成尽调报告</a-button>
          </a-space>
        </div>
      </a-col>

      <a-col :xs="24" :lg="16">
        <div class="page-card" style="min-height: 500px">
          <h3 style="margin-bottom: 16px; font-weight: 600">报告输出</h3>

          <div v-if="reportContent" style="white-space: pre-wrap; background: var(--bg-primary); padding: 20px; border-radius: 12px; font-size: 14px; line-height: 1.8; max-height: 600px; overflow-y: auto">
            {{ reportContent }}
          </div>

          <div v-else-if="preReviewResult">
            <div class="traffic-light" style="margin-bottom: 16px; font-size: 18px">
              <span class="traffic-dot" :class="preReviewResult.traffic_light?.toLowerCase()"></span>
              <span style="font-weight: 700">{{ { GREEN: '低风险 - 建议推进', YELLOW: '中风险 - 需关注', RED: '高风险 - 谨慎评估' }[preReviewResult.traffic_light] }}</span>
            </div>
            <div v-if="preReviewResult.matched_rules?.length" style="margin-bottom: 12px">
              <h4>命中规则:</h4>
              <a-tag v-for="(r, i) in preReviewResult.matched_rules" :key="i" :color="{ HIGH: 'red', MEDIUM: 'orange', LOW: 'green' }[r.risk_level]" style="margin: 4px">
                {{ r.rule_name || r.target_value }}
              </a-tag>
            </div>
            <div v-if="preReviewResult.summary" style="white-space: pre-wrap; background: var(--bg-primary); padding: 16px; border-radius: 10px; font-size: 13px">
              {{ preReviewResult.summary }}
            </div>
          </div>

          <a-empty v-else description="选择项目并执行 AI 操作以查看报告" />
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectsApi, aiApi } from '../api'
import { message } from 'ant-design-vue'

const projects = ref([])
const selectedProjectId = ref(null)
const selectedProject = ref(null)
const loading = ref(false)
const reportContent = ref('')
const preReviewResult = ref(null)

onMounted(async () => {
  try { const { data } = await projectsApi.list({ page: 1, page_size: 100 }); projects.value = data.items || [] } catch {}
})

async function loadProject() {
  reportContent.value = ''
  preReviewResult.value = null
  if (selectedProjectId.value) {
    try { const { data } = await projectsApi.get(selectedProjectId.value); selectedProject.value = data } catch {}
  }
}

async function runAI(type) {
  loading.value = true; reportContent.value = ''; preReviewResult.value = null
  try {
    if (type === 'pre_review') {
      const { data } = await aiApi.preReview({ project_id: selectedProjectId.value })
      preReviewResult.value = data
    } else {
      const { data } = await aiApi.generateReport({ project_id: selectedProjectId.value, report_type: type })
      reportContent.value = data.content
    }
    message.success('AI 任务完成')
    await loadProject()
  } catch (e) {
    const detail = e.response?.data?.detail
    let errMsg = 'AI 任务失败'
    if (typeof detail === 'string') {
      errMsg = detail
    } else if (detail?.message) {
      errMsg = detail.message
    } else if (e.message) {
      errMsg = e.message.includes('timeout') ? '请求超时，请稍后重试' : e.message
    } else if (!e.response) {
      errMsg = '网络错误，请检查连接后重试'
    }
    message.error(errMsg)
  } finally { loading.value = false }
}

function statusName(s) {
  const map = { PRE_REVIEW: '智能预审', DATA_COLLECTION: '材料准备', NDRC_FILING_PENDING: '发改委备案', NDRC_APPROVED: '发改委通过', MOFCOM_FILING_PENDING: '商务部备案', MOFCOM_APPROVED: '商务部通过', BANK_REG_PENDING: '银行登记', FUNDS_REMITTED: '资金汇出', POST_INVESTMENT: '投后管理' }
  return map[s] || s
}
</script>
