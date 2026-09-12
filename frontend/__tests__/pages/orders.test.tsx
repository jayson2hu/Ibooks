import { fireEvent, render, screen } from '@testing-library/react';
import OrdersPage from '@/app/orders/page';
import { api } from '@/lib/api';

const push = jest.fn();
const router = { push };

jest.mock('next/navigation', () => ({
    useRouter: () => router,
}));

jest.mock('@/lib/api', () => ({
    api: {
        orders: {
            my: jest.fn(),
            cancel: jest.fn(),
        },
        resources: { download: jest.fn() },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const paidOrder = {
    id: 1,
    order_no: 'ORD-1',
    user_id: 1,
    resource_id: 9,
    amount: 10,
    coin_amount: 10,
    payment_method: 'coin',
    status: 'paid',
    created_at: '2026-09-10T00:00:00Z',
    updated_at: '2026-09-10T00:00:00Z',
    resource: { id: 9, slug: 'ordered-book', title: 'Ordered Book' },
};

describe('OrdersPage resource delivery', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
        localStorage.setItem('token', 'token');
        jest.mocked(api.orders.my).mockResolvedValue({
            data: { items: [paidOrder], total: 1, page: 1, page_size: 10, pages: 1 },
        } as never);
    });

    it('uses the explicit download endpoint when a paid order requests its resource', async () => {
        jest.mocked(api.resources.download).mockResolvedValue({
            data: {
                cloud_link: 'https://pan.example.com/ordered-book',
                backup_links: [],
                access_code: 'code',
            },
        } as never);

        render(<OrdersPage />);
        fireEvent.click(await screen.findByRole('button', { name: '获取资源' }));

        expect(await screen.findByRole('link', { name: '打开链接' })).toHaveAttribute(
            'href',
            'https://pan.example.com/ordered-book',
        );
        expect(api.resources.download).toHaveBeenCalledWith('ordered-book');
    });

    it('renders an actionable API failure instead of an empty delivery panel', async () => {
        jest.mocked(api.resources.download).mockRejectedValue(new Error('offline'));

        render(<OrdersPage />);
        fireEvent.click(await screen.findByRole('button', { name: '获取资源' }));

        expect(await screen.findByText('资源链接加载失败')).toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: '资源链接' })).not.toBeInTheDocument();
    });
});
