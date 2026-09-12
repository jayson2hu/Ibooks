'use client';

import { createContext, useContext } from 'react';

import {
    DEFAULT_PUBLIC_SITE_SETTINGS,
    type PublicSiteSettings,
} from '@/lib/siteSettings';

const SiteSettingsContext = createContext<PublicSiteSettings>(DEFAULT_PUBLIC_SITE_SETTINGS);

export function SiteSettingsProvider({
    children,
    settings,
}: {
    children: React.ReactNode;
    settings: PublicSiteSettings;
}) {
    return (
        <SiteSettingsContext.Provider value={settings}>
            {children}
        </SiteSettingsContext.Provider>
    );
}

export function useSiteSettings(): PublicSiteSettings {
    return useContext(SiteSettingsContext);
}
