<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>数据字典</h2>
      <p>管理系统配置选项</p>
    </div>

    <a-row :gutter="16">
      <a-col :span="8">
        <div class="page-card">
          <h3 style="margin-bottom: 16px">字典类型</h3>
          <a-button type="primary" block style="margin-bottom: 16px" @click="showTypeModal = true">
            <template #icon><PlusOutlined /></template>
            新增类型
          </a-button>
          <a-list size="small" bordered :dataSource="types" :loading="loadingTypes">
            <template #renderItem="{ item }">
              <a-list-item
                :class="{ 'type-item-active': selectedType === item.dict_type }"
                class="type-item"
                @click="selectType(item.dict_type)"
              >
                {{ item.dict_type }}
              </a-list-item>
            </template>
          </a-list>
        </div>
      </a-col>
      <a-col :span="16">
        <div class="page-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <h3>{{ selectedType || '请选择字典类型' }}</h3>
            <a-button v-if="selectedType" type="primary" @click="showValueModal = true">
              <template #icon><PlusOutlined /></template>
              新增字典值
            </a-button>
          </div>
          <a-table
            v-if="selectedType"
            :dataSource="values"
            :columns="valueColumns"
            :loading="loadingValues"
            rowKey="dict_id"
            :pagination="{ pageSize: 20 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'is_active'">
                <a-tag :color="record.is_active ? 'green' : 'red'">{{ record.is_active ? '启用' : '停用' }}</a-tag>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="editValue(record)">编辑</a-button>
                  <a-popconfirm title="确定删除?" @confirm="deleteValue(record.dict_id)">
                    <a-button type="link" danger size="small">删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
          <a-empty v-else description="请从左侧选择字典类型" />
        </div>
      </a-col>
    </a-row>

    <a-modal v-model:open="showTypeModal" title="新增字典类型" @ok="handleCreateType" :confirmLoading="loading">
      <a-form layout="vertical">
        <a-form-item label="类型代码" required>
          <a-input v-model:value="typeForm.dict_type" placeholder="如: investment_path" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showValueModal" :title="editingValue ? '编辑字典值' : '新增字典值'" @ok="handleSaveValue" :confirmLoading="loading">
      <a-form layout="vertical">
        <a-form-item label="类型" required>
          <a-input v-model:value="valueForm.dict_type" :disabled="!!editingValue" />
        </a-form-item>
        <a-form-item label="显示文本" required>
          <a-input v-model:value="valueForm.dict_label" placeholder="如: 直接投资" />
        </a-form-item>
        <a-form-item label="存储值" required>
          <a-input v-model:value="valueForm.dict_value" placeholder="如: DIRECT" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="valueForm.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="启用状态">
          <a-switch v-model:checked="valueForm.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { dictionariesApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const loadingTypes = ref(false)
const loadingValues = ref(false)
const types = ref([])
const values = ref([])
const selectedType = ref(null)
const showTypeModal = ref(false)
const showValueModal = ref(false)
const editingValue = ref(null)

const typeForm = reactive({ dict_type: '' })
const valueForm = reactive({
  dict_type: '',
  dict_label: '',
  dict_value: '',
  sort_order: 0,
  is_active: true,
})

const valueColumns = [
  { title: '显示文本', dataIndex: 'dict_label' },
  { title: '存储值', dataIndex: 'dict_value' },
  { title: '排序', dataIndex: 'sort_order', width: 80 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '操作', key: 'actions', width: 120 },
]

onMounted(fetchTypes)

async function fetchTypes() {
  loadingTypes.value = true
  try {
    const { data } = await dictionariesApi.listTypes()
    types.value = data || []
  } catch {
    message.error('获取字典类型失败')
  } finally {
    loadingTypes.value = false
  }
}

async function selectType(type) {
  selectedType.value = type
  await fetchValues()
}

async function fetchValues() {
  if (!selectedType.value) return
  loadingValues.value = true
  try {
    const { data } = await dictionariesApi.list({ dict_type: selectedType.value })
    values.value = data || []
  } catch {
    message.error('获取字典值失败')
  } finally {
    loadingValues.value = false
  }
}

async function handleCreateType() {
  if (!typeForm.dict_type) {
    message.error('请输入类型代码')
    return
  }
  loading.value = true
  try {
    await dictionariesApi.create({ ...typeForm, dict_label: typeForm.dict_type, dict_value: typeForm.dict_type })
    message.success('创建成功')
    showTypeModal.value = false
    typeForm.dict_type = ''
    await fetchTypes()
  } catch {
    message.error('创建失败')
  } finally {
    loading.value = false
  }
}

function editValue(record) {
  editingValue.value = record
  Object.assign(valueForm, {
    dict_type: record.dict_type,
    dict_label: record.dict_label,
    dict_value: record.dict_value,
    sort_order: record.sort_order,
    is_active: !!record.is_active,
  })
  showValueModal.value = true
}

async function handleSaveValue() {
  if (!valueForm.dict_label || !valueForm.dict_value) {
    message.error('请填写完整信息')
    return
  }
  loading.value = true
  try {
    if (editingValue.value) {
      await dictionariesApi.update(editingValue.value.dict_id, valueForm)
    } else {
      await dictionariesApi.create(valueForm)
    }
    message.success('保存成功')
    showValueModal.value = false
    editingValue.value = null
    Object.assign(valueForm, { dict_type: selectedType.value, dict_label: '', dict_value: '', sort_order: 0, is_active: true })
    await fetchValues()
  } catch {
    message.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function deleteValue(id) {
  try {
    await dictionariesApi.delete(id)
    message.success('删除成功')
    await fetchValues()
  } catch {
    message.error('删除失败')
  }
}
</script>

<style scoped>
.type-item {
  cursor: pointer;
}
.type-item:hover {
  background: #f5f5f5;
}
.type-item-active {
  background: #e6f7ff;
}
</style>
