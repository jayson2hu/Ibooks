import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import SettingsPage from '@/app/admin/settings/page';
import { api, getApiErrorMessage } from '@/lib/api';


jest.mock('@/lib/api', () => ({
    api: {
        settings: {
            getGrouped: jest.fn(),
            batchUpdate: jest.fn(),
            testEmail: jest.fn(),
        },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const getGroupedMock = api.settings.getGrouped as jest.MockedFunction<typeof api.settings.getGrouped>;
const batchUpdateMock = api.settings.batchUpdate as jest.MockedFunction<typeof api.settings.batchUpdate>;
const testEmailMock = api.settings.testEmail as jest.MockedFunction<typeof api.settings.testEmail>;
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

async function openEmailSettings() {
    render(<SettingsPage />);
    expect(await screen.findByDisplayValue('Ibooks')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '邮件设置' }));
}

describe('Admin email settings', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        getGroupedMock.mockResolvedValue({
            data: [
                {
                    category: 'general',
                    settings: [{ key: 'site_name', value: 'Ibooks' }],
                },
                {
                    category: 'email',
                    settings: [
                        { key: 'smtp_host', value: 'stale-db-host.example.com' },
                        { key: 'smtp_port', value: '2525' },
                        { key: 'smtp_password', value: 'must-not-be-loaded-or-saved' },
                    ],
                },
            ],
        } as never);
        batchUpdateMock.mockResolvedValue({ data: { message: 'saved' } } as never);
        testEmailMock.mockResolvedValue({
            data: { message: '测试邮件已发送到当前管理员邮箱' },
        } as never);
    });

    it('explains environment-managed SMTP settings and exposes no editable credentials', async () => {
        await openEmailSettings();

        expect(screen.getByText('SMTP 配置由后端环境管理')).toBeInTheDocument();
        expect(screen.getByText(/保存设置.*不会修改这些连接信息或密钥/)).toBeInTheDocument();
        expect(screen.getByText(/EMAIL_PASSWORD/)).toBeInTheDocument();
        expect(screen.queryByLabelText('SMTP主机')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('SMTP端口')).not.toBeInTheDocument();
    });

    it('shows an accessible loading and success state while testing real SMTP', async () => {
        const request = createDeferred<Awaited<ReturnType<typeof api.settings.testEmail>>>();
        testEmailMock.mockReturnValue(request.promise);
        await openEmailSettings();

        fireEvent.click(screen.getByRole('button', { name: '发送测试邮件' }));

        expect(screen.getByRole('button', { name: '发送中...' })).toBeDisabled();
        expect(testEmailMock).toHaveBeenCalledTimes(1);

        await act(async () => {
            request.resolve({
                data: { message: '测试邮件已发送到当前管理员邮箱' },
            } as never);
            await request.promise;
        });

        expect(await screen.findByRole('status')).toHaveTextContent(
            '测试邮件已发送到当前管理员邮箱'
        );
        expect(screen.getByRole('button', { name: '发送测试邮件' })).toBeEnabled();
    });

    it('announces a safe API error and restores the test button', async () => {
        testEmailMock.mockRejectedValue(new Error('SMTP provider exposed a secret'));
        getApiErrorMessageMock.mockReturnValueOnce('邮件服务暂不可用，请稍后重试');
        await openEmailSettings();

        fireEvent.click(screen.getByRole('button', { name: '发送测试邮件' }));

        expect(await screen.findByRole('alert')).toHaveTextContent('邮件服务暂不可用，请稍后重试');
        expect(screen.getByRole('button', { name: '发送测试邮件' })).toBeEnabled();
    });

    it('never includes legacy SMTP database fields in the batch save payload', async () => {
        render(<SettingsPage />);
        expect(await screen.findByDisplayValue('Ibooks')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '保存设置' }));

        await waitFor(() => expect(batchUpdateMock).toHaveBeenCalledTimes(1));
        const [payload] = batchUpdateMock.mock.calls[0];
        expect(payload).not.toEqual(
            expect.arrayContaining([
                expect.objectContaining({ key: expect.stringMatching(/^smtp_/i) }),
            ])
        );
    });

    it('does not expose or save settings that have no runtime consumer', async () => {
        getGroupedMock.mockResolvedValueOnce({
            data: [
                {
                    category: 'legacy',
                    settings: [
                        { key: 'admin_email', value: 'unused@example.com' },
                        { key: 'theme_mode', value: 'dark' },
                        { key: 'comments_enabled', value: 'true' },
                        { key: 'max_file_size_mb', value: '100' },
                        { key: 'allowed_file_types', value: 'zip' },
                    ],
                },
            ],
        } as never);
        render(<SettingsPage />);

        expect(await screen.findByDisplayValue('资源市场')).toBeInTheDocument();
        expect(screen.queryByText('管理员邮箱')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: '存储设置' })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '外观设置' }));
        expect(screen.queryByText('主题模式')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '功能设置' }));
        expect(screen.queryByText('评论功能')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '保存设置' }));
        await waitFor(() => expect(batchUpdateMock).toHaveBeenCalledTimes(1));
        const [payload] = batchUpdateMock.mock.calls[0];
        expect(payload).not.toEqual(expect.arrayContaining([
            expect.objectContaining({
                key: expect.stringMatching(
                    /^(admin_email|theme_mode|comments_enabled|max_file_size_mb|allowed_file_types)$/
                ),
            }),
        ]));
    });

    it('cannot overwrite settings with defaults when the initial load fails', async () => {
        getGroupedMock.mockRejectedValueOnce(new Error('offline'));
        render(<SettingsPage />);

        expect(await screen.findByRole('alert')).toHaveTextContent('无法加载系统设置');
        expect(screen.getByRole('button', { name: '保存设置' })).toBeDisabled();
        expect(screen.getByText(/不会提交任何默认值/)).toBeInTheDocument();
        expect(batchUpdateMock).not.toHaveBeenCalled();

        fireEvent.click(screen.getByRole('button', { name: '重新加载' }));

        expect(await screen.findByDisplayValue('Ibooks')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: '保存设置' })).toBeEnabled();
    });
});
