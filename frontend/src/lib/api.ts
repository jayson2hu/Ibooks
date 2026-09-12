/**
 * API client for backend communication
 */
import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import type {
    AdminResourceListParams,
    AdminUserUpdate,
    AlipayCreateResponse,
    ApiError,
    AuditLog,
    Category,
    CategoryCreateInput,
    CategoryUpdateInput,
    CoinLedger,
    Contact,
    CrawlerConfig,
    CrawlerRunResponse,
    CrawlerStatus,
    Order,
    PaginatedResponse,
    RechargeOrder,
    RechargePackage,
    Resource,
    ResourceAccess,
    ResourceAccessCheck,
    SeoGenerationResponse,
    SigninResult,
    SigninStatus,
    SiteSettingsGroup,
    SiteSettingUpdate,
    User,
    Wallet,
} from '@/types';

const publicApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const serverApiUrl = process.env.INTERNAL_API_URL || publicApiUrl;
const API_URL = typeof window === 'undefined' ? serverApiUrl : publicApiUrl;
const API_PREFIX = '/api/v1';
const AUTH_REFRESH_THRESHOLD_MS = 5 * 60 * 1000;
const AUTH_REFRESH_RETRY_DELAY_MS = 30 * 1000;

interface AuthTokenResponse {
    access_token?: string;
    refresh_token?: string;
}

interface AuthenticatedRequestConfig extends InternalAxiosRequestConfig {
    __ibooksAuthToken?: string;
    __ibooksAuthRetry?: boolean;
}

let refreshRequest: Promise<string> | null = null;
let refreshSourceToken: string | null = null;
let refreshRetryAfter = 0;

type QueryParams = Record<string, string | number | boolean | undefined>;

export function getApiErrorDetail(error: unknown): ApiError['detail'] | undefined {
    return axios.isAxiosError<ApiError>(error) ? error.response?.data?.detail : undefined;
}

export function getApiErrorStatus(error: unknown): number | undefined {
    return axios.isAxiosError<ApiError>(error) ? error.response?.status : undefined;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
    const detail = getApiErrorDetail(error);
    if (typeof detail === 'string' && detail) {
        return detail;
    }
    return detail && typeof detail === 'object' && detail.message ? detail.message : fallback;
}

function getTokenExpiryMs(token: string): number | null {
    const payloadPart = token.split('.')[1];
    if (!payloadPart) {
        return null;
    }

    try {
        const normalized = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
        const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
        const payload = JSON.parse(atob(padded)) as { exp?: unknown };
        const expirySeconds = Number(payload.exp);
        return Number.isFinite(expirySeconds) ? expirySeconds * 1000 : null;
    } catch {
        return null;
    }
}

export function shouldRefreshAccessToken(
    token: string,
    now = Date.now(),
    hasRefreshToken = false,
): boolean {
    const expiry = getTokenExpiryMs(token);
    if (expiry === null) {
        return false;
    }
    return expiry <= now ? hasRefreshToken : expiry - now <= AUTH_REFRESH_THRESHOLD_MS;
}

function canRefreshForRequest(url?: string): boolean {
    if (!url) {
        return true;
    }

    return ![
        '/auth/register',
        '/auth/login',
        '/auth/admin/login',
        '/auth/verify-email',
        '/auth/forgot-password',
        '/auth/reset-password',
        '/auth/refresh',
        '/auth/logout',
    ].some((path) => url.startsWith(path));
}

function getReplacementAccessToken(sourceToken: string): string | null {
    if (typeof window === 'undefined') {
        return null;
    }

    const storedToken = localStorage.getItem('token');
    return storedToken && storedToken !== sourceToken ? storedToken : null;
}

function getRequestAccessToken(config?: AuthenticatedRequestConfig): string | null {
    if (config?.__ibooksAuthToken) {
        return config.__ibooksAuthToken;
    }

    const headers = config?.headers as unknown as {
        get?: (name: string) => unknown;
        Authorization?: unknown;
        authorization?: unknown;
    } | undefined;
    const authorization = typeof headers?.get === 'function'
        ? headers.get('Authorization')
        : headers?.Authorization ?? headers?.authorization;

    if (typeof authorization !== 'string' || !authorization.startsWith('Bearer ')) {
        return null;
    }
    return authorization.slice('Bearer '.length);
}

