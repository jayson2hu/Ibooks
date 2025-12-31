'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface ResourceFormProps {
    initialData?: any;
    isEdit?: boolean;
}

export default function ResourceForm({ initialData, isEdit }: ResourceFormProps) {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [categories, setCategories] = useState<any[]>([]);

    const [formData, setFormData] = useState({
        title: '',
        slug: '',
        description: '',
        category_id: '',
        price: 0,
        original_price: 0,
        cloud_link: '',
        cloud_code: '',
        tags: '',
        is_published: true,
        is_featured: false,
        cover_image_url: '',
        ...initialData
    });

    useEffect(() => {
        // Fetch categories for dropdown
        const fetchCategories = async () => {
            try {
                const response = await api.categories.list(false);
                setCategories(response.data || []);
            } catch (error) {
                console.error('Failed to fetch categories', error);
            }
        };
        fetchCategories();
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload = {
                ...formData,
                price: Number(formData.price),
                original_price: Number(formData.original_price),
                category_id: Number(formData.category_id),
                tags: typeof formData.tags === 'string' ? formData.tags.split(',').map((t: string) => t.trim()) : formData.tags
            };

            if (isEdit && initialData?.id) {
                await api.resources.update(initialData.id, payload);
            } else {
                await api.resources.create(payload);
            }

            router.push('/admin/resources');
        } catch (error) {
            console.error('Submit failed:', error);
            alert('保存失败，请检查表单');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-4xl bg-white p-8 rounded-xl shadow-sm border border-gray-100">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Basic Info */}
                <div className="col-span-2">
                    <h3 className="text-lg font-semibold mb-4 border-b pb-2">基本信息</h3>
                </div>

                <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">资源标题</label>
                    <input
                        type="text"
                        name="title"
                        required
                        value={formData.title}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
                    <select
                        name="category_id"
                        required
                        value={formData.category_id}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    >
                        <option value="">选择分类</option>
                        {categories.map(cat => (
                            <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">标签 (逗号分隔)</label>
                    <input
                        type="text"
                        name="tags"
                        value={formData.tags}
                        onChange={handleChange}
                        placeholder="Python, 教程, 电子书"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea
                        name="description"
                        rows={4}
                        value={formData.description}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                {/* Pricing & Delivery */}
                <div className="col-span-2 mt-4">
                    <h3 className="text-lg font-semibold mb-4 border-b pb-2">价格与交付</h3>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">价格 (元)</label>
                    <input
                        type="number"
                        name="price"
                        min="0"
                        step="0.01"
                        value={formData.price}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">原价 (元)</label>
                    <input
                        type="number"
                        name="original_price"
                        min="0"
                        step="0.01"
                        value={formData.original_price}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">网盘链接</label>
                    <input
                        type="text"
                        name="cloud_link"
                        value={formData.cloud_link}
                        onChange={handleChange}
                        placeholder="https://pan.baidu.com/s/..."
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">提取码</label>
                    <input
                        type="text"
                        name="cloud_code"
                        value={formData.cloud_code}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">封面图片URL</label>
                    <input
                        type="text"
                        name="cover_image_url"
                        value={formData.cover_image_url}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                {/* Settings */}
                <div className="col-span-2 mt-4">
                    <h3 className="text-lg font-semibold mb-4 border-b pb-2">设置</h3>
                </div>

                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            name="is_published"
                            checked={formData.is_published}
                            onChange={handleChange}
                            className="w-5 h-5 text-primary rounded focus:ring-primary"
                        />
                        <span>立即发布</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            name="is_featured"
                            checked={formData.is_featured}
                            onChange={handleChange}
                            className="w-5 h-5 text-primary rounded focus:ring-primary"
                        />
                        <span>设为精选</span>
                    </label>
                </div>
            </div>

            <div className="flex justify-end gap-4 pt-6 border-t border-gray-100">
                <button
                    type="button"
                    onClick={() => router.back()}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                    取消
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    className="px-8 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50"
                >
                    {loading ? '保存中...' : '保存资源'}
                </button>
            </div>
        </form>
    );
}
