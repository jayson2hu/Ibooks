'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export type AdminRole = 'admin' | 'moderator';

const ADMIN_ROLES: AdminRole[] = ['admin', 'moderator'];

const MODERATOR_ROUTE_PREFIXES = [
    '/admin/resources',
    '/admin/categories',
    '/admin/contacts',
    '/admin/seo',
    '/admin/crawler',
];

export function canAccessAdminPath(role: AdminRole, pathname: string): boolean {
    if (role === 'admin' || pathname === '/admin') {
        return true;
    }

    return MODERATOR_ROUTE_PREFIXES.some(
        (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
}

/**
 * Hook to protect admin routes - redirects to login if not authenticated.
 */
export function useAdminAuth() {
    const router = useRouter();
    const pathname = usePathname();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const [role, setRole] = useState<AdminRole | null>(null);

    useEffect(() => {
        // Skip auth check for login page
        if (pathname === '/admin/login') {
            setIsAuthenticated(true); // Don't block login page
            setRole(null);
            return;
        }

        const token = localStorage.getItem('token');
        const storedRole = localStorage.getItem('user_role');

        if (!token || !ADMIN_ROLES.includes(storedRole as AdminRole)) {
            setIsAuthenticated(false);
            setRole(null);
            router.replace('/admin/login');
            return;
        }

        setRole(storedRole as AdminRole);
        setIsAuthenticated(true);

        if (!canAccessAdminPath(storedRole as AdminRole, pathname)) {
            router.replace('/admin');
        }
    }, [router, pathname]);

    const canAccessRoute = role ? canAccessAdminPath(role, pathname) : false;

    return { isAuthenticated, isLoading: isAuthenticated === null, role, canAccessRoute };
}
