'use client';

import { useCallback, useEffect, useState } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import type { AdminUserUpdate, User } from '@/types';

export default function UserManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [updatingId, setUpdatingId] = useState<number | null>(null);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(0);
    const pageSize = 20;

    const fetchUsers = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const response = await api.admin.getUsers({ page, page_size: pageSize });
            setUsers(response.data.items);
            setTotal(response.data.total);
            setPages(response.data.pages);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '无法加载用户列表'));
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => {
        void fetchUsers();
    }, [fetchUsers]);

    const updateUser = async (id: number, data: AdminUserUpdate) => {
        setUpdatingId(id);
        setError('');
        try {
            const response = await api.admin.updateUser(id, data);
            setUsers((prev) => prev.map((user) => user.id === id ? response.data : user));
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '用户更新失败'));
        } finally {
            setUpdatingId(null);
        }
    };

    const toggleStatus = (user: User) => {
        const nextStatus = user.status === 'active' ? 'suspended' : 'active';
        updateUser(user.id, { status: nextStatus });
    };

    const changeRole = (user: User, role: User['role']) => {
        updateUser(user.id, { role });
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">用户管理</h1>
            </div>

            {error && (
                <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            {/* Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-4 font-medium text-gray-500">ID</th>
                            <th className="px-6 py-4 font-medium text-gray-500">用户名</th>
                            <th className="px-6 py-4 font-medium text-gray-500">邮箱</th>
                            <th className="px-6 py-4 font-medium text-gray-500">角色</th>
                            <th className="px-6 py-4 font-medium text-gray-500">状态</th>
                            <th className="px-6 py-4 font-medium text-gray-500">注册时间</th>
                            <th className="px-6 py-4 font-medium text-gray-500">操作</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {loading ? (
                            <tr>
                                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                                    加载中...
                                </td>
                            </tr>
                        ) : (
                            users.map((user) => (
                                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 text-gray-500">#{user.id}</td>
                                    <td className="px-6 py-4 font-medium text-gray-900">
                                        <div className="flex items-center gap-2">
                                            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">
                                                {user.username[0].toUpperCase()}
                                            </div>
                                            {user.username}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-gray-600">{user.email}</td>
                                    <td className="px-6 py-4">
                                        <select
                                            value={user.role}
                                            disabled={updatingId === user.id || user.role === 'admin'}
                                            onChange={(e) => changeRole(user, e.target.value as User['role'])}
                                            className="rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 disabled:bg-gray-50 disabled:text-gray-400"
                                        >
                                            <option value="user">用户</option>
                                            <option value="moderator">协管员</option>
                                            <option value="admin">管理员</option>
                                        </select>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 text-xs rounded-full ${user.status === 'active'
                                                ? 'bg-green-50 text-green-600'
                                                : 'bg-red-50 text-red-600'
                                            }`}>
                                            {user.status === 'active' ? '正常' : '封禁'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-500 text-sm">
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            onClick={() => toggleStatus(user)}
                                            disabled={updatingId === user.id || user.role === 'admin'}
                                            className={`text-sm disabled:cursor-not-allowed disabled:text-gray-300 ${user.status === 'active'
                                                    ? 'text-red-500 hover:text-red-700'
                                                    : 'text-green-500 hover:text-green-700'
                                                }`}
                                        >
                                            {updatingId === user.id ? '处理中...' : user.status === 'active' ? '封禁' : '解封'}
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                <span>共 {total} 条，当前页 {users.length} 条记录</span>
                <div className="flex gap-2">
                    <button
                        onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                        disabled={page === 1 || loading}
                        className="rounded border border-gray-200 px-3 py-1 disabled:opacity-50"
                    >
                        上一页
                    </button>
                    <span className="px-2 py-1">第 {page} 页</span>
                    <button
                        onClick={() => setPage((prev) => prev + 1)}
                        disabled={loading || page >= pages}
                        className="rounded border border-gray-200 px-3 py-1 disabled:opacity-50"
                    >
                        下一页
                    </button>
                </div>
            </div>
        </div>
    );
}
