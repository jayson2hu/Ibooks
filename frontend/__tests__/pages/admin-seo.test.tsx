import { act, fireEvent, render, screen } from '@testing-library/react';

import AdminSeoPage from '@/app/admin/seo/page';
import { api, getApiErrorDetail, getApiErrorMessage } from '@/lib/api';


jest.mock('@/lib/api', () => ({
    api: {
        seo: {
            generateAll: jest.fn(),
            submitBaidu: jest.fn(),
        },
    },
    getApiErrorDetail: jest.fn(),
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const generateAllMock = api.seo.generateAll as jest.MockedFunction<typeof api.seo.generateAll>;
const getApiErrorDetailMock = getApiErrorDetail as jest.MockedFunction<typeof getApiErrorDetail>;
const getApiErrorMessageMock = getApiErrorMessage as jest.MockedFunction<typeof getApiErrorMessage>;

function createDeferred<Value>() {
    let resolve!: (value: Value) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<Value>((resolvePromise, rejectPromise) => {
        resolve = resolvePromise;
        reject = rejectPromise;
    });
    return { promise, resolve, reject };
}

describe('AdminSeoPage generation feedback', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        getApiErrorDetailMock.mockReturnValue(undefined);
        getApiErrorMessageMock.mockImplementation((_error, fallback) => fallback);
    });

    it('keeps the action loading until the backend confirms every generated file', async () => {
        const request = createDeferred<Awaited<ReturnType<typeof api.seo.generateAll>>>();
        generateAllMock.mockReturnValue(request.promise);
        render(<AdminSeoPage />);

        fireEvent.click(screen.getByRole('button', { name: '生成全部文件' }));

        expect(screen.getByRole('button', { name: '生成中...' })).toBeDisabled();
        expect(screen.queryByRole('status')).not.toBeInTheDocument();

        await act(async () => {
            request.resolve({
                data: {
                    message: 'SEO 文件生成完成',
                    generated: ['sitemap.xml', 'rss.xml', 'robots.txt'],
                },
            } as never);
            await request.promise;
        });

        expect(await screen.findByRole('status')).toHaveTextContent('SEO 文件生成完成');
        expect(screen.getByRole('status')).toHaveTextContent(
            '已生成：sitemap.xml、rss.xml、robots.txt'
        );
        expect(screen.getByRole('button', { name: '生成全部文件' })).toBeEnabled();
    });

    it('shows partial failure details and allows a retry', async () => {
        generateAllMock
            .mockRejectedValueOnce(new Error('database-password=secret'))
            .mockResolvedValueOnce({
                data: {
                    message: 'SEO 文件生成完成',
                    generated: ['sitemap.xml', 'rss.xml', 'robots.txt'],
                },
            } as never);
        getApiErrorDetailMock.mockReturnValueOnce({
            message: '部分 SEO 文件生成失败，请重试',
            generated: ['sitemap.xml', 'robots.txt'],
            failed: ['rss.xml'],
        });
        getApiErrorMessageMock.mockReturnValueOnce('部分 SEO 文件生成失败，请重试');
        render(<AdminSeoPage />);

        fireEvent.click(screen.getByRole('button', { name: '生成全部文件' }));

        expect(await screen.findByRole('alert')).toHaveTextContent('已生成：sitemap.xml、robots.txt');
        expect(screen.getByRole('alert')).toHaveTextContent('失败：rss.xml');
        expect(screen.getByRole('alert')).not.toHaveTextContent('database-password');

        fireEvent.click(screen.getByRole('button', { name: '重新生成' }));

        expect(await screen.findByRole('status')).toHaveTextContent('SEO 文件生成完成');
        expect(generateAllMock).toHaveBeenCalledTimes(2);
    });
});
