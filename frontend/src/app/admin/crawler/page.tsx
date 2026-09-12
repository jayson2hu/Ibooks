'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import type { CrawlerConfig, CrawlerStatus } from '@/types';

const defaults: CrawlerStatus = {
    source_key: '1024',
    source_name: '1024 resources', source_site: '1024zyz.com', enabled: false,
    interval_minutes: 180, max_pages: 2, request_timeout_seconds: 15,
    target_category_id: null, available_fields: [], is_running: false,
    last_status: 'idle', last_count: 0,
};

export default function CrawlerAdminPage() {
    const [status, setStatus] = useState<CrawlerStatus>(defaults);
    const [categories, setCategories] = useState<Array<{ id: number; name: string }>>([]);
    const [loading, setLoading] = useState(true);
    const [hasLoadedConfig, setHasLoadedConfig] = useState(false);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const load = useCallback(async () => {
        setLoading(true); setHasLoadedConfig(false); setError('');
        try {
            const [crawlerResponse, configResponse, categoryResponse] = await Promise.all([
                api.crawler.status(),
                api.crawler.getConfig(),
                api.categories.list(true),
            ]);
            const config = configResponse.data;
            setStatus({
                ...defaults,
                ...crawlerResponse.data,
                ...config,
                available_fields: crawlerResponse.data.available_fields.map((field) => ({
                    ...field,
                    enabled: field.required || config.enabled_fields.includes(field.key),
                })),
            });
            setCategories(categoryResponse.data || []);
            setHasLoadedConfig(true);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '无法加载爬虫状态'));
        } finally { setLoading(false); }
    }, []);
    useEffect(() => { void load(); }, [load]);

    const enabledFields = useMemo(() => status.available_fields.filter((field) => field.enabled && !field.required).map((field) => field.key), [status.available_fields]);
    const update = (changes: Partial<CrawlerStatus>) => setStatus((current) => ({ ...current, ...changes }));
    const save = async () => {
        if (!hasLoadedConfig) {
            setError('爬虫配置尚未成功加载，请重试后再保存');
            return;
        }
        setSaving(true); setMessage(''); setError('');
        try {
            const config: CrawlerConfig = {
                enabled: status.enabled,
                interval_minutes: Math.min(10080, Math.max(10, status.interval_minutes)),
                max_pages: Math.min(50, Math.max(1, status.max_pages)),
                request_timeout_seconds: Math.min(120, Math.max(1, status.request_timeout_seconds)),
                target_category_id: status.target_category_id ?? null,
                enabled_fields: enabledFields,
            };
            await api.crawler.updateConfig(config);
            setMessage('爬虫设置已保存');
            await load();
        } catch (error: unknown) { setError(getApiErrorMessage(error, '保存失败')); }
        finally { setSaving(false); }
    };
    const run = async () => {
        if (!hasLoadedConfig) {
            setError('爬虫配置尚未成功加载，请重试后再运行');
            return;
        }
        setSaving(true); setMessage(''); setError('');
        try { const response = await api.crawler.run(); setMessage(response.data?.message || '爬虫运行完成'); await load(); }
        catch (error: unknown) { setError(getApiErrorMessage(error, '爬虫运行失败')); }
        finally { setSaving(false); }
    };

    return <div className="max-w-4xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-bold text-gray-900">爬虫管理</h1><p className="mt-1 text-sm text-gray-600">配置 {status.source_name} 的定时同步和手动运行。</p></div><div className="flex gap-3"><button type="button" onClick={run} disabled={saving || loading || !hasLoadedConfig || status.is_running} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">{status.is_running ? '运行中...' : '立即运行'}</button><button type="button" onClick={save} disabled={saving || loading || !hasLoadedConfig} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">保存设置</button></div></div>
        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}{!hasLoadedConfig && !loading && <button type="button" onClick={() => void load()} className="ml-3 font-medium underline">重新加载</button>}</div>}
        {message && <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">{message}</div>}
        {!loading && !hasLoadedConfig && <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">配置尚未加载，成功重新加载前不会运行爬虫或提交默认配置。</div>}
        <fieldset disabled={loading || !hasLoadedConfig} className={`space-y-6 ${loading || !hasLoadedConfig ? 'opacity-60' : ''}`}>
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between"><div><h2 className="font-semibold text-gray-900">运行状态</h2><p className="text-sm text-gray-500">{status.source_site} · 最近同步 {status.last_run_at ? new Date(status.last_run_at).toLocaleString() : '尚未运行'}</p></div><span className={`rounded-full px-3 py-1 text-xs font-medium ${status.last_status === 'success' ? 'bg-green-100 text-green-700' : status.last_status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>{status.last_status} · {status.last_count} 条</span></div>
            {status.last_message && <p className="text-sm text-gray-600">{status.last_message}</p>}
            <label className="flex items-center gap-3 text-sm font-medium text-gray-700"><input type="checkbox" checked={status.enabled} onChange={(event) => update({ enabled: event.target.checked })} />启用定时爬虫</label>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3"><label className="text-sm text-gray-700">间隔（分钟）<input type="number" min="10" max="10080" value={status.interval_minutes} onChange={(event) => update({ interval_minutes: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" /></label><label className="text-sm text-gray-700">最大页数<input type="number" min="1" max="50" value={status.max_pages} onChange={(event) => update({ max_pages: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" /></label><label className="text-sm text-gray-700">超时（秒）<input type="number" min="1" max="120" value={status.request_timeout_seconds} onChange={(event) => update({ request_timeout_seconds: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" /></label></div>
            <label className="block text-sm text-gray-700">导入目标分类<select value={status.target_category_id ?? ''} onChange={(event) => update({ target_category_id: event.target.value ? Number(event.target.value) : null })} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"><option value="">不指定分类</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
        </section>
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"><h2 className="font-semibold text-gray-900">同步字段</h2><p className="mt-1 mb-4 text-sm text-gray-500">标题、来源地址和外部 ID 始终同步，其他字段可按需关闭。</p><div className="grid grid-cols-1 gap-3 sm:grid-cols-2">{status.available_fields.map((field) => <label key={field.key} className="flex gap-3 rounded-lg border border-gray-200 p-3 text-sm"><input type="checkbox" checked={field.enabled} disabled={field.required} onChange={(event) => setStatus((current) => ({ ...current, available_fields: current.available_fields.map((item) => item.key === field.key ? { ...item, enabled: event.target.checked } : item) }))} /><span><span className="font-medium text-gray-800">{field.label}{field.required ? '（必填）' : ''}</span><span className="block text-xs text-gray-500">{field.description}</span></span></label>)}</div></section>
        </fieldset>
    </div>;
}
