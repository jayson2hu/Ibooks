/** @type {import('next').NextConfig} */
const standaloneBuild = process.env.NEXT_OUTPUT_STANDALONE === 'true';
const rewriteApiUrl = (
  process.env.INTERNAL_API_URL
  || process.env.NEXT_PUBLIC_API_URL
  || 'http://localhost:8000'
).replace(/\/+$/, '');
const scriptSources = [
  "'self'",
  "'unsafe-inline'",
  ...(process.env.NODE_ENV === 'development' ? ["'unsafe-eval'"] : []),
];
const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src ${scriptSources.join(' ')}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https: http:",
  "font-src 'self' data:",
  "connect-src 'self' https: http: ws: wss:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join('; ');
const securityHeaders = [
  { key: 'Content-Security-Policy', value: contentSecurityPolicy },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
];

const nextConfig = {
  // Enable React Strict Mode for better development
  reactStrictMode: true,
  poweredByHeader: false,

  // Keep tracing scoped to this app when a parent directory also has a lockfile.
  outputFileTracingRoot: __dirname,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  },

  // Expose backend-generated SEO artifacts through the public frontend origin.
  async rewrites() {
    return [
      {
        source: '/sitemap.xml',
        destination: `${rewriteApiUrl}/sitemap.xml`,
      },
      {
        source: '/rss.xml',
        destination: `${rewriteApiUrl}/rss.xml`,
      },
      {
        source: '/robots.txt',
        destination: `${rewriteApiUrl}/robots.txt`,
      },
      {
        source: '/generated/:path*',
        destination: `${rewriteApiUrl}/generated/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },

  // Docker uses the standalone server; local production previews keep the
  // standard `next start` output so `npm run build && npm start` works.
  ...(standaloneBuild ? { output: 'standalone' } : {}),
}

module.exports = nextConfig
