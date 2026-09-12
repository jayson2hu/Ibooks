'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api, getApiErrorDetail, getApiErrorMessage, getApiErrorStatus } from '@/lib/api';
import CopyButton from '@/components/common/CopyButton';
import type { ResourceAccess, Wallet } from '@/types';

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
    const [retrieving, setRetrieving] = useState(false);
    const [error, setError] = useState('');
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [hasAccess, setHasAccess] = useState(isFree);
    const [accessDenied, setAccessDenied] = useState(false);
    const [wallet, setWallet] = useState<Wallet | null>(null);

    const checkAccess = useCallback(async () => {
        const token = localStorage.getItem('token');
        setIsLoggedIn(Boolean(token));
        setAccess(null);
        setError('');

        if (isFree) {
            setHasAccess(true);
            setAccessDenied(false);
            setLoading(false);
            return;
        }

        if (!token) {
            setHasAccess(false);
            setAccessDenied(true);
            setLoading(false);
            return;
        }

        setLoading(true);
        const walletRequest = api.wallet.me().catch(() => null);
        try {
            await api.resources.getAccess(slug);
            // Permission checks must not count as downloads or reveal links
            // before the user explicitly requests the resource.
            setHasAccess(true);
            setAccessDenied(false);
        } catch (caught: unknown) {
            const status = getApiErrorStatus(caught);
            if (status === 401 || status === 402) {
                if (status === 401) {
                    setIsLoggedIn(false);
                }
                setHasAccess(false);
                setAccessDenied(true);
                return;
            }
            setError(getApiErrorMessage(caught, '资源访问权限确认失败'));
        } finally {
            const walletResponse = await walletRequest;
            if (walletResponse) {
                setWallet(walletResponse.data);
            }
            setLoading(false);
        }
    }, [isFree, slug]);

    useEffect(() => {
        void checkAccess();
    }, [checkAccess]);

    const handleRetrieve = async () => {
        setRetrieving(true);
        setError('');
        try {
            const response = await api.resources.download(slug);
            setAccess(response.data);
        } catch (caught: unknown) {
            const status = getApiErrorStatus(caught);
            if (status === 401 || status === 402) {
                if (status === 401) {
                    setIsLoggedIn(false);
                }
                setHasAccess(false);
                setAccessDenied(true);
            }
            setError(getApiErrorMessage(caught, '资源获取失败，请稍后重试'));
        } finally {
            setRetrieving(false);
        }
    };

    const handlePurchase = async () => {
        setBuying(true);
        setError('');
        try {
            const orderResponse = await api.orders.create(resourceId);
            if (orderResponse.data.status !== 'paid') {
                setError('订单尚未支付，请到我的订单中查看状态');
                return;
            }

            setHasAccess(true);
            setAccessDenied(false);
            const walletResponse = await api.wallet.me().catch(() => null);
            if (walletResponse) {
                setWallet(walletResponse.data);
            }
        } catch (caught: unknown) {
            const status = getApiErrorStatus(caught);
            if (status === 409) {
                try {
                    await api.resources.getAccess(slug);
                    setHasAccess(true);
                    setAccessDenied(false);
                } catch {
                    setError('已购买记录存在，但资源权限刷新失败，请到我的订单中重试');
                }
            } else if (status === 402) {
                const detail = getApiErrorDetail(caught);
                const balance = typeof detail === 'object' ? detail.balance ?? wallet?.balance ?? 0 : wallet?.balance ?? 0;
                const required = typeof detail === 'object' ? detail.required_coins ?? coinPrice : coinPrice;
                setError(`书币余额不足，当前 ${balance}，需要 ${required}`);
            } else {
                setError(getApiErrorMessage(caught, '创建订单失败，请稍后重试'));
            }
        } finally {
            setBuying(false);
        }
    };

    if (loading) {
        return (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-tertiary" role="status">
                正在确认资源访问权限...
            </div>
        );
    }

    if (!isFree && accessDenied) {
        const balance = wallet?.balance;
        const insufficient = isLoggedIn && balance !== undefined && coinPrice > 0 && balance < coinPrice;

        return (
            <div className="space-y-3">
                {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
                        {error}
                    </div>
                )}
                {isLoggedIn && insufficient ? (
                    <Link href="/recharge" className="btn btn-primary w-full block text-center">去充值</Link>
                ) : isLoggedIn ? (
                    <button type="button" className="btn btn-primary w-full" disabled={buying} onClick={handlePurchase}>
                        {buying ? '正在创建订单...' : '立即购买'}
                    </button>
                ) : (
                    <Link href="/login" className="btn btn-primary w-full block text-center">登录后购买</Link>
                )}
                <p className="text-xs text-tertiary text-center">
                    资源价格 {coinPrice} 书币
                    {isLoggedIn && balance !== undefined && `，当前余额 ${balance} 书币`}
                </p>
            </div>
        );
    }

    if (error && !access) {
        return (
            <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
                <p>{error}</p>
                <button type="button" className="font-medium underline" onClick={() => void checkAccess()}>重试</button>
            </div>
        );
    }

    if (hasAccess && !access) {
        return (
            <button type="button" className="btn btn-primary w-full" disabled={retrieving} onClick={handleRetrieve}>
                {retrieving ? '正在获取资源...' : '获取资源'}
            </button>
        );
    }

    const links = access
        ? [...(access.cloud_link ? [access.cloud_link] : []), ...(access.backup_links || [])]
        : [];

    if (links.length === 0) {
        return (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800" role="status">
                当前资源暂未配置云盘链接，请稍后再试。
            </div>
        );
    }

    return (
        <div className="space-y-3 rounded-lg border border-green-200 bg-green-50 p-4">
            <h3 className="font-semibold text-green-900">资源链接</h3>
            <div className="space-y-2">
                {links.map((link, index) => (
                    <div key={`${link}-${index}`} className="rounded bg-white p-3 text-sm">
                        <div className="mb-2 break-all text-gray-700">{link}</div>
                        <div className="flex gap-2">
                            <a href={link} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">打开链接</a>
                            <CopyButton value={link} label="复制链接" className="text-gray-600 hover:text-gray-900" />
                        </div>
                    </div>
                ))}
            </div>

            {access?.access_code && (
                <div className="flex items-center justify-between rounded bg-white p-3 text-sm">
                    <span className="text-gray-600">提取码</span>
                    <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-gray-900">{access.access_code}</span>
                        <CopyButton value={access.access_code} label="复制" className="text-primary hover:underline" />
                    </div>
                </div>
            )}
        </div>
    );
}
