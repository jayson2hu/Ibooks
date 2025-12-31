'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ResourceCard from '@/components/resource/ResourceCard';

export default function SearchPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const initialQuery = searchParams.get('q') || '';

    const [query, setQuery] = useState(initialQuery);
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        router.push(`/search?q=${encodeURIComponent(query)}`);

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/search?q=${encodeURIComponent(query)}&page=1&page_size=20`
            );
            const data = await response.json();
            setResults(data.items || []);
            setTotal(data.total || 0);
        } catch (error) {
            console.error('Search failed:', error);
            setResults([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Search Bar */}
                <div className="max-w-3xl mx-auto mb-12">
                    <h1 className="text-4xl font-bold text-center mb-8">搜索资源</h1>

                    <form onSubmit={handleSearch} className="relative">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="搜索电子书、课程、文档..."
                            className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-full focus:border-primary focus:outline-none"
                        />
                        <button
                            type="submit"
                            className="absolute right-2 top-1/2 -translate-y-1/2 btn btn-primary rounded-full px-8"
                        >
                            搜索
                        </button>
                    </form>

                    {/* Popular Searches */}
                    <div className="mt-6 text-center">
                        <span className="text-sm text-tertiary mr-3">热门搜索：</span>
                        {['Python', 'JavaScript', 'React', '机器学习', 'UI设计'].map((tag) => (
                            <button
                                key={tag}
                                onClick={() => {
                                    setQuery(tag);
                                    handleSearch(new Event('submit') as any);
                                }}
                                className="text-sm text-primary hover:underline mx-2"
                            >
                                {tag}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Results */}
                {loading ? (
                    <div className="text-center py-16">
                        <div className="text-2xl mb-4">🔍</div>
                        <p className="text-xl text-secondary">搜索中...</p>
                    </div>
                ) : results.length > 0 ? (
                    <>
                        <div className="mb-6">
                            <p className="text-secondary">
                                找到 <span className="font-semibold text-primary">{total}</span> 个相关结果
                            </p>
                        </div>

                        <div className="grid grid-4 gap-6">
                            {results.map((resource) => (
                                <ResourceCard key={resource.id} resource={resource} />
                            ))}
                        </div>
                    </>
                ) : query ? (
                    <div className="text-center py-16">
                        <div className="text-3xl mb-4">🔍</div>
                        <p className="text-xl text-secondary mb-4">
                            没有找到与 "{query}" 相关的资源
                        </p>
                        <p className="text-secondary">
                            尝试使用其他关键词或浏览分类
                        </p>
                    </div>
                ) : (
                    <div className="text-center py-16">
                        <div className="text-3xl mb-4">🔎</div>
                        <p className="text-xl text-secondary">
                            输入关键词搜索您需要的资源
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
