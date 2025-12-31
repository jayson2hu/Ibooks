'use client';

import ResourceForm from '@/components/admin/ResourceForm';

export default function NewResourcePage() {
    return (
        <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-6">发布新资源</h1>
            <ResourceForm />
        </div>
    );
}
