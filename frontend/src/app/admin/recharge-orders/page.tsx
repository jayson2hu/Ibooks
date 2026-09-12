'use client';

import { useCallback, useEffect, useState } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import type { PaginatedResponse, RechargeOrder, RechargeOrderStatus } from '@/types';

const statusLabels: Record<RechargeOrderStatus, string> = {
    pending: '待支付',
    paid: '已支付',
    cancelled: '已取消',
    failed: '失败',
};

function formatDate(value?: string | null) {
    return value ? new Date(value).toLocaleString('zh-CN') : '-';
}

export default function AdminRechargeOrdersPage() {
    const [orders, setOrders] = useState<RechargeOrder[]>([]);
    const [status, setStatus] = useState('');
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const loadOrders = useCallback(async (targetPage: number) => {
        setLoading(true);
        setError('');
        try {
            const response = await api.admin.getRechargeOrders({
                page: targetPage,
                page_size: 20,
                status: status || undefined,
            });
            const data = response.data as PaginatedResponse<RechargeOrder>;
            setOrders(data.items);
            setPage(data.page);
            setPages(data.pages);
            setTotal(data.total);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '充值订单加载失败'));
        } finally {
            setLoading(false);
        }
    }, [status]);

    useEffect(() => {
        void loadOrders(1);
    }, [loadOrders]);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">充值订单</h1>
                <p className="mt-1 text-gray-600">查看用户通过第三方渠道购买书币的订单</p>
            </div>

            {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

            <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-lg border border-gray-300 px-3 py-2">
                    <option value="">全部状态</option>
                    {Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <button onClick={() => loadOrders(page)} className="rounded-lg border border-gray-300 px-4 py-2 hover:bg-gray-50">刷新</button>
            </div>

            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b border-gray-200 bg-gray-50 text-sm text-gray-600">
                            <tr>
                                <th className="px-6 py-4">充值单号</th>
                                <th className="px-6 py-4">用户</th>
                                <th className="px-6 py-4">套餐</th>
                                <th className="px-6 py-4">金额</th>
                                <th className="px-6 py-4">书币</th>
                                <th className="px-6 py-4">渠道</th>
                                <th className="px-6 py-4">状态</th>
                                <th className="px-6 py-4">时间</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                <tr><td colSpan={8} className="px-6 py-10 text-center text-gray-500">加载中...</td></tr>
                            ) : orders.length === 0 ? (
                                <tr><td colSpan={8} className="px-6 py-10 text-center text-gray-500">暂无充值订单</td></tr>
                            ) : orders.map((order) => (
                                <tr key={order.recharge_no} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 font-mono text-xs">{order.recharge_no}</td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{order.user?.username || `用户 #${order.user_id}`}</div>
                                        <div className="text-xs text-gray-500">{order.user?.email || '-'}</div>
                                    </td>
                                    <td className="px-6 py-4">{order.package?.name || '-'}</td>
                                    <td className="px-6 py-4">¥{Number(order.amount).toFixed(2)}</td>
                                    <td className="px-6 py-4 font-bold text-orange-600">{order.coins + order.bonus_coins}</td>
                                    <td className="px-6 py-4">{order.payment_method === 'alipay' ? '支付宝' : '微信'}</td>
                                    <td className="px-6 py-4">{statusLabels[order.status]}</td>
                                    <td className="px-6 py-4 text-sm text-gray-600">
                                        <div>{formatDate(order.created_at)}</div>
                                        <div className="text-xs text-gray-400">支付：{formatDate(order.paid_at)}</div>
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
                    <button disabled={page <= 1 || loading} onClick={() => loadOrders(page - 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">上一页</button>
                    <button disabled={page >= pages || loading} onClick={() => loadOrders(page + 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">下一页</button>
                </div>
            </div>
        </div>
    );
}
