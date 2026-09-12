import { api } from '@/lib/api';
import type { Metadata } from 'next';
import CategoriesBrowser from '@/components/category/CategoriesBrowser';
import type { Category, Resource } from '@/types';

export const metadata: Metadata = {
    title: '分类浏览',
    description: '按分类浏览所有资源，找到您感兴趣的内容',
};

// Docker builds the frontend before the backend is running. Fetch mutable
// catalog data at request time so a build-time outage cannot freeze an empty page.
export const dynamic = 'force-dynamic';

export default async function CategoriesPage() {
    let categories: Category[] = [];
    let initialResources: Resource[] = [];
    let categoriesLoadFailed = false;
    let initialResourcesLoadFailed = false;

    try {
        const categoryResponse = await api.categories.list(true);
        categories = categoryResponse.data || [];
    } catch (error) {
        console.error('Failed to fetch categories:', error);
        categoriesLoadFailed = true;
    }
    try {
        const resourceResponse = await api.resources.list({ page: 1, page_size: 12 });
        initialResources = resourceResponse.data?.items || [];
    } catch (error) {
        console.error('Failed to fetch initial resources:', error);
        initialResourcesLoadFailed = true;
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

                <CategoriesBrowser
                    categories={categories}
                    initialResources={initialResources}
                    categoriesLoadFailed={categoriesLoadFailed}
                    initialResourcesLoadFailed={initialResourcesLoadFailed}
                />
            </div>
        </div>
    );
}
