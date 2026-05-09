'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

export default function ResetPasswordPage() {
    const searchParams = useSearchParams();
    const token = searchParams.get('token') || '';
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage('');
        setError('');

        if (!token) {
            setError('重置链接缺少 token');
            return;
        }

        if (password !== confirmPassword) {
            setError('两次输入的密码不一致');
            return;
        }

        setLoading(true);
        try {
            const response = await api.auth.resetPassword(token, password);
            setMessage(response.data?.message || '密码重置成功');
        } catch (err: any) {
            setError(err.response?.data?.detail || '密码重置失败');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-sm border border-gray-100">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">重置密码</h1>
                <p className="text-gray-600 mb-6">请输入新密码。</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        minLength={8}
                        placeholder="新密码"
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        minLength={8}
                        placeholder="确认新密码"
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />

                    {message && <div className="rounded bg-green-50 p-3 text-sm text-green-700">{message}</div>}
                    {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary w-full"
                    >
                        {loading ? '提交中...' : '重置密码'}
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
