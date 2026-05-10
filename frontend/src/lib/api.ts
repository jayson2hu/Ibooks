/**
 * API client for backend communication
 */
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Create axios instance
const apiClient = axios.create({
    baseURL: `${API_URL}${API_PREFIX}`,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
    (config) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized - clear token and redirect to login
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                localStorage.removeItem('user_role');

                // Redirect to appropriate login page based on current URL
                const currentPath = window.location.pathname;
                const isAdminRoute = currentPath.startsWith('/admin');
                const loginPath = isAdminRoute ? '/admin/login' : '/login';

                // Only redirect if not already on a login page
                if (currentPath !== loginPath) {
                    window.location.href = loginPath;
                }
            }
        }
        return Promise.reject(error);
    }
);

// API functions

export const api = {
    // Authentication
    auth: {
        register: (data: { email: string; username: string; password: string }) =>
            apiClient.post('/auth/register', data),
        login: (data: { email: string; password: string }) =>
            apiClient.post('/auth/login', data),
        adminLogin: (data: { email: string; password: string }) =>
            apiClient.post('/auth/admin/login', data),
        verifyEmail: (token: string) =>
            apiClient.get(`/auth/verify-email?token=${encodeURIComponent(token)}`),
        forgotPassword: (email: string) =>
            apiClient.post('/auth/forgot-password', { email }),
        resetPassword: (token: string, password: string) =>
            apiClient.post('/auth/reset-password', { token, password }),
        logout: async () => {
            try {
                await apiClient.post('/auth/logout');
            } finally {
                if (typeof window !== 'undefined') {
                    localStorage.removeItem('token');
                    localStorage.removeItem('user_role');
                }
            }
        },
        clearLocalAuth: () => {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                localStorage.removeItem('user_role');
            }
        },
        getMe: () => apiClient.get('/auth/me'),
    },

    // Resources
    resources: {
        list: (params?: {
            page?: number;
            page_size?: number;
            category_id?: number;
            resource_type?: string;
            is_featured?: boolean;
            is_free?: boolean;
            search?: string;
        }) => apiClient.get('/resources', { params }),
        get: (slug: string) => apiClient.get(`/resources/${slug}`),
        getAccess: (slug: string) => apiClient.get(`/resources/${slug}/access`),
        create: (data: any) => apiClient.post('/resources', data),
        update: (id: number, data: any) => apiClient.patch(`/resources/${id}`, data),
        delete: (id: number) => apiClient.delete(`/resources/${id}`),
    },

    // Categories
    categories: {
        list: (activeOnly = true) =>
            apiClient.get('/categories', { params: { active_only: activeOnly } }),
        tree: (activeOnly = true) =>
            apiClient.get('/categories/tree', { params: { active_only: activeOnly } }),
        get: (slug: string) => apiClient.get(`/categories/${slug}`),
        create: (data: any) => apiClient.post('/categories', data),
        update: (id: number, data: any) => apiClient.patch(`/categories/${id}`, data),
        delete: (id: number) => apiClient.delete(`/categories/${id}`),
    },

    // Contacts
    contacts: {
        list: (activeOnly = true) =>
            apiClient.get('/contacts', { params: { active_only: activeOnly } }),
        adminList: () =>
            apiClient.get('/contacts', { params: { active_only: false } }),
        update: (id: number, data: any) => apiClient.patch(`/contacts/${id}`, data),
        delete: (id: number) => apiClient.delete(`/contacts/${id}`),
    },

    // FAQs
    faqs: {
        list: (activeOnly = true, category?: string) =>
            apiClient.get('/faqs', { params: { active_only: activeOnly, category } }),
        get: (id: number) => apiClient.get(`/faqs/${id}`),
        create: (data: any) => apiClient.post('/faqs', data),
        update: (id: number, data: any) => apiClient.patch(`/faqs/${id}`, data),
        delete: (id: number) => apiClient.delete(`/faqs/${id}`),
    },

    // Search
    search: (query: string, page = 1, pageSize = 20) =>
        apiClient.get('/search', {
            params: { q: query, page, page_size: pageSize },
        }),

    // Settings
    settings: {
        getAll: (category?: string) =>
            apiClient.get('/settings', { params: category ? { category } : {} }),
        getAdminSettings: () => apiClient.get('/settings/admin'),
        getGrouped: () => apiClient.get('/settings/grouped'),
        get: (key: string) => apiClient.get(`/settings/${key}`),
        update: (key: string, value: string) =>
            apiClient.put(`/settings/${key}`, { value }),
        batchUpdate: (settings: Array<{ key: string; value: string }>) =>
            apiClient.post('/settings/batch', { settings }),
    },

    // Admin
    admin: {
        getStats: () => apiClient.get('/admin/stats'),
        getUsers: (params?: any) => apiClient.get('/admin/users', { params }),
        updateUser: (id: number, data: any) => apiClient.patch(`/admin/users/${id}`, data),
        getAuditLogs: (params?: any) => apiClient.get('/admin/audit-logs', { params }),
        getWallets: (params?: any) => apiClient.get('/admin/wallets', { params }),
        adjustWallet: (userId: number, data: { amount: number; description?: string }) =>
            apiClient.post(`/admin/wallets/${userId}/adjust`, data),
        getCoinLedger: (params?: any) => apiClient.get('/admin/coin-ledger', { params }),
        getRechargeOrders: (params?: any) => apiClient.get('/admin/recharge-orders', { params }),
        getRechargePackages: (params?: any) => apiClient.get('/admin/recharge-packages', { params }),
        createRechargePackage: (data: any) => apiClient.post('/admin/recharge-packages', data),
        updateRechargePackage: (id: number, data: any) => apiClient.patch(`/admin/recharge-packages/${id}`, data),
        getSigninSettings: () => apiClient.get('/admin/settings/signin'),
        updateSigninSettings: (data: { enabled: boolean; reward_coins: number }) =>
            apiClient.put('/admin/settings/signin', data),
    },

    // Orders
    orders: {
        create: (resourceId: number) => apiClient.post('/orders', { resource_id: resourceId }),
        my: (params?: any) => apiClient.get('/orders/my', { params }),
        list: (params?: any) => apiClient.get('/orders', { params }),
        adminList: (params?: any) => apiClient.get('/orders', { params }),
        get: (orderNo: string) => apiClient.get(`/orders/${orderNo}`),
        cancel: (orderNo: string) => apiClient.patch(`/orders/${orderNo}/cancel`),
    },

    // Wallet
    wallet: {
        me: () => apiClient.get('/wallet/me'),
        ledger: (params?: any) => apiClient.get('/wallet/ledger', { params }),
    },

    // Daily sign-in
    signin: {
        status: () => apiClient.get('/signin/status'),
        claim: () => apiClient.post('/signin'),
    },

    // Recharge
    recharge: {
        packages: () => apiClient.get('/recharge/packages'),
        createOrder: (packageId: number, paymentMethod: 'alipay' | 'wechat' = 'alipay') =>
            apiClient.post('/recharge/orders', { package_id: packageId, payment_method: paymentMethod }),
        myOrders: (params?: any) => apiClient.get('/recharge/orders/my', { params }),
        getOrder: (rechargeNo: string) => apiClient.get(`/recharge/orders/${rechargeNo}`),
        cancelOrder: (rechargeNo: string) => apiClient.patch(`/recharge/orders/${rechargeNo}/cancel`),
        alipayCreate: (rechargeNo: string) =>
            apiClient.post('/recharge/alipay/create', { recharge_no: rechargeNo }),
    },
};

export default apiClient;
