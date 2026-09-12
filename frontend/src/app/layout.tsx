import type { CSSProperties } from 'react';
import type { Metadata } from 'next';
import AppChrome from '@/components/layout/AppChrome';
import { fetchPublicSiteSettings, getPrimaryColorVariables } from '@/lib/siteSettings';
import '../styles/globals.css';

export async function generateMetadata(): Promise<Metadata> {
    const { siteName, siteDescription } = await fetchPublicSiteSettings();
    const defaultTitle = `${siteName} - 精选电子书、课程和文档`;

    return {
        title: {
            default: defaultTitle,
            template: `%s | ${siteName}`,
        },
        description: siteDescription,
        keywords: ['电子书', '视频课程', '技术文档', '数字资源', '在线学习'],
        authors: [{ name: siteName }],
        creator: siteName,
        publisher: siteName,
        metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
        openGraph: {
            type: 'website',
            locale: 'zh_CN',
            siteName,
            title: defaultTitle,
            description: siteDescription,
            images: [
                {
                    url: '/og-image.jpg',
                    width: 1200,
                    height: 630,
                    alt: siteName,
                },
            ],
        },
        twitter: {
            card: 'summary_large_image',
            title: siteName,
            description: siteDescription,
            images: ['/og-image.jpg'],
        },
        robots: {
            index: true,
            follow: true,
            googleBot: {
                index: true,
                follow: true,
                'max-video-preview': -1,
                'max-image-preview': 'large',
                'max-snippet': -1,
            },
        },
    };
}

export default async function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const settings = await fetchPublicSiteSettings();
    const colorVariables = getPrimaryColorVariables(settings.primaryColor) as CSSProperties;

    return (
        <html lang="zh-CN" style={colorVariables}>
            <head>
                <link rel="icon" href="/favicon.svg" />
                <link rel="manifest" href="/manifest.json" />
            </head>
            <body>
                <AppChrome settings={settings}>{children}</AppChrome>
            </body>
        </html>
    );
}
