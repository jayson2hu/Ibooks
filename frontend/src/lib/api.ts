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
        logout: () => {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
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
        getAuditLogs: (params?: any) => apiClient.get('/admin/audit-logs', { params }),
    },
};

export default apiClient;
