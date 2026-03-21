<template>
  <div class="fade-in-up">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><h2>境外标的管理</h2><p>管理 ODI 投资的境外企业标的信息</p></div>
      <a-button type="primary" @click="showModal = true"><PlusOutlined /> 新增境外标的</a-button>
    </div>
    <div class="page-card">
      <a-table :dataSource="entities" :columns="columns" :loading="loading" rowKey="entity_id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'registered_capital'">{{ record.registered_capital ? Number(record.registered_capital).toLocaleString() + ' ' + record.currency : '-' }}</template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="startEdit(record)">编辑</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.entity_id)">
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
    <a-modal v-model:open="showModal" :title="editId ? '编辑境外标的' : '新增境外标的'" @ok="handleSubmit" :confirmLoading="submitting" :width="640">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="中文名称" required><a-input v-model:value="form.overseas_name_cn" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="英文名称"><a-input v-model:value="form.overseas_name_en" /></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="投资目的国" required><a-input v-model:value="form.target_country" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="行业代码"><a-input v-model:value="form.overseas_industry_code" /></a-form-item></a-col>
          <a-col :span="4"><a-form-item label="注册资本"><a-input-number v-model:value="form.registered_capital" style="width:100%" /></a-form-item></a-col>
          <a-col :span="4"><a-form-item label="币种"><a-select v-model:value="form.currency"><a-select-option value="USD">USD</a-select-option><a-select-option value="HKD">HKD</a-select-option><a-select-option value="SGD">SGD</a-select-option><a-select-option value="EUR">EUR</a-select-option></a-select></a-form-item></a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { entitiesApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const entities = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const editId = ref(null)
const form = reactive({ overseas_name_cn: '', overseas_name_en: '', target_country: '', overseas_industry_code: '', registered_capital: null, currency: 'USD' })

const columns = [
  { title: '中文名称', dataIndex: 'overseas_name_cn', width: 180 },
  { title: '英文名称', dataIndex: 'overseas_name_en', width: 180 },
  { title: '目的国/地区', dataIndex: 'target_country', width: 120 },
  { title: '行业代码', dataIndex: 'overseas_industry_code', width: 100 },
  { title: '注册资本', key: 'registered_capital', width: 150 },
  { title: '操作', key: 'actions', width: 140 },
]

onMounted(fetch)

async function fetch() {
  loading.value = true
  try { const { data } = await entitiesApi.listOverseas(); entities.value = data } catch {} finally { loading.value = false }
}

function startEdit(r) {
  editId.value = r.entity_id
  Object.assign(form, { overseas_name_cn: r.overseas_name_cn, overseas_name_en: r.overseas_name_en, target_country: r.target_country, overseas_industry_code: r.overseas_industry_code, registered_capital: r.registered_capital, currency: r.currency })
  showModal.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editId.value) { await entitiesApi.updateOverseas(editId.value, form); message.success('更新成功') }
    else { await entitiesApi.createOverseas(form); message.success('创建成功') }
    showModal.value = false; editId.value = null
    Object.assign(form, { overseas_name_cn: '', overseas_name_en: '', target_country: '', overseas_industry_code: '', registered_capital: null, currency: 'USD' })
    await fetch()
  } catch (e) { message.error(e.response?.data?.detail || '操作失败') } finally { submitting.value = false }
}

async function handleDelete(id) {
  try { await entitiesApi.deleteOverseas(id); message.success('已删除'); await fetch() } catch { message.error('删除失败') }
}
</script>
