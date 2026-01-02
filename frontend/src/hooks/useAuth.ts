'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface User {
    email: string;
    role: string;
    // Add other fields as needed
}

export function useAuth() {
    const router = useRouter();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = () => {
        const token = localStorage.getItem('token');
        if (token) {
            setIsAuthenticated(true);
            // Optionally fetch user details here if needed immediately
            // fetchUser(); 
        } else {
            setIsAuthenticated(false);
            setUser(null);
        }
        setIsLoading(false);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setUser(null);
        router.push('/login');
        router.refresh();
    };

    const adminLogout = () => {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setUser(null);
        router.push('/admin/login');
        // router.refresh(); // careful with refresh on some next versions
    };

    return {
        isAuthenticated,
        isLoading,
        user,
        logout,
        adminLogout,
        checkAuth
    };
}
