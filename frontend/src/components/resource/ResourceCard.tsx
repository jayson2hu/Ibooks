import Link from 'next/link';
import ResourceCover from '@/components/common/ResourceCover';
import type { Resource } from '@/types';

interface ResourceCardProps {
    resource: Resource;
}

export default function ResourceCard({ resource }: ResourceCardProps) {
    return (
        <Link href={`/resources/${resource.slug}`} className="card group">
            {/* Cover Image */}
            <div className="relative h-48 bg-gray-200 rounded-lg overflow-hidden mb-4">
                <ResourceCover
                    src={resource.cover_image_url}
                    alt={resource.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />

                {/* Badges */}
                <div className="absolute top-2 left-2 flex gap-2">
                    {resource.is_featured && (
                        <span className="badge bg-accent">精选</span>
                    )}
                    {resource.is_free && (
                        <span className="badge bg-success">免费</span>
                    )}
                </div>
            </div>

            {/* Content */}
            <div>
                <h3 className="font-semibold text-lg mb-2 line-clamp-2 group-hover:text-primary transition-colors">
                    {resource.title}
                </h3>

                {resource.excerpt && (
                    <p className="text-secondary text-sm mb-3 line-clamp-2">
                        {resource.excerpt}
                    </p>
                )}

                {/* Tags */}
                {resource.tags && resource.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                        {resource.tags.slice(0, 3).map((tag, index) => (
                            <span
                                key={index}
                                className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded"
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4 text-tertiary">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            {resource.view_count}
                        </span>
                    </div>

                    {resource.is_free ? (
                        <span className="font-bold text-success">免费</span>
                    ) : (
                        <span className="font-bold text-primary">
                            {resource.coin_price} 书币
                        </span>
                    )}
                </div>
            </div>
        </Link>
    );
}
