import { render, screen } from '@testing-library/react';

import AppChrome from '@/components/layout/AppChrome';

let pathname = '/';

jest.mock('next/navigation', () => ({
    usePathname: () => pathname,
}));

jest.mock('@/components/layout/Header', () => ({
    __esModule: true,
    default: () => <header>Public header</header>,
}));

jest.mock('@/components/layout/Footer', () => ({
    __esModule: true,
    default: () => <footer>Public footer</footer>,
}));

jest.mock('@/components/common/FloatingContact', () => ({
    __esModule: true,
    default: () => <aside>Floating contact</aside>,
}));

describe('AppChrome', () => {
    it('renders the public shell for storefront routes', () => {
        pathname = '/resources';
        render(<AppChrome><div>Page content</div></AppChrome>);

        expect(screen.getByText('Public header')).toBeInTheDocument();
        expect(screen.getByText('Public footer')).toBeInTheDocument();
        expect(screen.getByText('Floating contact')).toBeInTheDocument();
        expect(screen.getByRole('main')).toHaveTextContent('Page content');
    });

    it.each(['/admin', '/admin/login', '/admin/resources']) (
        'does not overlay the admin shell on %s',
        (adminPath) => {
            pathname = adminPath;
            render(<AppChrome><div>Admin content</div></AppChrome>);

            expect(screen.queryByText('Public header')).not.toBeInTheDocument();
            expect(screen.queryByText('Public footer')).not.toBeInTheDocument();
            expect(screen.queryByText('Floating contact')).not.toBeInTheDocument();
            expect(screen.queryByRole('main')).not.toBeInTheDocument();
            expect(screen.getByText('Admin content')).toBeInTheDocument();
        },
    );
});
