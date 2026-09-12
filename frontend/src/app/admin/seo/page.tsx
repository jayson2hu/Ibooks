'use client';

import { useState } from 'react';
import { api, getApiErrorDetail, getApiErrorMessage } from '@/lib/api';

interface GenerationFeedback {
    kind: 'success' | 'error';
    message: string;
    generated: string[];
    failed: string[];
}

export default function AdminSeoPage() {
    const [urls, setUrls] = useState('');
    const [submissionStatus, setSubmissionStatus] = useState('');
    const [generationFeedback, setGenerationFeedback] = useState<GenerationFeedback | null>(null);
    const [generating, setGenerating] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const generateAll = async () => {
        setGenerating(true);
        setGenerationFeedback(null);
        try {
            const response = await api.seo.generateAll();
            setGenerationFeedback({
                kind: 'success',
                message: response.data.message,
                generated: response.data.generated,
                failed: [],
            });
        } catch (error: unknown) {
            const detail = getApiErrorDetail(error);
            const failureDetail = detail && typeof detail === 'object' ? detail : undefined;
            setGenerationFeedback({
                kind: 'error',
                message: getApiErrorMessage(error, 'SEO 文件生成失败，请稍后重试'),
                generated: failureDetail?.generated || [],
                failed: failureDetail?.failed || [],
            });
        } finally {
            setGenerating(false);
        }
    };

    const submitBaidu = async () => {
        const values = urls.split(/\r?\n/).map((url) => url.trim()).filter(Boolean);
        if (values.length === 0) {
            setSubmissionStatus('请至少输入一个 URL');
            return;
        }
        setSubmitting(true);
        setSubmissionStatus('');
        try {
            const response = await api.seo.submitBaidu(values);
            setSubmissionStatus(response.data?.skipped ? '百度推送未启用或缺少 API Key，已跳过' : `百度推送完成，共提交 ${response.data?.submitted ?? values.length} 个 URL`);
        } catch (error: unknown) {
            setSubmissionStatus(getApiErrorMessage(error, '百度推送失败'));
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="max-w-3xl space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">SEO 管理</h1>
                <p className="mt-2 text-sm text-gray-600">生成站点 SEO 文件，或将公开页面提交到已配置的百度站长平台。</p>
            </div>
            <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900">生成 SEO 文件</h2>
                <p className="mt-1 text-sm text-gray-500">包括 sitemap、RSS 和 robots.txt。</p>
                <button type="button" onClick={generateAll} disabled={generating} className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
                    {generating ? '生成中...' : '生成全部文件'}
                </button>
                {generationFeedback && (
                    <div
                        role={generationFeedback.kind === 'error' ? 'alert' : 'status'}
                        className={`mt-4 rounded-lg border px-4 py-3 text-sm ${
                            generationFeedback.kind === 'error'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-green-200 bg-green-50 text-green-800'
                        }`}
                    >
                        <p>{generationFeedback.message}</p>
                        {generationFeedback.generated.length > 0 && (
                            <p className="mt-1">已生成：{generationFeedback.generated.join('、')}</p>
                        )}
                        {generationFeedback.failed.length > 0 && (
                            <p className="mt-1">失败：{generationFeedback.failed.join('、')}</p>
                        )}
                        {generationFeedback.kind === 'error' && (
                            <button
                                type="button"
                                onClick={generateAll}
                                disabled={generating}
                                className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
                            >
                                重新生成
                            </button>
                        )}
                    </div>
                )}
            </section>
            <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900">百度 URL 推送</h2>
                <p className="mt-1 text-sm text-gray-500">每行一个完整 URL。只有配置 `SEO_SUBMIT_BAIDU=true` 和 `BAIDU_API_KEY` 后才会实际提交。</p>
                <textarea value={urls} onChange={(event) => setUrls(event.target.value)} rows={8} placeholder="https://example.com/resources/example" className="mt-4 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
                <button type="button" onClick={submitBaidu} disabled={submitting} className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
                    {submitting ? '提交中...' : '提交到百度'}
                </button>
                {submissionStatus && (
                    <div role="status" className="mt-4 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
                        {submissionStatus}
                    </div>
                )}
            </section>
        </div>
    );
}
