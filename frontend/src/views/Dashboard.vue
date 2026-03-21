<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>工作台</h2>
      <p>欢迎回来, {{ userStore.user?.full_name || userStore.user?.username }}！以下是您的业务概览。</p>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="[16, 16]" style="margin-bottom: 24px">
      <a-col :xs="24" :sm="12" :lg="6" v-for="(stat, i) in stats" :key="i">
        <div class="stat-card">
          <div class="stat-icon" :style="{ background: stat.bg, color: stat.color }">
            <component :is="stat.icon" />
          </div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]">
      <!-- 项目状态分布 -->
      <a-col :xs="24" :lg="14">
        <div class="page-card">
          <h3 style="margin-bottom: 16px; font-weight: 600">项目状态分布</h3>
          <div v-if="statusStats.length" style="display: flex; flex-direction: column; gap: 12px">
            <div v-for="s in statusStats" :key="s.status" style="display: flex; align-items: center; gap: 12px">
              <span style="width: 140px; font-size: 13px; color: var(--text-secondary)">{{ statusName(s.status) }}</span>
              <a-progress :percent="s.percent" :strokeColor="statusColor(s.status)" :showInfo="false" style="flex: 1" />
              <span style="width: 40px; text-align: right; font-weight: 600">{{ s.count }}</span>
            </div>
          </div>
          <a-empty v-else description="暂无项目数据" />
        </div>
      </a-col>

      <!-- 快捷操作 -->
      <a-col :xs="24" :lg="10">
        <div class="page-card">
          <h3 style="margin-bottom: 16px; font-weight: 600">快捷操作</h3>
          <a-space direction="vertical" style="width: 100%" :size="12">
            <a-button type="primary" block size="large" @click="$router.push('/projects')">
              <template #icon><PlusOutlined /></template>
              新建 ODI 项目
            </a-button>
            <a-button block size="large" @click="$router.push('/entities/domestic')">
              <template #icon><BankOutlined /></template>
              管理境内主体
            </a-button>
            <a-button block size="large" @click="$router.push('/ai/reports')">
              <template #icon><RobotOutlined /></template>
              AI 报告生成
            </a-button>
            <a-button block size="large" @click="$router.push('/billing')">
              <template #icon><WalletOutlined /></template>
              查看计费详情
            </a-button>
          </a-space>
        </div>

        <!-- 账户信息 -->
        <div class="page-card" style="margin-top: 16px">
          <h3 style="margin-bottom: 16px; font-weight: 600">账户信息</h3>
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="机构名称">{{ userStore.tenant?.agency_name }}</a-descriptions-item>
            <a-descriptions-item label="订阅计划">
              <a-tag :color="userStore.tenant?.subscription_plan === 'ANNUAL' ? 'gold' : 'default'">
                {{ userStore.tenant?.subscription_plan === 'ANNUAL' ? '年费会员' : '基础版' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="剩余点数">
              <span style="font-weight: 700; font-size: 18px; color: var(--primary-color)">
                {{ userStore.tenant?.balance_credits || 0 }}
              </span>
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { projectsApi } from '../api'
import { PlusOutlined, BankOutlined, RobotOutlined, WalletOutlined } from '@ant-design/icons-vue'

const userStore = useUserStore()
const projects = ref([])

const STATUS_LIST = [
  'PRE_REVIEW', 'DATA_COLLECTION', 'NDRC_FILING_PENDING', 'NDRC_APPROVED',
  'MOFCOM_FILING_PENDING', 'MOFCOM_APPROVED', 'BANK_REG_PENDING', 'FUNDS_REMITTED', 'POST_INVESTMENT'
]

onMounted(async () => {
  try {
    const { data } = await projectsApi.list({ page: 1, page_size: 200 })
    projects.value = data.items || []
  } catch {}
})

const stats = computed(() => {
  const total = projects.value.length
  const active = projects.value.filter(p => !['FUNDS_REMITTED', 'POST_INVESTMENT'].includes(p.status)).length
  return [
    { label: '项目总数', value: total, icon: 'ProjectOutlined', bg: '#dbeafe', color: '#1a56db' },
    { label: '进行中', value: active, icon: 'ThunderboltOutlined', bg: '#d1fae5', color: '#059669' },
    { label: '剩余点数', value: userStore.tenant?.balance_credits || 0, icon: 'WalletOutlined', bg: '#fef3c7', color: '#d97706' },
    { label: '已完成', value: total - active, icon: 'CheckCircleOutlined', bg: '#ede9fe', color: '#7c3aed' },
  ]
})

const statusStats = computed(() => {
  const countMap = {}
  projects.value.forEach(p => { countMap[p.status] = (countMap[p.status] || 0) + 1 })
  const total = projects.value.length || 1
  return STATUS_LIST.filter(s => countMap[s]).map(s => ({
    status: s, count: countMap[s], percent: Math.round((countMap[s] / total) * 100)
  }))
})

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
    PRE_REVIEW: '#1a56db', DATA_COLLECTION: '#0284c7', NDRC_FILING_PENDING: '#7c3aed',
    NDRC_APPROVED: '#059669', MOFCOM_FILING_PENDING: '#d97706', MOFCOM_APPROVED: '#059669',
    BANK_REG_PENDING: '#0284c7', FUNDS_REMITTED: '#059669', POST_INVESTMENT: '#64748b',
  }
  return map[s] || '#94a3b8'
}
</script>
