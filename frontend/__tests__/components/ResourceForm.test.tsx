import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ResourceForm from '@/components/admin/ResourceForm';
import { api } from '@/lib/api';
import type { Category, ResourceDetail } from '@/types';

const push = jest.fn();
const back = jest.fn();

jest.mock('next/navigation', () => ({
    useRouter: () => ({ push, back }),
}));

jest.mock('@/lib/api', () => ({
    api: {
        categories: { list: jest.fn() },
        resources: { create: jest.fn(), update: jest.fn() },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const category: Category = {
    id: 7,
    name: '技术资料',
    slug: 'technical',
    description: null,
    parent_id: null,
    icon: null,
    color: null,
    cover_image_url: null,
    is_active: true,
    sort_order: 0,
    resource_count: 0,
    created_at: '2026-09-10T00:00:00Z',
};

const listCategoriesMock = api.categories.list as jest.MockedFunction<typeof api.categories.list>;
const createResourceMock = api.resources.create as jest.MockedFunction<typeof api.resources.create>;
const updateResourceMock = api.resources.update as jest.MockedFunction<typeof api.resources.update>;

async function selectRequiredFields(title: string) {
    await screen.findByRole('option', { name: '技术资料' });
    fireEvent.change(screen.getByLabelText('资源标题'), { target: { value: title } });
    fireEvent.change(screen.getByLabelText('分类'), { target: { value: String(category.id) } });
}

describe('ResourceForm multi-value URLs', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        listCategoriesMock.mockResolvedValue({ data: [category] } as never);
        createResourceMock.mockResolvedValue({ data: { id: 1 } } as never);
        updateResourceMock.mockResolvedValue({ data: { id: 42 } } as never);
    });

    it('creates a resource with trimmed backup links and preview images', async () => {
        render(<ResourceForm />);
        await selectRequiredFields('多链接资源');

        fireEvent.change(screen.getByLabelText('备用网盘链接'), {
            target: {
                value: '  https://backup.example.com/resource  \n\nhttps://mirror.example.com/resource',
            },
        });
        fireEvent.change(screen.getByLabelText('预览图片 URL'), {
            target: {
                value: 'https://images.example.com/preview-1.jpg\n https://images.example.com/preview-2.jpg ',
            },
        });
        fireEvent.click(screen.getByRole('button', { name: '保存资源' }));

        await waitFor(() => expect(createResourceMock).toHaveBeenCalledWith(expect.objectContaining({
            backup_links: [
                'https://backup.example.com/resource',
                'https://mirror.example.com/resource',
            ],
            preview_images: [
                'https://images.example.com/preview-1.jpg',
                'https://images.example.com/preview-2.jpg',
            ],
        })));
        expect(push).toHaveBeenCalledWith('/admin/resources');
    });

    it('loads and updates existing URL arrays, including clearing backup links', async () => {
        const resource: Partial<ResourceDetail> = {
            id: 42,
            title: '已有资源',
            category_id: category.id,
            tags: ['测试'],
            backup_links: [
                'https://backup.example.com/old',
                'https://mirror.example.com/old',
            ],
            preview_images: ['https://images.example.com/old.jpg'],
            is_published: true,
            is_featured: false,
        };

        render(<ResourceForm initialData={resource} isEdit />);
        await screen.findByRole('option', { name: '技术资料' });
        expect(screen.getByLabelText('备用网盘链接')).toHaveValue(
            'https://backup.example.com/old\nhttps://mirror.example.com/old',
        );
        expect(screen.getByLabelText('预览图片 URL')).toHaveValue(
            'https://images.example.com/old.jpg',
        );

        fireEvent.change(screen.getByLabelText('备用网盘链接'), { target: { value: '' } });
        fireEvent.change(screen.getByLabelText('预览图片 URL'), {
            target: { value: 'https://images.example.com/new.jpg' },
        });
        fireEvent.click(screen.getByRole('button', { name: '保存资源' }));

        await waitFor(() => expect(updateResourceMock).toHaveBeenCalledWith(42, expect.objectContaining({
            backup_links: [],
            preview_images: ['https://images.example.com/new.jpg'],
        })));
        expect(push).toHaveBeenCalledWith('/admin/resources');
    });

    it('shows inline errors and does not submit malformed or duplicate URLs', async () => {
        render(<ResourceForm />);
        await selectRequiredFields('无效链接资源');

        fireEvent.change(screen.getByLabelText('备用网盘链接'), {
            target: { value: 'ftp://example.com/file' },
        });
        fireEvent.change(screen.getByLabelText('预览图片 URL'), {
            target: {
                value: 'https://images.example.com/repeated.jpg\nhttps://images.example.com/repeated.jpg',
            },
        });
        fireEvent.click(screen.getByRole('button', { name: '保存资源' }));

        expect(await screen.findByText('备用网盘链接第 1 行必须是有效的 HTTP/HTTPS URL')).toBeInTheDocument();
        expect(screen.getByText('预览图片 URL不能包含重复 URL')).toBeInTheDocument();
        expect(createResourceMock).not.toHaveBeenCalled();
        expect(updateResourceMock).not.toHaveBeenCalled();
    });
});
