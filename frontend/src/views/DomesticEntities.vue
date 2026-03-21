<template>
  <div class="fade-in-up">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><h2>境内主体管理</h2><p>管理参与 ODI 投资的境内企业信息</p></div>
      <a-button type="primary" @click="showModal = true"><PlusOutlined /> 新增境内主体</a-button>
    </div>
    <div class="page-card">
      <a-table :dataSource="entities" :columns="columns" :loading="loading" rowKey="entity_id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'net_assets'">{{ record.net_assets ? Number(record.net_assets).toLocaleString() + ' 元' : '-' }}</template>
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
    <a-modal v-model:open="showModal" :title="editId ? '编辑境内主体' : '新增境内主体'" @ok="handleSubmit" :confirmLoading="submitting" :width="640">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="企业名称" required><a-input v-model:value="form.company_name" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="统一信用代码" required><a-input v-model:value="form.uscc" /></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="行业代码"><a-input v-model:value="form.industry_code" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="净资产(元)"><a-input-number v-model:value="form.net_assets" style="width:100%" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="净利润(元)"><a-input-number v-model:value="form.net_profit" style="width:100%" /></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="法定代表人"><a-input v-model:value="form.legal_representative" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="注册地址"><a-input v-model:value="form.registered_address" /></a-form-item></a-col>
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
const form = reactive({ company_name: '', uscc: '', industry_code: '', net_assets: null, net_profit: null, legal_representative: '', registered_address: '' })

const columns = [
  { title: '企业名称', dataIndex: 'company_name', width: 200 },
  { title: '统一信用代码', dataIndex: 'uscc', width: 200 },
  { title: '行业代码', dataIndex: 'industry_code', width: 100 },
  { title: '净资产', key: 'net_assets', width: 150 },
  { title: '法定代表人', dataIndex: 'legal_representative', width: 100 },
  { title: '操作', key: 'actions', width: 140 },
]

onMounted(fetch)

async function fetch() {
  loading.value = true
  try { const { data } = await entitiesApi.listDomestic(); entities.value = data } catch {} finally { loading.value = false }
}

function startEdit(r) {
  editId.value = r.entity_id
  Object.assign(form, { company_name: r.company_name, uscc: r.uscc, industry_code: r.industry_code, net_assets: r.net_assets, net_profit: r.net_profit, legal_representative: r.legal_representative, registered_address: r.registered_address })
  showModal.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editId.value) { await entitiesApi.updateDomestic(editId.value, form); message.success('更新成功') }
    else { await entitiesApi.createDomestic(form); message.success('创建成功') }
    showModal.value = false; editId.value = null
    Object.assign(form, { company_name: '', uscc: '', industry_code: '', net_assets: null, net_profit: null, legal_representative: '', registered_address: '' })
    await fetch()
  } catch (e) { message.error(e.response?.data?.detail || '操作失败') } finally { submitting.value = false }
}

async function handleDelete(id) {
  try { await entitiesApi.deleteDomestic(id); message.success('已删除'); await fetch() } catch { message.error('删除失败') }
}
</script>
