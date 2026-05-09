'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import CopyButton from '@/components/common/CopyButton';
import type { Order, ResourceAccess, Wallet } from '@/types';

interface ResourceAccessCardProps {
    resourceId: number;
    slug: string;
    isFree: boolean;
    coinPrice: number;
}

export default function ResourceAccessCard({ resourceId, slug, isFree, coinPrice }: ResourceAccessCardProps) {
    const [access, setAccess] = useState<ResourceAccess | null>(null);
    const [loading, setLoading] = useState(true);
    const [buying, setBuying] = useState(false);
    const [error, setError] = useState('');
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [accessDenied, setAccessDenied] = useState(false);
    const [wallet, setWallet] = useState<Wallet | null>(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        setIsLoggedIn(Boolean(token));

        if (!isFree && !token) {
            setLoading(false);
            setAccessDenied(true);
            return;
        }

        const fetchAccess = async () => {
            setLoading(true);
            setError('');
            setAccessDenied(false);
            try {
                if (!isFree) {
                    const walletResponse = await api.wallet.me();
                    setWallet(walletResponse.data);
                }
                const response = await api.resources.getAccess(slug);
                setAccess(response.data);
            } catch (err: any) {
                const status = err.response?.status;
                if (status === 401 || status === 402) {
                    setAccessDenied(true);
                    return;
                }
                setError(err.response?.data?.detail || '资源链接加载失败');
            } finally {
                setLoading(false);
            }
        };

        fetchAccess();
    }, [slug]);

    const handlePurchase = async () => {
        setBuying(true);
        setError('');
        try {
            const orderResponse = await api.orders.create(resourceId);
            const order = orderResponse.data as Order;

            if (order.status === 'paid') {
                const accessResponse = await api.resources.getAccess(slug);
                setAccess(accessResponse.data);
                setAccessDenied(false);
                const walletResponse = await api.wallet.me();
                setWallet(walletResponse.data);
                return;
            }
        } catch (err: any) {
            if (err.response?.status === 409) {
                try {
                    const accessResponse = await api.resources.getAccess(slug);
                    setAccess(accessResponse.data);
                    setAccessDenied(false);
                    return;
                } catch {
                    setError('已购买记录存在，但资源链接刷新失败，请到我的订单中重试');
                }
            } else if (err.response?.status === 402) {
                const detail = err.response?.data?.detail;
                const balance = detail?.balance ?? wallet?.balance ?? 0;
                const required = detail?.required_coins ?? coinPrice;
                setError(`书币余额不足，当前 ${balance}，需要 ${required}`);
            } else {
                setError(err.response?.data?.detail || '创建订单失败，请稍后重试');
            }
        } finally {
            setBuying(false);
        }
    };

    if (loading) {
        return (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-tertiary">
                正在确认资源访问权限...
            </div>
        );
    }

    if (!isFree && accessDenied) {
        const balance = wallet?.balance ?? 0;
        const insufficient = isLoggedIn && coinPrice > 0 && balance < coinPrice;

        return (
            <div className="space-y-3">
                {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {error}
                    </div>
                )}
                {isLoggedIn && insufficient ? (
                    <Link href="/recharge" className="btn btn-primary w-full block text-center">
                        去充值
                    </Link>
                ) : isLoggedIn ? (
                    <button
                        type="button"
                        className="btn btn-primary w-full"
                        disabled={buying}
                        onClick={handlePurchase}
                    >
                        {buying ? '正在创建订单...' : '立即购买'}
                    </button>
                ) : (
                    <Link href="/login" className="btn btn-primary w-full block text-center">
                        登录后购买
                    </Link>
                )}
                <p className="text-xs text-tertiary text-center">
                    资源价格 {coinPrice} 书币
                    {isLoggedIn && `，当前余额 ${balance} 书币`}
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
            </div>
        );
    }

    if (!access?.cloud_link && (!access?.backup_links || access.backup_links.length === 0)) {
        return (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
                当前资源暂未配置云盘链接，请稍后再试。
            </div>
        );
    }

    const links = [
        ...(access.cloud_link ? [access.cloud_link] : []),
        ...(access.backup_links || []),
    ];

    return (
        <div className="space-y-3 rounded-lg border border-green-200 bg-green-50 p-4">
            <h3 className="font-semibold text-green-900">资源链接</h3>
            <div className="space-y-2">
                {links.map((link, index) => (
                    <div key={`${link}-${index}`} className="rounded bg-white p-3 text-sm">
                        <div className="mb-2 break-all text-gray-700">{link}</div>
                        <div className="flex gap-2">
                            <a
                                href={link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline"
                            >
                                打开链接
                            </a>
                            <CopyButton
                                value={link}
                                label="复制链接"
                                className="text-gray-600 hover:text-gray-900"
                            />
                        </div>
                    </div>
                ))}
            </div>

            {access.access_code && (
                <div className="flex items-center justify-between rounded bg-white p-3 text-sm">
                    <span className="text-gray-600">提取码</span>
                    <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-gray-900">{access.access_code}</span>
                        <CopyButton
                            value={access.access_code}
                            label="复制"
                            className="text-primary hover:underline"
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
