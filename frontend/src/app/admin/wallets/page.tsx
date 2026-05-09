'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { AdminWallet, PaginatedResponse } from '@/types';

export default function AdminWalletsPage() {
    const [wallets, setWallets] = useState<AdminWallet[]>([]);
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [adjustingUserId, setAdjustingUserId] = useState<number | null>(null);

    const loadWallets = async (targetPage = page) => {
        setLoading(true);
        setError('');
        try {
            const response = await api.admin.getWallets({
                page: targetPage,
                page_size: 20,
                search: search || undefined,
            });
            const data = response.data as PaginatedResponse<AdminWallet>;
            setWallets(data.items);
            setPage(data.page);
            setPages(data.pages);
            setTotal(data.total);
        } catch (err: any) {
            setError(err.response?.data?.detail || '钱包列表加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadWallets(1);
    }, []);

    const adjustWallet = async (wallet: AdminWallet) => {
        const rawAmount = window.prompt('输入调整书币数量，正数加币，负数扣币');
        if (!rawAmount) return;
        const amount = Number(rawAmount);
        if (!Number.isInteger(amount) || amount === 0) {
            setError('调整数量必须是非 0 整数');
            return;
        }
        const description = window.prompt('调整说明', '后台手动调整') || '后台手动调整';
        setAdjustingUserId(wallet.user_id);
        setError('');
        try {
            await api.admin.adjustWallet(wallet.user_id, { amount, description });
            await loadWallets(page);
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : detail?.message || '钱包调整失败');
        } finally {
            setAdjustingUserId(null);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">钱包管理</h1>
                <p className="mt-1 text-gray-600">查看用户余额，并进行后台调币</p>
            </div>

            {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

            <div className="flex gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    onKeyDown={(event) => event.key === 'Enter' && loadWallets(1)}
                    placeholder="搜索邮箱或用户名"
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                />
                <button onClick={() => loadWallets(1)} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
                    搜索
                </button>
            </div>

            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b border-gray-200 bg-gray-50 text-sm text-gray-600">
                            <tr>
                                <th className="px-6 py-4">用户</th>
                                <th className="px-6 py-4">余额</th>
                                <th className="px-6 py-4">累计充值</th>
                                <th className="px-6 py-4">累计消费</th>
                                <th className="px-6 py-4">累计奖励</th>
                                <th className="px-6 py-4">操作</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-500">加载中...</td></tr>
                            ) : wallets.length === 0 ? (
                                <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-500">暂无钱包</td></tr>
                            ) : wallets.map((wallet) => (
                                <tr key={wallet.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{wallet.user?.username || `用户 #${wallet.user_id}`}</div>
                                        <div className="text-xs text-gray-500">{wallet.user?.email || '-'}</div>
                                    </td>
                                    <td className="px-6 py-4 font-bold text-orange-600">{wallet.balance} 书币</td>
                                    <td className="px-6 py-4">{wallet.total_recharged}</td>
                                    <td className="px-6 py-4">{wallet.total_spent}</td>
                                    <td className="px-6 py-4">{wallet.total_rewarded}</td>
                                    <td className="px-6 py-4">
                                        <button
                                            disabled={adjustingUserId === wallet.user_id}
                                            onClick={() => adjustWallet(wallet)}
                                            className="text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50"
                                        >
                                            调整余额
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-600">
                <span>第 {page} / {pages || 1} 页，共 {total} 条</span>
                <div className="flex gap-2">
                    <button disabled={page <= 1 || loading} onClick={() => loadWallets(page - 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">上一页</button>
                    <button disabled={page >= pages || loading} onClick={() => loadWallets(page + 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">下一页</button>
                </div>
            </div>
        </div>
    );
}
