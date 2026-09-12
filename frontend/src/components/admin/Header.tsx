'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Menu } from 'lucide-react';
import type { AdminRole } from '@/hooks/useAdminAuth';

export default function AdminHeader({ role, onMenuOpen }: { role: AdminRole | null; onMenuOpen?: () => void }) {
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const { adminLogout } = useAuth();
    const router = useRouter();

    const submitSearch = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const query = searchQuery.trim();
        if (query) {
            router.push(`/admin/resources?search=${encodeURIComponent(query)}`);
        }
    };

    return (
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
            <div className="flex items-center justify-between gap-4 px-4 py-3 sm:px-8 sm:py-4">
                <button type="button" onClick={onMenuOpen} aria-label="打开菜单" className="rounded-lg p-2 text-gray-600 hover:bg-gray-100 md:hidden">
                    <Menu className="h-5 w-5" />
                </button>
                <form className="hidden flex-1 max-w-xl sm:block" onSubmit={submitSearch}>
                    <div className="relative">
                        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                            type="text"
                            aria-label="搜索资源"
                            placeholder="搜索资源..."
                            value={searchQuery}
                            onChange={(event) => setSearchQuery(event.target.value)}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </form>

                {/* Right Section */}
                <div className="flex items-center gap-4">
                    {role === 'admin' && (
                        <Link
                            href="/admin/audit"
                            aria-label="查看审计日志"
                            title="查看审计日志"
                            className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                        </Link>
                    )}

                    {/* User Menu */}
                    <div className="relative">
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-semibold">
                                A
                            </div>
                            <div className="text-left hidden md:block">
                                <div className="text-sm font-semibold text-gray-900">{role === 'moderator' ? 'Moderator' : 'Admin'}</div>
                                <div className="text-xs text-gray-500">{role === 'moderator' ? '内容审核员' : '管理员'}</div>
                            </div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>

                        {/* Dropdown */}
                        {showUserMenu && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                                {role === 'admin' && (
                                    <Link href="/admin/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                        系统设置
                                    </Link>
                                )}
                                {role === 'admin' && <div className="border-t border-gray-200 my-1"></div>}
                                <button
                                    onClick={() => adminLogout()}
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                                >
                                    退出登录
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
