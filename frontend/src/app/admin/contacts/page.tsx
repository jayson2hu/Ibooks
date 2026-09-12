'use client';

import { useState, useEffect } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import type { Contact } from '@/types';

interface ContactFormData {
    type: Contact['type'];
    label: string;
    value: string;
    description?: string;
    qr_code_url?: string;
    is_copyable: boolean;
    is_clickable: boolean;
    link_url?: string;
    display_order: number;
    show_in_header: boolean;
    show_in_footer: boolean;
    show_in_contact_page: boolean;
    show_in_sidebar: boolean;
}

export default function ContactManagement() {
    const emptyForm: ContactFormData = {
        type: 'wechat',
        label: '',
        value: '',
        description: '',
        qr_code_url: '',
        is_copyable: true,
        is_clickable: false,
        link_url: '',
        display_order: 0,
        show_in_header: false,
        show_in_footer: true,
        show_in_contact_page: true,
        show_in_sidebar: false,
    };
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [updatingId, setUpdatingId] = useState<number | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [formData, setFormData] = useState(emptyForm);

    const fetchContacts = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await api.contacts.adminList();
            setContacts(response.data || []);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '无法加载联系方式'));
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
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '状态更新失败'));
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
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '删除失败'));
        } finally {
            setUpdatingId(null);
        }
    };

    const openCreate = () => {
        setEditingId(null);
        setFormData(emptyForm);
        setIsFormOpen(true);
    };

    const openEdit = (contact: Contact) => {
        setEditingId(contact.id);
        setFormData({ ...emptyForm, ...contact });
        setIsFormOpen(true);
    };

    const handleFormChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value, type } = event.target;
        setFormData((previous) => ({
            ...previous,
            [name]: type === 'checkbox' ? (event.target as HTMLInputElement).checked : value,
        }));
    };

    const handleSave = async (event: React.FormEvent) => {
        event.preventDefault();
        setUpdatingId(editingId ?? -1);
        setError('');
        try {
            const payload = { ...formData, display_order: Number(formData.display_order) };
            const response = editingId
                ? await api.contacts.update(editingId, payload)
                : await api.contacts.create(payload);
            setContacts((previous) => editingId
                ? previous.map((contact) => contact.id === editingId ? response.data : contact)
                : [response.data, ...previous]);
            setEditingId(null);
            setFormData(emptyForm);
            setIsFormOpen(false);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '保存联系方式失败'));
        } finally {
            setUpdatingId(null);
        }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">联系方式管理</h1>
                <button onClick={openCreate} className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors">
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
                                <button onClick={() => openEdit(contact)} className="p-1 text-blue-600 bg-blue-50 rounded hover:bg-blue-100" title="编辑">✏️</button>
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
                                    {/* User-configured QR URLs can come from arbitrary external hosts. */}
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
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

            {isFormOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
                    <form onSubmit={handleSave} className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-gray-900">{editingId ? '编辑联系方式' : '添加联系方式'}</h2>
                            <button type="button" onClick={() => { setEditingId(null); setFormData(emptyForm); setIsFormOpen(false); }} className="text-gray-500 hover:text-gray-900" aria-label="关闭">×</button>
                        </div>
                        {!editingId && (
                            <label className="block text-sm text-gray-700">类型
                                <select name="type" value={formData.type} onChange={handleFormChange} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2">
                                    <option value="wechat">微信</option>
                                    <option value="wechat_qr">微信二维码</option>
                                    <option value="qq">QQ</option>
                                    <option value="email">邮箱</option>
                                    <option value="phone">电话</option>
                                    <option value="other">其他</option>
                                </select>
                            </label>
                        )}
                        <label className="block text-sm text-gray-700">名称
                            <input name="label" value={formData.label} onChange={handleFormChange} required className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                        </label>
                        <label className="block text-sm text-gray-700">内容
                            <input name="value" value={formData.value} onChange={handleFormChange} required className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                        </label>
                        <label className="block text-sm text-gray-700">跳转链接（可选）
                            <input name="link_url" value={formData.link_url} onChange={handleFormChange} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                        </label>
                        <label className="block text-sm text-gray-700">二维码图片 URL（可选）
                            <input name="qr_code_url" value={formData.qr_code_url} onChange={handleFormChange} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                        </label>
                        <label className="block text-sm text-gray-700">说明
                            <textarea name="description" value={formData.description} onChange={handleFormChange} rows={2} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                        </label>
                        <div className="flex flex-wrap gap-4 text-sm text-gray-700">
                            <label className="flex items-center gap-2"><input type="checkbox" name="is_copyable" checked={formData.is_copyable} onChange={handleFormChange} />可复制</label>
                            <label className="flex items-center gap-2"><input type="checkbox" name="is_clickable" checked={formData.is_clickable} onChange={handleFormChange} />可点击</label>
                            <label className="flex items-center gap-2"><input type="checkbox" name="show_in_header" checked={formData.show_in_header} onChange={handleFormChange} />全局浮窗</label>
                            <label className="flex items-center gap-2"><input type="checkbox" name="show_in_footer" checked={formData.show_in_footer} onChange={handleFormChange} />显示在页脚</label>
                            <label className="flex items-center gap-2"><input type="checkbox" name="show_in_contact_page" checked={formData.show_in_contact_page} onChange={handleFormChange} />联系页面</label>
                            <label className="flex items-center gap-2"><input type="checkbox" name="show_in_sidebar" checked={formData.show_in_sidebar} onChange={handleFormChange} />资源侧栏</label>
                        </div>
                        <div className="flex justify-end gap-3 pt-2">
                            <button type="button" onClick={() => { setEditingId(null); setFormData(emptyForm); setIsFormOpen(false); }} className="rounded-lg border border-gray-300 px-4 py-2">取消</button>
                            <button type="submit" disabled={updatingId !== null} className="rounded-lg bg-primary px-4 py-2 text-white disabled:opacity-50">保存</button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}
