'use client';

import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import ResourceCover from '@/components/common/ResourceCover';
import type { AdminResourceListParams, Category, Resource } from '@/types';

const PAGE_SIZE = 10;
type PublicationFilter = 'all' | 'published' | 'draft';

function ResourceManagementContent() {
    const searchParams = useSearchParams();
    const searchFromUrl = searchParams.get('search') || '';
    const [resources, setResources] = useState<Resource[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(0);
    const [search, setSearch] = useState(searchFromUrl);
    const [categoryId, setCategoryId] = useState('');
    const [publicationFilter, setPublicationFilter] = useState<PublicationFilter>('all');
    const [loadError, setLoadError] = useState('');
    const [categoryError, setCategoryError] = useState('');

    const categoryNames = useMemo(
        () => new Map(categories.map((category) => [category.id, category.name])),
        [categories],
    );

    useEffect(() => {
        setPage(1);
        setSearch(searchFromUrl);
    }, [searchFromUrl]);

    useEffect(() => {
        let cancelled = false;
        setCategoryError('');

        api.categories.list(false)
            .then((response) => {
                if (!cancelled) {
                    setCategories(response.data);
                }
            })
            .catch(() => {
                if (!cancelled) {
                    setCategories([]);
                    setCategoryError('分类加载失败，暂时无法按分类筛选。');
                }
            });

        return () => {
            cancelled = true;
        };
    }, []);

    const fetchResources = useCallback(async () => {
        setLoading(true);
        setLoadError('');
        try {
            const params: AdminResourceListParams = {
                page,
                page_size: PAGE_SIZE,
            };
            const normalizedSearch = search.trim();
            if (normalizedSearch) {
                params.search = normalizedSearch;
            }
            if (categoryId) {
                params.category_id = Number(categoryId);
            }
            if (publicationFilter !== 'all') {
                params.is_published = publicationFilter === 'published';
            }

            const response = await api.admin.getResources(params);
            setResources(response.data.items);
            setTotal(response.data.total);
            setPages(response.data.pages);
        } catch {
            setResources([]);
            setTotal(0);
            setPages(0);
            setLoadError('资源加载失败，请稍后重试。');
        } finally {
            setLoading(false);
        }
    }, [categoryId, page, publicationFilter, search]);

    useEffect(() => {
        fetchResources();
    }, [fetchResources]);

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
                        aria-label="搜索资源标题"
                        placeholder="搜索资源标题..."
                        value={search}
                        onChange={(event) => {
                            setPage(1);
                            setSearch(event.target.value);
                        }}
                        className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
                    />
                </div>
                <select
                    aria-label="按分类筛选"
                    value={categoryId}
                    onChange={(event) => {
                        setPage(1);
                        setCategoryId(event.target.value);
                    }}
                    className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-primary bg-white"
                >
                    <option value="">所有分类</option>
                    {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                            {category.name}
                        </option>
                    ))}
                </select>
                <select
                    aria-label="按发布状态筛选"
                    value={publicationFilter}
                    onChange={(event) => {
                        setPage(1);
                        setPublicationFilter(event.target.value as PublicationFilter);
                    }}
                    className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-primary bg-white"
                >
                    <option value="all">所有状态</option>
                    <option value="published">已发布</option>
                    <option value="draft">草稿</option>
                </select>
            </div>

            {categoryError && (
                <div role="alert" className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                    {categoryError}
                </div>
            )}

            {loadError && (
                <div role="alert" className="mb-4 flex items-center justify-between gap-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    <span>{loadError}</span>
                    <button
                        type="button"
                        onClick={fetchResources}
                        className="font-medium underline underline-offset-2"
                    >
                        重新加载
                    </button>
                </div>
            )}

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
                        ) : resources.length === 0 ? (
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
                                            <ResourceCover
                                                src={resource.cover_image_url}
                                                alt={resource.title}
                                                className="w-full h-full object-cover"
                                            />
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
                                            {resource.category_id
                                                ? categoryNames.get(resource.category_id) || '未分类'
                                                : '未分类'}
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
                        disabled={pages === 0 || page >= pages}
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

export default function ResourceManagement() {
    return (
        <Suspense fallback={<div className="py-8 text-center text-gray-500">正在加载资源...</div>}>
            <ResourceManagementContent />
        </Suspense>
    );
}
