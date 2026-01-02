'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import StatsCard from '@/components/admin/StatsCard';
import StatsSkeleton from '@/components/admin/StatsSkeleton';
import ErrorMessage from '@/components/admin/ErrorMessage';
import { api } from '@/lib/api';
import { useAdminAuth } from '@/hooks/useAdminAuth';

interface Stats {
    users: number;
    resources: number;
    published_resources: number;
    categories: number;
    total_views: number;
    total_downloads: number;
}

export default function AdminDashboard() {
    const { isAuthenticated, isLoading: isAuthLoading } = useAdminAuth();
    const [stats, setStats] = useState<Stats | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStats = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const response = await api.admin.getStats();
            setStats(response.data);
        } catch (err: any) {
            console.error('Failed to fetch stats:', err);
            setError(err.response?.data?.detail || '无法加载统计数据，请稍后重试');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        // Only fetch stats if authenticated
        if (isAuthenticated) {
            fetchStats();
        }
    }, [isAuthenticated]);

    // Format number with commas
    const formatNumber = (num: number): string => {
        return num.toLocaleString('zh-CN');
    };

    // Map API stats to display cards
    const statsCards = stats ? [
        {
            title: '总资源数',
            value: formatNumber(stats.resources),
            change: undefined,
            changeType: 'increase' as const,
            icon: '📚',
            iconBg: 'bg-blue-100'
        },
        {
            title: '已发布资源',
            value: formatNumber(stats.published_resources),
            change: undefined,
            changeType: 'increase' as const,
            icon: '✅',
            iconBg: 'bg-green-100'
        },
        {
            title: '总用户数',
            value: formatNumber(stats.users),
            change: undefined,
            changeType: 'increase' as const,
            icon: '👥',
            iconBg: 'bg-purple-100'
        },
        {
            title: '总浏览量',
            value: formatNumber(stats.total_views),
            change: undefined,
            changeType: 'increase' as const,
            icon: '👁️',
            iconBg: 'bg-yellow-100'
        },
    ] : [];


    const recentResources = [
        { id: 1, title: 'Python 完全指南 2025', type: '电子书', date: '2025-12-01', status: '已发布' },
        { id: 2, title: 'React 高级教程', type: '视频课程', date: '2025-12-01', status: '已发布' },
        { id: 3, title: 'Next.js 14 实战', type: '文档', date: '2025-11-30', status: '待审核' },
        { id: 4, title: 'TypeScript 深入浅出', type: '电子书', date: '2025-11-30', status: '已发布' },
    ];

    const recentOrders = [
        { id: 1001, user: '张三', resource: 'Python 完全指南', amount: '¥99', status: '已完成' },
        { id: 1002, user: '李四', resource: 'React 高级教程', amount: '¥199', status: '已完成' },
        { id: 1003, user: '王五', resource: 'Next.js 14 实战', amount: '¥149', status: '进行中' },
        { id: 1004, user: '赵六', resource: 'TypeScript 深入浅出', amount: '¥129', status: '已完成' },
    ];

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">仪表盘</h1>
                <p className="mt-1 text-gray-600">欢迎回来，这是您的数据概览</p>
            </div>

            {/* Stats Grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatsSkeleton />
                    <StatsSkeleton />
                    <StatsSkeleton />
                    <StatsSkeleton />
                </div>
            ) : error ? (
                <ErrorMessage message={error} onRetry={fetchStats} />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {statsCards.map((stat, index) => (
                        <StatsCard key={index} {...stat} />
                    ))}
                </div>
            )}

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Resources */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                    <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-900">最新资源</h2>
                        <Link href="/admin/resources" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                            查看全部 →
                        </Link>
                    </div>
                    <div className="p-6">
                        <div className="space-y-4">
                            {recentResources.map((resource) => (
                                <div key={resource.id} className="flex items-center justify-between">
                                    <div className="flex-1">
                                        <h3 className="text-sm font-medium text-gray-900">{resource.title}</h3>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {resource.type} • {resource.date}
                                        </p>
                                    </div>
                                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${resource.status === '已发布'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-yellow-100 text-yellow-700'
                                        }`}>
                                        {resource.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Recent Orders */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                    <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-900">最新订单</h2>
                        <Link href="/admin/orders" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                            查看全部 →
                        </Link>
                    </div>
                    <div className="p-6">
                        <div className="space-y-4">
                            {recentOrders.map((order) => (
                                <div key={order.id} className="flex items-center justify-between">
                                    <div className="flex-1">
                                        <h3 className="text-sm font-medium text-gray-900">#{order.id} - {order.user}</h3>
                                        <p className="text-xs text-gray-500 mt-1">{order.resource}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm font-bold text-gray-900">{order.amount}</p>
                                        <span className={`text-xs ${order.status === '已完成'
                                            ? 'text-green-600'
                                            : 'text-blue-600'
                                            }`}>
                                            {order.status}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-8 text-white">
                <h2 className="text-2xl font-bold mb-2">快速操作</h2>
                <p className="text-blue-100 mb-6">点击下方按钮快速访问常用功能</p>
                <div className="flex flex-wrap gap-3">
                    <Link href="/admin/resources/new" className="px-5 py-2.5 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors">
                        + 添加资源
                    </Link>
                    <Link href="/admin/users" className="px-5 py-2.5 bg-white/10 backdrop-blur-sm text-white rounded-lg font-medium hover:bg-white/20 transition-colors">
                        管理用户
                    </Link>
                    <Link href="/admin/settings" className="px-5 py-2.5 bg-white/10 backdrop-blur-sm text-white rounded-lg font-medium hover:bg-white/20 transition-colors">
                        系统设置
                    </Link>
                </div>
            </div>
        </div>
    );
}
