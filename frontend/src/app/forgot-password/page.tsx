'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');
        setError('');

        try {
            const response = await api.auth.forgotPassword(email);
            setMessage(response.data?.message || '如果邮箱存在，我们已发送密码重置邮件');
        } catch (err: any) {
            setError(err.response?.data?.detail || '提交失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-sm border border-gray-100">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">忘记密码</h1>
                <p className="text-gray-600 mb-6">输入邮箱，我们会发送密码重置链接。</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="you@example.com"
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />

                    {message && <div className="rounded bg-green-50 p-3 text-sm text-green-700">{message}</div>}
                    {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary w-full"
                    >
                        {loading ? '提交中...' : '发送重置邮件'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
                        返回登录
                    </Link>
                </div>
            </div>
        </div>
    );
}
