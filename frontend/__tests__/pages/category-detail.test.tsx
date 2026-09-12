import { render, screen } from '@testing-library/react';
import { notFound } from 'next/navigation';

import CategoryDetailPage, { generateMetadata } from '@/app/categories/[slug]/page';
import { api, getApiErrorStatus } from '@/lib/api';

jest.mock('next/navigation', () => ({
    notFound: jest.fn(() => {
        throw new Error('NEXT_NOT_FOUND');
    }),
}));

jest.mock('@/lib/api', () => ({
    getApiErrorStatus: jest.fn(),
    api: {
        categories: { get: jest.fn() },
        resources: { list: jest.fn() },
    },
}));

jest.mock('@/components/resource/ResourceCard', () => ({
    __esModule: true,
    default: ({ resource }: { resource: { title: string } }) => <div>{resource.title}</div>,
}));

describe('CategoryDetailPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders the category URL emitted by the sitemap', async () => {
        jest.mocked(api.categories.get).mockResolvedValue({
            data: {
                id: 7,
                name: '编程开发',
                slug: 'programming',
                description: '开发资源',
                icon: '💻',
            },
        } as never);
        jest.mocked(api.resources.list).mockResolvedValue({
            data: {
                items: [{ id: 11, title: 'Python 指南' }],
            },
        } as never);

        const page = await CategoryDetailPage({
            params: Promise.resolve({ slug: 'programming' }),
        });
        render(page);

        expect(screen.getByRole('heading', { name: '编程开发' })).toBeInTheDocument();
        expect(screen.getByText('Python 指南')).toBeInTheDocument();
        expect(api.resources.list).toHaveBeenCalledWith({
            page: 1,
            page_size: 24,
            category_id: 7,
        });
    });

    it('publishes category-specific metadata and a canonical URL', async () => {
        jest.mocked(api.categories.get).mockResolvedValue({
            data: {
                id: 8,
                name: '产品设计',
                slug: 'product-design',
                description: '设计资源',
            },
        } as never);

        await expect(generateMetadata({
            params: Promise.resolve({ slug: 'product-design' }),
        })).resolves.toMatchObject({
            title: '产品设计',
            description: '设计资源',
            alternates: { canonical: '/categories/product-design' },
        });
    });

    it('uses the not-found route only when the category API returns 404', async () => {
        const failure = new Error('missing category');
        jest.mocked(api.categories.get).mockRejectedValue(failure);
        jest.mocked(getApiErrorStatus).mockReturnValue(404);

        await expect(CategoryDetailPage({
            params: Promise.resolve({ slug: 'missing' }),
        })).rejects.toThrow('NEXT_NOT_FOUND');

        expect(notFound).toHaveBeenCalledTimes(1);
    });

    it('lets server and network failures reach the route error boundary', async () => {
        const failure = new Error('upstream unavailable');
        jest.mocked(api.categories.get).mockRejectedValue(failure);
        jest.mocked(getApiErrorStatus).mockReturnValue(500);

        await expect(CategoryDetailPage({
            params: Promise.resolve({ slug: 'programming' }),
        })).rejects.toBe(failure);

        expect(notFound).not.toHaveBeenCalled();
    });

    it('shows a real reload action when category resources fail', async () => {
        jest.mocked(api.categories.get).mockResolvedValue({
            data: {
                id: 7,
                name: '编程开发',
                slug: 'programming',
                description: '开发资源',
            },
        } as never);
        jest.mocked(api.resources.list).mockRejectedValue(new Error('network error'));

        const page = await CategoryDetailPage({
            params: Promise.resolve({ slug: 'programming' }),
        });
        render(page);

        expect(screen.getByRole('alert')).toHaveTextContent('分类资源加载失败');
        expect(screen.getByRole('link', { name: '重新加载' })).toHaveAttribute(
            'href',
            '/categories/programming',
        );
        expect(screen.queryByText('该分类暂无已发布资源')).not.toBeInTheDocument();
    });
});
