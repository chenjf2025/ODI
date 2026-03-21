import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, tenantsApi } from '../api'

export const useUserStore = defineStore('user', () => {
    const user = ref(null)
    const tenant = ref(null)
    const token = ref(localStorage.getItem('token') || '')

    const isLoggedIn = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'ADMIN')
    const isOperator = computed(() => ['ADMIN', 'OPERATOR'].includes(user.value?.role))

    async function login(credentials) {
        const { data } = await authApi.login(credentials)
        token.value = data.access_token
        localStorage.setItem('token', data.access_token)
        await fetchUser()
        return data
    }

    async function register(data) {
        const { data: res } = await authApi.register(data)
        token.value = res.access_token
        localStorage.setItem('token', res.access_token)
        await fetchUser()
        return res
    }

    async function fetchUser() {
        try {
            const { data } = await authApi.getMe()
            user.value = data
            const { data: t } = await tenantsApi.getCurrent()
            tenant.value = t
        } catch {
            logout()
        }
    }

    function logout() {
        token.value = ''
        user.value = null
        tenant.value = null
        localStorage.removeItem('token')
    }

    return { user, tenant, token, isLoggedIn, isAdmin, isOperator, login, register, fetchUser, logout }
})
