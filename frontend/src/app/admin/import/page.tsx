'use client';

import { useState } from 'react';
import apiClient, { getApiErrorMessage } from '@/lib/api'; // Direct access for upload

interface ImportResult {
    message: string;
    statistics: {
        total: number;
        success: number;
        failed: number;
        errors: string[];
    };
}

export default function BulkImportPage() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<ImportResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setResult(null);
            setError(null);
        }
    };

    const handleDownloadTemplate = async () => {
        try {
            // Direct download link or API call
            // Assuming backend provides a GET endpoint that returns the file
            const response = await apiClient.get('/bulk-import/template', {
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'resource_import_template.xlsx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error('Download failed:', err);
            alert('模板下载失败');
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await apiClient.post<ImportResult>('/bulk-import/resources', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResult(response.data);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '上传失败，请检查文件格式'));
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">批量导入资源</h1>

            {/* Step 1: Download Template */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
                        1
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-gray-900 mb-2">下载导入模板</h2>
                        <p className="text-gray-500 mb-4">
                            请先下载标准Excel模板，按照格式填写资源信息。注意：
                        </p>
                        <ul className="list-disc list-inside text-sm text-gray-500 mb-4 space-y-1">
                            <li>红色标题列为必填项</li>
                            <li>分类名称必须存在于系统中</li>
                            <li>书币价格请填写非负整数（0表示免费）</li>
                            <li>多个标签请用逗号分隔</li>
                        </ul>
                        <button
                            onClick={handleDownloadTemplate}
                            className="text-primary hover:underline flex items-center gap-2"
                        >
                            <span>📥</span>
                            <span>下载 Excel 模板</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Step 2: Upload File */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
                        2
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-gray-900 mb-2">上传文件</h2>
                        <p className="text-gray-500 mb-4">
                            选择填写好的 Excel (.xlsx, .xls) 或 CSV 文件进行上传。
                        </p>

                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:bg-gray-50 transition-colors cursor-pointer relative">
                            <input
                                type="file"
                                accept=".xlsx,.xls,.csv"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                            <div className="text-4xl mb-2">📄</div>
                            {file ? (
                                <div>
                                    <p className="font-medium text-gray-900">{file.name}</p>
                                    <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                                </div>
                            ) : (
                                <div>
                                    <p className="font-medium text-gray-900">点击或拖拽文件到此处</p>
                                    <p className="text-sm text-gray-500">支持 .xlsx, .xls, .csv</p>
                                </div>
                            )}
                        </div>

                        {file && (
                            <div className="mt-4 flex justify-end">
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-primary-dark disabled:opacity-50 flex items-center gap-2"
                                >
                                    {uploading ? (
                                        <>
                                            <span className="animate-spin">⏳</span>
                                            <span>导入中...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>⬆️</span>
                                            <span>开始导入</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Result Feedback */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700 flex items-start gap-3">
                    <span>❌</span>
                    <div>
                        <p className="font-semibold">导入失败</p>
                        <p className="text-sm">{error}</p>
                    </div>
                </div>
            )}

            {result && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 text-green-700">
                    <div className="flex items-start gap-3 mb-2">
                        <span>✅</span>
                        <div>
                            <p className="font-semibold">导入完成</p>
                            <p className="text-sm">
                                成功导入: <b>{result.statistics.success}</b> 条，
                                失败: <b>{result.statistics.failed}</b> 条
                            </p>
                        </div>
                    </div>

                    {result.statistics.errors.length > 0 && (
                        <div className="mt-4 bg-white p-4 rounded border border-green-200 text-sm">
                            <p className="font-semibold text-red-600 mb-2">错误详情：</p>
                            <ul className="list-disc list-inside space-y-1 text-gray-600 max-h-40 overflow-y-auto">
                                {result.statistics.errors.map((err, idx) => (
                                    <li key={idx}>
                                        {err}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
