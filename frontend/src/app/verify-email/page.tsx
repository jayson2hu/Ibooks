'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

export default function VerifyEmailPage() {
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState('正在验证邮箱...');

    useEffect(() => {
        const verify = async () => {
            if (!token) {
                setStatus('error');
                setMessage('验证链接缺少 token');
                return;
            }

            try {
                const response = await api.auth.verifyEmail(token);
                setStatus('success');
                setMessage(response.data?.message || '邮箱验证成功');
            } catch (err: any) {
                setStatus('error');
                setMessage(err.response?.data?.detail || '邮箱验证失败');
            }
        };

        verify();
    }, [token]);

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-sm border border-gray-100 text-center">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">邮箱验证</h1>
                <p className={status === 'error' ? 'text-red-600' : status === 'success' ? 'text-green-600' : 'text-gray-600'}>
                    {message}
                </p>
                <Link href="/login" className="btn btn-primary mt-6 inline-block">
                    前往登录
                </Link>
            </div>
        </div>
    );
}
