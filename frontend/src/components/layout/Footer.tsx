'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import CopyButton from '@/components/common/CopyButton';
import { useSiteSettings } from '@/contexts/SiteSettingsContext';
import type { Contact } from '@/types';

export default function Footer() {
    const { copyrightText, footerBrandText, siteName, siteDescription } = useSiteSettings();
    const [contacts, setContacts] = useState<Contact[]>([]);

    useEffect(() => {
        api.contacts.list(true)
            .then((response) => setContacts((response.data || []).filter((contact) => contact.show_in_footer)))
            .catch((error) => console.error('Failed to fetch footer contacts:', error));
    }, []);

    return (
        <footer className="bg-gray-900 text-white">
            {/* Main Footer */}
            <div className="container py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                    {/* Brand */}
                    <div>
                        <div className="text-2xl font-bold mb-4">📚 {siteName}</div>
                        <p className="text-gray-400 text-sm">
                            {siteDescription}
                        </p>
                        {footerBrandText !== siteDescription && (
                            <p className="mt-2 text-xs text-gray-500">{footerBrandText}</p>
                        )}
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="font-semibold mb-4">快速链接</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link href="/resources" className="text-gray-400 hover:text-white transition-colors">
                                    浏览资源
                                </Link>
                            </li>
                            <li>
                                <Link href="/categories" className="text-gray-400 hover:text-white transition-colors">
                                    分类
                                </Link>
                            </li>
                            <li>
                                <Link href="/search" className="text-gray-400 hover:text-white transition-colors">
                                    搜索
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Support */}
                    <div>
                        <h3 className="font-semibold mb-4">帮助与支持</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link href="/about" className="text-gray-400 hover:text-white transition-colors">
                                    关于我们
                                </Link>
                            </li>
                            <li>
                                <Link href="/contact" className="text-gray-400 hover:text-white transition-colors">
                                    联系方式
                                </Link>
                            </li>
                            <li>
                                <Link href="/faq" className="text-gray-400 hover:text-white transition-colors">
                                    常见问题
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Legal */}
                    <div>
                        <h3 className="font-semibold mb-4">法律信息</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link href="/privacy" className="text-gray-400 hover:text-white transition-colors">
                                    隐私政策
                                </Link>
                            </li>
                            <li>
                                <Link href="/terms" className="text-gray-400 hover:text-white transition-colors">
                                    服务条款
                                </Link>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Bottom Bar */}
            <div className="border-t border-gray-800">
                <div className="container py-6">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-400">
                        <p>
                            {copyrightText || `© ${new Date().getFullYear()} ${siteName}. 保留所有权利.`}
                        </p>
                        <div className="flex flex-wrap gap-4">
                            {contacts.slice(0, 4).map((contact) => (
                                contact.is_clickable && contact.link_url ? (
                                    <a key={contact.id} href={contact.link_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                                        {contact.label}
                                    </a>
                                ) : contact.is_copyable ? (
                                    <CopyButton key={contact.id} value={contact.value} label={contact.label} className="hover:text-white transition-colors" />
                                ) : (
                                    <span key={contact.id}>{contact.label}: {contact.value}</span>
                                )
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
