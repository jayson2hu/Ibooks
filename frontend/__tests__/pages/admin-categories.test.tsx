import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import CategoriesPage from '@/app/admin/categories/page';
import { api, getApiErrorMessage } from '@/lib/api';
import type { Category } from '@/types';

jest.mock('@/lib/api', () => ({
    api: {
        categories: {
            list: jest.fn(),
            create: jest.fn(),
            update: jest.fn(),
            delete: jest.fn(),
        },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const listCategoriesMock = api.categories.list as jest.MockedFunction<typeof api.categories.list>;
const createCategoryMock = api.categories.create as jest.MockedFunction<typeof api.categories.create>;
const updateCategoryMock = api.categories.update as jest.MockedFunction<typeof api.categories.update>;
const mockedGetApiErrorMessage = getApiErrorMessage as jest.MockedFunction<typeof getApiErrorMessage>;

const categories: Category[] = [
    {
        id: 1,
        name: '父分类',
        slug: 'parent',
        description: '父分类描述',
        parent_id: null,
        is_active: true,
        sort_order: 0,
        resource_count: 2,
        created_at: '2026-09-10T00:00:00Z',
    },
    {
        id: 2,
        name: '子分类',
        slug: 'child',
        description: '子分类描述',
        parent_id: 1,
        is_active: false,
        sort_order: 3,
        resource_count: 0,
        created_at: '2026-09-10T00:00:00Z',
    },
    {
        id: 3,
        name: '其他分类',
        slug: 'other',
        description: null,
        parent_id: null,
        is_active: true,
        sort_order: 5,
        resource_count: 0,
        created_at: '2026-09-10T00:00:00Z',
    },
];

function createDeferred<Value>() {
    let resolve!: (value: Value) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<Value>((resolvePromise, rejectPromise) => {
        resolve = resolvePromise;
        reject = rejectPromise;
    });
    return { promise, resolve, reject };
}

async function renderCategoriesPage() {
    render(<CategoriesPage />);
    expect(await screen.findByText('父分类描述')).toBeInTheDocument();
}

describe('Admin categories management', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        listCategoriesMock.mockResolvedValue({ data: categories } as never);
        updateCategoryMock.mockImplementation(async (id, payload) => ({
            data: {
                ...categories.find((category) => category.id === id),
                ...payload,
                id,
                slug: id === 2 ? 'updated-child' : 'created-category',
            },
        } as never));
    });

    it('creates a category, applies display settings, and refreshes the list', async () => {
        const request = createDeferred<Awaited<ReturnType<typeof api.categories.create>>>();
        createCategoryMock.mockReturnValue(request.promise);
        await renderCategoriesPage();

        fireEvent.click(screen.getByRole('button', { name: '添加分类' }));
        const dialog = screen.getByRole('dialog', { name: '创建分类' });
        await waitFor(() => expect(within(dialog).getByLabelText(/分类名称/)).toHaveFocus());

        fireEvent.change(within(dialog).getByLabelText(/分类名称/), { target: { value: '新分类' } });
        fireEvent.change(within(dialog).getByLabelText('描述'), { target: { value: '新的分类描述' } });
        fireEvent.change(within(dialog).getByLabelText('父分类'), { target: { value: '1' } });
        fireEvent.change(within(dialog).getByLabelText(/排序值/), { target: { value: '7' } });
        fireEvent.click(within(dialog).getByRole('checkbox', { name: '启用分类' }));
        fireEvent.click(within(dialog).getByRole('button', { name: '保存分类' }));

        expect(await within(dialog).findByRole('button', { name: /保存中/ })).toBeDisabled();
        expect(createCategoryMock).toHaveBeenCalledWith({
            name: '新分类',
            description: '新的分类描述',
            parent_id: 1,
        });

        await act(async () => {
            request.resolve({
                data: {
                    ...categories[2],
                    id: 4,
                    name: '新分类',
                    slug: 'new-category',
                    description: '新的分类描述',
                    parent_id: 1,
                    sort_order: 0,
                    is_active: true,
                },
            } as never);
            await request.promise;
        });

        await waitFor(() => expect(updateCategoryMock).toHaveBeenCalledWith(4, {
            sort_order: 7,
            is_active: false,
        }));
        await waitFor(() => expect(listCategoriesMock).toHaveBeenCalledTimes(2));
        expect(await screen.findByRole('status')).toHaveTextContent('分类创建成功');
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('edits all mutable fields and excludes the category itself from parent choices', async () => {
        await renderCategoriesPage();
        const childRow = screen.getByRole('row', { name: /子分类 child/ });
        fireEvent.click(within(childRow).getByRole('button', { name: '编辑' }));

        const dialog = screen.getByRole('dialog', { name: '编辑分类' });
        expect(within(dialog).getByLabelText('Slug（自动生成）')).toHaveValue('child');
        expect(within(dialog).queryByRole('option', { name: /子分类/ })).not.toBeInTheDocument();

        fireEvent.change(within(dialog).getByLabelText(/分类名称/), { target: { value: '更新后的子分类' } });
        fireEvent.change(within(dialog).getByLabelText('描述'), { target: { value: '更新后的描述' } });
        fireEvent.change(within(dialog).getByLabelText('父分类'), { target: { value: '' } });
        fireEvent.change(within(dialog).getByLabelText(/排序值/), { target: { value: '8' } });
        fireEvent.click(within(dialog).getByRole('button', { name: '保存分类' }));

        await waitFor(() => expect(updateCategoryMock).toHaveBeenCalledWith(2, {
            name: '更新后的子分类',
            description: '更新后的描述',
            parent_id: null,
            sort_order: 8,
            is_active: false,
        }));
        expect(await screen.findByRole('status')).toHaveTextContent('分类更新成功');
    });

    it('validates required name and integer sort order before calling the API', async () => {
        await renderCategoriesPage();
        fireEvent.click(screen.getByRole('button', { name: '添加分类' }));
        const dialog = screen.getByRole('dialog', { name: '创建分类' });

        fireEvent.change(within(dialog).getByLabelText(/分类名称/), { target: { value: '   ' } });
        fireEvent.change(within(dialog).getByLabelText(/排序值/), { target: { value: '1.5' } });
        fireEvent.click(within(dialog).getByRole('button', { name: '保存分类' }));

        expect(await within(dialog).findByText('请输入分类名称')).toBeInTheDocument();
        expect(within(dialog).getByText('排序值必须是整数')).toBeInTheDocument();
        expect(createCategoryMock).not.toHaveBeenCalled();
    });

    it('shows backend errors and supports closing the dialog with Escape', async () => {
        createCategoryMock.mockRejectedValue(new Error('conflict'));
        mockedGetApiErrorMessage.mockReturnValueOnce('同名分类已存在');
        await renderCategoriesPage();
        const openButton = screen.getByRole('button', { name: '添加分类' });
        openButton.focus();
        fireEvent.click(openButton);
        const dialog = screen.getByRole('dialog', { name: '创建分类' });

        fireEvent.change(within(dialog).getByLabelText(/分类名称/), { target: { value: '重复分类' } });
        fireEvent.click(within(dialog).getByRole('button', { name: '保存分类' }));

        expect(await within(dialog).findByRole('alert')).toHaveTextContent('同名分类已存在');
        fireEvent.keyDown(document, { key: 'Escape' });
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        expect(openButton).toHaveFocus();
    });
});
