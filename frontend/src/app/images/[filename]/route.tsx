import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

interface CoverTheme {
    eyebrow: string;
    title: string;
    subtitle: string;
    from: string;
    to: string;
    accent: string;
}

const coverThemes: Record<string, CoverTheme> = {
    'python-guide': {
        eyebrow: 'PROGRAMMING',
        title: 'Python Guide',
        subtitle: 'From fundamentals to real-world projects',
        from: '#2563eb',
        to: '#06b6d4',
        accent: '#facc15',
    },
    'react-course': {
        eyebrow: 'FRONTEND',
        title: 'React 18',
        subtitle: 'Build modern web applications',
        from: '#0f172a',
        to: '#2563eb',
        accent: '#67e8f9',
    },
    'go-microservices': {
        eyebrow: 'BACKEND',
        title: 'Go Microservices',
        subtitle: 'Reliable systems at scale',
        from: '#0891b2',
        to: '#0f766e',
        accent: '#a7f3d0',
    },
    'figma-guide': {
        eyebrow: 'DESIGN SYSTEMS',
        title: 'Figma Guide',
        subtitle: 'Design consistent product experiences',
        from: '#7c3aed',
        to: '#db2777',
        accent: '#fbcfe8',
    },
    'ux-thinking': {
        eyebrow: 'USER EXPERIENCE',
        title: 'UX Thinking',
        subtitle: 'Research, structure and interaction',
        from: '#ea580c',
        to: '#e11d48',
        accent: '#fed7aa',
    },
    'ml-projects': {
        eyebrow: 'ARTIFICIAL INTELLIGENCE',
        title: 'ML Projects',
        subtitle: 'Learn machine learning by building',
        from: '#4f46e5',
        to: '#9333ea',
        accent: '#c4b5fd',
    },
    'data-analyst': {
        eyebrow: 'DATA SCIENCE',
        title: 'Data Analyst',
        subtitle: 'SQL, Python and visualization',
        from: '#0369a1',
        to: '#0d9488',
        accent: '#99f6e4',
    },
    'pm-handbook': {
        eyebrow: 'PRODUCT MANAGEMENT',
        title: 'Product Handbook',
        subtitle: 'From discovery to delivery',
        from: '#4f46e5',
        to: '#c026d3',
        accent: '#f5d0fe',
    },
    'time-management': {
        eyebrow: 'PERSONAL GROWTH',
        title: 'Time Management',
        subtitle: 'Plan deliberately and work with focus',
        from: '#059669',
        to: '#65a30d',
        accent: '#d9f99d',
    },
};

function getCoverKey(filename: string): string {
    return filename.toLowerCase().replace(/\.(?:jpe?g|png|webp)$/i, '');
}

export async function GET(
    _request: Request,
    { params }: { params: Promise<{ filename: string }> },
) {
    const { filename } = await params;
    const theme = coverThemes[getCoverKey(filename)];

    if (!theme) {
        return new Response(null, { status: 404 });
    }

    return new ImageResponse(
        (
            <div
                style={{
                    alignItems: 'stretch',
                    background: `linear-gradient(135deg, ${theme.from}, ${theme.to})`,
                    color: 'white',
                    display: 'flex',
                    flexDirection: 'column',
                    fontFamily: 'Arial, sans-serif',
                    height: '100%',
                    justifyContent: 'space-between',
                    overflow: 'hidden',
                    padding: '72px',
                    position: 'relative',
                    width: '100%',
                }}
            >
                <div
                    style={{
                        background: 'rgba(255,255,255,0.14)',
                        border: '2px solid rgba(255,255,255,0.24)',
                        borderRadius: '999px',
                        display: 'flex',
                        fontSize: 24,
                        fontWeight: 700,
                        letterSpacing: 5,
                        padding: '14px 26px',
                        alignSelf: 'flex-start',
                    }}
                >
                    {theme.eyebrow}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 900 }}>
                    <div style={{ display: 'flex', fontSize: 90, fontWeight: 800, letterSpacing: -4, lineHeight: 1 }}>
                        {theme.title}
                    </div>
                    <div style={{ color: 'rgba(255,255,255,0.82)', display: 'flex', fontSize: 34, lineHeight: 1.3 }}>
                        {theme.subtitle}
                    </div>
                </div>

                <div style={{ alignItems: 'center', display: 'flex', fontSize: 28, fontWeight: 700, justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', letterSpacing: 3 }}>IBOOKS RESOURCE</div>
                    <div
                        style={{
                            alignItems: 'center',
                            background: theme.accent,
                            borderRadius: 24,
                            color: theme.from,
                            display: 'flex',
                            fontSize: 42,
                            height: 88,
                            justifyContent: 'center',
                            width: 88,
                        }}
                    >
                        ↗
                    </div>
                </div>

                <div
                    style={{
                        background: 'rgba(255,255,255,0.10)',
                        borderRadius: '999px',
                        display: 'flex',
                        height: 420,
                        position: 'absolute',
                        right: -190,
                        top: -170,
                        width: 420,
                    }}
                />
            </div>
        ),
        {
            width: 1200,
            height: 900,
            headers: {
                'Cache-Control': 'public, max-age=86400, stale-while-revalidate=604800',
            },
        },
    );
}
