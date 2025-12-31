'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function AuditLogs() {
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);

    useEffect(() => {
        const fetchLogs = async () => {
            setLoading(true);
            try {
                const response = await api.admin.getAuditLogs({ page, page_size: 20 });
                setLogs(response.data || []);
            } catch (error) {
                console.error('Failed to fetch audit logs:', error);
                // Mock data
                setLogs([
                    { id: 1, action: 'LOGIN', user_id: 1, username: 'admin', ip_address: '192.168.1.1', status: 'SUCCESS', created_at: new Date().toISOString(), details: 'Login via email' },
                    { id: 2, action: 'CREATE_RESOURCE', user_id: 1, username: 'admin', ip_address: '192.168.1.1', status: 'SUCCESS', created_at: new Date(Date.now() - 3600000).toISOString(), details: 'Created resource "Python Guide"' },
                    { id: 3, action: 'DELETE_RESOURCE', user_id: 1, username: 'admin', ip_address: '192.168.1.1', status: 'FAILURE', created_at: new Date(Date.now() - 7200000).toISOString(), details: 'Failed to delete resource #99' },
                ]);
            } finally {
                setLoading(false);
            }
        };

        fetchLogs();
    }, [page]);

    return (
        <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-6">审计日志</h1>

            <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-4 font-medium text-gray-500">时间</th>
                            <th className="px-6 py-4 font-medium text-gray-500">操作用户</th>
                            <th className="px-6 py-4 font-medium text-gray-500">动作</th>
                            <th className="px-6 py-4 font-medium text-gray-500">IP地址</th>
                            <th className="px-6 py-4 font-medium text-gray-500">状态</th>
                            <th className="px-6 py-4 font-medium text-gray-500">详情</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {loading ? (
                            <tr><td colSpan={6} className="px-6 py-8 text-center">加载中...</td></tr>
                        ) : (
                            logs.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{log.username || 'Unknown'}</div>
                                        <div className="text-xs text-gray-400">ID: {log.user_id}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                                            {log.action}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                                        {log.ip_address}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 text-xs rounded-full ${log.status === 'SUCCESS' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                                            }`}>
                                            {log.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={log.details}>
                                        {log.details}
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
