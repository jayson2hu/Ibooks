'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function UserManagement() {
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            // Assuming we have a user list API. If not, we might need to add it or use a placeholder.
            // For now, let's mock it or assume api.admin.getUsers exists
            // const response = await api.admin.getUsers({ page, page_size: 10 });
            // setUsers(response.data || []);
            // setTotal(response.total || 0);

            // Mock data since we might not have exposed user list API yet
            setUsers([
                { id: 1, username: 'admin', email: 'admin@example.com', role: 'ADMIN', status: 'ACTIVE', created_at: new Date().toISOString() },
                { id: 2, username: 'user1', email: 'user1@example.com', role: 'USER', status: 'ACTIVE', created_at: new Date().toISOString() },
                { id: 3, username: 'user2', email: 'user2@example.com', role: 'USER', status: 'BANNED', created_at: new Date().toISOString() },
            ]);
            setTotal(3);
        } catch (error) {
            console.error('Failed to fetch users:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, [page]);

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">用户管理</h1>
            </div>

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
                                        <span className={`px-2 py-1 text-xs rounded-full ${user.role === 'ADMIN'
                                                ? 'bg-purple-50 text-purple-600'
                                                : 'bg-gray-100 text-gray-600'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 text-xs rounded-full ${user.status === 'ACTIVE'
                                                ? 'bg-green-50 text-green-600'
                                                : 'bg-red-50 text-red-600'
                                            }`}>
                                            {user.status === 'ACTIVE' ? '正常' : '封禁'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-500 text-sm">
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <button className="text-blue-500 hover:text-blue-700 text-sm mr-3">
                                            编辑
                                        </button>
                                        {user.status === 'ACTIVE' ? (
                                            <button className="text-red-500 hover:text-red-700 text-sm">
                                                封禁
                                            </button>
                                        ) : (
                                            <button className="text-green-500 hover:text-green-700 text-sm">
                                                解封
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
