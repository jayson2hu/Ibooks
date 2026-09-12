import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AdminDashboard from '@/app/admin/page';
import { api } from '@/lib/api';
import { useAdminAuth } from '@/hooks/useAdminAuth';

jest.mock('@/lib/api', () => ({
    api: {
        admin: { getStats: jest.fn() },
        resources: { list: jest.fn() },
        orders: { adminList: jest.fn() },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

jest.mock('@/hooks/useAdminAuth', () => ({
    useAdminAuth: jest.fn(),
}));

const mockedUseAdminAuth = useAdminAuth as jest.MockedFunction<typeof useAdminAuth>;
const getStatsMock = api.admin.getStats as jest.MockedFunction<typeof api.admin.getStats>;
const listResourcesMock = api.resources.list as jest.MockedFunction<typeof api.resources.list>;
const listOrdersMock = api.orders.adminList as jest.MockedFunction<typeof api.orders.adminList>;

const stats = {
    users: 3,
    resources: 4,
    published_resources: 2,
    categories: 1,
    total_views: 10,
    total_downloads: 5,
};

describe('AdminDashboard role-aware content', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        getStatsMock.mockResolvedValue({ data: stats } as never);
        listResourcesMock.mockResolvedValue({
            data: {
                items: [{
                    id: 1,
                    title: '待审核资源',
                    resource_type: 'ebook',
                    created_at: '2026-09-10T00:00:00Z',
                    is_published: false,
                }],
            },
        } as never);
        listOrdersMock.mockResolvedValue({
            data: {
                items: [{
                    id: 2,
                    order_no: 'ORDER-2',
                    coin_amount: 20,
                    status: 'paid',
                    created_at: '2026-09-10T00:00:00Z',
                    resource: { title: '已购资源' },
                    user: { email: 'reader@example.com' },
                }],
            },
        } as never);
    });

    it('shows resources without requesting administrator-only orders for moderators', async () => {
        mockedUseAdminAuth.mockReturnValue({
            isAuthenticated: true,
            isLoading: false,
            role: 'moderator',
            canAccessRoute: true,
        });

        render(<AdminDashboard />);

        expect(await screen.findByText('待审核资源')).toBeInTheDocument();
        expect(screen.queryByText('最新订单')).not.toBeInTheDocument();
        expect(listOrdersMock).not.toHaveBeenCalled();
    });

    it('loads and displays recent orders for administrators', async () => {
        mockedUseAdminAuth.mockReturnValue({
            isAuthenticated: true,
            isLoading: false,
            role: 'admin',
            canAccessRoute: true,
        });

        render(<AdminDashboard />);

        expect(await screen.findByText('#ORDER-2')).toBeInTheDocument();
        expect(screen.getByText('已购资源 - reader@example.com')).toBeInTheDocument();
        await waitFor(() => expect(listOrdersMock).toHaveBeenCalledTimes(1));
    });

    it('shows a retryable error instead of an empty order state when order loading fails', async () => {
        mockedUseAdminAuth.mockReturnValue({
            isAuthenticated: true,
            isLoading: false,
            role: 'admin',
            canAccessRoute: true,
        });
        listOrdersMock
            .mockRejectedValueOnce(new Error('orders unavailable'))
            .mockResolvedValueOnce({
                data: {
                    items: [{
                        id: 3,
                        order_no: 'ORDER-3',
                        coin_amount: 30,
                        status: 'paid',
                        created_at: '2026-09-10T00:00:00Z',
                    }],
                },
            } as never);

        render(<AdminDashboard />);

        expect(await screen.findByRole('alert')).toHaveTextContent('无法加载最新订单');
        expect(screen.queryByText('暂无订单')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '重新加载订单' }));

        expect(await screen.findByText('#ORDER-3')).toBeInTheDocument();
        await waitFor(() => expect(listOrdersMock).toHaveBeenCalledTimes(2));
    });
});
