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
            <a-button type="primary" block :disabled="!selectedProjectId" :loading="loadingTypes.pre_review" @click="runAI('pre_review')">🔍 智能预审</a-button>
            <a-button block :disabled="!selectedProjectId" :loading="loadingTypes.feasibility" @click="runAI('feasibility')">📋 生成可研报告</a-button>
            <a-button block :disabled="!selectedProjectId" :loading="loadingTypes.due_diligence" @click="runAI('due_diligence')">📑 生成尽调报告</a-button>
          </a-space>
        </div>
      </a-col>

      <a-col :xs="24" :lg="16">
        <div class="page-card" style="min-height: 500px">
          <div v-if="hasAnyReport" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="font-weight:600;margin:0">报告输出</h3>
            <a-button size="small" @click="exportPDF(activeReportTab)"><FilePdfOutlined /> 导出 PDF</a-button>
          </div>

          <a-tabs v-if="hasAnyReport" v-model:activeKey="activeReportTab" style="margin-bottom: 12px">
            <a-tab-pane key="pre_review" v-if="selectedProject?.pre_review_report">
              <template #tab>🔍 智能预审</template>
              <div class="traffic-light" style="margin-bottom: 16px; font-size: 18px">
                <span class="traffic-dot" :class="selectedProject.pre_review_report.traffic_light?.toLowerCase()"></span>
                <span style="font-weight: 700">{{ TRAFFIC_MAP[selectedProject.pre_review_report.traffic_light] }}</span>
              </div>
              <div v-if="selectedProject.pre_review_report.matched_rules?.length" style="margin-bottom: 12px">
                <h4>命中规则:</h4>
                <a-tag v-for="(r, i) in selectedProject.pre_review_report.matched_rules" :key="i" :color="RISK_MAP[r.risk_level]" style="margin: 4px">
                  {{ r.rule_name || r.target_value }}
                </a-tag>
              </div>
              <div v-if="selectedProject.pre_review_report.ai_analysis" class="markdown-body">
                <div v-html="renderMarkdown(selectedProject.pre_review_report.ai_analysis)"></div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="feasibility" v-if="selectedProject?.feasibility_report">
              <template #tab>📋 可研报告</template>
              <div class="markdown-body">
                <div v-html="renderMarkdown(selectedProject.feasibility_report)"></div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="due_diligence" v-if="selectedProject?.due_diligence_report">
              <template #tab>📑 尽调报告</template>
              <div class="markdown-body">
                <div v-html="renderMarkdown(selectedProject.due_diligence_report)"></div>
              </div>
            </a-tab-pane>
          </a-tabs>

          <a-empty v-if="!hasAnyReport" description="选择项目并执行 AI 操作以查看报告" />

  <!-- PDF 导出专用隐藏区域（不受 max-height 限制） -->
  <div ref="pdfExportRef" style="position:absolute;left:-9999px;top:0;width:794px;padding:20px;background:white"></div>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { projectsApi, aiApi } from '../api'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { FilePdfOutlined } from '@ant-design/icons-vue'

marked.setOptions({ breaks: true, gfm: true })

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

const projects = ref([])
const selectedProjectId = ref(null)
const selectedProject = ref(null)
const loadingTypes = ref({ pre_review: false, feasibility: false, due_diligence: false })
const reportContent = ref('')
const preReviewResult = ref(null)
const inlineError = ref('')
const activeReportTab = ref('pre_review')
const hasAnyReport = computed(() =>
  selectedProject.value?.pre_review_report ||
  selectedProject.value?.feasibility_report ||
  selectedProject.value?.due_diligence_report
)

const TRAFFIC_MAP = { GREEN: '低风险 - 建议推进', YELLOW: '中风险 - 需关注', RED: '高风险 - 谨慎评估' }
const RISK_MAP = { HIGH: 'red', MEDIUM: 'orange', LOW: 'green' }
const pdfExportRef = ref(null)

onMounted(async () => {
  try { const { data } = await projectsApi.list({ page: 1, page_size: 100 }); projects.value = data.items || [] } catch {}
})

