'use client';

import { usePathname } from 'next/navigation';

import FloatingContact from '@/components/common/FloatingContact';
import Footer from '@/components/layout/Footer';
import Header from '@/components/layout/Header';
import { SiteSettingsProvider } from '@/contexts/SiteSettingsContext';
import { DEFAULT_PUBLIC_SITE_SETTINGS, type PublicSiteSettings } from '@/lib/siteSettings';

export default function AppChrome({
    children,
    settings = DEFAULT_PUBLIC_SITE_SETTINGS,
}: {
    children: React.ReactNode;
    settings?: PublicSiteSettings;
}) {
    const pathname = usePathname();
    const isAdminRoute = pathname === '/admin' || pathname?.startsWith('/admin/');

    if (isAdminRoute) {
        return <SiteSettingsProvider settings={settings}>{children}</SiteSettingsProvider>;
    }

    return (
        <SiteSettingsProvider settings={settings}>
            <Header />
            <main>{children}</main>
            <FloatingContact />
            <Footer />
        </SiteSettingsProvider>
    );
}
