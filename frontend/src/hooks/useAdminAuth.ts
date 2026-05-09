'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

const ADMIN_ROLES = ['admin', 'moderator'];

/**
 * Hook to protect admin routes - redirects to login if not authenticated.
 */
export function useAdminAuth() {
    const router = useRouter();
    const pathname = usePathname();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

    useEffect(() => {
        // Skip auth check for login page
        if (pathname === '/admin/login') {
            setIsAuthenticated(true); // Don't block login page
            return;
        }

        const token = localStorage.getItem('token');
        const role = localStorage.getItem('user_role');

        if (!token || !ADMIN_ROLES.includes(role ?? '')) {
            setIsAuthenticated(false);
            router.replace('/admin/login');
            return;
        }

        setIsAuthenticated(true);
    }, [router, pathname]);

    return { isAuthenticated, isLoading: isAuthenticated === null };
}
