import { api } from '@/lib/api';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

interface PageProps {
    params: {
        slug: string;
    };
}

// Generate metadata for SEO
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    try {
        const response = await api.resources.get(params.slug);
        const resource = response.data;

        return {
            title: resource.meta_title || resource.title,
            description: resource.meta_description || resource.excerpt || resource.description,
            keywords: resource.meta_keywords?.split(',') || resource.tags,
            openGraph: {
                title: resource.title,
                description: resource.excerpt || resource.description,
                images: resource.cover_image_url ? [resource.cover_image_url] : [],
                type: 'website',
            },
        };
    } catch (error) {
        return {
            title: '资源详情',
        };
    }
}

export default async function ResourceDetailPage({ params }: PageProps) {
    let resource = null;

    try {
        const response = await api.resources.get(params.slug);
        resource = response.data;
    } catch (error) {
        notFound();
    }

    if (!resource) {
        notFound();
    }

    // JSON-LD structured data for SEO
    const jsonLd = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        name: resource.title,
        description: resource.description,
        image: resource.cover_image_url,
        offers: {
            '@type': 'Offer',
            price: resource.price,
            priceCurrency: 'CNY',
            availability: 'https://schema.org/InStock',
        },
    };

    return (
        <>
            {/* JSON-LD */}
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
            />

            <div className="min-h-screen pt-20">
                <div className="container py-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Main Content */}
                        <div className="lg:col-span-2">
                            {/* Cover Image */}
                            <div className="relative h-96 bg-gray-200 rounded-lg overflow-hidden mb-6">
                                {resource.cover_image_url ? (
                                    <img
                                        src={resource.cover_image_url}
                                        alt={resource.title}
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-8xl">
                                        📁
                                    </div>
                                )}
                            </div>

                            {/* Title and Description */}
                            <div className="mb-8">
                                <div className="flex items-center gap-3 mb-4">
                                    {resource.is_featured && (
                                        <span className="badge bg-accent">精选</span>
                                    )}
                                    {resource.is_free && (
                                        <span className="badge bg-success">免费</span>
                                    )}
                                </div>

                                <h1 className="text-4xl font-bold mb-4">{resource.title}</h1>

                                {resource.excerpt && (
                                    <p className="text-xl text-secondary mb-4">{resource.excerpt}</p>
                                )}

                                {/* Stats */}
                                <div className="flex items-center gap-6 text-tertiary">
                                    <span className="flex items-center gap-2">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                        </svg>
                                        {resource.view_count} 次查看
                                    </span>
                                    <span className="flex items-center gap-2">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        {resource.download_count} 次下载
                                    </span>
                                </div>
                            </div>

                            {/* Description */}
                            <div className="prose max-w-none mb-8">
                                <h2 className="text-2xl font-bold mb-4">详细介绍</h2>
                                <div className="text-secondary whitespace-pre-wrap">
                                    {resource.description}
                                </div>
                            </div>

                            {/* Tags */}
                            {resource.tags && resource.tags.length > 0 && (
                                <div className="mb-8">
                                    <h3 className="text-xl font-semibold mb-3">标签</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {resource.tags.map((tag: string, index: number) => (
                                            <span
                                                key={index}
                                                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                                            >
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Sidebar */}
                        <div className="lg:col-span-1">
                            <div className="card sticky top-24">
                                {/* Price */}
                                <div className="mb-6">
                                    {resource.original_price && resource.original_price > resource.price && (
                                        <span className="text-tertiary line-through text-sm block mb-1">
                                            ¥{resource.original_price}
                                        </span>
                                    )}
                                    {resource.is_free ? (
                                        <span className="text-3xl font-bold text-success">免费</span>
                                    ) : (
                                        <span className="text-3xl font-bold text-primary">¥{resource.price}</span>
                                    )}
                                </div>

                                {/* Info */}
                                <div className="space-y-3 mb-6 text-sm">
                                    {resource.file_size && (
                                        <div className="flex justify-between">
                                            <span className="text-tertiary">文件大小</span>
                                            <span className="font-medium">{resource.file_size}</span>
                                        </div>
                                    )}
                                    {resource.file_format && (
                                        <div className="flex justify-between">
                                            <span className="text-tertiary">文件格式</span>
                                            <span className="font-medium">{resource.file_format}</span>
                                        </div>
                                    )}
                                    {resource.resource_type && (
                                        <div className="flex justify-between">
                                            <span className="text-tertiary">资源类型</span>
                                            <span className="font-medium">{resource.resource_type}</span>
                                        </div>
                                    )}
                                </div>

                                {/* CTA */}
                                <button className="btn btn-primary w-full mb-3">
                                    获取资源
                                </button>
                                <button className="btn btn-secondary w-full">
                                    分享
                                </button>

                                {/* Note */}
                                <p className="text-xs text-tertiary mt-4 text-center">
                                    资源通过云盘链接交付
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
