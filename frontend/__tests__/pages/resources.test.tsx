import { render, screen } from '@testing-library/react';

import ResourcesPage from '@/app/resources/page';
import { api } from '@/lib/api';

jest.mock('@/lib/api', () => ({
    api: {
        resources: { list: jest.fn() },
    },
}));

jest.mock('@/components/resource/ResourceCard', () => ({
    __esModule: true,
    default: ({ resource }: { resource: { title: string } }) => <div>{resource.title}</div>,
}));

describe('ResourcesPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('shows a retryable error instead of a zero-count empty state after an API failure', async () => {
        jest.mocked(api.resources.list).mockRejectedValue(new Error('network unavailable'));

        const page = await ResourcesPage({
            searchParams: Promise.resolve({
                page: '2',
                category_id: '7',
                is_featured: 'true',
                search: 'Python 指南',
            }),
        });
        render(page);

        expect(screen.getByRole('alert')).toHaveTextContent('资源列表加载失败');
        expect(screen.getByRole('link', { name: '重新加载' })).toHaveAttribute(
            'href',
            '/resources?page=2&category_id=7&is_featured=true&search=Python+%E6%8C%87%E5%8D%97',
        );
        expect(screen.queryByText('共找到 0 个资源')).not.toBeInTheDocument();
        expect(screen.queryByText('暂无资源')).not.toBeInTheDocument();
    });

    it('preserves every active filter while paging', async () => {
        jest.mocked(api.resources.list).mockResolvedValue({
            data: {
                items: [{ id: 1, title: 'Python 指南' }],
                total: 40,
                page: 2,
                page_size: 12,
                pages: 4,
            },
        } as never);

        const page = await ResourcesPage({
            searchParams: Promise.resolve({
                page: '2',
                category_id: '7',
                is_featured: 'true',
                is_free: 'true',
                search: 'Python',
            }),
        });
        render(page);

        expect(screen.getByRole('link', { name: '上一页' })).toHaveAttribute(
            'href',
            '/resources?category_id=7&is_featured=true&is_free=true&search=Python',
        );
        expect(screen.getByRole('link', { name: '下一页' })).toHaveAttribute(
            'href',
            '/resources?page=3&category_id=7&is_featured=true&is_free=true&search=Python',
        );
    });
});
