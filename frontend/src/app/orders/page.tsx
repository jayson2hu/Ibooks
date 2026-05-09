'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import CopyButton from '@/components/common/CopyButton';
import type { Order, OrderStatus, PaginatedResponse, PaymentMethod, ResourceAccess } from '@/types';

const statusLabels: Record<OrderStatus, string> = {
    pending: '待支付',
    paid: '已支付',
    cancelled: '已取消',
    refunded: '已退款',
};

const statusClasses: Record<OrderStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-green-100 text-green-800',
    cancelled: 'bg-gray-100 text-gray-700',
    refunded: 'bg-blue-100 text-blue-700',
};

const paymentMethodLabels: Record<PaymentMethod, string> = {
    alipay: '支付宝',
    wechat: '微信',
    free: '免费',
    coin: '书币',
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

function OrdersContent() {
    const router = useRouter();
    const [orders, setOrders] = useState<Order[]>([]);
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [actionOrderNo, setActionOrderNo] = useState('');
    const [error, setError] = useState('');
    const [accessOrderNo, setAccessOrderNo] = useState('');
    const [access, setAccess] = useState<ResourceAccess | null>(null);

    const loadOrders = async (targetPage = page) => {
        setLoading(true);
        setError('');
        if (!localStorage.getItem('token')) {
            setLoading(false);
            router.push('/login');
            return;
        }
        try {
            const response = await api.orders.my({ page: targetPage, page_size: 10 });
            const data = response.data as PaginatedResponse<Order>;
            setOrders(data.items);
            setPage(data.page);
            setPages(data.pages);
            setTotal(data.total);
        } catch (err: any) {
            setError(err.response?.data?.detail || '订单加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadOrders(1);
    }, []);

    const cancelOrder = async (orderNo: string) => {
        setActionOrderNo(orderNo);
        setError('');
        try {
            await api.orders.cancel(orderNo);
            await loadOrders(page);
        } catch (err: any) {
            setError(err.response?.data?.detail || '取消订单失败');
        } finally {
            setActionOrderNo('');
        }
    };

    const showAccess = async (order: Order) => {
        if (!order.resource?.slug) {
            setError('订单缺少资源信息，无法获取链接');
            return;
        }
        setActionOrderNo(order.order_no);
        setError('');
        try {
            const response = await api.resources.getAccess(order.resource.slug);
            setAccess(response.data);
            setAccessOrderNo(order.order_no);
        } catch (err: any) {
            setError(err.response?.data?.detail || '资源链接加载失败');
        } finally {
            setActionOrderNo('');
        }
    };

    const activeAccessLinks = access
        ? [
            ...(access.cloud_link ? [access.cloud_link] : []),
            ...(access.backup_links || []),
        ]
        : [];

    return (
        <div className="min-h-screen pt-24">
            <div className="container py-8">
                <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">我的订单</h1>
                        <p className="mt-2 text-sm text-gray-600">查看购买记录并获取已购买资源。</p>
                    </div>
                    <Link href="/resources" className="btn btn-secondary">
                        浏览资源
                    </Link>
                </div>

                {error && (
                    <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        {error}
                    </div>
                )}

                {accessOrderNo && (
                    <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
                        <div className="mb-3 flex items-center justify-between gap-4">
                            <h2 className="font-semibold text-green-900">资源链接</h2>
                            <button
                                type="button"
                                className="text-sm text-green-800 hover:underline"
                                onClick={() => {
                                    setAccessOrderNo('');
                                    setAccess(null);
                                }}
                            >
                                收起
                            </button>
                        </div>
                        <div className="space-y-2">
                            {activeAccessLinks.map((link, index) => (
                                <div key={`${link}-${index}`} className="rounded bg-white p-3 text-sm">
                                    <div className="mb-2 break-all text-gray-700">{link}</div>
                                    <div className="flex gap-2">
                                        <a href={link} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                            打开链接
                                        </a>
                                        <CopyButton value={link} label="复制链接" className="text-gray-600 hover:text-gray-900" />
                                    </div>
                                </div>
                            ))}
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
                    </div>
                )}

                <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                    <div className="border-b border-gray-100 px-6 py-4 text-sm text-gray-600">
                        共 {total} 条订单
                    </div>
                    {loading ? (
                        <div className="p-8 text-center text-gray-500">正在加载订单...</div>
                    ) : orders.length === 0 ? (
                        <div className="p-10 text-center">
                            <p className="mb-4 text-gray-600">暂无订单</p>
                            <Link href="/resources" className="btn btn-primary">
                                去挑选资源
                            </Link>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100">
                            {orders.map((order) => (
                                <div key={order.order_no} className="p-6">
                                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                                        <div className="min-w-0">
                                            <div className="mb-2 flex flex-wrap items-center gap-3">
                                                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusClasses[order.status]}`}>
                                                    {statusLabels[order.status]}
                                                </span>
                                                <span className="font-mono text-sm text-gray-500">{order.order_no}</span>
                                            </div>
                                            <h2 className="truncate text-lg font-semibold text-gray-900">
                                                {order.resource?.title || `资源 #${order.resource_id}`}
                                            </h2>
                                            <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500">
                                                <span>{order.coin_amount > 0 ? `${order.coin_amount} 书币` : '免费'}</span>
                                                <span>支付方式 {paymentMethodLabels[order.payment_method || 'free']}</span>
                                                <span>下单 {formatDate(order.created_at)}</span>
                                                {order.paid_at && <span>支付 {formatDate(order.paid_at)}</span>}
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {order.resource?.slug && (
                                                <Link href={`/resources/${order.resource.slug}`} className="btn btn-secondary">
                                                    查看资源
                                                </Link>
                                            )}
                                            {order.status === 'paid' && (
                                                <button
                                                    type="button"
                                                    className="btn btn-primary"
                                                    disabled={actionOrderNo === order.order_no}
                                                    onClick={() => showAccess(order)}
                                                >
                                                    获取资源
                                                </button>
                                            )}
                                            {order.status === 'pending' && (
                                                <button
                                                    type="button"
                                                    className="btn btn-secondary"
                                                    disabled={actionOrderNo === order.order_no}
                                                    onClick={() => cancelOrder(order.order_no)}
                                                >
                                                    取消订单
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {pages > 1 && (
                    <div className="mt-6 flex items-center justify-between">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            disabled={page <= 1 || loading}
                            onClick={() => loadOrders(page - 1)}
                        >
                            上一页
                        </button>
                        <span className="text-sm text-gray-600">
                            第 {page} / {pages} 页
                        </span>
                        <button
                            type="button"
                            className="btn btn-secondary"
                            disabled={page >= pages || loading}
                            onClick={() => loadOrders(page + 1)}
                        >
                            下一页
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function OrdersPage() {
    return <OrdersContent />;
}
