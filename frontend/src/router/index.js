import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { public: true },
    },
    {
        path: '/',
        component: () => import('../layouts/MainLayout.vue'),
        children: [
            { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
            { path: 'ai', name: 'AIWorkspace', component: () => import('../views/AIWorkspace.vue') },
            { path: 'projects', name: 'Projects', component: () => import('../views/Projects.vue') },
            { path: 'projects/:id', name: 'ProjectDetail', component: () => import('../views/ProjectDetail.vue') },
            { path: 'entities/domestic', name: 'DomesticEntities', component: () => import('../views/DomesticEntities.vue') },
            { path: 'entities/overseas', name: 'OverseasEntities', component: () => import('../views/OverseasEntities.vue') },
            { path: 'ai/reports', name: 'AIReports', component: () => import('../views/AIReports.vue') },
            { path: 'rules', name: 'Rules', component: () => import('../views/Rules.vue') },
            { path: 'billing', name: 'Billing', component: () => import('../views/Billing.vue') },
            { path: 'departments', name: 'Departments', component: () => import('../views/Departments.vue') },
            { path: 'dictionaries', name: 'Dictionaries', component: () => import('../views/Dictionaries.vue') },
            { path: 'approvals', name: 'Approvals', component: () => import('../views/Approvals.vue') },
            { path: 'remittances', name: 'Remittances', component: () => import('../views/Remittances.vue') },
            { path: 'declarations', name: 'Declarations', component: () => import('../views/Declarations.vue') },
            { path: 'logs', name: 'Logs', component: () => import('../views/Logs.vue') },
            { path: 'sensitive-words', name: 'SensitiveWords', component: () => import('../views/SensitiveWords.vue') },
            { path: 'admin/llm', name: 'LLMConfig', component: () => import('../views/LLMConfig.vue') },
        ],
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    if (!to.meta.public && !token) {
        next('/login')
    } else {
        next()
    }
})

export default router
