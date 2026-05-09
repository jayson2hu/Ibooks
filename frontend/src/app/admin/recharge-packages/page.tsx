'use client';

import { FormEvent, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { RechargePackage } from '@/types';

const EMPTY_FORM = {
    name: '',
    amount: '',
    coins: '',
    bonus_coins: '0',
    sort_order: '0',
    is_active: true,
};

export default function AdminRechargePackagesPage() {
    const [packages, setPackages] = useState<RechargePackage[]>([]);
    const [form, setForm] = useState(EMPTY_FORM);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const loadPackages = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await api.admin.getRechargePackages();
            setPackages(response.data || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || '充值套餐加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPackages();
    }, []);

    const submitPackage = async (event: FormEvent) => {
        event.preventDefault();
        setSaving(true);
        setError('');
        try {
            await api.admin.createRechargePackage({
                name: form.name,
                amount: form.amount,
                coins: Number(form.coins),
                bonus_coins: Number(form.bonus_coins || 0),
                sort_order: Number(form.sort_order || 0),
                is_active: form.is_active,
            });
            setForm(EMPTY_FORM);
            await loadPackages();
        } catch (err: any) {
            setError(err.response?.data?.detail || '充值套餐保存失败');
        } finally {
            setSaving(false);
        }
    };

    const togglePackage = async (item: RechargePackage) => {
        setError('');
        try {
            await api.admin.updateRechargePackage(item.id, { is_active: !item.is_active });
            await loadPackages();
        } catch (err: any) {
            setError(err.response?.data?.detail || '套餐状态更新失败');
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">充值套餐</h1>
                <p className="mt-1 text-gray-600">配置用户可购买的书币套餐</p>
            </div>

            {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

            <form onSubmit={submitPackage} className="grid gap-4 rounded-xl border border-gray-200 bg-white p-6 shadow-sm md:grid-cols-6">
                <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="套餐名称" className="rounded-lg border px-3 py-2 md:col-span-2" />
                <input required value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="金额，例如 9.90" className="rounded-lg border px-3 py-2" />
                <input required value={form.coins} onChange={(e) => setForm({ ...form, coins: e.target.value })} placeholder="书币" className="rounded-lg border px-3 py-2" />
                <input value={form.bonus_coins} onChange={(e) => setForm({ ...form, bonus_coins: e.target.value })} placeholder="赠币" className="rounded-lg border px-3 py-2" />
                <input value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value })} placeholder="排序" className="rounded-lg border px-3 py-2" />
                <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                    启用
                </label>
                <button disabled={saving} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50 md:col-span-5">
                    {saving ? '保存中...' : '新增套餐'}
                </button>
            </form>

            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b border-gray-200 bg-gray-50 text-sm text-gray-600">
                            <tr>
                                <th className="px-6 py-4">名称</th>
                                <th className="px-6 py-4">金额</th>
                                <th className="px-6 py-4">书币</th>
                                <th className="px-6 py-4">赠币</th>
                                <th className="px-6 py-4">排序</th>
                                <th className="px-6 py-4">状态</th>
                                <th className="px-6 py-4">操作</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                <tr><td colSpan={7} className="px-6 py-10 text-center text-gray-500">加载中...</td></tr>
                            ) : packages.length === 0 ? (
                                <tr><td colSpan={7} className="px-6 py-10 text-center text-gray-500">暂无套餐</td></tr>
                            ) : packages.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 font-medium text-gray-900">{item.name}</td>
                                    <td className="px-6 py-4">¥{Number(item.amount).toFixed(2)}</td>
                                    <td className="px-6 py-4">{item.coins}</td>
                                    <td className="px-6 py-4">{item.bonus_coins}</td>
                                    <td className="px-6 py-4">{item.sort_order}</td>
                                    <td className="px-6 py-4">{item.is_active ? '启用' : '停用'}</td>
                                    <td className="px-6 py-4">
                                        <button onClick={() => togglePackage(item)} className="text-sm font-medium text-blue-600 hover:text-blue-700">
                                            {item.is_active ? '停用' : '启用'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
