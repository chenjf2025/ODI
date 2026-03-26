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

    <!-- 本环节所需文件 -->
    <div class="page-card" style="margin-bottom: 16px" v-if="currentStepDocs">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h3 style="font-weight:600">📋 {{ currentStepDocs.step_name }} - 所需文件</h3>
        <a-tag :color="currentStepDocs.documents.length >= currentStepDocs.requirements.filter(r=>r.required).length ? 'green' : 'orange'">
          {{ currentStepDocs.documents.length }}/{{ currentStepDocs.requirements.filter(r=>r.required).length }} 已上传
        </a-tag>
      </div>
      <a-list size="small" bordered>
        <a-list-item v-for="req in currentStepDocs.requirements" :key="req.type">
          <a-list-item-meta>
            <template #title>
              <a-space>
                <span>{{ req.name }}</span>
                <a-tag v-if="req.required" color="red" size="small">必填</a-tag>
                <a-tag v-else color="default" size="small">选填</a-tag>
              </a-space>
            </template>
            <template #description>
              <span style="color:var(--text-muted);font-size:12px">{{ req.description }}</span>
            </template>
          </a-list-item-meta>
          <template #actions>
            <div v-if="currentStepDocs.documents.find(d => d.document_type === req.type)" style="display:flex;align-items:center;gap:8px">
              <a-tag color="green"><FileOutlined /> {{ currentStepDocs.documents.find(d => d.document_type === req.type).document_name }}</a-tag>
              <a-button type="text" danger size="small" @click="deleteDoc(req.type)"><DeleteOutlined /></a-button>
            </div>
            <a-upload
              v-else
              :showUploadList="false"
              :customRequest="(opt) => uploadDoc(req.type, req.name, opt)"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            >
              <a-button size="small"><UploadOutlined /> 上传</a-button>
            </a-upload>
          </template>
        </a-list-item>
      </a-list>
      <div v-if="currentStepDocs.documents.find(d => d.review_result)" style="margin-top:12px;padding:12px;background:var(--bg-primary);border-radius:8px">
        <b style="font-size:13px">AI 审核结果：</b>
        <div style="margin-top:8px;white-space:pre-wrap;font-size:13px;color:var(--text-secondary)">{{ currentStepDocs.documents[0].review_result }}</div>
      </div>
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
              <a-button type="primary" size="small" @click="runPreReview" :loading="loadingTypes.pre_review">智能预审</a-button>
              <a-button size="small" @click="generateReport('feasibility')" :loading="loadingTypes.feasibility">生成可研报告</a-button>
              <a-button size="small" @click="generateReport('due_diligence')" :loading="loadingTypes.due_diligence">生成尽调报告</a-button>
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

    <a-tabs style="margin-top: 16px">
      <a-tab-pane key="approvals" tab="审批流程">
        <div class="page-card">
          <div style="margin-bottom: 16px">
            <a-space>
              <a-button type="primary" size="small" @click="initiateApproval" :loading="loadingApprovals">发起审批</a-button>
            </a-space>
          </div>
          <a-table :dataSource="projectApprovals" :columns="approvalColumns" :loading="loadingApprovals" rowKey="flow_id" :pagination="{ pageSize: 10 }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="approvalStatusColor(record.status)">{{ approvalStatusName(record.status) }}</a-tag>
              </template>
              <template v-if="column.key === 'current_level'">{{ approvalLevelName(record.current_level) }}</template>
              <template v-if="column.key === 'created_at'">{{ new Date(record.created_at).toLocaleDateString('zh-CN') }}</template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>
      <a-tab-pane key="remittances" tab="付汇记录">
        <div class="page-card">
          <div style="margin-bottom: 16px">
            <a-button type="primary" size="small" @click="showRemittanceModal = true">新增付汇</a-button>
          </div>
          <a-table :dataSource="projectRemittances" :columns="remittanceColumns" :loading="loadingRemittances" rowKey="record_id" :pagination="{ pageSize: 10 }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'remittance_amount'">{{ Number(record.remittance_amount).toLocaleString() }} {{ record.currency }}</template>
              <template v-if="column.key === 'remittance_date'">{{ record.remittance_date ? new Date(record.remittance_date).toLocaleDateString('zh-CN') : '-' }}</template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>
      <a-tab-pane key="declarations" tab="申报记录">
        <div class="page-card">
          <div style="margin-bottom: 16px">
            <a-button type="primary" size="small" @click="showDeclarationModal = true">新增申报</a-button>
          </div>
          <a-table :dataSource="projectDeclarations" :columns="declarationColumns" :loading="loadingDeclarations" rowKey="record_id" :pagination="{ pageSize: 10 }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'target'">
                <a-tag :color="declarationTargetColor(record.target)">{{ declarationTargetName(record.target) }}</a-tag>
              </template>
              <template v-if="column.key === 'status'">
                <a-tag :color="declarationStatusColor(record.status)">{{ declarationStatusName(record.status) }}</a-tag>
              </template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 状态推进弹窗 -->
    <a-modal v-model:open="showRemittanceModal" title="新增付汇" @ok="handleCreateRemittance" :confirmLoading="savingRemittance">
      <a-form :model="remittanceForm" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="付汇金额" required>
              <a-input-number v-model:value="remittanceForm.remittance_amount" style="width: 100%" :min="0" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="币种" required>
              <a-select v-model:value="remittanceForm.currency">
                <a-select-option value="USD">USD</a-select-option>
                <a-select-option value="CNY">CNY</a-select-option>
                <a-select-option value="HKD">HKD</a-select-option>
                <a-select-option value="EUR">EUR</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="收款账户名">
          <a-input v-model:value="remittanceForm.receiver_account_name" placeholder="请输入收款账户名" />
        </a-form-item>
        <a-form-item label="收款银行">
          <a-input v-model:value="remittanceForm.receiver_bank_name" placeholder="请输入收款银行" />
        </a-form-item>
        <a-form-item label="收款账号">
          <a-input v-model:value="remittanceForm.receiver_account_no" placeholder="请输入收款账号" />
        </a-form-item>
        <a-form-item label="付汇日期">
          <a-date-picker v-model:value="remittanceForm.remittance_date" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showDeclarationModal" title="新增申报" @ok="handleCreateDeclaration" :confirmLoading="savingDeclaration">
      <a-form :model="declarationForm" layout="vertical">
        <a-form-item label="申报主体" required>
          <a-select v-model:value="declarationForm.target" placeholder="选择申报主体">
            <a-select-option value="NDRC">发改委</a-select-option>
            <a-select-option value="MOFCOM">商务部</a-select-option>
            <a-select-option value="SAFE">外汇局</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="declarationForm.remark" :rows="2" placeholder="请输入备注" />
        </a-form-item>
      </a-form>
    </a-modal>

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

  <!-- PDF 导出专用隐藏区域 -->
  <div ref="pdfExportRef" style="position:absolute;left:-9999px;top:0;width:794px;padding:20px;background:white"></div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, aiApi, exportApi, uploadApi, approvalsApi, remittancesApi, declarationsApi } from '../api'
