'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

/**
 * Hook to protect admin routes - redirects to login if not authenticated
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

        // Check for token in localStorage
        const token = localStorage.getItem('token');
        console.log('useAdminAuth check - pathname:', pathname, 'token exists:', !!token);

        if (!token) {
            // No token, redirect to admin login
            console.log('No token found, redirecting to login');
            setIsAuthenticated(false);
            router.replace('/admin/login');
        } else {
            // Token exists, mark as authenticated
            console.log('Token found, user authenticated');
            setIsAuthenticated(true);
        }
    }, [router, pathname]);

    return { isAuthenticated, isLoading: isAuthenticated === null };
}