function setRequestAccessToken(config: AuthenticatedRequestConfig, token: string): void {
    config.__ibooksAuthToken = token;
    const authorization = `Bearer ${token}`;
    const headers = config.headers as unknown as {
        set?: (name: string, value: string) => void;
        Authorization?: string;
    };
    if (typeof headers.set === 'function') {
        headers.set('Authorization', authorization);
    } else {
        headers.Authorization = authorization;
    }
}

async function refreshAccessToken(token: string): Promise<string> {
    const replacementToken = getReplacementAccessToken(token);
    if (replacementToken) {
        return replacementToken;
    }

    if (Date.now() < refreshRetryAfter) {
        return token;
    }

    if (refreshRequest) {
        if (refreshSourceToken !== token) {
            return getReplacementAccessToken(token) || token;
        }
        const refreshedToken = await refreshRequest;
        return getReplacementAccessToken(token) || refreshedToken;
    }

    const refreshToken = localStorage.getItem('refresh_token') || token;
    refreshSourceToken = token;
    refreshRequest = axios
        .post<AuthTokenResponse>(
            `${API_URL}${API_PREFIX}/auth/refresh`,
            undefined,
            {
                headers: { Authorization: `Bearer ${refreshToken}` },
                timeout: 10000,
            },
        )
        .then((response) => {
            const refreshedToken = response.data?.access_token;
            if (!refreshedToken) {
                throw new Error('Refresh response did not contain an access token');
            }

            const externallyRefreshedToken = getReplacementAccessToken(token);
            if (externallyRefreshedToken) {
                refreshRetryAfter = 0;
                return externallyRefreshedToken;
            }

            localStorage.setItem('token', refreshedToken);
            if (response.data.refresh_token) {
                localStorage.setItem('refresh_token', response.data.refresh_token);
            }
            refreshRetryAfter = 0;
            return refreshedToken;
        })
        .catch(() => {
            const externallyRefreshedToken = getReplacementAccessToken(token);
            if (externallyRefreshedToken) {
                refreshRetryAfter = 0;
                return externallyRefreshedToken;
            }

            // The current token may still be valid. Let the original request
            // proceed and leave final 401/503 handling to the normal response path.
            refreshRetryAfter = Date.now() + AUTH_REFRESH_RETRY_DELAY_MS;
            return token;
        })
        .finally(() => {
            refreshRequest = null;
            refreshSourceToken = null;
        });

    const refreshedToken = await refreshRequest;
    return getReplacementAccessToken(token) || refreshedToken;
}

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
    async (config) => {
        const authenticatedConfig = config as AuthenticatedRequestConfig;
        let token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        const hasRefreshToken = typeof window !== 'undefined'
            && Boolean(localStorage.getItem('refresh_token'));
        if (
            token
            && canRefreshForRequest(config.url)
            && shouldRefreshAccessToken(token, Date.now(), hasRefreshToken)
        ) {
            token = await refreshAccessToken(token);
        }
        if (token) {
            setRequestAccessToken(authenticatedConfig, token);
        } else {
            authenticatedConfig.__ibooksAuthToken = getRequestAccessToken(authenticatedConfig) || undefined;
        }
        return authenticatedConfig;
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
            if (typeof window !== 'undefined') {
                const requestConfig = error.config as AuthenticatedRequestConfig | undefined;
                const requestToken = getRequestAccessToken(requestConfig);
                const currentToken = localStorage.getItem('token');

                if (
                    requestConfig
                    && requestToken
                    && currentToken
                    && currentToken !== requestToken
                    && !requestConfig.__ibooksAuthRetry
                ) {
                    requestConfig.__ibooksAuthRetry = true;
                    setRequestAccessToken(requestConfig, currentToken);
                    return apiClient.request(requestConfig);
                }

                // Only the credentials actually rejected by this request may be
                // cleared. Another tab may already have rotated the access token.
                if (currentToken !== requestToken) {
                    return Promise.reject(error);
                }

                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
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
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_role');
                }
            }
        },
        clearLocalAuth: () => {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
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
        }) => apiClient.get<PaginatedResponse<Resource>>('/resources', { params }),
        get: (slug: string) => apiClient.get<Resource>(`/resources/${slug}`),
        getAccess: (slug: string) => apiClient.get<ResourceAccessCheck>(`/resources/${slug}/access`),
        recordView: (slug: string) => apiClient.post<void>(`/resources/${slug}/view`),
        download: (slug: string) => apiClient.post<ResourceAccess>(`/resources/${slug}/download`),
        create: (data: object) => apiClient.post('/resources', data),
        update: (id: number, data: object) => apiClient.patch(`/resources/${id}`, data),
        delete: (id: number) => apiClient.delete(`/resources/${id}`),
    },

    // Categories
    categories: {
        list: (activeOnly = true) =>
            apiClient.get<Category[]>('/categories', { params: { active_only: activeOnly } }),
        tree: (activeOnly = true) =>
            apiClient.get('/categories/tree', { params: { active_only: activeOnly } }),
        get: (slug: string) => apiClient.get<Category>(`/categories/${slug}`),
        create: (data: CategoryCreateInput) => apiClient.post<Category>('/categories', data),
        update: (id: number, data: CategoryUpdateInput) => apiClient.patch<Category>(`/categories/${id}`, data),
        delete: (id: number) => apiClient.delete(`/categories/${id}`),
    },

    // Contacts
    contacts: {
        list: (activeOnly = true) =>
            apiClient.get<Contact[]>('/contacts', { params: { active_only: activeOnly } }),
        adminList: () =>
            apiClient.get<Contact[]>('/contacts', { params: { active_only: false } }),
        create: (data: object) => apiClient.post<Contact>('/contacts', data),
        update: (id: number, data: object) => apiClient.patch<Contact>(`/contacts/${id}`, data),
        delete: (id: number) => apiClient.delete(`/contacts/${id}`),
    },

    // FAQs
    faqs: {
        list: (activeOnly = true, category?: string) =>
            apiClient.get('/faqs', { params: { active_only: activeOnly, category } }),
        get: (id: number) => apiClient.get(`/faqs/${id}`),
        create: (data: object) => apiClient.post('/faqs', data),
        update: (id: number, data: object) => apiClient.patch(`/faqs/${id}`, data),
        delete: (id: number) => apiClient.delete(`/faqs/${id}`),
    },

    // Search
    search: (
        query: string,
        page = 1,
        pageSize = 20,
        scope: 'all' | 'course' | 'ebook' | 'doc' = 'all',
    ) =>
        apiClient.get<PaginatedResponse<Resource>>('/search', {
            params: { q: query, scope, page, page_size: pageSize },
        }),

    // Settings
    settings: {
        getAll: (category?: string) =>
            apiClient.get('/settings', { params: category ? { category } : {} }),
        getAdminSettings: () => apiClient.get('/settings/admin'),
        getGrouped: () => apiClient.get<SiteSettingsGroup[]>('/settings/grouped'),
        get: (key: string) => apiClient.get(`/settings/${key}`),
        update: (key: string, value: string) =>
            apiClient.put(`/settings/${key}`, { value }),
        batchUpdate: (settings: SiteSettingUpdate[]) =>
            apiClient.post('/settings/batch', { settings }),
        testEmail: () => apiClient.post<{ message: string }>('/settings/test-email'),
    },

    // SEO
    seo: {
        generateAll: () => apiClient.post<SeoGenerationResponse>(
            '/seo/generate-all',
            undefined,
            { timeout: 60000 },
        ),
        submitBaidu: (urls: string[]) => apiClient.post('/seo/submit-baidu', { urls }),
    },

    // Crawler administration
    crawler: {
        status: () => apiClient.get<CrawlerStatus>('/crawler/1024/status'),
        getConfig: () => apiClient.get<CrawlerConfig>('/crawler/1024/config'),
        updateConfig: (config: CrawlerConfig) =>
            apiClient.put<CrawlerConfig>('/crawler/1024/config', config),
        run: () => apiClient.post<CrawlerRunResponse>('/crawler/1024/run'),
    },

    // Admin
    admin: {
        getStats: () => apiClient.get('/admin/stats'),
        getResources: (params?: AdminResourceListParams) =>
            apiClient.get<PaginatedResponse<Resource>>('/admin/resources', { params }),
        getResource: (id: number) => apiClient.get(`/admin/resources/${id}`),
        getUsers: (params?: QueryParams) => apiClient.get<PaginatedResponse<User>>('/admin/users', { params }),
        updateUser: (id: number, data: AdminUserUpdate) => apiClient.patch<User>(`/admin/users/${id}`, data),
        getAuditLogs: (params?: QueryParams) => apiClient.get<PaginatedResponse<AuditLog>>('/admin/audit-logs', { params }),
        getWallets: (params?: QueryParams) => apiClient.get('/admin/wallets', { params }),
        adjustWallet: (userId: number, data: { amount: number; description?: string }) =>
            apiClient.post(`/admin/wallets/${userId}/adjust`, data),
        getCoinLedger: (params?: QueryParams) => apiClient.get('/admin/coin-ledger', { params }),
        getRechargeOrders: (params?: QueryParams) => apiClient.get('/admin/recharge-orders', { params }),
        getRechargePackages: (params?: QueryParams) => apiClient.get<RechargePackage[]>('/admin/recharge-packages', { params }),
        createRechargePackage: (data: object) => apiClient.post<RechargePackage>('/admin/recharge-packages', data),
        updateRechargePackage: (id: number, data: object) => apiClient.patch<RechargePackage>(`/admin/recharge-packages/${id}`, data),
        getSigninSettings: () => apiClient.get('/admin/settings/signin'),
        updateSigninSettings: (data: { enabled: boolean; reward_coins: number }) =>
            apiClient.put('/admin/settings/signin', data),
    },

    // Orders
    orders: {
        create: (resourceId: number) => apiClient.post<Order>('/orders', { resource_id: resourceId }),
        my: (params?: QueryParams) => apiClient.get<PaginatedResponse<Order>>('/orders/my', { params }),
        list: (params?: QueryParams) => apiClient.get<PaginatedResponse<Order>>('/orders', { params }),
        adminList: (params?: QueryParams) => apiClient.get<PaginatedResponse<Order>>('/orders', { params }),
        get: (orderNo: string) => apiClient.get<Order>(`/orders/${orderNo}`),
        cancel: (orderNo: string) => apiClient.patch<Order>(`/orders/${orderNo}/cancel`),
    },

    // Wallet
    wallet: {
        me: () => apiClient.get<Wallet>('/wallet/me'),
        ledger: (params?: QueryParams) => apiClient.get<PaginatedResponse<CoinLedger>>('/wallet/ledger', { params }),
    },

    // Daily sign-in
    signin: {
        status: () => apiClient.get<SigninStatus>('/signin/status'),
        claim: () => apiClient.post<SigninResult>('/signin'),
    },

    // Recharge
    recharge: {
        packages: () => apiClient.get<RechargePackage[]>('/recharge/packages'),
        createOrder: (packageId: number) =>
            apiClient.post<RechargeOrder>('/recharge/orders', { package_id: packageId, payment_method: 'alipay' }),
        myOrders: (params?: QueryParams) => apiClient.get<PaginatedResponse<RechargeOrder>>('/recharge/orders/my', { params }),
        getOrder: (rechargeNo: string) => apiClient.get<RechargeOrder>(`/recharge/orders/${rechargeNo}`),
        cancelOrder: (rechargeNo: string) => apiClient.patch<RechargeOrder>(`/recharge/orders/${rechargeNo}/cancel`),
        alipayCreate: (rechargeNo: string) =>
            apiClient.post<AlipayCreateResponse>('/recharge/alipay/create', { recharge_no: rechargeNo }),
    },
};

export default apiClient;
