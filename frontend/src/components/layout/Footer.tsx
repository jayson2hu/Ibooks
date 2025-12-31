'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function Footer() {
    const [copyrightText, setCopyrightText] = useState('© 2025 资源市场. 保留所有权利.');
    const [brandText, setBrandText] = useState('提供优质的电子书、视频课程和技术文档，助力您的学习和成长。');

    useEffect(() => {
        // Fetch copyright text from settings
        const fetchSettings = async () => {
            try {
                const response = await api.settings.get('copyright_text');
                if (response.data?.value) {
                    setCopyrightText(response.data.value);
                }
            } catch (error) {
                console.error('Failed to fetch copyright text:', error);
                // Keep default value on error
            }

            try {
                const response = await api.settings.get('footer_brand_text');
                if (response.data?.value) {
                    setBrandText(response.data.value);
                }
            } catch (error) {
                console.error('Failed to fetch brand text:', error);
                // Keep default value on error
            }
        };

        fetchSettings();
    }, []);

    return (
        <footer className="bg-gray-900 text-white">
            {/* Main Footer */}
            <div className="container py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                    {/* Brand */}
                    <div>
                        <div className="text-2xl font-bold mb-4">📚 资源市场</div>
                        <p className="text-gray-400 text-sm">
                            {brandText}
                        </p>
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
                        <p>{copyrightText}</p>
                        <div className="flex gap-6">
                            <a href="#" className="hover:text-white transition-colors">
                                微信
                            </a>
                            <a href="#" className="hover:text-white transition-colors">
                                QQ
                            </a>
                            <a href="#" className="hover:text-white transition-colors">
                                邮箱
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
