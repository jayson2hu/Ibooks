'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, getApiErrorMessage } from '@/lib/api';
import type { Category, ResourceDetail } from '@/types';

interface ResourceFormProps {
    initialData?: Partial<ResourceDetail>;
    isEdit?: boolean;
}

interface ResourceFormData {
    title: string;
    slug: string;
    description: string;
    category_id: number | '';
    price: number | string;
    coin_price: number | string;
    original_price: number | string;
    cloud_link: string;
    backup_links: string;
    access_code: string;
    tags: string;
    is_published: boolean;
    is_featured: boolean;
    cover_image_url: string;
    preview_images: string;
}

type MultiUrlField = 'backup_links' | 'preview_images';
type ResourceFormErrors = Partial<Record<MultiUrlField, string>>;

const MAX_RESOURCE_URLS = 20;
const MAX_RESOURCE_URL_LENGTH = 2048;

function parseAndValidateUrlLines(value: string, label: string): { urls: string[]; error?: string } {
    const urls = value
        .split(/\r?\n/)
        .map((url) => url.trim())
        .filter(Boolean);

    if (urls.length > MAX_RESOURCE_URLS) {
        return { urls, error: `${label}最多填写 ${MAX_RESOURCE_URLS} 条` };
    }

    const seen = new Set<string>();
    for (const [index, url] of urls.entries()) {
        if (url.length > MAX_RESOURCE_URL_LENGTH) {
            return { urls, error: `${label}第 ${index + 1} 行不能超过 ${MAX_RESOURCE_URL_LENGTH} 个字符` };
        }
        if (/\s/.test(url) || !/^https?:\/\/[^/?#]+(?:[/?#]|$)/i.test(url)) {
            return { urls, error: `${label}第 ${index + 1} 行必须是有效的 HTTP/HTTPS URL` };
        }

        try {
            const parsed = new URL(url);
            if (
                !['http:', 'https:'].includes(parsed.protocol)
                || !parsed.hostname
                || parsed.username
                || parsed.password
            ) {
                return { urls, error: `${label}第 ${index + 1} 行必须是无账号凭据的 HTTP/HTTPS URL` };
            }
        } catch {
            return { urls, error: `${label}第 ${index + 1} 行必须是有效的 HTTP/HTTPS URL` };
        }

        if (seen.has(url)) {
            return { urls, error: `${label}不能包含重复 URL` };
        }
        seen.add(url);
    }

    return { urls };
}

export default function ResourceForm({ initialData, isEdit }: ResourceFormProps) {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [categories, setCategories] = useState<Category[]>([]);
    const [fieldErrors, setFieldErrors] = useState<ResourceFormErrors>({});

    const [formData, setFormData] = useState<ResourceFormData>(() => ({
        title: initialData?.title || '',
        slug: initialData?.slug || '',
        description: initialData?.description || '',
        category_id: initialData?.category_id ?? '',
        price: initialData?.price ?? 0,
        coin_price: initialData?.coin_price ?? 0,
        original_price: initialData?.original_price ?? 0,
        cloud_link: initialData?.cloud_link || '',
        backup_links: initialData?.backup_links?.join('\n') || '',
        access_code: initialData?.access_code || '',
        tags: initialData?.tags?.join(', ') || '',
        is_published: initialData?.is_published ?? true,
        is_featured: initialData?.is_featured ?? false,
        cover_image_url: initialData?.cover_image_url || '',
        preview_images: initialData?.preview_images?.join('\n') || '',
    }));

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
        setFormData((prev) => ({
            ...prev,
            [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
        }));
        if (name === 'backup_links' || name === 'preview_images') {
            setFieldErrors((current) => ({ ...current, [name]: undefined }));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const backupLinks = parseAndValidateUrlLines(formData.backup_links, '备用网盘链接');
        const previewImages = parseAndValidateUrlLines(formData.preview_images, '预览图片 URL');
        const nextErrors: ResourceFormErrors = {
            backup_links: backupLinks.error,
            preview_images: previewImages.error,
        };
        setFieldErrors(nextErrors);
        if (backupLinks.error || previewImages.error) {
            return;
        }

        setLoading(true);

        try {
            const payload = {
                ...formData,
                price: Number(formData.price),
                coin_price: Number(formData.coin_price),
                original_price: Number(formData.original_price),
                category_id: Number(formData.category_id),
                tags: typeof formData.tags === 'string' ? formData.tags.split(',').map((t: string) => t.trim()) : formData.tags,
                backup_links: backupLinks.urls,
                preview_images: previewImages.urls,
            };

            if (isEdit && initialData?.id) {
                await api.resources.update(initialData.id, payload);
            } else {
                await api.resources.create(payload);
            }

            router.push('/admin/resources');
        } catch (error: unknown) {
            alert(getApiErrorMessage(error, '保存失败，请检查表单'));
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
                    <label htmlFor="resource-title" className="block text-sm font-medium text-gray-700 mb-1">资源标题</label>
                    <input
                        id="resource-title"
                        type="text"
                        name="title"
                        required
                        value={formData.title}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                </div>

                <div>
                    <label htmlFor="resource-category" className="block text-sm font-medium text-gray-700 mb-1">分类</label>
                    <select
                        id="resource-category"
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

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">售价 (书币)</label>
                    <input
                        type="number"
                        name="coin_price"
                        min="0"
                        step="1"
                        value={formData.coin_price}
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

                <div className="col-span-2">
                    <label htmlFor="resource-backup-links" className="block text-sm font-medium text-gray-700 mb-1">
                        备用网盘链接
                    </label>
                    <textarea
                        id="resource-backup-links"
                        name="backup_links"
                        rows={4}
                        value={formData.backup_links}
                        onChange={handleChange}
                        disabled={loading}
                        aria-invalid={Boolean(fieldErrors.backup_links)}
                        aria-describedby={fieldErrors.backup_links ? 'resource-backup-links-error' : 'resource-backup-links-help'}
                        placeholder={'https://backup.example.com/resource\nhttps://mirror.example.com/resource'}
                        className="w-full resize-y px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:bg-gray-100"
                    />
                    {fieldErrors.backup_links ? (
                        <p id="resource-backup-links-error" role="alert" className="mt-1 text-sm text-red-600">
                            {fieldErrors.backup_links}
                        </p>
                    ) : (
                        <p id="resource-backup-links-help" className="mt-1 text-xs text-gray-500">
                            每行一个 HTTP/HTTPS URL，最多 20 条；留空可清除全部备用链接。
                        </p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">提取码</label>
                    <input
                        type="text"
                        name="access_code"
                        value={formData.access_code}
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

                <div className="col-span-2">
                    <label htmlFor="resource-preview-images" className="block text-sm font-medium text-gray-700 mb-1">
                        预览图片 URL
                    </label>
                    <textarea
                        id="resource-preview-images"
                        name="preview_images"
                        rows={4}
                        value={formData.preview_images}
                        onChange={handleChange}
                        disabled={loading}
                        aria-invalid={Boolean(fieldErrors.preview_images)}
                        aria-describedby={fieldErrors.preview_images ? 'resource-preview-images-error' : 'resource-preview-images-help'}
                        placeholder={'https://images.example.com/preview-1.jpg\nhttps://images.example.com/preview-2.jpg'}
                        className="w-full resize-y px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:bg-gray-100"
                    />
                    {fieldErrors.preview_images ? (
                        <p id="resource-preview-images-error" role="alert" className="mt-1 text-sm text-red-600">
                            {fieldErrors.preview_images}
                        </p>
                    ) : (
                        <p id="resource-preview-images-help" className="mt-1 text-xs text-gray-500">
                            每行一个 HTTP/HTTPS 图片 URL，最多 20 条；保存顺序即展示顺序。
                        </p>
                    )}
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
