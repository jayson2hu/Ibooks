'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BoltIcon, 
  ShieldCheckIcon, 
  SparklesIcon,
  RocketLaunchIcon,
  AcademicCapIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import HeroSection from '@/components/home/HeroSection';
import EnhancedSearchBar from '@/components/home/EnhancedSearchBar';
import ResourceCard from '@/components/home/ResourceCard';
import CategoryTabs from '@/components/home/CategoryTabs';
import { ResourceGridSkeleton } from '@/components/home/SkeletonLoader';
import { FeaturesSection } from '@/components/home/FeatureCard';
import {
    filterHomepageResources,
    type HomepageResourceFilter,
} from '@/lib/resourceFilters';

interface Resource {
    id: number;
    title: string;
    description: string;
    slug: string;
    resource_type: string;
    price: number;
    coin_price?: number;
    is_free: boolean;
    cover_image_url?: string;
    view_count?: number;
    created_at?: string;
}

interface ResourceListEnvelope {
    items?: Resource[];
    data?: Resource[];
}

function extractResources(payload: unknown): Resource[] {
    if (Array.isArray(payload)) {
        return payload as Resource[];
    }

    if (payload && typeof payload === 'object') {
        const envelope = payload as ResourceListEnvelope;
        if (Array.isArray(envelope.items)) {
            return envelope.items;
        }
        if (Array.isArray(envelope.data)) {
            return envelope.data;
        }
    }

    return [];
}

export default function HomePage() {
    const [featuredResources, setFeaturedResources] = useState<Resource[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<HomepageResourceFilter>('all');
    const router = useRouter();

    const fetchFeaturedResources = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.resources.list({ is_featured: true, page_size: 20 });
            setFeaturedResources(extractResources(response.data));
        } catch (error) {
            console.error('Failed to fetch featured resources:', error);
            setError('加载资源失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchFeaturedResources();
    }, [fetchFeaturedResources]);

    const handleSearch = (query: string, scope: string) => {
        if (query.trim()) {
            router.push(`/search?q=${encodeURIComponent(query)}&scope=${scope}`);
        }
    };

    const handleRetry = () => {
        fetchFeaturedResources();
    };

    // 分类标签配置
    const categoryTabs = [
        { id: 'all', label: '全部', icon: <SparklesIcon className="w-4 h-4" /> },
        { id: 'new', label: '最新', icon: <RocketLaunchIcon className="w-4 h-4" /> },
        { id: 'course', label: '视频课程', icon: <AcademicCapIcon className="w-4 h-4" /> },
        { id: 'ebook', label: '电子书', icon: <BookOpenIcon className="w-4 h-4" /> },
        { id: 'free', label: '免费资源', icon: <BoltIcon className="w-4 h-4" /> },
    ];

    // 特色功能配置
    const features = [
        {
            icon: <BoltIcon className="w-full h-full" />,
            title: '极速下载',
            description: '云盘直链交付，无需等待，即刻获取您需要的资源'
        },
        {
            icon: <ShieldCheckIcon className="w-full h-full" />,
            title: '安全保障',
            description: '所有资源经过严格审核，确保内容质量和安全性'
        },
        {
            icon: <SparklesIcon className="w-full h-full" />,
            title: '持续更新',
            description: '每日新增优质资源，保持内容新鲜度和时效性'
        },
    ];

    // 根据活动标签筛选资源
    const filteredResources = Array.isArray(featuredResources)
        ? filterHomepageResources(featuredResources, activeTab)
        : [];

    return (
        <>
            {/* 英雄区 */}
            <HeroSection
                title="发现优质资源，提升技能水平"
                subtitle="精选电子书、视频课程和技术文档，助力您的学习之旅"
            >
                <EnhancedSearchBar onSubmit={handleSearch} />
            </HeroSection>

            {/* 推荐资源区 */}
            <section className="py-16 bg-gradient-to-b from-white to-gray-50">
                <div className="container mx-auto px-4">
                    {/* 区块标题 */}
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-10">
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6 }}
                            className="flex items-center gap-3"
                        >
                            <div className="w-1 h-10 bg-gradient-to-b from-indigo-600 to-purple-600 rounded-full" />
                            <div>
                                <h2 className="text-2xl md:text-3xl font-bold text-gray-800">
                                    精选推荐
                                </h2>
                                <p className="text-sm text-gray-500 mt-1">为您精心挑选的优质资源</p>
                            </div>
                        </motion.div>

                        {/* 分类标签 */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6 }}
                        >
                            <CategoryTabs
                                tabs={categoryTabs}
                                activeTab={activeTab}
                                onChange={(tab) => setActiveTab(tab as HomepageResourceFilter)}
                            />
                        </motion.div>
                    </div>

                    {/* 资源网格 */}
                    {loading ? (
                        <ResourceGridSkeleton count={10} />
                    ) : error ? (
                        <div className="text-center py-20">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <p className="text-gray-600 mb-4">{error}</p>
                            <button
                                onClick={handleRetry}
                                className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200"
                            >
                                重试
                            </button>
                        </div>
                    ) : filteredResources.length > 0 ? (
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeTab}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3 }}
                                className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
                            >
                                {filteredResources.map((resource) => (
                                    <ResourceCard key={resource.id} resource={resource} />
                                ))}
                            </motion.div>
                        </AnimatePresence>
                    ) : (
                        <div className="text-center py-20">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                                </svg>
                            </div>
                            <p className="text-gray-500">暂无资源</p>
                        </div>
                    )}
                </div>
            </section>

            {/* 特色功能区 */}
            <FeaturesSection features={features} />
        </>
    );
}
