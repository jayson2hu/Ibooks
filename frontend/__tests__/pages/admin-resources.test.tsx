import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import ResourceManagement from '@/app/admin/resources/page';
import { api } from '@/lib/api';
import type { Resource } from '@/types';

jest.mock('next/navigation', () => ({
    useSearchParams: () => new URLSearchParams('search=Python'),
}));

jest.mock('@/lib/api', () => ({
    api: {
        admin: {
            getResources: jest.fn(),
        },
        categories: {
            list: jest.fn(),
        },
        resources: {
            delete: jest.fn(),
        },
    },
}));

jest.mock('@/components/common/ResourceCover', () => ({
    __esModule: true,
    default: ({ alt }: { alt: string }) => <span>{alt}</span>,
}));

const draftResource: Resource = {
    id: 9,
    title: 'Python 草稿',
    slug: 'python-draft',
    category_id: 7,
    tags: [],
    price: 0,
    coin_price: 0,
    is_free: true,
    is_published: false,
    is_featured: false,
    view_count: 1,
    download_count: 0,
    created_at: '2026-09-10T00:00:00Z',
    updated_at: '2026-09-10T00:00:00Z',
};

describe('ResourceManagement', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.mocked(api.categories.list).mockResolvedValue({
            data: [{
                id: 7,
                name: '电子书',
                slug: 'ebooks',
                is_active: true,
                sort_order: 0,
                resource_count: 1,
                created_at: '2026-09-10T00:00:00Z',
            }],
        } as never);
        jest.mocked(api.admin.getResources).mockResolvedValue({
            data: {
                items: [draftResource],
                total: 1,
                page: 1,
                page_size: 10,
                pages: 1,
            },
        } as never);
    });

    it('uses the admin inventory with the header search query', async () => {
        render(<ResourceManagement />);

        expect(screen.getByRole('textbox', { name: '搜索资源标题' })).toHaveValue('Python');
        await waitFor(() => expect(api.admin.getResources).toHaveBeenCalledWith({
            page: 1,
            page_size: 10,
            search: 'Python',
        }));
        expect(api.categories.list).toHaveBeenCalledWith(false);
    });

    it('passes controlled category and draft filters to the admin API', async () => {
        render(<ResourceManagement />);

        const categorySelect = await screen.findByRole('combobox', { name: '按分类筛选' });
        fireEvent.change(categorySelect, { target: { value: '7' } });

        await waitFor(() => expect(api.admin.getResources).toHaveBeenLastCalledWith({
            page: 1,
            page_size: 10,
            search: 'Python',
            category_id: 7,
        }));

        fireEvent.change(
            screen.getByRole('combobox', { name: '按发布状态筛选' }),
            { target: { value: 'draft' } },
        );

        await waitFor(() => expect(api.admin.getResources).toHaveBeenLastCalledWith({
            page: 1,
            page_size: 10,
            search: 'Python',
            category_id: 7,
            is_published: false,
        }));
    });

    it('renders draft resources with their category name', async () => {
        render(<ResourceManagement />);

        const row = (await screen.findByTitle('Python 草稿')).closest('tr');
        expect(row).not.toBeNull();
        expect(within(row as HTMLTableRowElement).getByText('草稿')).toBeInTheDocument();
        expect(within(row as HTMLTableRowElement).getByText('电子书')).toBeInTheDocument();
    });

    it('shows an actionable error when the admin inventory cannot load', async () => {
        jest.mocked(api.admin.getResources).mockRejectedValueOnce(new Error('network down'));

        render(<ResourceManagement />);

        expect(await screen.findByText('资源加载失败，请稍后重试。')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: '重新加载' })).toBeInTheDocument();
    });
});
