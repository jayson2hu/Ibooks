import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ResourceAccessCard from '@/components/resource/ResourceAccessCard';
import { api } from '@/lib/api';

jest.mock('@/lib/api', () => ({
    api: {
        resources: {
            getAccess: jest.fn(),
            download: jest.fn(),
        },
        orders: { create: jest.fn() },
        wallet: { me: jest.fn() },
    },
    getApiErrorStatus: jest.fn((error: { status?: number }) => error?.status),
    getApiErrorDetail: jest.fn(() => undefined),
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const walletResponse = {
    data: {
        id: 1,
        user_id: 1,
        balance: 100,
        total_recharged: 100,
        total_spent: 0,
        total_rewarded: 0,
        created_at: '2026-09-10T00:00:00Z',
        updated_at: '2026-09-10T00:00:00Z',
    },
};

const accessResponse = {
    data: {
        cloud_link: 'https://pan.example.com/book',
        backup_links: [],
        access_code: 'abcd',
    },
};

describe('ResourceAccessCard explicit delivery', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
        jest.mocked(api.wallet.me).mockResolvedValue(walletResponse as never);
    });

    it('does not fetch or count a free download until the user clicks 获取资源', async () => {
        jest.mocked(api.resources.download).mockResolvedValue(accessResponse as never);

        render(<ResourceAccessCard resourceId={1} slug="free-book" isFree coinPrice={0} />);

        const retrieve = await screen.findByRole('button', { name: '获取资源' });
        expect(api.resources.getAccess).not.toHaveBeenCalled();
        expect(api.resources.download).not.toHaveBeenCalled();

        fireEvent.click(retrieve);

        expect(await screen.findByRole('link', { name: '打开链接' })).toHaveAttribute(
            'href',
            'https://pan.example.com/book',
        );
        expect(api.resources.download).toHaveBeenCalledWith('free-book');
    });

    it('uses the access endpoint only as a paid-resource permission check', async () => {
        localStorage.setItem('token', 'token');
        jest.mocked(api.resources.getAccess).mockResolvedValue({
            data: { has_access: true },
        } as never);
        jest.mocked(api.resources.download).mockResolvedValue(accessResponse as never);

        render(<ResourceAccessCard resourceId={2} slug="owned-book" isFree={false} coinPrice={20} />);

        const retrieve = await screen.findByRole('button', { name: '获取资源' });
        expect(api.resources.getAccess).toHaveBeenCalledWith('owned-book');
        expect(api.resources.download).not.toHaveBeenCalled();
        expect(screen.queryByRole('link', { name: '打开链接' })).not.toBeInTheDocument();

        fireEvent.click(retrieve);

        expect(await screen.findByRole('link', { name: '打开链接' })).toHaveAttribute(
            'href',
            'https://pan.example.com/book',
        );
        expect(api.resources.download).toHaveBeenCalledWith('owned-book');
    });

    it('turns a completed purchase into access without counting a download', async () => {
        localStorage.setItem('token', 'token');
        jest.mocked(api.resources.getAccess).mockRejectedValueOnce({ status: 402 });
        jest.mocked(api.orders.create).mockResolvedValue({ data: { status: 'paid' } } as never);

        render(<ResourceAccessCard resourceId={2} slug="paid-book" isFree={false} coinPrice={20} />);

        fireEvent.click(await screen.findByRole('button', { name: '立即购买' }));

        expect(await screen.findByRole('button', { name: '获取资源' })).toBeInTheDocument();
        expect(api.orders.create).toHaveBeenCalledWith(2);
        expect(api.resources.download).not.toHaveBeenCalled();
        await waitFor(() => expect(api.wallet.me).toHaveBeenCalled());
    });

    it('shows an explicit empty state when delivery data has no configured links', async () => {
        jest.mocked(api.resources.download).mockResolvedValue({
            data: { cloud_link: null, backup_links: [], access_code: null },
        } as never);

        render(<ResourceAccessCard resourceId={3} slug="empty-book" isFree coinPrice={0} />);
        fireEvent.click(await screen.findByRole('button', { name: '获取资源' }));

        expect(await screen.findByText('当前资源暂未配置云盘链接，请稍后再试。')).toBeInTheDocument();
    });
});
