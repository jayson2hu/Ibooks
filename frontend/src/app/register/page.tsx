'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api, getApiErrorMessage } from '@/lib/api';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setMessage('');
        setError('');

        if (password !== confirmPassword) {
            setError('两次输入的密码不一致');
            return;
        }

        setLoading(true);
        try {
            await api.auth.register({ email, username, password });
            setMessage('注册成功，请查收验证邮件后再登录。');
            setEmail('');
            setUsername('');
            setPassword('');
            setConfirmPassword('');
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '注册失败，请稍后重试'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
            <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-sm border border-gray-100">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">创建账户</h1>
                <p className="text-gray-600 mb-6">注册后即可使用书币购买资源。</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="register-email" className="block text-sm font-medium text-gray-700 mb-1">邮箱地址</label>
                        <input id="register-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                        <label htmlFor="register-username" className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                        <input id="register-username" type="text" value={username} onChange={(event) => setUsername(event.target.value)} required minLength={2} autoComplete="username" className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                        <label htmlFor="register-password" className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                        <input id="register-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete="new-password" className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                        <label htmlFor="register-confirm-password" className="block text-sm font-medium text-gray-700 mb-1">确认密码</label>
                        <input id="register-confirm-password" type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required minLength={8} autoComplete="new-password" className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>

                    {message && <div className="rounded bg-green-50 p-3 text-sm text-green-700">{message}</div>}
                    {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

                    <button type="submit" disabled={loading} className="btn btn-primary w-full">
                        {loading ? '注册中...' : '注册'}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm text-gray-600">
                    已有账户？{' '}
                    <Link href="/login" className="text-blue-600 hover:text-blue-700">返回登录</Link>
                </div>
            </div>
        </div>
    );
}
