import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import ResourceCard from '@/components/resource/ResourceCard';
import { api, getApiErrorStatus } from '@/lib/api';
import type { Category, Resource } from '@/types';

interface PageProps {
    params: Promise<{
        slug: string;
    }>;
}

async function getCategory(slug: string): Promise<Category> {
    const response = await api.categories.get(slug);
    return response.data;
}

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    try {
        const { slug } = await params;
        const category = await getCategory(slug);
        return {
            title: category.name,
            description: category.description || `浏览${category.name}分类下的精选资源`,
            alternates: {
                canonical: `/categories/${category.slug}`,
            },
        };
    } catch (error) {
        return {
            title: getApiErrorStatus(error) === 404 ? '分类不存在' : '分类详情',
        };
    }
}

export default async function CategoryDetailPage({ params }: PageProps) {
    const { slug } = await params;

    let category: Category;
    try {
        category = await getCategory(slug);
    } catch (error) {
        if (getApiErrorStatus(error) === 404) {
            notFound();
        }
        throw error;
    }

    let resources: Resource[] = [];
    let loadFailed = false;
    try {
        const response = await api.resources.list({
            page: 1,
            page_size: 24,
            category_id: category.id,
        });
        resources = response.data?.items || [];
    } catch (error) {
        console.error('Failed to load category resources:', error);
        loadFailed = true;
    }

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                <nav aria-label="面包屑" className="mb-6 text-sm text-tertiary">
                    <Link href="/categories" className="hover:text-primary">资源分类</Link>
                    <span aria-hidden="true" className="mx-2">/</span>
                    <span>{category.name}</span>
                </nav>

                <header className="mb-10">
                    <div className="flex items-center gap-4">
                        <div
                            className="flex h-16 w-16 items-center justify-center rounded-xl text-3xl"
                            style={{ backgroundColor: category.color || '#eef2ff' }}
                            aria-hidden="true"
                        >
                            {category.icon || '📁'}
                        </div>
                        <div>
                            <h1 className="text-4xl font-bold">{category.name}</h1>
                            {category.description && (
                                <p className="mt-2 max-w-3xl text-secondary">{category.description}</p>
                            )}
                        </div>
                    </div>
                </header>

                {loadFailed ? (
                    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-6 text-center text-red-700">
                        <p>分类资源加载失败，请稍后重试。</p>
                        <a
                            href={`/categories/${encodeURIComponent(category.slug)}`}
                            className="mt-4 inline-flex rounded-lg bg-red-700 px-4 py-2 font-medium text-white hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
                        >
                            重新加载
                        </a>
                    </div>
                ) : resources.length > 0 ? (
                    <section aria-label={`${category.name}资源`} className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                        {resources.map((resource) => (
                            <ResourceCard key={resource.id} resource={resource} />
                        ))}
                    </section>
                ) : (
                    <div className="rounded-lg border border-gray-100 bg-white py-16 text-center text-secondary">
                        该分类暂无已发布资源
                    </div>
                )}
            </div>
        </div>
    );
}
