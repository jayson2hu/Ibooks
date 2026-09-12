describe('backend-generated SEO rewrites', () => {
  const originalInternalApiUrl = process.env.INTERNAL_API_URL;
  const originalPublicApiUrl = process.env.NEXT_PUBLIC_API_URL;

  afterEach(() => {
    if (originalInternalApiUrl === undefined) {
      delete process.env.INTERNAL_API_URL;
    } else {
      process.env.INTERNAL_API_URL = originalInternalApiUrl;
    }
    if (originalPublicApiUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = originalPublicApiUrl;
    }
    jest.resetModules();
  });

  async function loadRewrites({ internalUrl, publicUrl }) {
    if (internalUrl === undefined) {
      delete process.env.INTERNAL_API_URL;
    } else {
      process.env.INTERNAL_API_URL = internalUrl;
    }
    if (publicUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = publicUrl;
    }
    jest.resetModules();

    const config = jest.requireActual('../../next.config.js');
    return config.rewrites();
  }

  it('prefers the server-only internal backend URL', async () => {
    await expect(loadRewrites({
      internalUrl: 'http://backend:8000/',
      publicUrl: 'https://api.example.com',
    })).resolves.toEqual([
      {
        source: '/sitemap.xml',
        destination: 'http://backend:8000/sitemap.xml',
      },
      {
        source: '/rss.xml',
        destination: 'http://backend:8000/rss.xml',
      },
      {
        source: '/robots.txt',
        destination: 'http://backend:8000/robots.txt',
      },
      {
        source: '/generated/:path*',
        destination: 'http://backend:8000/generated/:path*',
      },
    ]);
  });

  it('falls back to the browser-facing API URL for local development', async () => {
    await expect(loadRewrites({
      publicUrl: 'http://localhost:8000/',
    })).resolves.toEqual([
      {
        source: '/sitemap.xml',
        destination: 'http://localhost:8000/sitemap.xml',
      },
      {
        source: '/rss.xml',
        destination: 'http://localhost:8000/rss.xml',
      },
      {
        source: '/robots.txt',
        destination: 'http://localhost:8000/robots.txt',
      },
      {
        source: '/generated/:path*',
        destination: 'http://localhost:8000/generated/:path*',
      },
    ]);
  });

  it('applies browser security headers and hides the framework signature', async () => {
    jest.resetModules();
    const config = jest.requireActual('../../next.config.js');
    const rules = await config.headers();

    expect(config.poweredByHeader).toBe(false);
    expect(rules).toHaveLength(1);
    expect(rules[0].source).toBe('/(.*)');

    const headers = Object.fromEntries(
      rules[0].headers.map(({ key, value }) => [key, value]),
    );
    expect(headers['X-Frame-Options']).toBe('DENY');
    expect(headers['X-Content-Type-Options']).toBe('nosniff');
    expect(headers['Content-Security-Policy']).toContain("object-src 'none'");
    expect(headers['Content-Security-Policy']).toContain("frame-ancestors 'none'");
    expect(headers['Permissions-Policy']).toContain('camera=()');
  });
});
