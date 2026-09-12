import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import WalletPage from '@/app/wallet/page';
import { api } from '@/lib/api';

const push = jest.fn();
const router = { push };
let searchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
    useRouter: () => router,
    useSearchParams: () => searchParams,
}));

jest.mock('@/lib/api', () => ({
    api: {
        wallet: {
            me: jest.fn(),
            ledger: jest.fn(),
        },
        signin: {
            status: jest.fn(),
            claim: jest.fn(),
        },
        recharge: {
            getOrder: jest.fn(),
        },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const walletResponse = {
    data: {
        id: 1,
        user_id: 1,
        balance: 20,
        total_recharged: 20,
        total_spent: 0,
        total_rewarded: 0,
        created_at: '2026-09-10T00:00:00Z',
        updated_at: '2026-09-10T00:00:00Z',
    },
};

const paidOrderResponse = {
    data: {
        recharge_no: 'R202609100001',
        status: 'paid',
        coins: 100,
        bonus_coins: 20,
    },
};

describe('WalletPage payment return handling', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
        localStorage.setItem('token', 'test-token');
        searchParams = new URLSearchParams();

        jest.mocked(api.wallet.me).mockResolvedValue(walletResponse as never);
        jest.mocked(api.wallet.ledger).mockResolvedValue({ data: { items: [] } } as never);
        jest.mocked(api.signin.status).mockResolvedValue({
            data: { enabled: true, signed_in_today: false, reward_coins: 1 },
        } as never);
    });

    it('queries the returned recharge order and confirms credited coins', async () => {
        searchParams = new URLSearchParams(
            'payment_return=alipay&recharge_no=R202609100001',
        );
        jest.mocked(api.recharge.getOrder).mockResolvedValue(paidOrderResponse as never);

        render(<WalletPage />);

        expect(await screen.findByText('充值成功，120 书币已到账。')).toBeInTheDocument();
        expect(api.recharge.getOrder).toHaveBeenCalledWith('R202609100001');
        await waitFor(() => expect(api.wallet.me).toHaveBeenCalledTimes(2));
    });

    it('reports a malformed payment return without making an ambiguous query', async () => {
        searchParams = new URLSearchParams('payment_return=alipay');

        render(<WalletPage />);

        expect(await screen.findByText(
            '支付返回缺少充值订单号，无法自动确认到账状态。',
        )).toBeInTheDocument();
        expect(api.recharge.getOrder).not.toHaveBeenCalled();
    });

    it('allows a failed status query to be retried', async () => {
        searchParams = new URLSearchParams(
            'payment_return=alipay&recharge_no=R202609100001',
        );
        jest.mocked(api.recharge.getOrder)
            .mockRejectedValueOnce(new Error('temporary outage'))
            .mockResolvedValueOnce(paidOrderResponse as never);

        render(<WalletPage />);

        expect(await screen.findByText('充值订单状态查询失败，请稍后重试。')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: '重新查询' }));

        expect(await screen.findByText('充值成功，120 书币已到账。')).toBeInTheDocument();
        expect(api.recharge.getOrder).toHaveBeenCalledTimes(2);
    });
});
