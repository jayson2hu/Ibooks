export const DEFAULT_PUBLIC_SITE_SETTINGS = {
    siteName: '资源市场',
    siteDescription: '发现并获取高质量的电子书、视频课程、技术文档等数字资源',
    primaryColor: '#6366f1',
    footerBrandText: '提供优质的电子书、视频课程和技术文档，助力您的学习和成长。',
    copyrightText: '',
} as const;

export interface PublicSiteSettings {
    siteName: string;
    siteDescription: string;
    primaryColor: string;
    footerBrandText: string;
    copyrightText: string;
}

interface RawSiteSetting {
    key?: unknown;
    value?: unknown;
}

const HEX_COLOR_PATTERN = /^#[0-9a-f]{6}$/i;

export function isValidPrimaryColor(value: string): boolean {
    return HEX_COLOR_PATTERN.test(value.trim());
}

export function normalizePrimaryColor(value: unknown): string {
    if (typeof value !== 'string' || !isValidPrimaryColor(value)) {
        return DEFAULT_PUBLIC_SITE_SETTINGS.primaryColor;
    }
    return value.trim().toLowerCase();
}

function mixHexColor(hexColor: string, target: number, ratio: number): string {
    const channels = [1, 3, 5].map((offset) => Number.parseInt(hexColor.slice(offset, offset + 2), 16));
    return `#${channels
        .map((channel) => Math.round(channel + (target - channel) * ratio).toString(16).padStart(2, '0'))
        .join('')}`;
}

export function getPrimaryColorVariables(primaryColor: unknown) {
    const primary = normalizePrimaryColor(primaryColor);
    return {
        '--color-primary': primary,
        '--color-primary-dark': mixHexColor(primary, 0, 0.16),
        '--color-primary-light': mixHexColor(primary, 255, 0.25),
    } as const;
}

export function resolvePublicSiteSettings(payload: unknown): PublicSiteSettings {
    const values = new Map<string, string>();

    if (Array.isArray(payload)) {
        for (const item of payload as RawSiteSetting[]) {
            if (typeof item?.key === 'string' && typeof item.value === 'string') {
                values.set(item.key, item.value);
            }
        }
    }

    const siteName = values.get('site_name')?.trim();
    const siteDescription = values.get('site_description')?.trim();

    return {
        siteName: siteName || DEFAULT_PUBLIC_SITE_SETTINGS.siteName,
        siteDescription: siteDescription || DEFAULT_PUBLIC_SITE_SETTINGS.siteDescription,
        primaryColor: normalizePrimaryColor(values.get('primary_color')),
        footerBrandText: values.get('footer_brand_text')?.trim()
            || DEFAULT_PUBLIC_SITE_SETTINGS.footerBrandText,
        copyrightText: values.get('copyright_text')?.trim() || '',
    };
}

export async function fetchPublicSiteSettings(): Promise<PublicSiteSettings> {
    const apiBaseUrl = (
        process.env.INTERNAL_API_URL
        || process.env.NEXT_PUBLIC_API_URL
        || 'http://localhost:8000'
    ).replace(/\/$/, '');

    try {
        const response = await fetch(`${apiBaseUrl}/api/v1/settings`, {
            headers: { Accept: 'application/json' },
            next: { revalidate: 60 },
        });
        if (!response.ok) {
            return { ...DEFAULT_PUBLIC_SITE_SETTINGS };
        }
        return resolvePublicSiteSettings(await response.json());
    } catch {
        return { ...DEFAULT_PUBLIC_SITE_SETTINGS };
    }
}
