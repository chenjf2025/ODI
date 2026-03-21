<template>
  <div class="fade-in-up" v-if="project">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start">
      <div>
        <a-breadcrumb style="margin-bottom: 8px">
          <a-breadcrumb-item><a @click="$router.push('/projects')">项目管理</a></a-breadcrumb-item>
          <a-breadcrumb-item>{{ project.project_name }}</a-breadcrumb-item>
        </a-breadcrumb>
        <h2>{{ project.project_name }}</h2>
        <a-space>
          <a-tag :color="statusColor(project.status)" size="large">{{ statusName(project.status) }}</a-tag>
          <span style="color: var(--text-muted)">创建于 {{ new Date(project.created_at).toLocaleString('zh-CN') }}</span>
        </a-space>
      </div>
      <a-space>
        <a-button v-if="nextStatus" type="primary" @click="showTransition = true">
          推进至: {{ statusName(nextStatus) }}
        </a-button>
        <a-dropdown>
          <a-button>导出 <DownOutlined /></a-button>
          <template #overlay>
            <a-menu @click="handleExport">
              <a-menu-item key="ndrc">发改委 XML</a-menu-item>
              <a-menu-item key="mofcom">商务部 Excel</a-menu-item>
              <a-menu-item key="all">全部打包</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </a-space>
    </div>

    <!-- 状态流水线 -->
    <div class="page-card" style="margin-bottom: 16px; overflow-x: auto">
      <a-steps :current="currentStepIndex" size="small">
        <a-step v-for="s in STATUS_LIST" :key="s" :title="statusName(s)" />
      </a-steps>
    </div>

    <a-row :gutter="[16, 16]">
      <!-- 项目信息 -->
      <a-col :xs="24" :lg="14">
        <div class="page-card" style="margin-bottom: 16px">
          <h3 style="margin-bottom: 16px; font-weight: 600">投资信息</h3>
          <a-descriptions :column="2" bordered size="small">
            <a-descriptions-item label="投资金额">{{ project.investment_amount ? `${Number(project.investment_amount).toLocaleString()} ${project.currency}` : '-' }}</a-descriptions-item>
            <a-descriptions-item label="投资架构">{{ pathName(project.investment_path) }}</a-descriptions-item>
            <a-descriptions-item label="投资目的" :span="2">{{ project.purpose_description || '-' }}</a-descriptions-item>
          </a-descriptions>
        </div>

        <!-- AI 报告 -->
        <div class="page-card" style="margin-bottom: 16px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <h3 style="font-weight: 600">AI 生成报告</h3>
            <a-space>
              <a-button type="primary" size="small" @click="runPreReview" :loading="aiLoading">智能预审</a-button>
              <a-button size="small" @click="generateReport('feasibility')" :loading="aiLoading">生成可研报告</a-button>
              <a-button size="small" @click="generateReport('due_diligence')" :loading="aiLoading">生成尽调报告</a-button>
            </a-space>
          </div>

          <a-collapse v-if="hasAnyReport" :bordered="false" :activeKey="activeReportKeys" @change="keys => activeReportKeys = keys">
            <!-- 预审报告 -->
            <a-collapse-panel v-if="project.pre_review_report" key="pre_review">
              <template #header>
                <div style="display:flex;align-items:center;gap:10px">
                  <span style="font-weight:600">智能预审结果</span>
                  <span class="traffic-dot" :class="project.pre_review_report.traffic_light?.toLowerCase()" style="width:10px;height:10px"></span>
                  <a-tag :color="trafficColor(project.pre_review_report.traffic_light)" size="small">
                    {{ { GREEN: '通过', YELLOW: '需关注', RED: '高风险' }[project.pre_review_report.traffic_light] || '未评估' }}
                  </a-tag>
                </div>
              </template>
              <template #extra>
                <a-button type="link" size="small" @click.stop="exportPDF('pre_review')">
                  <FilePdfOutlined /> 导出 PDF
                </a-button>
              </template>
              <div ref="preReviewRef">
                <a-alert v-if="project.pre_review_report.asset_warning" :message="project.pre_review_report.asset_warning" type="warning" show-icon style="margin-bottom: 12px" />
                <div v-if="project.pre_review_report.ai_analysis" class="markdown-body" v-html="renderMarkdown(project.pre_review_report.ai_analysis)"></div>
              </div>
            </a-collapse-panel>

            <!-- 可研报告 -->
            <a-collapse-panel v-if="project.feasibility_report" key="feasibility">
              <template #header>
                <span style="font-weight:600">可行性研究报告</span>
              </template>
              <template #extra>
                <a-button type="link" size="small" @click.stop="exportPDF('feasibility')">
                  <FilePdfOutlined /> 导出 PDF
                </a-button>
              </template>
              <div ref="feasibilityRef" class="markdown-body" v-html="renderMarkdown(project.feasibility_report)"></div>
            </a-collapse-panel>

            <!-- 尽调报告 -->
            <a-collapse-panel v-if="project.due_diligence_report" key="due_diligence">
              <template #header>
                <span style="font-weight:600">尽职调查报告</span>
              </template>
              <template #extra>
                <a-button type="link" size="small" @click.stop="exportPDF('due_diligence')">
                  <FilePdfOutlined /> 导出 PDF
                </a-button>
              </template>
              <div ref="dueDiligenceRef" class="markdown-body" v-html="renderMarkdown(project.due_diligence_report)"></div>
            </a-collapse-panel>
          </a-collapse>

          <a-empty v-if="!hasAnyReport" description="暂无 AI 报告，点击上方按钮生成" />
        </div>
      </a-col>

      <!-- 侧边栏 -->
      <a-col :xs="24" :lg="10">
        <div class="page-card">
          <h3 style="margin-bottom: 16px; font-weight: 600">状态流转日志</h3>
          <a-timeline>
            <a-timeline-item v-for="log in statusLogs" :key="log.log_id" :color="log.to_status === project.status ? 'blue' : 'gray'">
              <p style="font-weight: 500">{{ statusName(log.to_status) }}</p>
              <p style="font-size: 12px; color: var(--text-muted)">{{ new Date(log.created_at).toLocaleString('zh-CN') }}</p>
              <p v-if="log.remark" style="font-size: 12px; color: var(--text-secondary)">{{ log.remark }}</p>
            </a-timeline-item>
          </a-timeline>
        </div>
      </a-col>
    </a-row>

    <!-- 状态推进弹窗 -->
    <a-modal v-model:open="showTransition" title="推进项目状态" @ok="handleTransition" :confirmLoading="transitioning">
      <p>将项目从 <a-tag>{{ statusName(project.status) }}</a-tag> 推进至 <a-tag color="blue">{{ statusName(nextStatus) }}</a-tag></p>
      
      <a-form layout="vertical">
        <a-form-item v-if="nextStatus === 'NDRC_APPROVED'" label="发改委备案通知书 (必件)" required>
          <a-upload
            v-model:file-list="ndrcFileList"
            :customRequest="uploadNDRC"
            :maxCount="1"
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            @remove="() => ndrcUrl = ''"
          >
            <a-button><UploadOutlined /> 选择文件并上传</a-button>
          </a-upload>
          <div v-if="ndrcUrl" style="margin-top: 8px; font-size: 13px">
            已成功上传: <a :href="ndrcUrl" target="_blank">{{ ndrcUrl.split('/').pop() }}</a>
          </div>
        </a-form-item>
        
        <a-form-item v-if="nextStatus === 'MOFCOM_APPROVED'" label="商务部企业境外投资证书 (必填)" required>
          <a-upload
            v-model:file-list="mofcomFileList"
            :customRequest="uploadMOFCOM"
            :maxCount="1"
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            @remove="() => mofcomUrl = ''"
          >
            <a-button><UploadOutlined /> 选择文件并上传</a-button>
          </a-upload>
          <div v-if="mofcomUrl" style="margin-top: 8px; font-size: 13px">
            已成功上传: <a :href="mofcomUrl" target="_blank">{{ mofcomUrl.split('/').pop() }}</a>
          </div>
        </a-form-item>

        <a-form-item label="备注">
          <a-textarea v-model:value="transitionRemark" :rows="2" placeholder="可选备注" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  <a-spin v-else style="display:flex;justify-content:center;margin-top:100px" />
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, aiApi, exportApi, uploadApi } from '../api'
import { message } from 'ant-design-vue'
import { DownOutlined, FilePdfOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { marked } from 'marked'

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

const route = useRoute()
const project = ref(null)
const statusLogs = ref([])
const aiLoading = ref(false)
const showTransition = ref(false)
const transitioning = ref(false)
const transitionRemark = ref('')
const ndrcUrl = ref('')
const mofcomUrl = ref('')
const ndrcFileList = ref([])
const mofcomFileList = ref([])
const activeReportKeys = ref(['pre_review', 'feasibility', 'due_diligence'])

// 报告容器 refs (用于 PDF 导出)
const preReviewRef = ref(null)
const feasibilityRef = ref(null)
const dueDiligenceRef = ref(null)

const STATUS_LIST = [
  'PRE_REVIEW', 'DATA_COLLECTION', 'NDRC_FILING_PENDING', 'NDRC_APPROVED',
  'MOFCOM_FILING_PENDING', 'MOFCOM_APPROVED', 'BANK_REG_PENDING', 'FUNDS_REMITTED', 'POST_INVESTMENT'
]

const TRANSITIONS = {
  PRE_REVIEW: 'DATA_COLLECTION', DATA_COLLECTION: 'NDRC_FILING_PENDING',
  NDRC_FILING_PENDING: 'NDRC_APPROVED', NDRC_APPROVED: 'MOFCOM_FILING_PENDING',
  MOFCOM_FILING_PENDING: 'MOFCOM_APPROVED', MOFCOM_APPROVED: 'BANK_REG_PENDING',
  BANK_REG_PENDING: 'FUNDS_REMITTED', FUNDS_REMITTED: 'POST_INVESTMENT',
}

const currentStepIndex = computed(() => STATUS_LIST.indexOf(project.value?.status) || 0)
const nextStatus = computed(() => TRANSITIONS[project.value?.status])
const hasAnyReport = computed(() =>
  project.value?.pre_review_report || project.value?.feasibility_report || project.value?.due_diligence_report
)

onMounted(fetchProject)

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function trafficColor(light) {
  return { GREEN: 'green', YELLOW: 'orange', RED: 'red' }[light] || 'default'
}

async function exportPDF(type) {
  const html2pdf = (await import('html2pdf.js')).default

  const refMap = {
    pre_review: preReviewRef,
    feasibility: feasibilityRef,
    due_diligence: dueDiligenceRef,
  }
  const nameMap = {
    pre_review: '智能预审报告',
    feasibility: '可行性研究报告',
    due_diligence: '尽职调查报告',
  }

  const targetRef = refMap[type]
  if (!targetRef?.value) {
    message.warning('请先展开报告面板')
    return
  }

  // 确保面板展开
  if (!activeReportKeys.value.includes(type)) {
    activeReportKeys.value = [...activeReportKeys.value, type]
    await nextTick()
  }

  message.loading({ content: '正在生成 PDF...', key: 'pdf', duration: 0 })

  const filename = `${project.value.project_name}-${nameMap[type]}.pdf`

  try {
    await html2pdf()
      .set({
        margin: [15, 15, 15, 15],
        filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      })
      .from(targetRef.value)
      .save()

    message.success({ content: 'PDF 导出成功', key: 'pdf' })
  } catch (e) {
    message.error({ content: 'PDF 导出失败', key: 'pdf' })
  }
}

async function fetchProject() {
  try {
    const { data } = await projectsApi.get(route.params.id)
    project.value = data
    statusLogs.value = data.status_logs || []
  } catch (e) {
    message.error('获取项目详情失败')
  }
}

async function uploadFile(options, urlRef) {
  const { file, onSuccess, onError } = options
  try {
    const { data } = await uploadApi.uploadFile(file)
    if (data.success) {
      urlRef.value = data.url
      onSuccess(data, file)
      message.success(`${file.name} 上传成功`)
    }
  } catch (error) {
    onError(error)
    message.error(`${file.name} 上传失败`)
  }
}

const uploadNDRC = (options) => uploadFile(options, ndrcUrl)
const uploadMOFCOM = (options) => uploadFile(options, mofcomUrl)

async function handleTransition() {
  if (nextStatus.value === 'NDRC_APPROVED' && !ndrcUrl.value && !project.value.ndrc_certificate_url) {
    message.error('请输入发改委备案通知书链接')
    return
  }
  if (nextStatus.value === 'MOFCOM_APPROVED' && !mofcomUrl.value && !project.value.mofcom_certificate_url) {
    message.error('请输入商务部投资证书链接')
    return
  }

  transitioning.value = true
  try {
    const payload = { 
      target_status: nextStatus.value, 
      remark: transitionRemark.value 
    }
    if (ndrcUrl.value) payload.ndrc_certificate_url = ndrcUrl.value
    if (mofcomUrl.value) payload.mofcom_certificate_url = mofcomUrl.value

    await projectsApi.updateStatus(project.value.project_id, payload)
    message.success('状态推进成功')
    showTransition.value = false
    transitionRemark.value = ''
    ndrcUrl.value = ''
    mofcomUrl.value = ''
    ndrcFileList.value = []
    mofcomFileList.value = []
    await fetchProject()
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    transitioning.value = false
  }
}

async function runPreReview() {
  aiLoading.value = true
  try {
    await aiApi.preReview({ project_id: project.value.project_id })
    message.success('预审完成')
    await fetchProject()
  } catch (e) {
    message.error(e.response?.data?.detail?.message || e.response?.data?.detail || '预审失败')
  } finally {
    aiLoading.value = false
  }
}

async function generateReport(type) {
  aiLoading.value = true
  try {
    await aiApi.generateReport({ project_id: project.value.project_id, report_type: type })
    message.success('报告生成成功')
    await fetchProject()
  } catch (e) {
    message.error(e.response?.data?.detail?.message || e.response?.data?.detail || '生成失败')
  } finally {
    aiLoading.value = false
  }
}

async function handleExport({ key }) {
  try {
    let res
    if (key === 'ndrc') res = await exportApi.ndrcXml(project.value.project_id)
    else if (key === 'mofcom') res = await exportApi.mofcomExcel(project.value.project_id)
    else res = await exportApi.package(project.value.project_id)

    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = key === 'ndrc' ? 'ndrc.xml' : key === 'mofcom' ? 'mofcom.xlsx' : 'export.zip'
    a.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  } catch {
    message.error('导出失败')
  }
}

function statusName(s) {
  const map = { PRE_REVIEW: '智能预审', DATA_COLLECTION: '材料准备', NDRC_FILING_PENDING: '发改委备案', NDRC_APPROVED: '发改委通过', MOFCOM_FILING_PENDING: '商务部备案', MOFCOM_APPROVED: '商务部通过', BANK_REG_PENDING: '银行登记', FUNDS_REMITTED: '资金汇出', POST_INVESTMENT: '投后管理' }
  return map[s] || s
}
function statusColor(s) {
  const map = { PRE_REVIEW: 'blue', DATA_COLLECTION: 'cyan', NDRC_FILING_PENDING: 'purple', NDRC_APPROVED: 'green', MOFCOM_FILING_PENDING: 'orange', MOFCOM_APPROVED: 'green', BANK_REG_PENDING: 'geekblue', FUNDS_REMITTED: 'green', POST_INVESTMENT: 'default' }
  return map[s] || 'default'
}
function pathName(p) {
  const map = { DIRECT: '直接投资', SPV_HK: '香港 SPV', SPV_SGP: '新加坡 SPV', MULTI_LAYER: '多层架构' }
  return map[p] || p
}
</script>

<style scoped>
/* Markdown 渲染样式 */
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

.markdown-body :deep(strong) { font-weight: 700; color: var(--text-primary); }

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--primary-color);
  padding: 8px 16px;
  margin: 12px 0;
  background: rgba(26, 86, 219, 0.05);
  border-radius: 0 6px 6px 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
}
.markdown-body :deep(th) {
  background: var(--bg-primary);
  font-weight: 600;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.markdown-body :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 16px 0;
}
</style>
