'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { AdminCoinLedger, CoinLedgerType, PaginatedResponse } from '@/types';

const typeLabels: Record<CoinLedgerType, string> = {
    recharge: '充值',
    purchase: '购买资源',
    refund: '退款',
    signin: '签到',
    admin_adjust: '后台调整',
};

function formatDate(value: string) {
    return new Date(value).toLocaleString('zh-CN');
}

export default function AdminCoinLedgerPage() {
    const [entries, setEntries] = useState<AdminCoinLedger[]>([]);
    const [type, setType] = useState('');
    const [userId, setUserId] = useState('');
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const loadEntries = async (targetPage = page) => {
        setLoading(true);
        setError('');
        try {
            const response = await api.admin.getCoinLedger({
                page: targetPage,
                page_size: 20,
                type: type || undefined,
                user_id: userId || undefined,
            });
            const data = response.data as PaginatedResponse<AdminCoinLedger>;
            setEntries(data.items);
            setPage(data.page);
            setPages(data.pages);
            setTotal(data.total);
        } catch (err: any) {
            setError(err.response?.data?.detail || '流水加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadEntries(1);
    }, []);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">资产流水</h1>
                <p className="mt-1 text-gray-600">查看所有书币余额变动记录</p>
            </div>

            {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

            <div className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm md:flex-row">
                <select value={type} onChange={(event) => setType(event.target.value)} className="rounded-lg border border-gray-300 px-3 py-2">
                    <option value="">全部类型</option>
                    {Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <input
                    value={userId}
                    onChange={(event) => setUserId(event.target.value)}
                    placeholder="用户 ID"
                    className="rounded-lg border border-gray-300 px-3 py-2"
                />
                <button onClick={() => loadEntries(1)} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">筛选</button>
            </div>

            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b border-gray-200 bg-gray-50 text-sm text-gray-600">
                            <tr>
                                <th className="px-6 py-4">用户</th>
                                <th className="px-6 py-4">类型</th>
                                <th className="px-6 py-4">变动</th>
                                <th className="px-6 py-4">变动后余额</th>
                                <th className="px-6 py-4">关联单号</th>
                                <th className="px-6 py-4">说明</th>
                                <th className="px-6 py-4">时间</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                <tr><td colSpan={7} className="px-6 py-10 text-center text-gray-500">加载中...</td></tr>
                            ) : entries.length === 0 ? (
                                <tr><td colSpan={7} className="px-6 py-10 text-center text-gray-500">暂无流水</td></tr>
                            ) : entries.map((entry) => (
                                <tr key={entry.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{entry.user?.username || `用户 #${entry.user_id}`}</div>
                                        <div className="text-xs text-gray-500">{entry.user?.email || '-'}</div>
                                    </td>
                                    <td className="px-6 py-4">{typeLabels[entry.type]}</td>
                                    <td className={`px-6 py-4 font-bold ${entry.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {entry.amount >= 0 ? '+' : ''}{entry.amount}
                                    </td>
                                    <td className="px-6 py-4">{entry.balance_after}</td>
                                    <td className="px-6 py-4 font-mono text-xs">{entry.related_order_no || '-'}</td>
                                    <td className="px-6 py-4 text-sm text-gray-600">{entry.description || '-'}</td>
                                    <td className="px-6 py-4 text-sm text-gray-600">{formatDate(entry.created_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-600">
                <span>第 {page} / {pages || 1} 页，共 {total} 条</span>
                <div className="flex gap-2">
                    <button disabled={page <= 1 || loading} onClick={() => loadEntries(page - 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">上一页</button>
                    <button disabled={page >= pages || loading} onClick={() => loadEntries(page + 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">下一页</button>
                </div>
            </div>
        </div>
    );
}