async function loadProject() {
  inlineError.value = ''
  reportContent.value = ''
  preReviewResult.value = null
  if (selectedProjectId.value) {
    try {
      const { data } = await projectsApi.get(selectedProjectId.value)
      selectedProject.value = data
      if (data.pre_review_report) {
        activeReportTab.value = 'pre_review'
      } else if (data.feasibility_report) {
        activeReportTab.value = 'feasibility'
      } else if (data.due_diligence_report) {
        activeReportTab.value = 'due_diligence'
      }
    } catch {}
  }
}

async function runAI(type) {
  loadingTypes.value[type] = true
  reportContent.value = ''
  preReviewResult.value = null
  inlineError.value = ''
  const savedReportContent = reportContent.value
  const savedPreReviewResult = preReviewResult.value
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
    reportContent.value = savedReportContent
    preReviewResult.value = savedPreReviewResult
    const detail = e.response?.data?.detail
    let errMsg = 'AI 任务失败'
    if (e.response?.status === 402 && detail?.error === 'INSUFFICIENT_FUNDS') {
      errMsg = `余额不足：当前 ${detail.current_balance} 点，需要 ${detail.required} 点，请到【系统配置-充值】充值点数`
    } else if (typeof detail === 'string') {
      errMsg = detail
    } else if (detail?.message) {
      errMsg = detail.message
    } else if (e.message) {
      errMsg = e.message.includes('timeout') ? '请求超时，请稍后重试' : e.message
    } else if (!e.response) {
      errMsg = '网络错误，请检查连接后重试'
    }
    inlineError.value = errMsg
    message.error(errMsg)
  } finally {
    loadingTypes.value[type] = false
  }
}

async function exportPDF(type) {
  if (!pdfExportRef.value) return
  const html2pdf = (await import('html2pdf.js')).default
  const nameMap = { pre_review: '智能预审报告', feasibility: '可行性研究报告', due_diligence: '尽职调查报告' }
  const proj = selectedProject.value

  let exportHTML = ''
  if (type === 'pre_review' && proj?.pre_review_report) {
    const pr = proj.pre_review_report
    const trafficColor = pr.traffic_light === 'GREEN' ? '#52c41a' : pr.traffic_light === 'YELLOW' ? '#faad14' : '#ff4d4f'
    const trafficText = TRAFFIC_MAP[pr.traffic_light] || pr.traffic_light
    exportHTML = `
      <div style="font-family: 'Noto Sans SC', Arial, sans-serif; padding: 0; color: #1a1a1a;">
        <div style="margin-bottom: 16px; font-size: 18px; font-weight: 700;">
          <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${trafficColor};margin-right:8px;vertical-align:middle;"></span>
          ${trafficText}
        </div>
        ${pr.matched_rules?.length ? `<div style="margin-bottom:16px"><strong>命中规则：</strong> ${pr.matched_rules.map(r => `<span style="background:#f0f0f0;padding:2px 8px;border-radius:4px;margin:2px;display:inline-block;">${r.rule_name || r.target_value}</span>`).join('')}</div>` : ''}
        <div class="markdown-body">${renderMarkdown(pr.ai_analysis || '')}</div>
      </div>`
  } else if (type === 'feasibility' && proj?.feasibility_report) {
    exportHTML = `<div style="font-family:'Noto Sans SC',Arial,sans-serif;"><div class="markdown-body">${renderMarkdown(proj.feasibility_report)}</div></div>`
  } else if (type === 'due_diligence' && proj?.due_diligence_report) {
    exportHTML = `<div style="font-family:'Noto Sans SC',Arial,sans-serif;"><div class="markdown-body">${renderMarkdown(proj.due_diligence_report)}</div></div>`
  }

  if (!exportHTML) return

  const CSS = `body{font-family:'Noto Sans SC',Arial,sans-serif;margin:0;padding:20px;color:#1a1a1a}.markdown-body{font-family:'Noto Sans SC',Arial,sans-serif}.markdown-body h1{font-size:22px;font-weight:700;margin:24px 0 12px;padding-bottom:8px;border-bottom:2px solid #e8e8e8}.markdown-body h2{font-size:18px;font-weight:700;margin:20px 0 10px;padding-bottom:6px;border-bottom:1px solid #e8e8e8}.markdown-body h3{font-size:16px;font-weight:600;margin:16px 0 8px}.markdown-body h4{font-size:14px;font-weight:600;margin:12px 0 6px}.markdown-body p{margin:8px 0;line-height:1.8}.markdown-body ul,.markdown-body ol{padding-left:24px;margin:8px 0}.markdown-body li{margin:4px 0}.markdown-body blockquote{border-left:4px solid #1a56db;padding:8px 16px;margin:12px 0;background:#f8faff;border-radius:0 6px 6px 0}.markdown-body table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px}.markdown-body th,.markdown-body td{border:1px solid #e8e8e8;padding:8px 12px;text-align:left}.markdown-body th{background:#fafafa;font-weight:600}.markdown-body code{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:13px}.markdown-body pre{background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;margin:12px 0}.markdown-body pre code{background:none;padding:0;color:inherit}.markdown-body hr{border:none;border-top:1px solid #e8e8e8;margin:16px 0}`
  const el = pdfExportRef.value
  el.innerHTML = `<style>${CSS}</style><div style="font-family:'Noto Sans SC',Arial,sans-serif;color:#1a1a1a;">${exportHTML}</div>`
  const origStyle = el.style.cssText
  el.style.cssText = 'position:fixed;left:0;top:0;width:210mm;padding:20px;background:white;z-index:9999;box-sizing:border-box'
  await nextTick()
  message.loading({ content: '正在生成 PDF...', key: 'pdf', duration: 0 })
  const filename = `${proj?.project_name || '报告'}-${nameMap[type]}.pdf`
  try {
    await html2pdf()
      .set({ margin: [10, 10, 10, 10], filename, html2canvas: { scale: 2, useCORS: true, logging: false }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }, pagebreak: { mode: ['avoid-all', 'css', 'legacy'] } })
      .from(el.lastElementChild || el)
      .save()
    message.success({ content: 'PDF 导出成功', key: 'pdf' })
  } catch (e) {
    message.error({ content: `PDF 导出失败: ${e.message}`, key: 'pdf' })
  } finally {
    el.style.cssText = origStyle
  }
}

