import type { Metadata } from 'next';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import FloatingContact from '@/components/common/FloatingContact';
import '../styles/globals.css';

export const metadata: Metadata = {
    title: {
        default: '资源市场 - 精选电子书、课程和文档',
        template: '%s | 资源市场',
    },
    description: '发现并获取高质量的电子书、视频课程、技术文档等数字资源。云盘直链交付，安全快速。',
    keywords: ['电子书', '视频课程', '技术文档', '数字资源', '在线学习'],
    authors: [{ name: '资源市场' }],
    creator: '资源市场',
    publisher: '资源市场',
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
    openGraph: {
        type: 'website',
        locale: 'zh_CN',
        url: '/',
        siteName: '资源市场',
        title: '资源市场 - 精选电子书、课程和文档',
        description: '发现并获取高质量的电子书、视频课程、技术文档等数字资源',
        images: [
            {
                url: '/og-image.jpg',
                width: 1200,
                height: 630,
                alt: '资源市场',
            },
        ],
    },
    twitter: {
        card: 'summary_large_image',
        title: '资源市场',
        description: '发现并获取高质量的数字资源',
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
    verification: {
        // Add your verification codes here
        // google: 'your-google-verification-code',
        // yandex: 'your-yandex-verification-code',
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="zh-CN">
            <head>
                <link rel="icon" href="/favicon.ico" />
                <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
                <link rel="manifest" href="/manifest.json" />
            </head>
            <body>
                <Header />
                <main>{children}</main>
                <FloatingContact />
                <Footer />
            </body>
        </html>
    );
}
