<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>
    <div class="login-container fade-in-up">
      <div class="login-header">
        <div class="login-logo">ODI</div>
        <h1>智能 ODI 合规平台</h1>
        <p>境外直接投资一站式管控</p>
      </div>

      <a-tabs v-model:activeKey="activeTab" centered>
        <a-tab-pane key="login" tab="登录">
          <a-form :model="loginForm" @finish="handleLogin" layout="vertical">
            <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
              <a-input v-model:value="loginForm.username" placeholder="用户名" size="large" />
            </a-form-item>
            <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
              <a-input-password v-model:value="loginForm.password" placeholder="密码" size="large" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" html-type="submit" block size="large" :loading="loading">
                登 录
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
        <a-tab-pane key="register" tab="注册">
          <a-form :model="registerForm" @finish="handleRegister" layout="vertical">
            <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
              <a-input v-model:value="registerForm.username" placeholder="用户名" size="large" />
            </a-form-item>
            <a-form-item name="email" :rules="[{ required: true, type: 'email', message: '请输入有效邮箱' }]">
              <a-input v-model:value="registerForm.email" placeholder="邮箱" size="large" />
            </a-form-item>
            <a-form-item name="password" :rules="[{ required: true, min: 6, message: '密码至少6位' }]">
              <a-input-password v-model:value="registerForm.password" placeholder="密码" size="large" />
            </a-form-item>
            <a-form-item name="agency_name">
              <a-input v-model:value="registerForm.agency_name" placeholder="机构名称（可选）" size="large" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" html-type="submit" block size="large" :loading="loading">
                注 册
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { message } from 'ant-design-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const activeTab = ref('login')

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', agency_name: '' })

async function handleLogin() {
  loading.value = true
  try {
    await userStore.login(loginForm)
    message.success('登录成功')
    router.push('/')
  } catch (e) {
    message.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  loading.value = true
  try {
    await userStore.register(registerForm)
    message.success('注册成功')
    router.push('/')
  } catch (e) {
    message.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.bg-orb-1 {
  width: 400px; height: 400px;
  background: #1a56db;
  top: -100px; left: -100px;
  animation: float 8s ease-in-out infinite;
}

.bg-orb-2 {
  width: 350px; height: 350px;
  background: #7c3aed;
  bottom: -50px; right: -50px;
  animation: float 10s ease-in-out infinite reverse;
}

.bg-orb-3 {
  width: 200px; height: 200px;
  background: #059669;
  top: 50%; left: 60%;
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-30px) scale(1.05); }
}

.login-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px;
  width: 420px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 64px; height: 64px;
  background: linear-gradient(135deg, #1a56db 0%, #7c3aed 100%);
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 16px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
}

.login-header p {
  color: #64748b;
  font-size: 14px;
}
</style>
