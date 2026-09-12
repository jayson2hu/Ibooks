'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { AdminRole } from '@/hooks/useAdminAuth';

const menuItems = [
    { name: '仪表盘', href: '/admin', icon: '📊', exact: true },
    { name: '资源管理', href: '/admin/resources', icon: '📚' },
    { name: '分类管理', href: '/admin/categories', icon: '🏷️' },
    { name: '用户管理', href: '/admin/users', icon: '👥', adminOnly: true },
    { name: '订单管理', href: '/admin/orders', icon: '🛒', adminOnly: true },
    { name: '钱包管理', href: '/admin/wallets', icon: '💰', adminOnly: true },
    { name: '资产流水', href: '/admin/coin-ledger', icon: '📒', adminOnly: true },
    { name: '充值订单', href: '/admin/recharge-orders', icon: '💳', adminOnly: true },
    { name: '充值套餐', href: '/admin/recharge-packages', icon: '🎁', adminOnly: true },
    { name: '联系方式', href: '/admin/contacts', icon: '☎️' },
    { name: '审计日志', href: '/admin/audit', icon: '🧾', adminOnly: true },
    { name: '批量导入', href: '/admin/import', icon: '📥', adminOnly: true },
    { name: '系统设置', href: '/admin/settings', icon: '⚙️', adminOnly: true },
    { name: 'SEO 管理', href: '/admin/seo', icon: '🔎' },
    { name: '爬虫管理', href: '/admin/crawler', icon: '🕷️' },
];

export default function AdminSidebar({ role, open = false, onClose }: { role: AdminRole | null; open?: boolean; onClose?: () => void }) {
    const pathname = usePathname();
    const visibleItems = menuItems.filter((item) => !item.adminOnly || role === 'admin');

    return (
        <>
        {open && <button type="button" aria-label="关闭菜单" onClick={onClose} className="fixed inset-0 z-30 bg-black/40 md:hidden" />}
        <aside className={`w-64 bg-slate-900 text-white min-h-screen fixed left-0 top-0 z-40 overflow-y-auto transition-transform md:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
            {/* Logo */}
            <div className="p-6 border-b border-slate-800">
                <Link href="/admin" className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-xl font-bold">
                        i
                    </div>
                    <div>
                        <div className="text-lg font-bold">iBooks</div>
                        <div className="text-xs text-slate-400">管理后台</div>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="px-3 py-4">
                <ul className="space-y-1">
                    {visibleItems.map((item) => {
                        const isActive = item.exact
                            ? pathname === item.href
                            : pathname.startsWith(item.href);

                        return (
                            <li key={item.href}>
                                <Link
                                    href={item.href}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${isActive
                                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                                            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                        }`}
                                >
                                    <span className="text-xl">{item.icon}</span>
                                    <span className="font-medium">{item.name}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            {/* Bottom Links */}
            <div className="sticky bottom-0 w-full p-4 border-t border-slate-800 bg-slate-900">
                <Link
                    href="/"
                    className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors px-4 py-2 rounded-lg hover:bg-slate-800"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    <span>返回前台</span>
                </Link>
            </div>
        </aside>
        </>
    );
}
