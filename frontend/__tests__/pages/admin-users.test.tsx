import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import UserManagement from '@/app/admin/users/page';
import { api } from '@/lib/api';

jest.mock('@/lib/api', () => ({
    api: {
        admin: {
            getUsers: jest.fn(),
            updateUser: jest.fn(),
        },
    },
    getApiErrorMessage: jest.fn((_error: unknown, fallback: string) => fallback),
}));

const user = {
    id: 1,
    email: 'reader@example.com',
    username: 'reader',
    role: 'user',
    status: 'active',
    is_email_verified: true,
    created_at: '2026-09-10T00:00:00Z',
};

describe('admin user pagination', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('uses backend page metadata instead of the current page length', async () => {
        jest.mocked(api.admin.getUsers)
            .mockResolvedValueOnce({
                data: { items: [user], total: 21, page: 1, page_size: 20, pages: 2 },
            } as never)
            .mockResolvedValueOnce({
                data: { items: [], total: 21, page: 2, page_size: 20, pages: 2 },
            } as never);

        render(<UserManagement />);

        expect(await screen.findByText('reader@example.com')).toBeInTheDocument();
        const nextButton = screen.getByRole('button', { name: '下一页' });
        expect(nextButton).toBeEnabled();

        fireEvent.click(nextButton);

        await waitFor(() => expect(api.admin.getUsers).toHaveBeenLastCalledWith({
            page: 2,
            page_size: 20,
        }));
        await waitFor(() => expect(screen.getByRole('button', { name: '下一页' })).toBeDisabled());
    });
});
