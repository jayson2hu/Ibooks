'use client';

import { useEffect, useState } from 'react';

interface ResourceCoverProps {
    src?: string | null;
    alt: string;
    className?: string;
    loading?: 'eager' | 'lazy';
}

function isSupportedImageSource(src?: string | null): src is string {
    if (!src) {
        return false;
    }

    return src.startsWith('/') || /^https?:\/\//i.test(src);
}

export default function ResourceCover({
    src,
    alt,
    className = 'w-full h-full object-cover',
    loading = 'lazy',
}: ResourceCoverProps) {
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        setFailed(false);
    }, [src]);

    if (!isSupportedImageSource(src) || failed) {
        return (
            <div
                role="img"
                aria-label={`${alt}（暂无封面）`}
                className={`relative flex items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 ${className}`}
            >
                <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-white/15" />
                <div className="absolute -bottom-8 -left-8 h-24 w-24 rounded-full bg-white/10" />
                <svg
                    aria-hidden="true"
                    className="relative h-1/3 w-1/3 min-h-8 min-w-8 max-h-16 max-w-16 text-white/95"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.8}
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                    />
                </svg>
            </div>
        );
    }

    return (
        // Resource covers may use arbitrary user-configured external hosts.
        // eslint-disable-next-line @next/next/no-img-element
        <img
            src={src}
            alt={alt}
            className={className}
            loading={loading}
            decoding="async"
            onError={() => setFailed(true)}
        />
    );
}
