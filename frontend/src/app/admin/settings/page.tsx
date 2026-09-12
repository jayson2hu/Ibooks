'use client';

import { useCallback, useEffect, useState } from 'react';
import { 
    CogIcon, 
    GlobeAltIcon, 
    ShieldCheckIcon, 
    BellIcon,
    PaintBrushIcon
} from '@heroicons/react/24/outline';
import { api, getApiErrorMessage } from '@/lib/api';
import { isValidPrimaryColor, normalizePrimaryColor } from '@/lib/siteSettings';

const DEFAULT_SETTINGS: Record<string, string> = {
    site_name: '资源市场',
    site_description: '发现并获取高质量的电子书、视频课程、技术文档等数字资源',
    primary_color: '#6366f1',
    user_registration_enabled: 'true',
    max_login_attempts: '10',
    session_timeout_minutes: '1440',
    signin_enabled: 'false',
    signin_reward_coins: '5',
};

const SETTINGS_CATEGORIES: Record<string, string> = {
    site_name: 'general',
    site_description: 'general',
    primary_color: 'appearance',
    user_registration_enabled: 'features',
    max_login_attempts: 'security',
    session_timeout_minutes: 'security',
    signin_enabled: 'signin',
    signin_reward_coins: 'signin',
};

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('basic');
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);
    const [hasLoadedSettings, setHasLoadedSettings] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState('');
    const [testEmailLoading, setTestEmailLoading] = useState(false);
    const [testEmailFeedback, setTestEmailFeedback] = useState<{
        type: 'success' | 'error';
        message: string;
    } | null>(null);
    const [settingsValues, setSettingsValues] = useState<Record<string, string>>(DEFAULT_SETTINGS);

    const tabs = [
        { id: 'basic', name: '基本设置', icon: CogIcon },
        { id: 'appearance', name: '外观设置', icon: PaintBrushIcon },
        { id: 'features', name: '功能设置', icon: GlobeAltIcon },
        { id: 'security', name: '安全设置', icon: ShieldCheckIcon },
        { id: 'email', name: '邮件设置', icon: BellIcon },
        { id: 'signin', name: '签到设置', icon: BellIcon },
    ];

    const fetchSettings = useCallback(async () => {
        setInitialLoading(true);
        setHasLoadedSettings(false);
        setError('');
        try {
            const response = await api.settings.getGrouped();
            const nextValues: Record<string, string> = { ...DEFAULT_SETTINGS };

            for (const group of response.data || []) {
                for (const setting of group.settings || []) {
                    if (Object.prototype.hasOwnProperty.call(SETTINGS_CATEGORIES, setting.key)) {
                        nextValues[setting.key] = setting.value;
                    }
                }
            }

            setSettingsValues(nextValues);
            setHasLoadedSettings(true);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '无法加载系统设置'));
        } finally {
            setInitialLoading(false);
        }
    }, []);

    useEffect(() => {
        void fetchSettings();
    }, [fetchSettings]);

    const setSetting = (key: string, value: string) => {
        setSettingsValues((prev) => ({ ...prev, [key]: value }));
    };

    const getSetting = (key: string) => settingsValues[key] ?? DEFAULT_SETTINGS[key] ?? '';

    const handleSave = async () => {
        if (!hasLoadedSettings) {
            setError('系统设置尚未成功加载，请重试后再保存');
            return;
        }
        if (!isValidPrimaryColor(getSetting('primary_color'))) {
            setError('主色调必须是 #RRGGBB 格式的颜色值');
            return;
        }
        setLoading(true);
        setError('');
        try {
            await api.settings.batchUpdate(
                Object.entries(settingsValues)
                    .filter(([key]) => Object.prototype.hasOwnProperty.call(SETTINGS_CATEGORIES, key))
                    .map(([key, value]) => ({
                        key,
                        value,
                        category: SETTINGS_CATEGORIES[key],
                    }))
            );
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (error: unknown) {
            setError(getApiErrorMessage(error, '保存失败，请重试'));
        } finally {
            setLoading(false);
        }
    };

    const handleTestEmail = async () => {
        setTestEmailLoading(true);
        setTestEmailFeedback(null);
        try {
            const response = await api.settings.testEmail();
            setTestEmailFeedback({
                type: 'success',
                message: response.data.message || '测试邮件已发送到当前管理员邮箱',
            });
        } catch (error: unknown) {
            setTestEmailFeedback({
                type: 'error',
                message: getApiErrorMessage(
                    error,
                    '测试邮件发送失败，请检查后端 SMTP 环境配置后重试'
                ),
            });
        } finally {
            setTestEmailLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
                    <p className="mt-1 text-gray-600">管理系统配置和偏好设置</p>
                </div>
                
                <button
                    onClick={handleSave}
                    disabled={loading || initialLoading || !hasLoadedSettings}
                    className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
                        saved 
                            ? 'bg-green-600 text-white' 
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                    } ${loading || initialLoading || !hasLoadedSettings ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                    {loading ? (
                        <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            保存中...
                        </>
                    ) : saved ? (
                        <>
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            已保存
                        </>
                    ) : (
                        '保存设置'
                    )}
                </button>
            </div>

            {error && (
                <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                    {!hasLoadedSettings && !initialLoading && (
                        <button
                            type="button"
                            onClick={() => void fetchSettings()}
                            className="ml-3 font-medium underline"
                        >
                            重新加载
                        </button>
                    )}
                </div>
            )}

            <div className="flex gap-6">
                {/* Sidebar */}
                <div className="w-64 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                    <nav className="space-y-1">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-lg transition-colors ${
                                        activeTab === tab.id
                                            ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                            : 'text-gray-600 hover:bg-gray-50'
                                    }`}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span className="font-medium">{tab.name}</span>
                                </button>
                            );
                        })}
                    </nav>
                </div>

                {/* Content */}
                <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-gray-900">
                            {tabs.find(tab => tab.id === activeTab)?.name}
                        </h2>
                    </div>
                    {initialLoading ? (
                        <div className="py-12 text-center text-gray-500">加载中...</div>
                    ) : !hasLoadedSettings ? (
                        <div className="py-12 text-center text-gray-500">
                            设置尚未加载，成功重新加载前不会提交任何默认值。
                        </div>
                    ) : (
                    <div className="space-y-6">
                        {activeTab === 'basic' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        网站名称
                                    </label>
                                    <input
                                        type="text"
                                        value={getSetting('site_name')}
                                        onChange={(e) => setSetting('site_name', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        网站描述
                                    </label>
                                    <textarea
                                        value={getSetting('site_description')}
                                        onChange={(e) => setSetting('site_description', e.target.value)}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </>
                        )}

                        {activeTab === 'appearance' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        主色调
                                    </label>
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="color"
                                            value={normalizePrimaryColor(getSetting('primary_color'))}
                                            onChange={(e) => setSetting('primary_color', e.target.value)}
                                            className="w-12 h-12 border border-gray-300 rounded-lg cursor-pointer"
                                        />
                                        <input
                                            type="text"
                                            value={getSetting('primary_color')}
                                            onChange={(e) => setSetting('primary_color', e.target.value)}
                                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>
                                </div>
                            </>
                        )}

                        {activeTab === 'features' && (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-700">用户注册</h3>
                                        <p className="text-sm text-gray-500">允许新用户注册账号</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={getSetting('user_registration_enabled') === 'true'}
                                            onChange={(e) => setSetting('user_registration_enabled', String(e.target.checked))}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                    </label>
                                </div>
                            </div>
                        )}

                        {activeTab === 'signin' && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-700">每日签到</h3>
                                        <p className="text-sm text-gray-500">开启后用户每天可领取一次书币奖励</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={getSetting('signin_enabled') === 'true'}
                                            onChange={(e) => setSetting('signin_enabled', String(e.target.checked))}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                    </label>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        签到奖励书币
                                    </label>
                                    <input
                                        type="number"
                                        min="1"
                                        value={getSetting('signin_reward_coins')}
                                        onChange={(e) => setSetting('signin_reward_coins', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <p className="text-sm text-gray-500 mt-1">保存后，新的签到记录会按该数量发放。</p>
                                </div>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        最大登录尝试次数
                                    </label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="10"
                                        value={getSetting('max_login_attempts')}
                                        onChange={(e) => setSetting('max_login_attempts', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <p className="text-sm text-gray-500 mt-1">同一客户端 IP 在 60 秒内超过此次数将暂时被限流</p>
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        会话超时时间（分钟）
                                    </label>
                                    <input
                                        type="number"
                                        min="5"
                                        max="1440"
                                        value={getSetting('session_timeout_minutes')}
                                        onChange={(e) => setSetting('session_timeout_minutes', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </>
                        )}

                        {activeTab === 'email' && (
                            <div className="space-y-6">
                                <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                                    <h3 className="text-sm font-semibold text-blue-900">SMTP 配置由后端环境管理</h3>
                                    <p className="mt-2 text-sm leading-6 text-blue-800">
                                        SMTP 主机、端口、发件账号和密码由后端环境变量配置。
                                        页面顶部的“保存设置”不会修改这些连接信息或密钥。
                                    </p>
                                    <p className="mt-2 text-xs leading-5 text-blue-700">
                                        运维配置项：EMAIL_SMTP_HOST、EMAIL_SMTP_PORT、EMAIL_FROM、
                                        EMAIL_USERNAME、EMAIL_PASSWORD 和 EMAIL_USE_TLS。
                                    </p>
                                </div>

                                <div className="rounded-lg border border-gray-200 p-4">
                                    <h4 className="text-sm font-medium text-gray-900">测试当前运行环境</h4>
                                    <p id="smtp-test-description" className="mt-2 text-sm text-gray-600">
                                        系统会向当前登录管理员的账号邮箱发送固定测试内容，不支持指定其他收件人。
                                    </p>
                                    <button
                                        type="button"
                                        onClick={handleTestEmail}
                                        disabled={testEmailLoading}
                                        aria-busy={testEmailLoading}
                                        aria-describedby="smtp-test-description smtp-test-feedback"
                                        className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                        {testEmailLoading && (
                                            <span
                                                aria-hidden="true"
                                                className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                                            />
                                        )}
                                        {testEmailLoading ? '发送中...' : '发送测试邮件'}
                                    </button>

                                    <div id="smtp-test-feedback" className="mt-3 min-h-5 text-sm">
                                        {testEmailFeedback && (
                                            <p
                                                role={testEmailFeedback.type === 'error' ? 'alert' : 'status'}
                                                className={
                                                    testEmailFeedback.type === 'error'
                                                        ? 'text-red-700'
                                                        : 'text-green-700'
                                                }
                                            >
                                                {testEmailFeedback.message}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                    )}
                </div>
            </div>
        </div>
    );
}
