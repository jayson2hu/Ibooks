import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import CrawlerAdminPage from '@/app/admin/crawler/page';
import { api } from '@/lib/api';


jest.mock('@/lib/api', () => ({
    api: {
        crawler: {
            status: jest.fn(),
            getConfig: jest.fn(),
            updateConfig: jest.fn(),
            run: jest.fn(),
        },
        categories: { list: jest.fn() },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const statusMock = api.crawler.status as jest.MockedFunction<typeof api.crawler.status>;
const getConfigMock = api.crawler.getConfig as jest.MockedFunction<typeof api.crawler.getConfig>;
const updateConfigMock = api.crawler.updateConfig as jest.MockedFunction<typeof api.crawler.updateConfig>;
const listCategoriesMock = api.categories.list as jest.MockedFunction<typeof api.categories.list>;

const crawlerStatus = {
    source_key: 'crawler_1024',
    source_name: '1024 resources',
    source_site: '1024zyz.com',
    enabled: false,
    interval_minutes: 180,
    max_pages: 2,
    request_timeout_seconds: 15,
    target_category_id: null,
    available_fields: [
        { key: 'title', label: '标题', description: '标题', required: true, enabled: true },
        { key: 'excerpt', label: '摘要', description: '摘要', required: false, enabled: false },
        { key: 'cover_image_url', label: '封面', description: '封面', required: false, enabled: false },
        { key: 'tags', label: '标签', description: '标签', required: false, enabled: false },
    ],
    is_running: false,
    last_run_at: null,
    last_status: 'idle',
    last_message: null,
    last_count: 0,
};

const crawlerConfig = {
    enabled: true,
    interval_minutes: 60,
    max_pages: 3,
    request_timeout_seconds: 20,
    target_category_id: 7,
    enabled_fields: ['excerpt'],
};


describe('CrawlerAdminPage configuration permissions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        statusMock.mockResolvedValue({ data: crawlerStatus } as never);
        getConfigMock.mockResolvedValue({ data: crawlerConfig } as never);
        updateConfigMock.mockResolvedValue({ data: crawlerConfig } as never);
        listCategoriesMock.mockResolvedValue({
            data: [{ id: 7, name: '课程' }],
        } as never);
    });

    it('loads and saves through the dedicated crawler config API', async () => {
        render(<CrawlerAdminPage />);

        expect(await screen.findByDisplayValue('60')).toBeInTheDocument();
        expect(screen.getByRole('checkbox', { name: '启用定时爬虫' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: /摘要/ })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: /封面/ })).not.toBeChecked();

        fireEvent.change(screen.getByLabelText('间隔（分钟）'), {
            target: { value: '90' },
        });
        fireEvent.click(screen.getByRole('checkbox', { name: /封面/ }));
        fireEvent.click(screen.getByRole('button', { name: '保存设置' }));

        await waitFor(() => expect(updateConfigMock).toHaveBeenCalledWith({
            enabled: true,
            interval_minutes: 90,
            max_pages: 3,
            request_timeout_seconds: 20,
            target_category_id: 7,
            enabled_fields: ['excerpt', 'cover_image_url'],
        }));
        expect(await screen.findByText('爬虫设置已保存')).toBeInTheDocument();
    });

    it('cannot run or overwrite defaults when configuration loading fails', async () => {
        statusMock.mockRejectedValueOnce(new Error('offline'));
        render(<CrawlerAdminPage />);

        expect(await screen.findByRole('alert')).toHaveTextContent('无法加载爬虫状态');
        expect(screen.getByRole('button', { name: '立即运行' })).toBeDisabled();
        expect(screen.getByRole('button', { name: '保存设置' })).toBeDisabled();
        expect(screen.getByText(/不会运行爬虫或提交默认配置/)).toBeInTheDocument();
        expect(updateConfigMock).not.toHaveBeenCalled();

        fireEvent.click(screen.getByRole('button', { name: '重新加载' }));

        expect(await screen.findByDisplayValue('60')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: '立即运行' })).toBeEnabled();
        expect(screen.getByRole('button', { name: '保存设置' })).toBeEnabled();
    });
});
