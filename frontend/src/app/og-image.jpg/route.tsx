import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET() {
    return new ImageResponse(
        (
            <div
                style={{
                    alignItems: 'center',
                    background: 'linear-gradient(135deg, #4f46e5 0%, #9333ea 55%, #ec4899 100%)',
                    color: 'white',
                    display: 'flex',
                    fontFamily: 'Arial, sans-serif',
                    height: '100%',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    padding: '72px 96px',
                    position: 'relative',
                    width: '100%',
                }}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 30, position: 'relative', width: '100%' }}>
                    <div style={{ alignItems: 'center', display: 'flex', gap: 22 }}>
                        <div
                            style={{
                                background: '#ffffff',
                                borderRadius: 16,
                                boxShadow: '14px 14px 0 rgba(255,255,255,0.25)',
                                display: 'flex',
                                height: 72,
                                width: 58,
                            }}
                        />
                        <div style={{ display: 'flex', fontSize: 42, fontWeight: 800, letterSpacing: 4 }}>IBOOKS</div>
                    </div>
                    <div style={{ display: 'flex', fontSize: 72, fontWeight: 800, letterSpacing: -2, lineHeight: 1.05 }}>
                        Curated Digital Resources
                    </div>
                    <div style={{ color: 'rgba(255,255,255,0.82)', display: 'flex', fontSize: 32 }}>
                        Books, courses and practical documents for continuous learning.
                    </div>
                </div>

                <div
                    style={{
                        border: '48px solid rgba(255,255,255,0.10)',
                        borderRadius: '999px',
                        display: 'flex',
                        height: 430,
                        position: 'absolute',
                        right: -160,
                        top: -190,
                        width: 430,
                    }}
                />
            </div>
        ),
        {
            width: 1200,
            height: 630,
            headers: {
                'Cache-Control': 'public, max-age=86400, stale-while-revalidate=604800',
            },
        },
    );
}
