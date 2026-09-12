'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ResourceCard from '@/components/resource/ResourceCard';
import { api } from '@/lib/api';
import type { Resource } from '@/types';

type SearchScope = 'all' | 'course' | 'ebook' | 'doc';

const PAGE_SIZE = 20;
const SEARCH_SCOPES: Array<{ value: SearchScope; label: string }> = [
    { value: 'all', label: '全站' },
    { value: 'course', label: '视频课程' },
    { value: 'ebook', label: '电子书' },
    { value: 'doc', label: '技术文档' },
];

function normalizeScope(value: string | null): SearchScope {
    return SEARCH_SCOPES.some((scope) => scope.value === value)
        ? value as SearchScope
        : 'all';
}

function normalizePage(value: string | null): number {
    const page = Number(value);
    return Number.isInteger(page) && page > 0 ? page : 1;
}

function buildSearchUrl(query: string, scope: SearchScope, page: number): string {
    return `/search?q=${encodeURIComponent(query)}&scope=${scope}&page=${page}`;
}

function SearchContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const initialQuery = searchParams.get('q') || '';
    const initialScope = normalizeScope(searchParams.get('scope'));
    const initialPage = normalizePage(searchParams.get('page'));

    const [query, setQuery] = useState(initialQuery);
    const [scope, setScope] = useState<SearchScope>(initialScope);
    const [results, setResults] = useState<Resource[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(0);
    const [error, setError] = useState('');
    const requestSequence = useRef(0);

    const fetchResults = useCallback(async (
        searchQuery: string,
        searchScope: SearchScope,
        searchPage: number,
    ) => {
        const normalizedQuery = searchQuery.trim();
        if (!normalizedQuery) {
            requestSequence.current += 1;
            setResults([]);
            setTotal(0);
            setPages(0);
            setError('');
            setLoading(false);
            return;
        }

        const requestId = ++requestSequence.current;
        setLoading(true);
        setError('');
        try {
            const response = await api.search(
                normalizedQuery,
                searchPage,
                PAGE_SIZE,
                searchScope,
            );
            const data = response.data;
            if (requestId === requestSequence.current) {
                setResults(data.items || []);
                setTotal(data.total || 0);
                setPages(data.pages || 0);
            }
        } catch (error) {
            console.error('Search failed:', error);
            if (requestId === requestSequence.current) {
                setResults([]);
                setTotal(0);
                setPages(0);
                setError('搜索服务暂时不可用，请稍后重试');
            }
        } finally {
            if (requestId === requestSequence.current) {
                setLoading(false);
            }
        }
    }, []);

    useEffect(() => {
        setQuery(initialQuery);
        setScope(initialScope);
        void fetchResults(initialQuery, initialScope, initialPage);
    }, [fetchResults, initialPage, initialQuery, initialScope]);

    const runSearch = (searchQuery: string, searchScope: SearchScope = scope) => {
        const normalizedQuery = searchQuery.trim();
        if (!normalizedQuery) return;

        setQuery(normalizedQuery);
        setScope(searchScope);
        if (
            normalizedQuery === initialQuery
            && searchScope === initialScope
            && initialPage === 1
        ) {
            void fetchResults(normalizedQuery, searchScope, 1);
            return;
        }
        router.push(buildSearchUrl(normalizedQuery, searchScope, 1));
    };

    const handleSearch = (event: React.FormEvent) => {
        event.preventDefault();
        runSearch(query, scope);
    };

    const navigateToPage = (page: number) => {
        if (page < 1 || page > pages || page === initialPage) return;
        router.push(buildSearchUrl(initialQuery, initialScope, page));
    };

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Search Bar */}
                <div className="max-w-3xl mx-auto mb-12">
                    <h1 className="text-4xl font-bold text-center mb-8">搜索资源</h1>

                    <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
                        <select
                            aria-label="搜索范围"
                            value={scope}
                            onChange={(event) => setScope(event.target.value as SearchScope)}
                            className="px-4 py-4 border-2 border-gray-300 rounded-full bg-white focus:border-primary focus:outline-none"
                        >
                            {SEARCH_SCOPES.map((searchScope) => (
                                <option key={searchScope.value} value={searchScope.value}>
                                    {searchScope.label}
                                </option>
                            ))}
                        </select>
                        <input
                            type="text"
                            aria-label="搜索关键词"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="搜索电子书、课程、文档..."
                            className="min-w-0 flex-1 px-6 py-4 text-lg border-2 border-gray-300 rounded-full focus:border-primary focus:outline-none"
                        />
                        <button
                            type="submit"
                            disabled={!query.trim() || loading}
                            className="btn btn-primary rounded-full px-8 disabled:cursor-not-allowed disabled:opacity-60"
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
                                type="button"
                                onClick={() => {
                                    setQuery(tag);
                                    runSearch(tag, scope);
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
                ) : error ? (
                    <div role="alert" className="text-center py-16">
                        <div className="text-3xl mb-4">⚠️</div>
                        <p className="text-xl text-red-700 mb-4">{error}</p>
                        <button
                            type="button"
                            onClick={() => void fetchResults(initialQuery, initialScope, initialPage)}
                            className="btn btn-primary"
                        >
                            重新搜索
                        </button>
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

                        {pages > 1 && (
                            <nav
                                aria-label="搜索结果分页"
                                className="mt-10 flex items-center justify-center gap-4"
                            >
                                <button
                                    type="button"
                                    onClick={() => navigateToPage(initialPage - 1)}
                                    disabled={initialPage <= 1}
                                    className="btn btn-secondary disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    上一页
                                </button>
                                <span className="text-secondary">
                                    第 {initialPage} / {pages} 页
                                </span>
                                <button
                                    type="button"
                                    onClick={() => navigateToPage(initialPage + 1)}
                                    disabled={initialPage >= pages}
                                    className="btn btn-secondary disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    下一页
                                </button>
                            </nav>
                        )}
                    </>
                ) : initialQuery ? (
                    <div className="text-center py-16">
                        <div className="text-3xl mb-4">🔍</div>
                        <p className="text-xl text-secondary mb-4">
                            没有找到与“{initialQuery}”相关的资源
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

export default function SearchPage() {
    return (
        <Suspense fallback={<div className="min-h-screen pt-20"><div className="container py-8 text-center text-gray-500">正在加载搜索...</div></div>}>
            <SearchContent />
        </Suspense>
    );
}
