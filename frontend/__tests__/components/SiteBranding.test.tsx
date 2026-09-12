import { render, screen, waitFor, within } from '@testing-library/react';

import Footer from '@/components/layout/Footer';
import Header from '@/components/layout/Header';
import { SiteSettingsProvider } from '@/contexts/SiteSettingsContext';
import type { PublicSiteSettings } from '@/lib/siteSettings';

const mockContactsList = jest.fn();

jest.mock('next/navigation', () => ({
    usePathname: () => '/resources',
    useRouter: () => ({ push: jest.fn() }),
}));

jest.mock('@/hooks/useAuth', () => ({
    useAuth: () => ({
        isAuthenticated: false,
        isLoading: false,
        logout: jest.fn(),
    }),
}));

jest.mock('@/lib/api', () => ({
    api: {
        contacts: {
            list: (...args: unknown[]) => mockContactsList(...args),
        },
    },
}));

const settings: PublicSiteSettings = {
    siteName: 'Ibooks Academy',
    siteDescription: 'Carefully selected study resources.',
    primaryColor: '#123456',
    footerBrandText: 'Keep learning every day.',
    copyrightText: 'Copyright Ibooks Academy',
};

describe('site branding', () => {
    beforeEach(() => {
        mockContactsList.mockResolvedValue({ data: [] });
    });

    it('uses runtime site settings in the public header and footer', async () => {
        render(
            <SiteSettingsProvider settings={settings}>
                <Header />
                <Footer />
            </SiteSettingsProvider>
        );

        await waitFor(() => expect(mockContactsList).toHaveBeenCalledWith(true));
        expect(within(screen.getByRole('banner')).getByText('Ibooks Academy')).toBeInTheDocument();
        expect(within(screen.getByRole('contentinfo')).getAllByText(/Ibooks Academy/)).toHaveLength(2);
        expect(screen.getByText('Carefully selected study resources.')).toBeInTheDocument();
        expect(screen.getByText('Keep learning every day.')).toBeInTheDocument();
        expect(screen.getByText('Copyright Ibooks Academy')).toBeInTheDocument();
    });
});
