'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api, getApiErrorMessage } from '@/lib/api';
import type { Order, OrderStatus, PaymentMethod } from '@/types';

const statusLabels: Record<OrderStatus, string> = {
    pending: '待支付',
    paid: '已支付',
    cancelled: '已取消',
    refunded: '已退款',
};

const statusClasses: Record<OrderStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    paid: 'bg-green-100 text-green-700',
    cancelled: 'bg-gray-100 text-gray-700',
    refunded: 'bg-blue-100 text-blue-700',
};

const paymentLabels: Record<PaymentMethod, string> = {
    alipay: '支付宝',
    wechat: '微信支付',
    free: '免费资源',
    coin: '书币',
};

function formatAmount(amount: number | string) {
    return Number(amount || 0).toFixed(2);
}

function formatDate(dateString?: string | null) {
    if (!dateString) {
        return '-';
    }
    return new Date(dateString).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

export default function OrderManagement() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const loadOrders = useCallback(async (targetPage: number, targetStatus: string) => {
        setLoading(true);
        setError('');
        try {
            const params: Record<string, string | number> = {
                page: targetPage,
                page_size: 20,
            };
            if (targetStatus) {
                params.status = targetStatus;
            }
            const response = await api.orders.adminList(params);
            const data = response.data;
            setOrders(data.items);
            setPage(data.page);
            setPages(data.pages);
            setTotal(data.total);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '订单加载失败'));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadOrders(1, status);
    }, [loadOrders, status]);

    const stats = useMemo(() => {
        const paidOrders = orders.filter((order) => order.status === 'paid');
        return {
            visible: orders.length,
            spentCoins: paidOrders.reduce((sum, order) => sum + Number(order.coin_amount || 0), 0),
            pending: orders.filter((order) => order.status === 'pending').length,
            paid: paidOrders.length,
        };
    }, [orders]);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">订单管理</h1>
                <p className="mt-1 text-gray-600">查看和管理所有订单</p>
            </div>

            {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-sm text-gray-600">总订单数</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{total}</p>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-sm text-gray-600">当前页消费书币</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stats.spentCoins} 书币</p>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-sm text-gray-600">当前页待支付</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stats.pending}</p>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-sm text-gray-600">当前页已支付</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stats.paid}</p>
                </div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col gap-4 sm:flex-row sm:items-center">
                <div className="flex-1 text-sm text-gray-600">
                    当前筛选显示 {stats.visible} 条记录
                </div>
                <select
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                    className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white"
                >
                    <option value="">所有状态</option>
                    <option value="pending">待支付</option>
                    <option value="paid">已支付</option>
                    <option value="cancelled">已取消</option>
                    <option value="refunded">已退款</option>
                </select>
                <button
                    type="button"
                    className="px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50"
                    disabled={loading}
                    onClick={() => loadOrders(page, status)}
                >
                    刷新
                </button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4 font-medium text-gray-600">订单号</th>
                                <th className="px-6 py-4 font-medium text-gray-600">用户</th>
                                <th className="px-6 py-4 font-medium text-gray-600">资源</th>
                                <th className="px-6 py-4 font-medium text-gray-600">书币</th>
                                <th className="px-6 py-4 font-medium text-gray-600">支付方式</th>
                                <th className="px-6 py-4 font-medium text-gray-600">状态</th>
                                <th className="px-6 py-4 font-medium text-gray-600">创建时间</th>
                                <th className="px-6 py-4 font-medium text-gray-600">操作</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={8} className="px-6 py-10 text-center text-gray-500">
                                        正在加载订单...
                                    </td>
                                </tr>
                            ) : orders.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="px-6 py-10 text-center text-gray-500">
                                        暂无订单
                                    </td>
                                </tr>
                            ) : (
                                orders.map((order) => (
                                    <tr key={order.order_no} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4">
                                            <span className="font-mono text-sm text-gray-900">{order.order_no}</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div>
                                                <div className="font-medium text-gray-900">
                                                    {order.user?.username || `用户 #${order.user_id}`}
                                                </div>
                                                <div className="text-xs text-gray-500">{order.user?.email || '-'}</div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-gray-900 max-w-xs truncate" title={order.resource?.title}>
                                                {order.resource?.title || `资源 #${order.resource_id}`}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="font-bold text-orange-600">{order.coin_amount} 书币</div>
                                            {Number(order.amount || 0) > 0 && (
                                                <div className="mt-1 text-xs text-gray-400">历史金额 ¥{formatAmount(order.amount)}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-gray-600">
                                                {order.payment_method ? paymentLabels[order.payment_method] || order.payment_method : '-'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusClasses[order.status]}`}>
                                                {statusLabels[order.status]}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-600">{formatDate(order.created_at)}</div>
                                            {order.paid_at && (
                                                <div className="text-xs text-gray-400 mt-1">支付: {formatDate(order.paid_at)}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            {order.resource?.slug ? (
                                                <Link
                                                    href={`/resources/${order.resource.slug}`}
                                                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                                                >
                                                    查看资源
                                                </Link>
                                            ) : (
                                                <span className="text-sm text-gray-400">-</span>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                    第 {page} / {pages || 1} 页，共 {total} 条记录
                </div>
                <div className="flex gap-2">
                    <button
                        disabled={page <= 1 || loading}
                        onClick={() => loadOrders(page - 1, status)}
                        className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        上一页
                    </button>
                    <span className="px-4 py-2 bg-blue-600 text-white rounded-lg">
                        {page}
                    </span>
                    <button
                        disabled={page >= pages || loading}
                        onClick={() => loadOrders(page + 1, status)}
                        className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        下一页
                    </button>
                </div>
            </div>
        </div>
    );
}
