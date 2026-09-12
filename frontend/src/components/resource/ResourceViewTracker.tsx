'use client';

import { useEffect, useRef } from 'react';
import { api } from '@/lib/api';

interface ResourceViewTrackerProps {
    slug: string;
}

export default function ResourceViewTracker({ slug }: ResourceViewTrackerProps) {
    const recordedSlug = useRef<string | null>(null);

    useEffect(() => {
        if (recordedSlug.current === slug) {
            return;
        }
        recordedSlug.current = slug;
        void api.resources.recordView(slug).catch(() => {
            // Analytics must never make an otherwise valid resource page fail.
        });
    }, [slug]);

    return null;
}