import { message } from 'ant-design-vue'
import { DownOutlined, FilePdfOutlined, UploadOutlined, FileOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { marked } from 'marked'

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

const route = useRoute()
const project = ref(null)
const statusLogs = ref([])
const loadingTypes = ref({ pre_review: false, feasibility: false, due_diligence: false })
const showTransition = ref(false)
const transitioning = ref(false)
const transitionRemark = ref('')
const ndrcUrl = ref('')
const mofcomUrl = ref('')
const ndrcFileList = ref([])
const mofcomFileList = ref([])
const activeReportKeys = ref(['pre_review', 'feasibility', 'due_diligence'])
const currentStepDocs = ref(null)
const projectApprovals = ref([])
const projectRemittances = ref([])
const projectDeclarations = ref([])
const loadingApprovals = ref(false)
const loadingRemittances = ref(false)
const loadingDeclarations = ref(false)
const showRemittanceModal = ref(false)
const showDeclarationModal = ref(false)
const savingRemittance = ref(false)
const savingDeclaration = ref(false)
const remittanceForm = reactive({
  remittance_amount: null,
  currency: 'USD',
  receiver_account_name: '',
  receiver_bank_name: '',
  receiver_account_no: '',
  remittance_date: null,
})
const declarationForm = reactive({
  target: null,
  remark: '',
})
const approvalColumns = [
  { title: '当前级别', key: 'current_level', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', key: 'created_at', width: 120 },
]
const remittanceColumns = [
  { title: '付汇金额', key: 'remittance_amount', width: 150 },
  { title: '收款账户', dataIndex: 'receiver_account_name', ellipsis: true },
  { title: '收款银行', dataIndex: 'receiver_bank_name', ellipsis: true },
  { title: '付汇日期', key: 'remittance_date', width: 120 },
]
const declarationColumns = [
  { title: '申报主体', key: 'target', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '回执号', dataIndex: 'receipt_no', ellipsis: true },
  { title: '备注', dataIndex: 'remark', ellipsis: true },
]

// 报告容器 refs (用于 PDF 导出)
const preReviewRef = ref(null)
const feasibilityRef = ref(null)
const dueDiligenceRef = ref(null)
const pdfExportRef = ref(null)

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

const TRAFFIC_MAP = { GREEN: '低风险 - 建议推进', YELLOW: '中风险 - 需关注', RED: '高风险 - 谨慎评估' }

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function trafficColor(light) {
  return { GREEN: 'green', YELLOW: 'orange', RED: 'red' }[light] || 'default'
}

async function exportPDF(type) {
  if (!pdfExportRef.value) return
  const html2pdf = (await import('html2pdf.js')).default
  const nameMap = { pre_review: '智能预审报告', feasibility: '可行性研究报告', due_diligence: '尽职调查报告' }
  const proj = project.value

  let exportHTML = ''
  if (type === 'pre_review' && proj?.pre_review_report) {
    const pr = proj.pre_review_report
    const trafficColor = pr.traffic_light === 'GREEN' ? '#52c41a' : pr.traffic_light === 'YELLOW' ? '#faad14' : '#ff4d4f'
    exportHTML = `
      <div style="font-family:'Noto Sans SC',Arial,sans-serif;padding:0;color:#1a1a1a;">
        ${pr.asset_warning ? `<div style="background:#fffbe6;border:1px solid #ffe58f;border-radius:6px;padding:10px 14px;margin-bottom:16px;font-size:13px;">⚠️ ${pr.asset_warning}</div>` : ''}
        <div style="margin-bottom:16px;font-size:18px;font-weight:700;">
          <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${trafficColor};margin-right:8px;vertical-align:middle;"></span>
          ${TRAFFIC_MAP[pr.traffic_light] || pr.traffic_light}
        </div>
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
  const filename = `${proj.project_name}-${nameMap[type]}.pdf`
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

async function fetchProject() {
  try {
    const { data } = await projectsApi.get(route.params.id)
    project.value = data
    statusLogs.value = data.status_logs || []
    await fetchStepDocs()
    await Promise.all([fetchApprovals(), fetchRemittances(), fetchDeclarations()])
  } catch (e) {
    message.error('获取项目详情失败')
  }
}

async function fetchApprovals() {
  if (!project.value) return
  loadingApprovals.value = true
  try {
    const { data } = await approvalsApi.listFlows({ project_id: project.value.project_id })
    projectApprovals.value = data || []
  } catch {} finally { loadingApprovals.value = false }
}

async function fetchRemittances() {
  if (!project.value) return
  loadingRemittances.value = true
  try {
    const { data } = await remittancesApi.list({ project_id: project.value.project_id })
    projectRemittances.value = data || []
  } catch {} finally { loadingRemittances.value = false }
}

async function fetchDeclarations() {
  if (!project.value) return
  loadingDeclarations.value = true
  try {
    const { data } = await declarationsApi.list({ project_id: project.value.project_id })
    projectDeclarations.value = data || []
  } catch {} finally { loadingDeclarations.value = false }
}

async function initiateApproval() {
  try {
    await approvalsApi.createFlow({ project_id: project.value.project_id })
    message.success('审批流程已发起')
    await fetchApprovals()
  } catch { message.error('发起审批失败') }
}

async function handleCreateRemittance() {
  if (!remittanceForm.remittance_amount) {
    message.error('请填写付汇金额')
    return
  }
  savingRemittance.value = true
  try {
    const payload = { ...remittanceForm, project_id: project.value.project_id }
    if (payload.remittance_date) payload.remittance_date = payload.remittance_date.format('YYYY-MM-DD')
    await remittancesApi.create(payload)
    message.success('付汇记录已创建')
    showRemittanceModal.value = false
    Object.assign(remittanceForm, { remittance_amount: null, currency: 'USD', receiver_account_name: '', receiver_bank_name: '', receiver_account_no: '', remittance_date: null })
    await fetchRemittances()
  } catch { message.error('创建失败') } finally { savingRemittance.value = false }
}

async function handleCreateDeclaration() {
  if (!declarationForm.target) {
    message.error('请选择申报主体')
    return
  }
  savingDeclaration.value = true
  try {
    await declarationsApi.create({ ...declarationForm, project_id: project.value.project_id })
    message.success('申报记录已创建')
    showDeclarationModal.value = false
    Object.assign(declarationForm, { target: null, remark: '' })
    await fetchDeclarations()
  } catch { message.error('创建失败') } finally { savingDeclaration.value = false }
}

function approvalStatusName(s) {
  const map = { PENDING: '待审批', APPROVED: '已通过', REJECTED: '已驳回', WITHDRAWN: '已撤回' }
  return map[s] || s
}
function approvalStatusColor(s) {
  const map = { PENDING: 'blue', APPROVED: 'green', REJECTED: 'red', WITHDRAWN: 'orange' }
  return map[s] || 'default'
}
function approvalLevelName(l) {
  const map = { FIRST: '一级', REVIEW: '复核', FINAL: '终审' }
  return map[l] || l
}
function declarationTargetName(t) {
  const map = { NDRC: '发改委', MOFCOM: '商务部', SAFE: '外汇局' }
  return map[t] || t
}
function declarationTargetColor(t) {
  const map = { NDRC: 'blue', MOFCOM: 'purple', SAFE: 'orange' }
  return map[t] || 'default'
}
function declarationStatusName(s) {
  const map = { PENDING: '待提交', IN_PROGRESS: '审核中', APPROVED: '已通过', REJECTED: '已驳回' }
  return map[s] || s
}
function declarationStatusColor(s) {
  const map = { PENDING: 'orange', IN_PROGRESS: 'blue', APPROVED: 'green', REJECTED: 'red' }
  return map[s] || 'default'
}

const STEP_NAME_MAP = {
  PRE_REVIEW: '智能预审', DATA_COLLECTION: '材料准备', NDRC_FILING_PENDING: '发改委备案',
  NDRC_APPROVED: '发改委通过', MOFCOM_FILING_PENDING: '商务部备案', MOFCOM_APPROVED: '商务部通过',
  BANK_REG_PENDING: '银行登记', FUNDS_REMITTED: '资金汇出', POST_INVESTMENT: '投后管理',
}

async function fetchStepDocs() {
  if (!project.value) return
  try {
    const { data } = await projectsApi.getDocuments(project.value.project_id)
    const currentStatus = project.value.status
    const stepData = data.find(s => s.step_status === currentStatus)
    if (stepData) {
      currentStepDocs.value = {
        ...stepData,
        step_name: STEP_NAME_MAP[stepData.step_status] || stepData.step_status,
      }
    } else {
      currentStepDocs.value = null
    }
  } catch (e) {
    currentStepDocs.value = null
  }
}

async function uploadDoc(docType, docName, options) {
  const { file, onSuccess, onError } = options
  try {
    const { data: fileData } = await uploadApi.uploadFile(file)
    if (!fileData.success) throw new Error('上传失败')
    await projectsApi.uploadDocument(project.value.project_id, {
      step_status: project.value.status,
      document_type: docType,
      document_name: docName,
      file_url: fileData.url,
      file_size: file.size,
    })
    message.success(`${file.name} 上传成功`)
    await fetchStepDocs()
    onSuccess(fileData, file)
  } catch (e) {
    message.error(`${file.name} 上传失败`)
    onError(e)
  }
}

async function deleteDoc(docType) {
  const doc = currentStepDocs.value?.documents?.find(d => d.document_type === docType)
  if (!doc) return
  try {
    await projectsApi.deleteDocument(project.value.project_id, doc.document_id)
    message.success('删除成功')
    await fetchStepDocs()
  } catch (e) {
    message.error('删除失败')
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
    const detail = e.response?.data?.detail
    if (detail && typeof detail === 'object') {
      message.error(detail.message || detail.error || '操作失败')
    } else {
      message.error(detail || '操作失败')
    }
  } finally {
    transitioning.value = false
  }
}

async function runPreReview() {
  loadingTypes.value.pre_review = true
  try {
    await aiApi.preReview({ project_id: project.value.project_id })
    message.success('预审完成')
    await fetchProject()
  } catch (e) {
    message.error(e.response?.data?.detail?.message || e.response?.data?.detail || '预审失败')
  } finally {
    loadingTypes.value.pre_review = false
  }
}

async function generateReport(type) {
  loadingTypes.value[type] = true
  try {
    await aiApi.generateReport({ project_id: project.value.project_id, report_type: type })
    message.success('报告生成成功')
    await fetchProject()
  } catch (e) {
    message.error(e.response?.data?.detail?.message || e.response?.data?.detail || '生成失败')
  } finally {
    loadingTypes.value[type] = false
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