function statusName(s) {
  const map = { PRE_REVIEW: '智能预审', DATA_COLLECTION: '材料准备', NDRC_FILING_PENDING: '发改委备案', NDRC_APPROVED: '发改委通过', MOFCOM_FILING_PENDING: '商务部备案', MOFCOM_APPROVED: '商务部通过', BANK_REG_PENDING: '银行登记', FUNDS_REMITTED: '资金汇出', POST_INVESTMENT: '投后管理' }
  return map[s] || s
}
</script>

<style scoped>
.markdown-body {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  padding: 16px 20px;
  background: var(--bg-primary);
  border-radius: 10px;
  max-height: 600px;
  overflow-y: auto;
}
.markdown-body :deep(h1) { font-size: 22px; font-weight: 700; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 2px solid var(--border-color); }
.markdown-body :deep(h2) { font-size: 18px; font-weight: 700; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border-color); }
.markdown-body :deep(h3) { font-size: 16px; font-weight: 600; margin: 16px 0 8px; }
.markdown-body :deep(h4) { font-size: 14px; font-weight: 600; margin: 12px 0 6px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 24px; margin: 8px 0; }
.markdown-body :deep(li) { margin: 4px 0; }
.markdown-body :deep(strong) { font-weight: 700; }
.markdown-body :deep(blockquote) { border-left: 4px solid var(--primary-color); padding: 8px 16px; margin: 12px 0; background: rgba(26,86,219,0.05); border-radius: 0 6px 6px 0; }
.markdown-body :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid var(--border-color); padding: 8px 12px; text-align: left; }
.markdown-body :deep(th) { background: var(--bg-primary); font-weight: 600; }
.markdown-body :deep(code) { background: rgba(0,0,0,0.06); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.markdown-body :deep(pre) { background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; }
.markdown-body :deep(pre code) { background: none; padding: 0; color: inherit; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid var(--border-color); margin: 16px 0; }
</style>
