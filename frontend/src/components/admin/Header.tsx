'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function AdminHeader() {
    const [showUserMenu, setShowUserMenu] = useState(false);

    return (
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
            <div className="flex items-center justify-between px-8 py-4">
                {/* Search Bar */}
                <div className="flex-1 max-w-xl">
                    <div className="relative">
                        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                            type="text"
                            placeholder="搜索资源、用户..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </div>

                {/* Right Section */}
                <div className="flex items-center gap-4">
                    {/* Notifications */}
                    <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                        </svg>
                        <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                    </button>

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
                                <div className="text-sm font-semibold text-gray-900">Admin</div>
                                <div className="text-xs text-gray-500">管理员</div>
                            </div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>

                        {/* Dropdown */}
                        {showUserMenu && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                                <Link href="/admin/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                    个人设置
                                </Link>
                                <Link href="/admin/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                    系统设置
                                </Link>
                                <div className="border-t border-gray-200 my-1"></div>
                                <button className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
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
