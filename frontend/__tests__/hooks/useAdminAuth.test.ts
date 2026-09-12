import { renderHook, waitFor } from '@testing-library/react';
import { useAdminAuth } from '@/hooks/useAdminAuth';

const replace = jest.fn();
let pathname = '/admin';

jest.mock('next/navigation', () => ({
    useRouter: () => ({ replace }),
    usePathname: () => pathname,
}));

describe('useAdminAuth', () => {
    beforeEach(() => {
        localStorage.clear();
        replace.mockClear();
        pathname = '/admin';
    });

    it('redirects when no token is present', async () => {
        const { result } = renderHook(() => useAdminAuth());

        await waitFor(() => expect(result.current.isAuthenticated).toBe(false));
        expect(replace).toHaveBeenCalledWith('/admin/login');
    });

    it('redirects a non-admin role', async () => {
        localStorage.setItem('token', 'token');
        localStorage.setItem('user_role', 'user');
        const { result } = renderHook(() => useAdminAuth());

        await waitFor(() => expect(result.current.isAuthenticated).toBe(false));
        expect(replace).toHaveBeenCalledWith('/admin/login');
    });

    it('allows an administrator', async () => {
        localStorage.setItem('token', 'token');
        localStorage.setItem('user_role', 'admin');
        const { result } = renderHook(() => useAdminAuth());

        await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
        expect(replace).not.toHaveBeenCalled();
        expect(result.current.role).toBe('admin');
    });

    it('allows a moderator and exposes the role for capability-aware UI', async () => {
        localStorage.setItem('token', 'token');
        localStorage.setItem('user_role', 'moderator');
        const { result } = renderHook(() => useAdminAuth());

        await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
        expect(result.current.role).toBe('moderator');
        expect(result.current.canAccessRoute).toBe(true);
        expect(replace).not.toHaveBeenCalled();
    });

    it('redirects a moderator away from an administrator-only route', async () => {
        pathname = '/admin/wallets';
        localStorage.setItem('token', 'token');
        localStorage.setItem('user_role', 'moderator');
        const { result } = renderHook(() => useAdminAuth());

        await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
        expect(result.current.canAccessRoute).toBe(false);
        expect(replace).toHaveBeenCalledWith('/admin');
    });
});
