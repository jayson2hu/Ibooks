'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function ContactManagement() {
    const [contacts, setContacts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [updatingId, setUpdatingId] = useState<number | null>(null);

    const fetchContacts = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await api.contacts.adminList();
            setContacts(response.data || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || '无法加载联系方式');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchContacts();
    }, []);

    const toggleStatus = async (id: number, currentStatus: boolean) => {
        setUpdatingId(id);
        setError('');
        try {
            const response = await api.contacts.update(id, { is_active: !currentStatus });
            setContacts((prev) => prev.map((contact) => contact.id === id ? response.data : contact));
        } catch (err: any) {
            setError(err.response?.data?.detail || '状态更新失败');
        } finally {
            setUpdatingId(null);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('确定删除此联系方式吗？')) return;
        setUpdatingId(id);
        setError('');
        try {
            await api.contacts.delete(id);
            setContacts((prev) => prev.filter((contact) => contact.id !== id));
        } catch (err: any) {
            setError(err.response?.data?.detail || '删除失败');
        } finally {
            setUpdatingId(null);
        }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">联系方式管理</h1>
                <button className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors">
                    + 添加联系方式
                </button>
            </div>

            {error && (
                <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-full text-center py-8 text-gray-500">加载中...</div>
                ) : contacts.length === 0 ? (
                    <div className="col-span-full text-center py-8 text-gray-500">暂无联系方式</div>
                ) : (
                    contacts.map((contact) => (
                        <div key={contact.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 relative group">
                            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={() => toggleStatus(contact.id, contact.is_active)}
                                    disabled={updatingId === contact.id}
                                    className={`p-1 rounded ${contact.is_active ? 'text-green-600 bg-green-50' : 'text-gray-400 bg-gray-100'}`}
                                    title={contact.is_active ? "已启用" : "已禁用"}
                                >
                                    {updatingId === contact.id ? '…' : contact.is_active ? '✅' : '🚫'}
                                </button>
                                <button className="p-1 text-blue-600 bg-blue-50 rounded hover:bg-blue-100" title="编辑">✏️</button>
                                <button
                                    onClick={() => handleDelete(contact.id)}
                                    disabled={updatingId === contact.id}
                                    className="p-1 text-red-600 bg-red-50 rounded hover:bg-red-100"
                                    title="删除"
                                >
                                    🗑️
                                </button>
                            </div>

                            <div className="flex items-center gap-4 mb-4">
                                <div className="text-3xl">
                                    {contact.type === 'wechat' ? '💬' :
                                        contact.type === 'qq' ? '🐧' :
                                            contact.type === 'email' ? '📧' :
                                                contact.type === 'phone' ? '📞' : '🔗'}
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900">{contact.label}</h3>
                                    <p className="text-xs text-gray-500 uppercase">{contact.type}</p>
                                </div>
                            </div>

                            <div className="bg-gray-50 p-3 rounded-lg mb-4 font-mono text-sm break-all">
                                {contact.value}
                            </div>

                            {contact.qr_code_url && (
                                <div className="mb-4 flex justify-center">
                                    <img src={contact.qr_code_url} alt="QR Code" className="w-32 h-32 object-contain border rounded" />
                                </div>
                            )}

                            <div className="flex flex-wrap gap-2 text-xs">
                                {contact.is_copyable && (
                                    <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded">可复制</span>
                                )}
                                {contact.is_clickable && (
                                    <span className="px-2 py-1 bg-purple-50 text-purple-600 rounded">可点击</span>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
