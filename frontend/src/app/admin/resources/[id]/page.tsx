'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import ResourceForm from '@/components/admin/ResourceForm';

export default function EditResourcePage() {
    const params = useParams<{ id: string }>();
    const [resource, setResource] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchResource = async () => {
            try {
                const response = await api.admin.getResource(Number(params.id));
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
