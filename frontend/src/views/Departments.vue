<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h2>部门管理</h2>
      <p>管理组织架构和部门信息</p>
    </div>

    <div class="page-card">
      <div style="margin-bottom: 16px">
        <a-space>
          <a-button type="primary" @click="showCreate = true">
            <template #icon><PlusOutlined /></template>
            新增部门
          </a-button>
        </a-space>
      </div>
      <a-tree
        v-if="treeData.length"
        :treeData="treeData"
        :show-icon="true"
        :selectable="true"
        @select="onSelect"
        :selectedKeys="selectedKeys"
        :defaultExpandAll="true"
      >
        <template #icon><BankOutlined /></template>
        <template #title="node">
          <a-space>
            <span>{{ node.department_name }}</span>
            <a-tag v-if="!node.is_active" color="red">停用</a-tag>
          </a-space>
        </template>
      </a-tree>
      <a-empty v-else description="暂无部门数据" />
    </div>

    <a-modal v-model:open="showCreate" title="新增部门" @ok="handleCreate" :confirmLoading="loading">
      <a-form :model="form" layout="vertical">
        <a-form-item label="上级部门">
          <a-tree-select
            v-model:value="form.parent_id"
            :treeData="flatTreeData"
            placeholder="选择上级部门（留空为根部门）"
            allowClear
            treeDefaultExpandAll
          />
        </a-form-item>
        <a-form-item label="部门名称" required>
          <a-input v-model:value="form.department_name" placeholder="请输入部门名称" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="form.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showEdit" title="编辑部门" @ok="handleUpdate" :confirmLoading="loading">
      <a-form :model="form" layout="vertical">
        <a-form-item label="上级部门">
          <a-tree-select
            v-model:value="form.parent_id"
            :treeData="flatTreeData.filter(d => d.department_id !== selectedId)"
            placeholder="选择上级部门"
            allowClear
            treeDefaultExpandAll
          />
        </a-form-item>
        <a-form-item label="部门名称" required>
          <a-input v-model:value="form.department_name" placeholder="请输入部门名称" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="form.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="form.is_active" checkedChildren="启用" unCheckedChildren="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { departmentsApi } from '../api'
import { message } from 'ant-design-vue'
import { PlusOutlined, BankOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const treeData = ref([])
const flatList = ref([])
const selectedKeys = ref([])
const selectedId = ref(null)
const showCreate = ref(false)
const showEdit = ref(false)

const form = reactive({
  parent_id: null,
  department_name: '',
  sort_order: 0,
  is_active: true,
})

onMounted(fetchDepartments)

function buildTree(depts, parentId = null) {
  return depts.filter(d => d.parent_id === parentId).map(d => ({
    ...d,
    title: d.department_name,
    key: d.department_id,
    children: buildTree(depts, d.department_id),
  }))
}

async function fetchDepartments() {
  try {
    const { data } = await departmentsApi.list()
    treeData.value = data || []
    const { data: flat } = await departmentsApi.listFlat()
    flatList.value = flat || []
  } catch {
    message.error('获取部门列表失败')
  }
}

const flatTreeData = computed(() => flatList.value.map(d => ({
  ...d,
  title: d.department_name,
  value: d.department_id,
})))

function onSelect(keys) {
  if (keys.length) {
    selectedId.value = keys[0]
    const dept = flatList.value.find(d => d.department_id === keys[0])
    if (dept) {
      Object.assign(form, {
        parent_id: dept.parent_id,
        department_name: dept.department_name,
        sort_order: dept.sort_order,
        is_active: !!dept.is_active,
      })
      showEdit.value = true
    }
  }
}

async function handleCreate() {
  if (!form.department_name) {
    message.error('请输入部门名称')
    return
  }
  loading.value = true
  try {
    await departmentsApi.create(form)
    message.success('创建成功')
    showCreate.value = false
    Object.assign(form, { parent_id: null, department_name: '', sort_order: 0, is_active: true })
    await fetchDepartments()
  } catch {
    message.error('创建失败')
  } finally {
    loading.value = false
  }
}

async function handleUpdate() {
  if (!form.department_name) {
    message.error('请输入部门名称')
    return
  }
  loading.value = true
  try {
    await departmentsApi.update(selectedId.value, form)
    message.success('更新成功')
    showEdit.value = false
    await fetchDepartments()
  } catch {
    message.error('更新失败')
  } finally {
    loading.value = false
  }
}
</script>
