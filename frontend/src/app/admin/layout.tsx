import AdminSidebar from '@/components/admin/Sidebar';
import AdminHeader from '@/components/admin/Header';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-gray-50">
            <AdminSidebar />
            <div className="ml-64">
                <AdminHeader />
                <main className="p-8">
                    {children}
                </main>
            </div>
        </div>
    );
}
