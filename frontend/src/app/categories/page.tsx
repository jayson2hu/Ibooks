import Link from 'next/link';
import { api } from '@/lib/api';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: '分类浏览',
    description: '按分类浏览所有资源，找到您感兴趣的内容',
};

export default async function CategoriesPage() {
    let categories = [];

    try {
        const response = await api.categories.list(true);
        categories = response.data || [];
    } catch (error) {
        console.error('Failed to fetch categories:', error);
    }

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold mb-4">资源分类</h1>
                    <p className="text-xl text-secondary">
                        浏览所有分类，找到您感兴趣的内容
                    </p>
                </div>

                {/* Categories Grid */}
                {categories.length > 0 ? (
                    <div className="grid grid-3 gap-6">
                        {categories.map((category: any) => (
                            <Link
                                key={category.id}
                                href={`/resources?category_id=${category.id}`}
                                className="card group hover:shadow-xl transition-all"
                            >
                                {/* Category Icon/Image */}
                                <div className="flex items-center gap-4 mb-4">
                                    {category.cover_image_url ? (
                                        <img
                                            src={category.cover_image_url}
                                            alt={category.name}
                                            className="w-16 h-16 rounded-lg object-cover"
                                        />
                                    ) : (
                                        <div
                                            className="w-16 h-16 rounded-lg flex items-center justify-center text-2xl"
                                            style={{ backgroundColor: category.color || '#6366f1' }}
                                        >
                                            {category.icon || '📁'}
                                        </div>
                                    )}

                                    <div className="flex-1">
                                        <h3 className="text-xl font-semibold group-hover:text-primary transition-colors">
                                            {category.name}
                                        </h3>
                                        <p className="text-sm text-tertiary">
                                            {category.resource_count || 0} 个资源
                                        </p>
                                    </div>
                                </div>

                                {/* Description */}
                                {category.description && (
                                    <p className="text-secondary text-sm line-clamp-2 mb-4">
                                        {category.description}
                                    </p>
                                )}

                                {/* View Link */}
                                <div className="text-primary text-sm font-medium flex items-center gap-1">
                                    查看资源
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-16">
                        <div className="text-6xl mb-4">📂</div>
                        <p className="text-xl text-secondary">暂无分类</p>
                    </div>
                )}

                {/* All Resources Link */}
                <div className="text-center mt-12">
                    <Link href="/resources" className="btn btn-secondary">
                        浏览所有资源
                    </Link>
                </div>
            </div>
        </div>
    );
}
