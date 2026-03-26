<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>系统日志</h2>
      <p>查看操作日志和登录记录</p>
    </div>

    <div class="page-card">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="system" tab="操作日志" />
        <a-tab-pane key="login" tab="登录日志" />
      </a-tabs>

      <a-table
        v-if="activeTab === 'system'"
        :dataSource="systemLogs"
        :columns="systemColumns"
        :loading="loading"
        rowKey="log_id"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleString('zh-CN') }}
          </template>
        </template>
      </a-table>

      <a-table
        v-else
        :dataSource="loginLogs"
        :columns="loginColumns"
        :loading="loading"
        rowKey="log_id"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'login_status'">
            <a-tag :color="record.login_status === 'SUCCESS' ? 'green' : 'red'">
              {{ record.login_status === 'SUCCESS' ? '成功' : '失败' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleString('zh-CN') }}
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { logsApi } from '../api'
import { message } from 'ant-design-vue'

const loading = ref(false)
const activeTab = ref('system')
const systemLogs = ref([])
const loginLogs = ref([])

const systemColumns = [
  { title: '用户', dataIndex: 'operator_name', width: 120 },
  { title: '操作', dataIndex: 'action', width: 120 },
  { title: '资源', dataIndex: 'resource', width: 150 },
  { title: '详情', dataIndex: 'detail', ellipsis: true },
  { title: 'IP地址', dataIndex: 'ip_address', width: 140 },
  { title: '时间', key: 'created_at', width: 180 },
]

const loginColumns = [
  { title: '用户名', dataIndex: 'username', width: 150 },
  { title: '登录状态', key: 'login_status', width: 100 },
  { title: 'IP地址', dataIndex: 'ip_address', width: 140 },
  { title: 'User-Agent', dataIndex: 'user_agent', ellipsis: true },
  { title: '时间', key: 'created_at', width: 180 },
]

onMounted(fetchLogs)

async function fetchLogs() {
  loading.value = true
  try {
    if (activeTab.value === 'system') {
      const { data } = await logsApi.listSystemLogs({ page_size: 100 })
      systemLogs.value = data || []
    } else {
      const { data } = await logsApi.listLoginLogs({ page_size: 100 })
      loginLogs.value = data || []
    }
  } catch {
    message.error('获取日志失败')
  } finally {
    loading.value = false
  }
}
</script>
