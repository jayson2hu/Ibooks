import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import SearchPage from '@/app/search/page';
import { api } from '@/lib/api';

const push = jest.fn();
let searchParams = 'q=Python';

jest.mock('next/navigation', () => ({
    useRouter: () => ({ push }),
    useSearchParams: () => new URLSearchParams(searchParams),
}));

jest.mock('@/lib/api', () => ({
    api: { search: jest.fn() },
}));

jest.mock('@/components/resource/ResourceCard', () => ({
    __esModule: true,
    default: ({ resource }: { resource: { title: string } }) => <div>{resource.title}</div>,
}));

describe('SearchPage', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);

    afterAll(() => {
        consoleError.mockRestore();
    });

    beforeEach(() => {
        searchParams = 'q=Python';
        push.mockClear();
        jest.mocked(api.search).mockReset();
    });

    it('searches immediately when the URL includes a query', async () => {
        jest.mocked(api.search).mockResolvedValue({
            data: {
                items: [{ id: 1, title: 'Python 完全指南' }],
                total: 1,
                page: 1,
                page_size: 20,
                pages: 1,
            },
        } as never);

        render(<SearchPage />);

        await waitFor(() => expect(api.search).toHaveBeenCalledWith('Python', 1, 20, 'all'));
        expect(await screen.findByText('Python 完全指南')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('shows a retryable service error instead of a false empty result', async () => {
        jest.mocked(api.search).mockRejectedValueOnce(new Error('offline'));
        render(<SearchPage />);

        expect(await screen.findByRole('alert')).toHaveTextContent('搜索服务暂时不可用');
        expect(screen.queryByText(/没有找到与/)).not.toBeInTheDocument();

        jest.mocked(api.search).mockResolvedValueOnce({
            data: {
                items: [{ id: 2, title: '重试后的结果' }],
                total: 1,
                page: 1,
                page_size: 20,
                pages: 1,
            },
        } as never);
        fireEvent.click(screen.getByRole('button', { name: '重新搜索' }));

        expect(await screen.findByText('重试后的结果')).toBeInTheDocument();
        expect(api.search).toHaveBeenCalledTimes(2);
    });

    it('honors the URL scope and exposes pagination navigation', async () => {
        searchParams = 'q=Python&scope=course&page=2';
        jest.mocked(api.search).mockResolvedValue({
            data: {
                items: [{ id: 3, title: 'Python 视频课程' }],
                total: 45,
                page: 2,
                page_size: 20,
                pages: 3,
            },
        } as never);

        render(<SearchPage />);

        await waitFor(() => expect(api.search).toHaveBeenCalledWith('Python', 2, 20, 'course'));
        expect(screen.getByRole('combobox', { name: '搜索范围' })).toHaveValue('course');
        expect(screen.getByText('第 2 / 3 页')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '下一页' }));
        expect(push).toHaveBeenCalledWith('/search?q=Python&scope=course&page=3');
    });

    it('starts a new scoped search on page one', async () => {
        jest.mocked(api.search).mockResolvedValue({
            data: { items: [], total: 0, page: 1, page_size: 20, pages: 0 },
        } as never);
        render(<SearchPage />);
        await waitFor(() => expect(api.search).toHaveBeenCalled());

        fireEvent.change(screen.getByRole('combobox', { name: '搜索范围' }), {
            target: { value: 'doc' },
        });
        fireEvent.change(screen.getByRole('textbox', { name: '搜索关键词' }), {
            target: { value: '架构' },
        });
        fireEvent.click(screen.getByRole('button', { name: '搜索' }));

        expect(push).toHaveBeenCalledWith('/search?q=%E6%9E%B6%E6%9E%84&scope=doc&page=1');
    });
});
