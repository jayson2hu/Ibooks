import { api } from '@/lib/api';
import ResourceCard from '@/components/resource/ResourceCard';
import type { Metadata } from 'next';
import Link from 'next/link';
import type { Resource } from '@/types';

export const metadata: Metadata = {
    title: '资源列表',
    description: '浏览所有可用的电子书、视频课程和技术文档',
};

interface PageProps {
    searchParams: Promise<{
        page?: string;
        category_id?: string;
        is_featured?: string;
        is_free?: string;
        search?: string;
    }>;
}

function buildResourcesHref(query: Awaited<PageProps['searchParams']>, page: number): string {
    const params = new URLSearchParams();
    if (page > 1) {
        params.set('page', String(page));
    }
    if (query.category_id) {
        params.set('category_id', query.category_id);
    }
    if (query.is_featured) {
        params.set('is_featured', query.is_featured);
    }
    if (query.is_free) {
        params.set('is_free', query.is_free);
    }
    if (query.search) {
        params.set('search', query.search);
    }

    const search = params.toString();
    return search ? `/resources?${search}` : '/resources';
}

export default async function ResourcesPage({ searchParams }: PageProps) {
    const query = await searchParams;
    const requestedPage = Number.parseInt(query.page || '1', 10);
    const page = Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1;
    const pageSize = 12;
    const requestedCategoryId = query.category_id
        ? Number.parseInt(query.category_id, 10)
        : undefined;
    const categoryId = requestedCategoryId && requestedCategoryId > 0
        ? requestedCategoryId
        : undefined;

    // Fetch resources from API
    let resources: Resource[] = [];
    let total = 0;
    let pages = 0;
    let loadFailed = false;

    try {
        const response = await api.resources.list({
            page,
            page_size: pageSize,
            category_id: categoryId,
            is_featured: query.is_featured === 'true' ? true : undefined,
            is_free: query.is_free === 'true' ? true : undefined,
            search: query.search,
        });

        const data = response.data;
        resources = data.items;
        total = data.total;
        pages = data.pages;
    } catch (error) {
        console.error('Failed to fetch resources:', error);
        loadFailed = true;
    }

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-4">
                        {query.search ? `搜索: ${query.search}` : '浏览资源'}
                    </h1>
                    {loadFailed ? (
                        <p className="text-secondary">资源数据暂时不可用</p>
                    ) : (
                        <p className="text-secondary">共找到 {total} 个资源</p>
                    )}
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-8">
                    <Link
                        href="/resources"
                        className={`btn ${!query.is_featured && !query.is_free ? 'btn-primary' : 'btn-secondary'}`}
                    >
                        全部
                    </Link>
                    <Link
                        href="/resources?is_featured=true"
                        className={`btn ${query.is_featured === 'true' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                        精选推荐
                    </Link>
                    <Link
                        href="/resources?is_free=true"
                        className={`btn ${query.is_free === 'true' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                        免费资源
                    </Link>
                </div>

                {/* Resource Grid */}
                {loadFailed ? (
                    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-8 text-center text-red-700">
                        <p className="text-lg font-medium">资源列表加载失败</p>
                        <p className="mt-2 text-sm">请检查网络连接，或稍后重新加载。</p>
                        <a
                            href={buildResourcesHref(query, page)}
                            className="mt-5 inline-flex rounded-lg bg-red-700 px-4 py-2 font-medium text-white hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
                        >
                            重新加载
                        </a>
                    </div>
                ) : resources.length > 0 ? (
                    <>
                        <div className="grid grid-4 gap-6 mb-8">
                            {resources.map((resource) => (
                                <ResourceCard key={resource.id} resource={resource} />
                            ))}
                        </div>

                        {/* Pagination */}
                        {pages > 1 && (
                            <div className="flex justify-center gap-2">
                                {page > 1 && (
                                    <Link
                                        href={buildResourcesHref(query, page - 1)}
                                        className="btn btn-secondary"
                                    >
                                        上一页
                                    </Link>
                                )}

                                {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                                    const pageNum = i + 1;
                                    return (
                                        <Link
                                            key={pageNum}
                                            href={buildResourcesHref(query, pageNum)}
                                            className={`btn ${page === pageNum ? 'btn-primary' : 'btn-secondary'}`}
                                        >
                                            {pageNum}
                                        </Link>
                                    );
                                })}

                                {page < pages && (
                                    <Link
                                        href={buildResourcesHref(query, page + 1)}
                                        className="btn btn-secondary"
                                    >
                                        下一页
                                    </Link>
                                )}
                            </div>
                        )}
                    </>
                ) : (
                    <div className="text-center py-16">
                        <div className="text-6xl mb-4">📭</div>
                        <p className="text-xl text-secondary">暂无资源</p>
                    </div>
                )}
            </div>
        </div>
    );
}
