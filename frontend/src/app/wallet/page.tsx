'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import type { CoinLedger, PaginatedResponse, SigninStatus, Wallet } from '@/types';

const ledgerLabels: Record<string, string> = {
    recharge: '充值',
    purchase: '购买资源',
    refund: '退款',
    signin: '签到奖励',
    admin_adjust: '后台调整',
};

function formatDate(value: string) {
    return new Date(value).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function WalletContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [wallet, setWallet] = useState<Wallet | null>(null);
    const [signinStatus, setSigninStatus] = useState<SigninStatus | null>(null);
    const [ledger, setLedger] = useState<CoinLedger[]>([]);
    const [loading, setLoading] = useState(true);
    const [claiming, setClaiming] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    const paymentReturned = searchParams.get('payment_return') === 'alipay';
    const rechargeNo = searchParams.get('recharge_no');

    const returnNotice = useMemo(() => {
        if (!paymentReturned) {
            return '';
        }
        return `充值结果正在确认中${rechargeNo ? `，订单号：${rechargeNo}` : ''}`;
    }, [paymentReturned, rechargeNo]);

    const loadWallet = async () => {
        setError('');
        if (!localStorage.getItem('token')) {
            setLoading(false);
            router.push('/login');
            return;
        }
        try {
            const [walletResponse, statusResponse, ledgerResponse] = await Promise.all([
                api.wallet.me(),
                api.signin.status(),
                api.wallet.ledger({ page: 1, page_size: 10 }),
            ]);
            setWallet(walletResponse.data);
            setSigninStatus(statusResponse.data);
            const ledgerData = ledgerResponse.data as PaginatedResponse<CoinLedger>;
            setLedger(ledgerData.items);
        } catch (err: any) {
            setError(err.response?.data?.detail || '钱包加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadWallet();
        const timer = paymentReturned ? window.setTimeout(loadWallet, 3000) : undefined;
        return () => {
            if (timer) {
                window.clearTimeout(timer);
            }
        };
    }, [paymentReturned]);

    const claimSignin = async () => {
        setClaiming(true);
        setError('');
        setNotice('');
        try {
            const response = await api.signin.claim();
            setNotice(`签到成功，获得 ${response.data.reward_coins} 书币`);
            await loadWallet();
        } catch (err: any) {
            setError(err.response?.data?.detail || '签到失败');
        } finally {
            setClaiming(false);
        }
    };

    return (
        <div className="min-h-screen pt-24">
            <div className="container py-8">
                <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">我的钱包</h1>
                        <p className="mt-2 text-sm text-gray-600">查看书币余额、签到奖励和资产流水。</p>
                    </div>
                    <Link href="/recharge" className="btn btn-primary">
                        充值书币
                    </Link>
                </div>

                {returnNotice && (
                    <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
                        {returnNotice}
                    </div>
                )}
                {notice && (
                    <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
                        {notice}
                    </div>
                )}
                {error && (
                    <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        {error}
                    </div>
                )}

                {loading ? (
                    <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
                        正在加载钱包...
                    </div>
                ) : (
                    <>
                        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
                            <div className="rounded-lg border border-gray-200 bg-white p-5">
                                <p className="text-sm text-gray-500">当前余额</p>
                                <p className="mt-2 text-3xl font-bold text-primary">{wallet?.balance ?? 0}</p>
                                <p className="mt-1 text-xs text-gray-500">书币</p>
                            </div>
                            <div className="rounded-lg border border-gray-200 bg-white p-5">
                                <p className="text-sm text-gray-500">累计充值</p>
                                <p className="mt-2 text-2xl font-semibold text-gray-900">{wallet?.total_recharged ?? 0}</p>
                            </div>
                            <div className="rounded-lg border border-gray-200 bg-white p-5">
                                <p className="text-sm text-gray-500">累计消费</p>
                                <p className="mt-2 text-2xl font-semibold text-gray-900">{wallet?.total_spent ?? 0}</p>
                            </div>
                            <div className="rounded-lg border border-gray-200 bg-white p-5">
                                <p className="text-sm text-gray-500">累计奖励</p>
                                <p className="mt-2 text-2xl font-semibold text-gray-900">{wallet?.total_rewarded ?? 0}</p>
                            </div>
                        </div>

                        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <h2 className="text-lg font-semibold text-gray-900">每日签到</h2>
                                    <p className="mt-1 text-sm text-gray-500">
                                        {signinStatus?.enabled
                                            ? `今日签到可得 ${signinStatus.reward_coins} 书币`
                                            : '签到活动暂未开启'}
                                    </p>
                                </div>
                                {signinStatus?.enabled && (
                                    <button
                                        type="button"
                                        className="btn btn-primary"
                                        disabled={claiming || signinStatus.signed_in_today}
                                        onClick={claimSignin}
                                    >
                                        {signinStatus.signed_in_today ? '今日已签到' : claiming ? '签到中...' : '签到'}
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="rounded-lg border border-gray-200 bg-white">
                            <div className="border-b border-gray-100 px-5 py-4">
                                <h2 className="font-semibold text-gray-900">资产流水</h2>
                            </div>
                            {ledger.length === 0 ? (
                                <div className="p-8 text-center text-gray-500">暂无流水</div>
                            ) : (
                                <div className="divide-y divide-gray-100">
                                    {ledger.map((entry) => (
                                        <div key={entry.id} className="flex items-center justify-between gap-4 p-5">
                                            <div>
                                                <p className="font-medium text-gray-900">{ledgerLabels[entry.type] || entry.type}</p>
                                                <p className="mt-1 text-sm text-gray-500">{formatDate(entry.created_at)}</p>
                                                {entry.description && (
                                                    <p className="mt-1 text-xs text-gray-500">{entry.description}</p>
                                                )}
                                            </div>
                                            <div className="text-right">
                                                <p className={`text-lg font-semibold ${entry.amount >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                                                    {entry.amount >= 0 ? '+' : ''}{entry.amount}
                                                </p>
                                                <p className="text-xs text-gray-500">余额 {entry.balance_after}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default function WalletPage() {
    return (
        <Suspense fallback={<div className="min-h-screen pt-24"><div className="container py-8 text-gray-500">正在加载钱包...</div></div>}>
            <WalletContent />
        </Suspense>
    );
}
