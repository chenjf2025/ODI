import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 120000,
})

// 请求拦截器 - 添加 Token
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// 响应拦截器 - 处理 401
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// ===== Auth =====
export const authApi = {
    login: data => api.post('/auth/login', data),
    register: data => api.post('/auth/register', data),
    getMe: () => api.get('/auth/me'),
}

// ===== Projects =====
export const projectsApi = {
    list: (params) => api.get('/projects', { params }),
    get: id => api.get(`/projects/${id}`),
    create: data => api.post('/projects', data),
    updateStatus: (id, data) => api.put(`/projects/${id}/status`, data),
    delete: id => api.delete(`/projects/${id}`),
    // 项目文档
    getDocuments: (projectId) => api.get(`/projects/${projectId}/documents`),
    uploadDocument: (projectId, data) => api.post(`/projects/${projectId}/documents`, data),
    deleteDocument: (projectId, documentId) => api.delete(`/projects/${projectId}/documents/${documentId}`),
}

// ===== Entities =====
export const entitiesApi = {
    listDomestic: () => api.get('/entities/domestic'),
    createDomestic: data => api.post('/entities/domestic', data),
    updateDomestic: (id, data) => api.put(`/entities/domestic/${id}`, data),
    deleteDomestic: id => api.delete(`/entities/domestic/${id}`),
    listOverseas: () => api.get('/entities/overseas'),
    createOverseas: data => api.post('/entities/overseas', data),
    updateOverseas: (id, data) => api.put(`/entities/overseas/${id}`, data),
    deleteOverseas: id => api.delete(`/entities/overseas/${id}`),
}

// ===== AI =====
export const aiApi = {
    preReview: data => api.post('/ai/pre-review', data),
    generateReport: data => api.post('/ai/generate-report', data),
    extractFinancial: data => api.post('/ai/extract-financial', data),
    chat: data => api.post('/ai/chat', data),
    chatStream: (data, { onChunk, onDone, onError }) => {
        const token = localStorage.getItem('token')
        return fetch('/api/ai/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : '',
            },
            body: JSON.stringify(data),
        }).then(resp => {
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`)
            }
            const reader = resp.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        if (buffer) {
                            try {
                                const parsed = JSON.parse(buffer)
                                if (parsed.type === 'error') {
                                    onError && onError(parsed.content)
                                }
                            } catch {}
                        }
                        onDone && onDone()
                        return
                    }
                    buffer += decoder.decode(value, { stream: true })
                    const lines = buffer.split('\n')
                    buffer = lines.pop()
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6))
                                if (data.type === 'chunk') {
                                    onChunk && onChunk(data.content)
                                } else if (data.type === 'error') {
                                    onError && onError(data.content)
                                } else if (data.type === 'done') {
                                    onDone && onDone()
                                }
                            } catch {}
                        }
                    }
                    read()
                })
            }
            read()
        })
    },
}

// ===== AI Conversations =====
export const conversationsApi = {
    list: () => api.get('/ai/conversations'),
    get: (sessionId) => api.get(`/ai/conversations/${sessionId}`),
    submitFeedback: (sessionId, data) => api.post(`/ai/conversations/${sessionId}/feedback`, data),
    delete: (sessionId) => api.delete(`/ai/conversations/${sessionId}`),
}

// ===== Rules =====
export const rulesApi = {
    list: (params) => api.get('/rules', { params }),
    get: id => api.get(`/rules/${id}`),
    create: data => api.post('/rules', data),
    update: (id, data) => api.put(`/rules/${id}`, data),
    delete: id => api.delete(`/rules/${id}`),
}

// ===== Tenants =====
export const tenantsApi = {
    getCurrent: () => api.get('/tenants/current'),
    update: data => api.put('/tenants/current', data),
    topup: data => api.post('/tenants/topup', data),
    getBillingLogs: (params) => api.get('/tenants/billing-logs', { params }),
}

// ===== Admin =====
export const adminApi = {
    listLLMConfigs: () => api.get('/admin/llm-configs'),
    createLLMConfig: data => api.post('/admin/llm-configs', data),
    updateLLMConfig: (id, data) => api.put(`/admin/llm-configs/${id}`, data),
    deleteLLMConfig: id => api.delete(`/admin/llm-configs/${id}`),
}

// ===== Export =====
export const exportApi = {
    ndrcXml: id => api.get(`/export/${id}/ndrc-xml`, { responseType: 'blob' }),
    mofcomExcel: id => api.get(`/export/${id}/mofcom-excel`, { responseType: 'blob' }),
    package: (id, type = 'all') => api.get(`/export/${id}/package`, { params: { export_type: type }, responseType: 'blob' }),
}

// ===== Upload =====
export const uploadApi = {
    uploadFile: file => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    }
}

export default api
