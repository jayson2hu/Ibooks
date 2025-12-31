'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function ResourceManagement() {
    const [resources, setResources] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [search, setSearch] = useState('');

    const fetchResources = async () => {
        setLoading(true);
        try {
            const response = await api.resources.list({
                page,
                page_size: 10,
                search: search
            });
            console.log('Admin API Response:', response.data); // 调试日志
            
            // 处理不同的响应结构
            let resourcesData = [];
            let totalCount = 0;
            
            if (response.data.items && Array.isArray(response.data.items)) {
                resourcesData = response.data.items;
                totalCount = response.data.total || response.data.count || 0;
            } else if (Array.isArray(response.data)) {
                resourcesData = response.data;
                totalCount = response.data.length;
            } else if (response.data.data && Array.isArray(response.data.data)) {
                resourcesData = response.data.data;
                totalCount = response.data.total || response.data.count || 0;
            } else {
                console.warn('Unexpected API response structure:', response.data);
                resourcesData = [];
                totalCount = 0;
            }
            
            setResources(resourcesData);
            setTotal(totalCount);
        } catch (error) {
            console.error('Failed to fetch resources:', error);
            setResources([]); // 确保设置为空数组
            setTotal(0);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchResources();
    }, [page, search]);

    const handleDelete = async (id: number) => {
        if (!confirm('确定要删除这个资源吗？此操作不可恢复。')) return;

        try {
            await api.resources.delete(id);
            fetchResources(); // Refresh list
        } catch (error) {
            console.error('Delete failed:', error);
            alert('删除失败');
        }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">资源管理</h1>
                <Link
                    href="/admin/resources/new"
                    className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors flex items-center gap-2"
                >
                    <span>+</span>
                    <span>发布资源</span>
                </Link>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 mb-6 flex gap-4">
                <div className="flex-1">
                    <input
                        type="text"
                        placeholder="搜索资源标题..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
                    />
                </div>
                <select className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-primary bg-white">
                    <option value="">所有分类</option>
                    <option value="ebook">电子书</option>
                    <option value="course">视频课程</option>
                </select>
                <select className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-primary bg-white">
                    <option value="">所有状态</option>
                    <option value="published">已发布</option>
                    <option value="draft">草稿</option>
                </select>
            </div>

            {/* Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-4 font-medium text-gray-500">ID</th>
                            <th className="px-6 py-4 font-medium text-gray-500">封面</th>
                            <th className="px-6 py-4 font-medium text-gray-500">标题</th>
                            <th className="px-6 py-4 font-medium text-gray-500">分类</th>
                            <th className="px-6 py-4 font-medium text-gray-500">价格</th>
                            <th className="px-6 py-4 font-medium text-gray-500">状态</th>
                            <th className="px-6 py-4 font-medium text-gray-500">数据</th>
                            <th className="px-6 py-4 font-medium text-gray-500">操作</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {loading ? (
                            <tr>
                                <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                                    加载中...
                                </td>
                            </tr>
                        ) : !Array.isArray(resources) || resources.length === 0 ? (
                            <tr>
                                <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                                    暂无数据
                                </td>
                            </tr>
                        ) : (
                            resources.map((resource) => (
                                <tr key={resource.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 text-gray-500">#{resource.id}</td>
                                    <td className="px-6 py-4">
                                        <div className="w-12 h-16 bg-gray-100 rounded overflow-hidden">
                                            {resource.cover_image_url ? (
                                                <img
                                                    src={resource.cover_image_url}
                                                    alt={resource.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-gray-300">
                                                    📷
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900 line-clamp-1" title={resource.title}>
                                            {resource.title}
                                        </div>
                                        <div className="text-xs text-gray-400 mt-1">
                                            {new Date(resource.created_at).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded-full">
                                            {resource.category?.name || '未分类'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-medium text-orange-500">
                                        {resource.price > 0 ? `¥${resource.price}` : '免费'}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 text-xs rounded-full ${resource.is_published
                                                ? 'bg-green-50 text-green-600'
                                                : 'bg-gray-100 text-gray-500'
                                            }`}>
                                            {resource.is_published ? '已发布' : '草稿'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-xs text-gray-500">
                                        <div>👁️ {resource.view_count}</div>
                                        <div>⬇️ {resource.download_count}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <Link
                                                href={`/admin/resources/${resource.id}`}
                                                className="text-blue-500 hover:text-blue-700"
                                            >
                                                编辑
                                            </Link>
                                            <button
                                                onClick={() => handleDelete(resource.id)}
                                                className="text-red-500 hover:text-red-700"
                                            >
                                                删除
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-6">
                <div className="text-sm text-gray-500">
                    共 {total} 条记录
                </div>
                <div className="flex gap-2">
                    <button
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}
                        className="px-4 py-2 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                        上一页
                    </button>
                    <span className="px-4 py-2 bg-primary text-white rounded">
                        {page}
                    </span>
                    <button
                        disabled={!Array.isArray(resources) || resources.length < 10}
                        onClick={() => setPage(p => p + 1)}
                        className="px-4 py-2 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                        下一页
                    </button>
                </div>
            </div>
        </div>
    );
}
