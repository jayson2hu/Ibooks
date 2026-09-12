'use client';

import { useState, useEffect } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import { formatAuditDetails } from '@/lib/audit';
import type { AuditLog } from '@/types';

export default function AuditLogs() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchLogs = async () => {
            setLoading(true);
            setError('');
            try {
                const response = await api.admin.getAuditLogs({ page, page_size: 20 });
                setLogs(response.data.items);
                setPages(response.data.pages);
                setTotal(response.data.total);
            } catch (error: unknown) {
                setLogs([]);
                setError(getApiErrorMessage(error, '审计日志加载失败，请稍后重试'));
            } finally {
                setLoading(false);
            }
        };

        void fetchLogs();
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
                            error ? (
                                <tr><td colSpan={6} className="px-6 py-8 text-center text-red-600">{error}</td></tr>
                            ) : logs.length === 0 ? (
                                <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-500">暂无审计日志</td></tr>
                            ) : logs.map((log) => {
                                const details = formatAuditDetails(log.details);

                                return <tr key={log.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{log.user_email || '系统'}</div>
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
                                        <span className={`px-2 py-1 text-xs rounded-full ${log.success ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                                            }`}>
                                            {log.success ? '成功' : '失败'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={details}>
                                        {details}
                                    </td>
                                </tr>
                            })
                        )}
                    </tbody>
                </table>
            </div>
            <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
                <span>第 {page} / {pages || 1} 页，共 {total} 条</span>
                <div className="flex gap-2">
                    <button type="button" disabled={page <= 1 || loading} onClick={() => setPage((current) => current - 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">上一页</button>
                    <button type="button" disabled={page >= pages || loading} onClick={() => setPage((current) => current + 1)} className="rounded-lg border px-4 py-2 disabled:opacity-50">下一页</button>
                </div>
            </div>
        </div>
    );
}
