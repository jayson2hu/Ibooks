import { fireEvent, render, screen } from '@testing-library/react';
import AdminHeader from '@/components/admin/Header';

const push = jest.fn();
const adminLogout = jest.fn();

jest.mock('next/navigation', () => ({
    useRouter: () => ({ push }),
}));

jest.mock('@/hooks/useAuth', () => ({
    useAuth: () => ({ adminLogout }),
}));

describe('AdminHeader', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('routes resource searches to the resource management page', () => {
        render(<AdminHeader role="admin" />);

        fireEvent.change(screen.getByRole('textbox', { name: '搜索资源' }), {
            target: { value: '  Python 入门  ' },
        });
        fireEvent.submit(screen.getByRole('textbox', { name: '搜索资源' }).closest('form')!);

        expect(push).toHaveBeenCalledWith(
            `/admin/resources?search=${encodeURIComponent('Python 入门')}`,
        );
    });

    it('links administrators to real audit events without a fake unread badge', () => {
        const { container } = render(<AdminHeader role="admin" />);

        expect(screen.getByRole('link', { name: '查看审计日志' })).toHaveAttribute(
            'href',
            '/admin/audit',
        );
        expect(container.querySelector('.bg-red-500')).not.toBeInTheDocument();
    });

    it('does not expose administrator audit navigation to moderators', () => {
        render(<AdminHeader role="moderator" />);

        expect(screen.queryByRole('link', { name: '查看审计日志' })).not.toBeInTheDocument();
    });
});
