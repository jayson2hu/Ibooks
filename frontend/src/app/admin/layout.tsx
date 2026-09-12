'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAdminAuth } from '@/hooks/useAdminAuth';
import AdminSidebar from '@/components/admin/Sidebar';
import AdminHeader from '@/components/admin/Header';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const isLoginPage = pathname === '/admin/login';
    const { isAuthenticated, isLoading, role, canAccessRoute } = useAdminAuth();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    useEffect(() => setSidebarOpen(false), [pathname]);

    // Don't apply auth protection or layout to login page
    if (isLoginPage) {
        return <>{children}</>;
    }

    // Show minimal loading state while checking authentication
    // This prevents the sidebar/layout from flashing before redirect
    if (isLoading || !isAuthenticated || !canAccessRoute) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-solid border-purple-600 border-r-transparent"></div>
                    <p className="mt-4 text-gray-600">正在验证身份...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <AdminSidebar role={role} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
            <div className="md:ml-64">
                <AdminHeader role={role} onMenuOpen={() => setSidebarOpen(true)} />
                <main className="p-4 sm:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
}
