/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React Strict Mode for better development
  reactStrictMode: true,

  // Image optimization
  images: {
    domains: ['localhost', 'example.com'],
    formats: ['image/avif', 'image/webp'],
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  },

  // Generate static pages at build time
  output: 'standalone',
}

module.exports = nextConfig
