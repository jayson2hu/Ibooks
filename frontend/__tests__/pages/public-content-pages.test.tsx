import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import CategoriesPage from '@/app/categories/page';
import ContactPage from '@/app/contact/page';
import FAQPage from '@/app/faq/page';
import CategoriesBrowser from '@/components/category/CategoriesBrowser';
import { api } from '@/lib/api';

const refresh = jest.fn();

jest.mock('next/navigation', () => ({
    useRouter: () => ({ refresh }),
}));

jest.mock('@/lib/api', () => ({
    api: {
        categories: { list: jest.fn() },
        contacts: { list: jest.fn() },
        faqs: { list: jest.fn() },
        resources: { list: jest.fn() },
    },
}));

jest.mock('@/components/resource/ResourceCard', () => ({
    __esModule: true,
    default: ({ resource }: { resource: { title: string } }) => <div>{resource.title}</div>,
}));

describe('public content page failure states', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('shows a retryable FAQ error instead of the empty state', async () => {
        jest.mocked(api.faqs.list).mockRejectedValue(new Error('network unavailable'));

        render(await FAQPage());

        expect(screen.getByRole('alert')).toHaveTextContent('常见问题加载失败，请稍后重试。');
        expect(screen.queryByText('暂无常见问题')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '重新加载' }));
        expect(refresh).toHaveBeenCalledTimes(1);
    });

    it('keeps the real FAQ empty state for a successful empty response', async () => {
        jest.mocked(api.faqs.list).mockResolvedValue({ data: [] } as never);

        render(await FAQPage());

        expect(screen.getByText('暂无常见问题')).toBeInTheDocument();
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('shows a retryable contacts error instead of an empty contact area', async () => {
        jest.mocked(api.contacts.list).mockRejectedValue(new Error('service unavailable'));

        render(await ContactPage());

        expect(screen.getByRole('alert')).toHaveTextContent('联系方式加载失败，请稍后重试。');
        expect(screen.queryByText('暂无联系方式')).not.toBeInTheDocument();
    });

    it('shows the real contacts empty state for a successful empty response', async () => {
        jest.mocked(api.contacts.list).mockResolvedValue({ data: [] } as never);

        render(await ContactPage());

        expect(screen.getByText('暂无联系方式')).toBeInTheDocument();
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('distinguishes category and initial-resource failures from empty data', async () => {
        jest.mocked(api.categories.list).mockRejectedValue(new Error('category failure'));
        jest.mocked(api.resources.list).mockRejectedValue(new Error('resource failure'));

        render(await CategoriesPage());

        const alerts = screen.getAllByRole('alert');
        expect(alerts[0]).toHaveTextContent('分类加载失败，请稍后重试。');
        expect(alerts[1]).toHaveTextContent('资源加载失败，请稍后重试。');
        expect(screen.queryByText('暂无分类')).not.toBeInTheDocument();
        expect(screen.queryByText('该分类暂无资源')).not.toBeInTheDocument();
    });

    it('keeps both category empty states after successful empty responses', async () => {
        jest.mocked(api.categories.list).mockResolvedValue({ data: [] } as never);
        jest.mocked(api.resources.list).mockResolvedValue({ data: { items: [] } } as never);

        render(await CategoriesPage());

        expect(screen.getByText('暂无分类')).toBeInTheDocument();
        expect(screen.getByText('该分类暂无资源')).toBeInTheDocument();
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('accepts fresh initial resources after a route refresh succeeds', async () => {
        const { rerender } = render(
            <CategoriesBrowser
                categories={[]}
                initialResources={[]}
                initialResourcesLoadFailed
            />,
        );

        expect(screen.getByRole('alert')).toHaveTextContent('资源加载失败，请稍后重试。');

        rerender(
            <CategoriesBrowser
                categories={[]}
                initialResources={[{ id: 8, title: '刷新后的资源' }] as never}
                initialResourcesLoadFailed={false}
            />,
        );

        expect(await screen.findByText('刷新后的资源')).toBeInTheDocument();
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('retries a failed client-side category filter', async () => {
        jest.mocked(api.resources.list)
            .mockRejectedValueOnce(new Error('temporary failure'))
            .mockResolvedValueOnce({
                data: { items: [{ id: 9, title: '重试后的资源' }] },
            } as never);

        render(
            <CategoriesBrowser
                categories={[{
                    id: 3,
                    name: '编程开发',
                    slug: 'programming',
                    resource_count: 1,
                }] as never}
                initialResources={[]}
            />,
        );

        fireEvent.click(screen.getByRole('button', { name: /编程开发/ }));
        expect(await screen.findByRole('alert')).toHaveTextContent('资源加载失败，请稍后重试。');
        expect(screen.queryByText('该分类暂无资源')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '重新加载' }));

        await waitFor(() => expect(screen.getByText('重试后的资源')).toBeInTheDocument());
        expect(api.resources.list).toHaveBeenCalledTimes(2);
        expect(api.resources.list).toHaveBeenLastCalledWith({
            page: 1,
            page_size: 12,
            category_id: 3,
        });
    });
});
