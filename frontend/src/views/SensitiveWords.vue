<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>敏感词管理</h2>
      <p>管理内容安全敏感词库</p>
    </div>

    <div class="page-card">
      <div style="margin-bottom: 16px">
        <a-space>
          <a-select v-model:value="levelFilter" placeholder="按等级筛选" style="width: 150px" allowClear @change="fetchWords">
            <a-select-option value="LOW">低风险</a-select-option>
            <a-select-option value="MEDIUM">中风险</a-select-option>
            <a-select-option value="HIGH">高风险</a-select-option>
            <a-select-option value="FORBIDDEN">禁止</a-select-option>
          </a-select>
          <a-button type="primary" @click="showCreate = true">
            <template #icon><PlusOutlined /></template>
            新增敏感词
          </a-button>
        </a-space>
      </div>

      <a-table
        :dataSource="words"
        :columns="columns"
        :loading="loading"
        rowKey="word_id"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'level'">
            <a-tag :color="levelColor(record.level)">{{ levelName(record.level) }}</a-tag>
          </template>
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'red'">{{ record.is_active ? '启用' : '停用' }}</a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleDateString('zh-CN') }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="editWord(record)">编辑</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.word_id)">
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="showCreate" :title="editingId ? '编辑敏感词' : '新增敏感词'" @ok="handleSave" :confirmLoading="loading">
      <a-form :model="form" layout="vertical">
        <a-form-item label="敏感词" required>
          <a-input v-model:value="form.word" placeholder="请输入敏感词" />
        </a-form-item>
        <a-form-item label="风险等级" required>
          <a-select v-model:value="form.level" placeholder="选择风险等级">
            <a-select-option value="LOW">低风险</a-select-option>
            <a-select-option value="MEDIUM">中风险</a-select-option>
            <a-select-option value="HIGH">高风险</a-select-option>
            <a-select-option value="FORBIDDEN">禁止</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" :rows="2" placeholder="请输入描述" />
        </a-form-item>
        <a-form-item label="启用状态">
          <a-switch v-model:checked="form.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { sensitiveWordsApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const words = ref([])
const levelFilter = ref(null)
const showCreate = ref(false)
const editingId = ref(null)

const form = reactive({
  word: '',
  level: 'LOW',
  description: '',
  is_active: true,
})

const columns = [
  { title: '敏感词', dataIndex: 'word', width: 150 },
  { title: '风险等级', key: 'level', width: 100 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '创建时间', key: 'created_at', width: 120 },
  { title: '操作', key: 'actions', width: 120 },
]

onMounted(fetchWords)

async function fetchWords() {
  loading.value = true
  try {
    const params = {}
    if (levelFilter.value) params.level = levelFilter.value
    const { data } = await sensitiveWordsApi.list(params)
    words.value = data || []
  } catch {
    message.error('获取敏感词列表失败')
  } finally {
    loading.value = false
  }
}

function editWord(record) {
  editingId.value = record.word_id
  Object.assign(form, {
    word: record.word,
    level: record.level,
    description: record.description || '',
    is_active: !!record.is_active,
  })
  showCreate.value = true
}

async function handleSave() {
  if (!form.word || !form.level) {
    message.error('请填写必填项')
    return
  }
  loading.value = true
  try {
    if (editingId.value) {
      await sensitiveWordsApi.update(editingId.value, form)
    } else {
      await sensitiveWordsApi.create(form)
    }
    message.success('保存成功')
    showCreate.value = false
    editingId.value = null
    Object.assign(form, { word: '', level: 'LOW', description: '', is_active: true })
    await fetchWords()
  } catch {
    message.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  try {
    await sensitiveWordsApi.delete(id)
    message.success('删除成功')
    await fetchWords()
  } catch {
    message.error('删除失败')
  }
}

function levelName(l) {
  const map = { LOW: '低风险', MEDIUM: '中风险', HIGH: '高风险', FORBIDDEN: '禁止' }
  return map[l] || l
}
function levelColor(l) {
  const map = { LOW: 'green', MEDIUM: 'orange', HIGH: 'red', FORBIDDEN: 'purple' }
  return map[l] || 'default'
}
</script>
