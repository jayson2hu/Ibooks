'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { AlipayCreateResponse, RechargePackage } from '@/types';

function formatMoney(value: number | string) {
    return Number(value || 0).toFixed(2);
}

export default function RechargePage() {
    const router = useRouter();
    const [packages, setPackages] = useState<RechargePackage[]>([]);
    const [loading, setLoading] = useState(true);
    const [submittingId, setSubmittingId] = useState<number | null>(null);
    const [error, setError] = useState('');

    const loadPackages = async () => {
        setLoading(true);
        setError('');
        if (!localStorage.getItem('token')) {
            setLoading(false);
            router.push('/login');
            return;
        }
        try {
            const response = await api.recharge.packages();
            setPackages(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || '充值套餐加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPackages();
    }, []);

    const startRecharge = async (packageId: number) => {
        setSubmittingId(packageId);
        setError('');
        try {
            const orderResponse = await api.recharge.createOrder(packageId, 'alipay');
            const paymentResponse = await api.recharge.alipayCreate(orderResponse.data.recharge_no);
            const payment = paymentResponse.data as AlipayCreateResponse;
            window.location.href = payment.payment_url;
        } catch (err: any) {
            setError(err.response?.data?.detail || '发起充值失败');
            setSubmittingId(null);
        }
    };

    return (
        <div className="min-h-screen pt-24">
            <div className="container py-8">
                <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">充值书币</h1>
                        <p className="mt-2 text-sm text-gray-600">选择套餐后使用支付宝完成充值。</p>
                    </div>
                    <Link href="/wallet" className="btn btn-secondary">
                        返回钱包
                    </Link>
                </div>

                {error && (
                    <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        {error}
                    </div>
                )}

                {loading ? (
                    <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
                        正在加载充值套餐...
                    </div>
                ) : packages.length === 0 ? (
                    <div className="rounded-lg border border-gray-200 bg-white p-10 text-center">
                        <p className="mb-4 text-gray-600">暂无可用充值套餐</p>
                        <Link href="/wallet" className="btn btn-secondary">
                            返回钱包
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {packages.map((item) => {
                            const totalCoins = item.coins + item.bonus_coins;
                            const isSubmitting = submittingId === item.id;
                            return (
                                <button
                                    key={item.id}
                                    type="button"
                                    className="rounded-lg border border-gray-200 bg-white p-6 text-left transition hover:border-primary hover:shadow-md disabled:cursor-not-allowed disabled:opacity-70"
                                    disabled={submittingId !== null}
                                    onClick={() => startRecharge(item.id)}
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div>
                                            <h2 className="text-lg font-semibold text-gray-900">{item.name}</h2>
                                            <p className="mt-2 text-3xl font-bold text-primary">{totalCoins}</p>
                                            <p className="mt-1 text-sm text-gray-500">
                                                {item.coins} 书币{item.bonus_coins > 0 ? ` + 赠送 ${item.bonus_coins}` : ''}
                                            </p>
                                        </div>
                                        <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                                            ¥{formatMoney(item.amount)}
                                        </span>
                                    </div>
                                    <div className="mt-6">
                                        <span className="btn btn-primary inline-block w-full text-center">
                                            {isSubmitting ? '跳转中...' : '支付宝支付'}
                                        </span>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
