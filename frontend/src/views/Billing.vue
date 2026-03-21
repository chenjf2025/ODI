<template>
  <div class="fade-in-up">
    <div class="page-header"><h2>计费中心</h2><p>查看账户余额、充值记录和消费明细</p></div>

    <a-row :gutter="[16, 16]" style="margin-bottom: 24px">
      <a-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-icon" style="background: #dbeafe; color: #1a56db">💰</div>
          <div class="stat-value">{{ userStore.tenant?.balance_credits || 0 }}</div>
          <div class="stat-label">当前点数余额</div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-icon" style="background: #fef3c7; color: #d97706">📋</div>
          <div class="stat-value">{{ userStore.tenant?.subscription_plan === 'ANNUAL' ? '年费会员' : '按件计费' }}</div>
          <div class="stat-label">订阅计划</div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="8">
        <div class="stat-card" style="cursor: pointer" @click="showTopup = true">
          <div class="stat-icon" style="background: #d1fae5; color: #059669">➕</div>
          <div class="stat-value" style="font-size: 18px">点击充值</div>
          <div class="stat-label">充值点数</div>
        </div>
      </a-col>
    </a-row>

    <div class="page-card">
      <h3 style="margin-bottom: 16px; font-weight: 600">消费记录</h3>
      <a-table :dataSource="logs" :columns="columns" :loading="loading" rowKey="transaction_id" :pagination="{ pageSize: 20 }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'billing_type'">
            <a-tag :color="typeColor(record.billing_type)">{{ typeName(record.billing_type) }}</a-tag>
          </template>
          <template v-if="column.key === 'credits_changed'">
            <span :style="{ color: record.credits_changed >= 0 ? '#059669' : '#dc2626', fontWeight: 600 }">
              {{ record.credits_changed >= 0 ? '+' : '' }}{{ record.credits_changed }}
            </span>
          </template>
          <template v-if="column.key === 'created_at'">{{ new Date(record.created_at).toLocaleString('zh-CN') }}</template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="showTopup" title="充值点数" @ok="handleTopup" :confirmLoading="topping">
      <a-form layout="vertical">
        <a-form-item label="充值点数">
          <a-input-number v-model:value="topupCredits" :min="1" :max="9999" style="width: 100%" />
        </a-form-item>
        <a-form-item label="备注"><a-input v-model:value="topupRemark" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tenantsApi } from '../api'
import { useUserStore } from '../stores/user'
import { message } from 'ant-design-vue'

const userStore = useUserStore()
const logs = ref([])
const loading = ref(false)
const showTopup = ref(false)
const topping = ref(false)
const topupCredits = ref(10)
const topupRemark = ref('')

const columns = [
  { title: '类型', key: 'billing_type', width: 120 },
  { title: '点数变动', key: 'credits_changed', width: 100 },
  { title: '变后余额', dataIndex: 'balance_after', width: 100 },
  { title: '备注', dataIndex: 'remark', ellipsis: true },
  { title: '时间', key: 'created_at', width: 180 },
]

onMounted(fetch)

async function fetch() {
  loading.value = true
  try { const { data } = await tenantsApi.getBillingLogs({ page: 1, page_size: 100 }); logs.value = data } catch {} finally { loading.value = false }
}

async function handleTopup() {
  topping.value = true
  try {
    await tenantsApi.topup({ credits: topupCredits.value, remark: topupRemark.value || '手动充值' })
    message.success('充值成功')
    showTopup.value = false
    await userStore.fetchUser()
    await fetch()
  } catch (e) { message.error('充值失败') } finally { topping.value = false }
}

function typeName(t) {
  const map = { PROJECT_DEDUCTION: '项目扣点', ANNUAL_RENEWAL: '年费续费', CREDIT_TOPUP: '点数充值' }
  return map[t] || t
}
function typeColor(t) {
  const map = { PROJECT_DEDUCTION: 'red', ANNUAL_RENEWAL: 'gold', CREDIT_TOPUP: 'green' }
  return map[t] || 'default'
}
</script>
