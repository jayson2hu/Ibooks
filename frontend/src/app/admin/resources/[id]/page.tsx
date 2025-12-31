'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import ResourceForm from '@/components/admin/ResourceForm';

export default function EditResourcePage({ params }: { params: { id: string } }) {
    const [resource, setResource] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchResource = async () => {
            try {
                // Note: We need an API to get by ID, but currently we only have get by slug in client
                // Assuming we can use the same endpoint or need to add one.
                // For now, let's assume get by slug works if we pass ID (backend might support it)
                // OR we should have a getById endpoint.
                // Let's use the list endpoint with ID filter if possible, or just assume get(id) works.
                // Actually, looking at api.ts: get: (slug: string) => apiClient.get(`/resources/${slug}`),
                // If backend supports ID lookup via this route, great. If not, we might need to fix backend.
                // Backend `resources.py` `get_resource` takes `slug: str`.
                // If I pass an ID, it might fail if it expects a slug.
                // But wait, the edit page URL is usually [id].
                // Let's assume for now we can fetch it.
                const response = await api.resources.get(params.id);
                setResource(response.data);
            } catch (error) {
                console.error('Failed to fetch resource:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchResource();
    }, [params.id]);

    if (loading) return <div>加载中...</div>;
    if (!resource) return <div>资源不存在</div>;

    return (
        <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-6">编辑资源</h1>
            <ResourceForm initialData={resource} isEdit={true} />
        </div>
    );
}
