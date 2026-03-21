<template>
  <a-layout class="app-layout">
    <a-layout-sider v-model:collapsed="collapsed" :trigger="null" collapsible :width="240">
      <div class="logo-area">
        <div class="logo-icon">ODI</div>
        <span class="logo-text" v-show="!collapsed">智能 ODI 平台</span>
      </div>
      <a-menu theme="dark" mode="inline" :selectedKeys="selectedKeys">
        <a-menu-item key="Dashboard" @click="$router.push('/')">
          <template #icon><DashboardOutlined /></template>
          <span>工作台</span>
        </a-menu-item>
        <a-menu-item key="Projects" @click="$router.push('/projects')">
          <template #icon><ProjectOutlined /></template>
          <span>项目管理</span>
        </a-menu-item>
        <a-sub-menu key="entities">
          <template #icon><BankOutlined /></template>
          <template #title>主体管理</template>
          <a-menu-item key="DomesticEntities" @click="$router.push('/entities/domestic')">境内主体</a-menu-item>
          <a-menu-item key="OverseasEntities" @click="$router.push('/entities/overseas')">境外标的</a-menu-item>
        </a-sub-menu>
        <a-menu-item key="AIReports" @click="$router.push('/ai/reports')">
          <template #icon><RobotOutlined /></template>
          <span>AI 报告</span>
        </a-menu-item>
        <a-menu-item key="Rules" @click="$router.push('/rules')">
          <template #icon><SafetyCertificateOutlined /></template>
          <span>规则管理</span>
        </a-menu-item>
        <a-menu-item key="Billing" @click="$router.push('/billing')">
          <template #icon><WalletOutlined /></template>
          <span>计费中心</span>
        </a-menu-item>
        <a-menu-item key="LLMConfig" v-if="userStore.isAdmin" @click="$router.push('/admin/llm')">
          <template #icon><SettingOutlined /></template>
          <span>系统配置</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header>
        <div style="display:flex;align-items:center;gap:12px">
          <MenuFoldOutlined v-if="!collapsed" @click="collapsed = true" style="font-size:18px;cursor:pointer" />
          <MenuUnfoldOutlined v-else @click="collapsed = false" style="font-size:18px;cursor:pointer" />
        </div>
        <div style="display:flex;align-items:center;gap:16px">
          <a-tag v-if="userStore.tenant" color="blue">
            {{ userStore.tenant.agency_name }}
          </a-tag>
          <a-dropdown>
            <a-space style="cursor:pointer">
              <a-avatar style="background:var(--primary-color)">
                {{ userStore.user?.full_name?.[0] || userStore.user?.username?.[0] || 'U' }}
              </a-avatar>
              <span>{{ userStore.user?.full_name || userStore.user?.username }}</span>
            </a-space>
            <template #overlay>
              <a-menu>
                <a-menu-item>
                  <a-tag :color="roleColor">{{ roleLabel }}</a-tag>
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item @click="handleLogout">
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content>
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  DashboardOutlined, ProjectOutlined, BankOutlined, RobotOutlined,
  SafetyCertificateOutlined, WalletOutlined, SettingOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined, LogoutOutlined
} from '@ant-design/icons-vue'

const collapsed = ref(false)
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const selectedKeys = computed(() => [route.name])

const roleLabel = computed(() => {
  const map = { ADMIN: '超级管理员', OPERATOR: '运营专员', CLIENT_USER: '客户' }
  return map[userStore.user?.role] || userStore.user?.role
})

const roleColor = computed(() => {
  const map = { ADMIN: 'red', OPERATOR: 'blue', CLIENT_USER: 'green' }
  return map[userStore.user?.role] || 'default'
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>
