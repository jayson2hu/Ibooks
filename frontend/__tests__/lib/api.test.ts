const requestUse = jest.fn();
const responseUse = jest.fn();
const axiosPost = jest.fn();
const client = {
    interceptors: {
        request: { use: requestUse },
        response: { use: responseUse },
    },
    get: jest.fn(),
    post: jest.fn(),
    request: jest.fn(),
    patch: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
};

jest.mock('axios', () => ({
    __esModule: true,
    default: {
        create: jest.fn(() => client),
        post: axiosPost,
        isAxiosError: jest.fn(() => false),
    },
}));

function createToken(expirySeconds: number): string {
    const payload = btoa(JSON.stringify({ exp: expirySeconds }))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
    return `header.${payload}.signature`;
}

describe('API 401 handling', () => {
    beforeEach(() => {
        jest.resetModules();
        requestUse.mockClear();
        responseUse.mockClear();
        axiosPost.mockReset();
        client.get.mockClear();
        client.post.mockClear();
        client.request.mockReset();
        client.put.mockClear();
        localStorage.clear();
        window.history.replaceState({}, '', '/login');
    });

    it('clears local authentication for unauthorized responses', async () => {
        localStorage.setItem('token', 'expired');
        localStorage.setItem('refresh_token', 'refresh-token');
        localStorage.setItem('user_role', 'admin');
        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const rejected = responseUse.mock.calls[0][1];
        const config = await addAuthentication({ url: '/resources', headers: {} });

        await expect(rejected({ response: { status: 401 }, config })).rejects.toBeDefined();
        expect(localStorage.getItem('token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();
        expect(localStorage.getItem('user_role')).toBeNull();
    });

    it('uses dedicated crawler configuration endpoints', async () => {
        const { api } = await import('@/lib/api');
        const config = {
            enabled: true,
            interval_minutes: 60,
            max_pages: 3,
            request_timeout_seconds: 20,
            target_category_id: null,
            enabled_fields: ['excerpt', 'tags'],
        };

        await api.crawler.getConfig();
        await api.crawler.updateConfig(config);

        expect(client.get).toHaveBeenCalledWith('/crawler/1024/config');
        expect(client.put).toHaveBeenCalledWith('/crawler/1024/config', config);
    });

    it('uses the dedicated administrator SMTP test endpoint', async () => {
        const { api } = await import('@/lib/api');

        await api.settings.testEmail();

        expect(client.post).toHaveBeenCalledWith('/settings/test-email');
    });

    it('separates resource permission checks from view and download actions', async () => {
        const { api } = await import('@/lib/api');

        await api.resources.getAccess('book');
        await api.resources.recordView('book');
        await api.resources.download('book');

        expect(client.get).toHaveBeenCalledWith('/resources/book/access');
        expect(client.post).toHaveBeenCalledWith('/resources/book/view');
        expect(client.post).toHaveBeenCalledWith('/resources/book/download');
    });

    it('refreshes a token near expiry before sending an authenticated request', async () => {
        const nowSeconds = Math.floor(Date.now() / 1000);
        localStorage.setItem('token', createToken(nowSeconds + 60));
        localStorage.setItem('refresh_token', 'current-refresh-token');
        axiosPost.mockResolvedValue({
            data: {
                access_token: 'refreshed-token',
                refresh_token: 'rotated-refresh-token',
            },
        });

        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const config = await addAuthentication({ url: '/resources', headers: {} });

        expect(axiosPost).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/auth/refresh',
            undefined,
            {
                headers: { Authorization: 'Bearer current-refresh-token' },
                timeout: 10000,
            },
        );
        expect(localStorage.getItem('token')).toBe('refreshed-token');
        expect(localStorage.getItem('refresh_token')).toBe('rotated-refresh-token');
        expect(config.headers.Authorization).toBe('Bearer refreshed-token');
    });

    it('does not refresh a token with substantial lifetime remaining', async () => {
        const nowSeconds = Math.floor(Date.now() / 1000);
        const token = createToken(nowSeconds + 30 * 60);
        localStorage.setItem('token', token);

        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const config = await addAuthentication({ url: '/resources', headers: {} });

        expect(axiosPost).not.toHaveBeenCalled();
        expect(config.headers.Authorization).toBe(`Bearer ${token}`);
    });

    it('uses a refresh token after the access token has expired', async () => {
        const nowSeconds = Math.floor(Date.now() / 1000);
        localStorage.setItem('token', createToken(nowSeconds - 60));
        localStorage.setItem('refresh_token', 'still-valid-refresh-token');
        axiosPost.mockResolvedValue({
            data: {
                access_token: 'recovered-access-token',
                refresh_token: 'rotated-after-expiry',
            },
        });

        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const config = await addAuthentication({ url: '/resources', headers: {} });

        expect(axiosPost).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/auth/refresh',
            undefined,
            {
                headers: { Authorization: 'Bearer still-valid-refresh-token' },
                timeout: 10000,
            },
        );
        expect(config.headers.Authorization).toBe('Bearer recovered-access-token');
    });

    it('shares one refresh request across concurrent API calls', async () => {
        const nowSeconds = Math.floor(Date.now() / 1000);
        localStorage.setItem('token', createToken(nowSeconds + 60));
        let resolveRefresh: ((value: { data: { access_token: string } }) => void) | undefined;
        axiosPost.mockImplementation(() => new Promise((resolve) => {
            resolveRefresh = resolve;
        }));

        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const firstRequest = addAuthentication({ url: '/resources', headers: {} });
        const secondRequest = addAuthentication({ url: '/orders', headers: {} });

        expect(axiosPost).toHaveBeenCalledTimes(1);
        resolveRefresh?.({ data: { access_token: 'shared-token' } });
        const [firstConfig, secondConfig] = await Promise.all([firstRequest, secondRequest]);

        expect(firstConfig.headers.Authorization).toBe('Bearer shared-token');
        expect(secondConfig.headers.Authorization).toBe('Bearer shared-token');
    });

    it('retries a stale 401 once with an access token written by another tab', async () => {
        localStorage.setItem('token', 'stale-token');
        localStorage.setItem('refresh_token', 'current-refresh-token');
        localStorage.setItem('user_role', 'admin');
        client.request.mockResolvedValue({ data: 'recovered' });

        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const rejected = responseUse.mock.calls[0][1];
        const config = await addAuthentication({ url: '/resources', headers: {} });

        localStorage.setItem('token', 'externally-refreshed-token');
        const recovered = await rejected({ response: { status: 401 }, config });

        expect(recovered).toEqual({ data: 'recovered' });
        expect(client.request).toHaveBeenCalledTimes(1);
        expect(client.request).toHaveBeenCalledWith(config);
        expect(config.headers.Authorization).toBe('Bearer externally-refreshed-token');
        expect(localStorage.getItem('token')).toBe('externally-refreshed-token');
        expect(localStorage.getItem('refresh_token')).toBe('current-refresh-token');
        expect(localStorage.getItem('user_role')).toBe('admin');

        localStorage.setItem('token', 'newest-external-token');
        await expect(rejected({ response: { status: 401 }, config })).rejects.toBeDefined();

        expect(client.request).toHaveBeenCalledTimes(1);
        expect(localStorage.getItem('token')).toBe('newest-external-token');
        expect(localStorage.getItem('refresh_token')).toBe('current-refresh-token');
        expect(localStorage.getItem('user_role')).toBe('admin');
    });

    it('uses an access token written by another tab when its refresh request fails', async () => {
        const nowSeconds = Math.floor(Date.now() / 1000);
        localStorage.setItem('token', createToken(nowSeconds + 60));
        localStorage.setItem('refresh_token', 'stale-refresh-token');
        let rejectRefresh: ((reason?: unknown) => void) | undefined;
        axiosPost.mockImplementation(() => new Promise((_resolve, reject) => {
            rejectRefresh = reject;
        }));

        await import('@/lib/api');
        const addAuthentication = requestUse.mock.calls[0][0];
        const pendingRequest = addAuthentication({ url: '/resources', headers: {} });

        expect(axiosPost).toHaveBeenCalledTimes(1);
        localStorage.setItem('token', 'external-access-token');
        localStorage.setItem('refresh_token', 'external-refresh-token');
        rejectRefresh?.(new Error('refresh token already rotated'));
        const config = await pendingRequest;

        expect(config.headers.Authorization).toBe('Bearer external-access-token');
        expect(localStorage.getItem('token')).toBe('external-access-token');
        expect(localStorage.getItem('refresh_token')).toBe('external-refresh-token');
    });
});
