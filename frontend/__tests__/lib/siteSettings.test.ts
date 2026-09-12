import {
    DEFAULT_PUBLIC_SITE_SETTINGS,
    fetchPublicSiteSettings,
    getPrimaryColorVariables,
    normalizePrimaryColor,
    resolvePublicSiteSettings,
} from '@/lib/siteSettings';

describe('public site settings', () => {
    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('normalizes the public settings payload and ignores unsafe colors', () => {
        expect(resolvePublicSiteSettings([
            { key: 'site_name', value: '  Ibooks  ' },
            { key: 'site_description', value: '  Curated learning resources  ' },
            { key: 'primary_color', value: 'not-a-color' },
            { key: 'footer_brand_text', value: '  Learn something useful.  ' },
            { key: 'copyright_text', value: '  Custom copyright  ' },
        ])).toEqual({
            siteName: 'Ibooks',
            siteDescription: 'Curated learning resources',
            primaryColor: DEFAULT_PUBLIC_SITE_SETTINGS.primaryColor,
            footerBrandText: 'Learn something useful.',
            copyrightText: 'Custom copyright',
        });
    });

    it('derives safe primary color variants', () => {
        expect(getPrimaryColorVariables('#336699')).toEqual({
            '--color-primary': '#336699',
            '--color-primary-dark': '#2b5681',
            '--color-primary-light': '#668cb3',
        });
        expect(normalizePrimaryColor('javascript:alert(1)')).toBe('#6366f1');
    });

    it('falls back safely when the settings API is unavailable', async () => {
        const fetchMock = jest.fn().mockRejectedValueOnce(new Error('offline'));
        Object.defineProperty(global, 'fetch', {
            configurable: true,
            value: fetchMock,
        });

        await expect(fetchPublicSiteSettings()).resolves.toEqual(DEFAULT_PUBLIC_SITE_SETTINGS);
        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/settings',
            expect.objectContaining({ next: { revalidate: 60 } })
        );
        Reflect.deleteProperty(global, 'fetch');
    });
});
