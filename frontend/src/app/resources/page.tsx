import { api } from '@/lib/api';
import ResourceCard from '@/components/resource/ResourceCard';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: '资源列表',
    description: '浏览所有可用的电子书、视频课程和技术文档',
};

interface PageProps {
    searchParams: {
        page?: string;
        category_id?: string;
        is_featured?: string;
        is_free?: string;
        search?: string;
    };
}

export default async function ResourcesPage({ searchParams }: PageProps) {
    const page = parseInt(searchParams.page || '1');
    const pageSize = 12;

    // Fetch resources from API
    let resources = [];
    let total = 0;
    let pages = 0;

    try {
        const response = await api.resources.list({
            page,
            page_size: pageSize,
            category_id: searchParams.category_id ? parseInt(searchParams.category_id) : undefined,
            is_featured: searchParams.is_featured === 'true' ? true : undefined,
            is_free: searchParams.is_free === 'true' ? true : undefined,
            search: searchParams.search,
        });

        const data = response.data;
        resources = data.items;
        total = data.total;
        pages = data.pages;
    } catch (error) {
        console.error('Failed to fetch resources:', error);
    }

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-4">
                        {searchParams.search ? `搜索: ${searchParams.search}` : '浏览资源'}
                    </h1>
                    <p className="text-secondary">
                        共找到 {total} 个资源
                    </p>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-8">
                    <a
                        href="/resources"
                        className={`btn ${!searchParams.is_featured && !searchParams.is_free ? 'btn-primary' : 'btn-secondary'}`}
                    >
                        全部
                    </a>
                    <a
                        href="/resources?is_featured=true"
                        className={`btn ${searchParams.is_featured === 'true' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                        精选推荐
                    </a>
                    <a
                        href="/resources?is_free=true"
                        className={`btn ${searchParams.is_free === 'true' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                        免费资源
                    </a>
                </div>

                {/* Resource Grid */}
                {resources.length > 0 ? (
                    <>
                        <div className="grid grid-4 gap-6 mb-8">
                            {resources.map((resource: any) => (
                                <ResourceCard key={resource.id} resource={resource} />
                            ))}
                        </div>

                        {/* Pagination */}
                        {pages > 1 && (
                            <div className="flex justify-center gap-2">
                                {page > 1 && (
                                    <a
                                        href={`/resources?page=${page - 1}`}
                                        className="btn btn-secondary"
                                    >
                                        上一页
                                    </a>
                                )}

                                {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                                    const pageNum = i + 1;
                                    return (
                                        <a
                                            key={pageNum}
                                            href={`/resources?page=${pageNum}`}
                                            className={`btn ${page === pageNum ? 'btn-primary' : 'btn-secondary'}`}
                                        >
                                            {pageNum}
                                        </a>
                                    );
                                })}

                                {page < pages && (
                                    <a
                                        href={`/resources?page=${page + 1}`}
                                        className="btn btn-secondary"
                                    >
                                        下一页
                                    </a>
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
