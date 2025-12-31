'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import ErrorMessage from '@/components/admin/ErrorMessage';

interface Category {
    id: number;
    name: string;
    slug: string;
    description: string | null;
    icon: string | null;
    parent_id: number | null;
    sort_order: number;
    is_active: boolean;
    created_at: string;
}

export default function CategoriesPage() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [editingCategory, setEditingCategory] = useState<Category | null>(null);

    const fetchCategories = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const response = await api.categories.list(false); // Get all categories including inactive
            console.log('Categories API Response:', response.data); // 调试日志
            
            // 处理不同的响应结构
            let categoriesData = [];
            if (response.data.items && Array.isArray(response.data.items)) {
                categoriesData = response.data.items;
            } else if (Array.isArray(response.data)) {
                categoriesData = response.data;
            } else if (response.data.data && Array.isArray(response.data.data)) {
                categoriesData = response.data.data;
            } else {
                console.warn('Unexpected categories API response structure:', response.data);
                categoriesData = [];
            }
            
            setCategories(categoriesData);
        } catch (err: any) {
            console.error('Failed to fetch categories:', err);
            setError(err.response?.data?.detail || '无法加载分类数据');
            setCategories([]); // 确保设置为空数组
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCategories();
    }, []);

    const handleDelete = async (id: number) => {
        if (!confirm('确定要删除这个分类吗？这将影响所有相关资源。')) {
            return;
        }

        try {
            await api.categories.delete(id);
            await fetchCategories();
        } catch (err: any) {
            alert(err.response?.data?.detail || '删除失败');
        }
    };

    const handleToggleActive = async (category: Category) => {
        try {
            await api.categories.update(category.id, {
                is_active: !category.is_active
            });
            await fetchCategories();
        } catch (err: any) {
            alert(err.response?.data?.detail || '更新失败');
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">分类管理</h1>
                    <p className="mt-1 text-gray-600">管理资源分类</p>
                </div>
                <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">分类管理</h1>
                    <p className="mt-1 text-gray-600">管理资源分类</p>
                </div>
                <ErrorMessage message={error} onRetry={fetchCategories} />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">分类管理</h1>
                    <p className="mt-1 text-gray-600">管理资源分类和层级结构</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    添加分类
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">总分类数</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">{Array.isArray(categories) ? categories.length : 0}</p>
                        </div>
                        <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-2xl">
                            📁
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">活跃分类</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">
                                {Array.isArray(categories) ? categories.filter(c => c.is_active).length : 0}
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-2xl">
                            ✅
                        </div>
                    </div>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">顶级分类</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">
                                {Array.isArray(categories) ? categories.filter(c => !c.parent_id).length : 0}
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-2xl">
                            🏷️
                        </div>
                    </div>
                </div>
            </div>

            {/* Categories Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    分类名称
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Slug
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    描述
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    排序
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    状态
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    操作
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {!Array.isArray(categories) || categories.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                                        暂无分类数据
                                    </td>
                                </tr>
                            ) : (
                                categories.map((category) => (
                                    <tr key={category.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                {category.icon && (
                                                    <span className="mr-2 text-xl">{category.icon}</span>
                                                )}
                                                <div>
                                                    <div className="text-sm font-medium text-gray-900">
                                                        {category.name}
                                                    </div>
                                                    {category.parent_id && (
                                                        <div className="text-xs text-gray-500">
                                                            子分类
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <code className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                                {category.slug}
                                            </code>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-600 max-w-xs truncate">
                                                {category.description || '-'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-sm text-gray-900">{category.sort_order}</span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <button
                                                onClick={() => handleToggleActive(category)}
                                                className={`px-2.5 py-1 text-xs font-medium rounded-full ${category.is_active
                                                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                                    } transition-colors`}
                                            >
                                                {category.is_active ? '活跃' : '禁用'}
                                            </button>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button
                                                onClick={() => setEditingCategory(category)}
                                                className="text-blue-600 hover:text-blue-900 mr-4"
                                            >
                                                编辑
                                            </button>
                                            <button
                                                onClick={() => handleDelete(category.id)}
                                                className="text-red-600 hover:text-red-900"
                                            >
                                                删除
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create/Edit Modal Placeholder */}
            {(showCreateModal || editingCategory) && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
                        <h2 className="text-xl font-bold mb-4">
                            {editingCategory ? '编辑分类' : '创建分类'}
                        </h2>
                        <p className="text-gray-600 mb-4">
                            分类创建/编辑功能即将推出
                        </p>
                        <button
                            onClick={() => {
                                setShowCreateModal(false);
                                setEditingCategory(null);
                            }}
                            className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        >
                            关闭
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
