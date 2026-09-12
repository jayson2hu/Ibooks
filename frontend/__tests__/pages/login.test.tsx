import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import LoginPage from '@/app/login/page';
import { api } from '@/lib/api';

const push = jest.fn();

jest.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
jest.mock('@/lib/api', () => ({
    api: { auth: { login: jest.fn() } },
}));

describe('LoginPage', () => {
    beforeEach(() => {
        localStorage.clear();
        push.mockClear();
        jest.mocked(api.auth.login).mockReset();
    });

    it('stores the token and navigates after successful login', async () => {
        jest.mocked(api.auth.login).mockResolvedValue({
            data: {
                access_token: 'access-token',
                refresh_token: 'refresh-token',
            },
        } as never);
        render(<LoginPage />);

        fireEvent.change(screen.getByLabelText('邮箱地址'), { target: { value: 'user@example.com' } });
        fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'Password123' } });
        fireEvent.click(screen.getByRole('button', { name: '登录' }));

        await waitFor(() => expect(api.auth.login).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Password123' }));
        expect(localStorage.getItem('token')).toBe('access-token');
        expect(localStorage.getItem('refresh_token')).toBe('refresh-token');
        expect(push).toHaveBeenCalledWith('/');
    });

    it('links users to registration and password recovery', () => {
        render(<LoginPage />);

        expect(screen.getByRole('link', { name: '立即注册' })).toHaveAttribute('href', '/register');
        expect(screen.getByRole('link', { name: '忘记密码？' })).toHaveAttribute('href', '/forgot-password');
    });
});
