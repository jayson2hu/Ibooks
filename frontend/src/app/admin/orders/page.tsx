'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function OrderManagement() {
    const [page, setPage] = useState(1);

    // Mock data structure - will be replaced with real API calls when order system is implemented
    const mockOrders = [
        {
            id: 1001,
            user: { name: '张三', email: 'zhang@example.com' },
            resource: { title: 'Python 完全指南 2025', id: 1 },
            amount: 99,
            status: 'completed',
            payment_method: '支付宝',
            created_at: '2025-12-30T10:30:00',
            paid_at: '2025-12-30T10:30:15'
        },
        {
            id: 1002,
            user: { name: '李四', email: 'li@example.com' },
            resource: { title: 'React 高级教程', id: 2 },
            amount: 199,
            status: 'completed',
            payment_method: '微信支付',
            created_at: '2025-12-30T14:20:00',
            paid_at: '2025-12-30T14:20:30'
        },
        {
            id: 1003,
            user: { name: '王五', email: 'wang@example.com' },
            resource: { title: 'Next.js 14 实战', id: 3 },
            amount: 149,
            status: 'pending',
            payment_method: '支付宝',
            created_at: '2025-12-31T09:15:00',
            paid_at: null
        },
        {
            id: 1004,
            user: { name: '赵六', email: 'zhao@example.com' },
            resource: { title: 'TypeScript 深入浅出', id: 4 },
            amount: 129,
            status: 'completed',
            payment_method: '微信支付',
            created_at: '2025-12-31T11:45:00',
            paid_at: '2025-12-31T11:45:20'
        },
    ];

    const getStatusBadge = (status: string) => {
        const styles = {
            completed: 'bg-green-100 text-green-700',
            pending: 'bg-yellow-100 text-yellow-700',
            failed: 'bg-red-100 text-red-700',
            refunded: 'bg-gray-100 text-gray-700'
        };
        const labels = {
            completed: '已完成',
            pending: '待支付',
            failed: '已失败',
            refunded: '已退款'
        };
        return (
            <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${styles[status as keyof typeof styles] || styles.pending}`}>
                {labels[status as keyof typeof labels] || status}
            </span>
        );
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">订单管理</h1>
                <p className="mt-1 text-gray-600">查看和管理所有订单</p>
            </div>

            {/* Coming Soon Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <span className="text-2xl">ℹ️</span>
                    <div>
                        <h3 className="font-semibold text-blue-900">功能开发中</h3>
                        <p className="text-sm text-blue-700 mt-1">
                            订单系统后端API正在开发中。当前显示的是模拟数据，用于展示界面设计。
                            完整功能将包括订单创建、支付处理、订单状态管理等。
                        </p>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">总订单数</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">156</p>
                        </div>
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                            📦
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">总收入</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">¥23,456</p>
                        </div>
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl">
                            💰
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">待处理</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">3</p>
                        </div>
                        <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center text-2xl">
                            ⏳
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">今日订单</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">8</p>
                        </div>
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-2xl">
                            📈
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex gap-4">
                <div className="flex-1">
                    <input
                        type="text"
                        placeholder="搜索订单号、用户名或资源名..."
                        className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                </div>
                <select className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white">
                    <option value="">所有状态</option>
                    <option value="completed">已完成</option>
                    <option value="pending">待支付</option>
                    <option value="failed">已失败</option>
                    <option value="refunded">已退款</option>
                </select>
                <select className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white">
                    <option value="">所有支付方式</option>
                    <option value="alipay">支付宝</option>
                    <option value="wechat">微信支付</option>
                </select>
            </div>

            {/* Orders Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="px-6 py-4 font-medium text-gray-600">订单号</th>
                            <th className="px-6 py-4 font-medium text-gray-600">用户</th>
                            <th className="px-6 py-4 font-medium text-gray-600">资源</th>
                            <th className="px-6 py-4 font-medium text-gray-600">金额</th>
                            <th className="px-6 py-4 font-medium text-gray-600">支付方式</th>
                            <th className="px-6 py-4 font-medium text-gray-600">状态</th>
                            <th className="px-6 py-4 font-medium text-gray-600">创建时间</th>
                            <th className="px-6 py-4 font-medium text-gray-600">操作</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {mockOrders.map((order) => (
                            <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4">
                                    <span className="font-mono text-sm text-gray-900">#{order.id}</span>
                                </td>
                                <td className="px-6 py-4">
                                    <div>
                                        <div className="font-medium text-gray-900">{order.user.name}</div>
                                        <div className="text-xs text-gray-500">{order.user.email}</div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="font-medium text-gray-900 max-w-xs truncate" title={order.resource.title}>
                                        {order.resource.title}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="font-bold text-orange-600">¥{order.amount}</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-sm text-gray-600">{order.payment_method}</span>
                                </td>
                                <td className="px-6 py-4">
                                    {getStatusBadge(order.status)}
                                </td>
                                <td className="px-6 py-4">
                                    <div className="text-sm text-gray-600">
                                        {formatDate(order.created_at)}
                                    </div>
                                    {order.paid_at && (
                                        <div className="text-xs text-gray-400 mt-1">
                                            支付: {formatDate(order.paid_at)}
                                        </div>
                                    )}
                                </td>
                                <td className="px-6 py-4">
                                    <button
                                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                                        onClick={() => alert('订单详情功能开发中')}
                                    >
                                        查看详情
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                    显示 1-4 条，共 4 条记录
                </div>
                <div className="flex gap-2">
                    <button
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}
                        className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        上一页
                    </button>
                    <span className="px-4 py-2 bg-blue-600 text-white rounded-lg">
                        {page}
                    </span>
                    <button
                        disabled={mockOrders.length < 10}
                        onClick={() => setPage(p => p + 1)}
                        className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        下一页
                    </button>
                </div>
            </div>
        </div>
    );
}
