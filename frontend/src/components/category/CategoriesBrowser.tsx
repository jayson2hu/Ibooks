'use client';

import { useEffect, useState } from 'react';
import RetryableError from '@/components/common/RetryableError';
import ResourceCard from '@/components/resource/ResourceCard';
import { api } from '@/lib/api';
import type { Category, Resource } from '@/types';

interface Props {
    categories: Category[];
    initialResources: Resource[];
    categoriesLoadFailed?: boolean;
    initialResourcesLoadFailed?: boolean;
}

export default function CategoriesBrowser({
    categories,
    initialResources,
    categoriesLoadFailed = false,
    initialResourcesLoadFailed = false,
}: Props) {
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [resources, setResources] = useState<Resource[]>(initialResources);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(
        initialResourcesLoadFailed ? '资源加载失败，请稍后重试。' : '',
    );
    const [retryCategoryId, setRetryCategoryId] = useState<number | null | undefined>(undefined);

    useEffect(() => {
        setResources(initialResources);
        setError(initialResourcesLoadFailed ? '资源加载失败，请稍后重试。' : '');
        setRetryCategoryId(undefined);
    }, [initialResources, initialResourcesLoadFailed]);

    const selectCategory = async (categoryId: number | null) => {
        setSelectedId(categoryId);
        setError('');
        setRetryCategoryId(undefined);
        setLoading(true);
        try {
            const response = await api.resources.list({
                page: 1,
                page_size: 12,
                category_id: categoryId ?? undefined,
            });
            setResources(response.data?.items || []);
        } catch (err) {
            console.error('Failed to filter resources:', err);
            setError('资源加载失败，请稍后重试。');
            setRetryCategoryId(categoryId);
        } finally {
            setLoading(false);
        }
    };

    return (
        <section aria-label="分类筛选">
            {categoriesLoadFailed ? (
                <div className="mb-12">
                    <RetryableError message="分类加载失败，请稍后重试。" />
                </div>
            ) : categories.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                    <button type="button" onClick={() => selectCategory(null)} className={`card text-left group transition-all ${selectedId === null ? 'ring-2 ring-primary' : 'hover:shadow-xl'}`}>
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 rounded-lg bg-slate-100 flex items-center justify-center text-2xl">📚</div>
                            <div>
                                <h2 className="text-xl font-semibold group-hover:text-primary">全部资源</h2>
                                <p className="text-sm text-tertiary">浏览最新资源</p>
                            </div>
                        </div>
                    </button>
                    {categories.map((category) => (
                        <button key={category.id} type="button" onClick={() => selectCategory(category.id)} className={`card text-left group transition-all ${selectedId === category.id ? 'ring-2 ring-primary' : 'hover:shadow-xl'}`}>
                            <div className="flex items-center gap-4">
                                {category.cover_image_url ? (
                                    <>
                                        {/* Category covers may use arbitrary user-configured external hosts. */}
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img src={category.cover_image_url} alt="" className="w-16 h-16 rounded-lg object-cover" />
                                    </>
                                ) : (
                                    <div className="w-16 h-16 rounded-lg flex items-center justify-center text-2xl" style={{ backgroundColor: category.color || '#6366f1' }}>
                                        {category.icon || '📁'}
                                    </div>
                                )}
                                <div className="min-w-0">
                                    <h2 className="text-xl font-semibold truncate group-hover:text-primary">{category.name}</h2>
                                    <p className="text-sm text-tertiary">{category.resource_count || 0} 个资源</p>
                                </div>
                            </div>
                            {category.description && <p className="text-secondary text-sm line-clamp-2 mt-4">{category.description}</p>}
                        </button>
                    ))}
                </div>
            ) : <div className="text-center py-16 text-secondary">暂无分类</div>}

            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">{selectedId === null ? '最新资源' : '分类资源'}</h2>
                {loading && <span className="text-sm text-tertiary">加载中...</span>}
            </div>
            {error ? (
                <RetryableError
                    message={error}
                    onRetry={retryCategoryId === undefined
                        ? undefined
                        : () => void selectCategory(retryCategoryId)}
                />
            ) : resources.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {resources.map((resource) => <ResourceCard key={resource.id} resource={resource} />)}
                </div>
            ) : !loading && (
                <div className="text-center py-12 text-secondary">该分类暂无资源</div>
            )}
        </section>
    );
}
