'use client';

import { useEffect, useState } from 'react';
import { 
    CogIcon, 
    GlobeAltIcon, 
    ShieldCheckIcon, 
    BellIcon,
    PaintBrushIcon,
    ServerIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';

const DEFAULT_SETTINGS: Record<string, string> = {
    site_name: '资源市场',
    site_description: '发现并获取高质量的电子书、视频课程、技术文档等数字资源',
    admin_email: 'admin@example.com',
    theme_mode: 'light',
    primary_color: '#6366f1',
    user_registration_enabled: 'true',
    comments_enabled: 'true',
    max_login_attempts: '5',
    session_timeout_minutes: '30',
    smtp_host: 'smtp.gmail.com',
    smtp_port: '587',
    max_file_size_mb: '10',
    allowed_file_types: 'pdf,epub,mobi,mp4,zip,rar',
    signin_enabled: 'false',
    signin_reward_coins: '5',
};

const SETTINGS_CATEGORIES: Record<string, string> = {
    site_name: 'general',
    site_description: 'general',
    admin_email: 'general',
    theme_mode: 'appearance',
    primary_color: 'appearance',
    user_registration_enabled: 'features',
    comments_enabled: 'features',
    max_login_attempts: 'security',
    session_timeout_minutes: 'security',
    smtp_host: 'email',
    smtp_port: 'email',
    max_file_size_mb: 'storage',
    allowed_file_types: 'storage',
    signin_enabled: 'signin',
    signin_reward_coins: 'signin',
};

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('basic');
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState('');
    const [settingsValues, setSettingsValues] = useState<Record<string, string>>(DEFAULT_SETTINGS);

    const tabs = [
        { id: 'basic', name: '基本设置', icon: CogIcon },
        { id: 'appearance', name: '外观设置', icon: PaintBrushIcon },
        { id: 'features', name: '功能设置', icon: GlobeAltIcon },
        { id: 'security', name: '安全设置', icon: ShieldCheckIcon },
        { id: 'email', name: '邮件设置', icon: BellIcon },
        { id: 'storage', name: '存储设置', icon: ServerIcon },
        { id: 'signin', name: '签到设置', icon: BellIcon },
    ];

    useEffect(() => {
        const fetchSettings = async () => {
            setInitialLoading(true);
            setError('');
            try {
                const response = await api.settings.getGrouped();
                const nextValues: Record<string, string> = { ...DEFAULT_SETTINGS };

                for (const group of response.data || []) {
                    for (const setting of group.settings || []) {
                        nextValues[setting.key] = setting.value;
                    }
                }

                setSettingsValues(nextValues);
            } catch (err: any) {
                setError(err.response?.data?.detail || '无法加载系统设置');
            } finally {
                setInitialLoading(false);
            }
        };

        fetchSettings();
    }, []);

    const setSetting = (key: string, value: string) => {
        setSettingsValues((prev) => ({ ...prev, [key]: value }));
    };

    const getSetting = (key: string) => settingsValues[key] ?? DEFAULT_SETTINGS[key] ?? '';

    const handleSave = async () => {
        setLoading(true);
        setError('');
        try {
            await api.settings.batchUpdate(
                Object.entries(settingsValues).map(([key, value]) => ({
                    key,
                    value,
                    category: SETTINGS_CATEGORIES[key] || 'general',
                }))
            );
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || '保存失败，请重试');
        } finally {
            setLoading(false);
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
                    disabled={loading || initialLoading}
                    className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
                        saved 
                            ? 'bg-green-600 text-white' 
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                    } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
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
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
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
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        管理员邮箱
                                    </label>
                                    <input
                                        type="email"
                                        value={getSetting('admin_email')}
                                        onChange={(e) => setSetting('admin_email', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </>
                        )}

                        {activeTab === 'appearance' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        主题模式
                                    </label>
                                    <select
                                        value={getSetting('theme_mode')}
                                        onChange={(e) => setSetting('theme_mode', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="light">浅色模式</option>
                                        <option value="dark">深色模式</option>
                                        <option value="auto">跟随系统</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        主色调
                                    </label>
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="color"
                                            value={getSetting('primary_color')}
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
                                
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-700">评论功能</h3>
                                        <p className="text-sm text-gray-500">允许用户对资源进行评论</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={getSetting('comments_enabled') === 'true'}
                                            onChange={(e) => setSetting('comments_enabled', String(e.target.checked))}
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
                                    <p className="text-sm text-gray-500 mt-1">超过此次数将锁定账户</p>
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
                            <>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            SMTP主机
                                        </label>
                                        <input
                                            type="text"
                                            placeholder="smtp.gmail.com"
                                            value={getSetting('smtp_host')}
                                            onChange={(e) => setSetting('smtp_host', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            SMTP端口
                                        </label>
                                        <input
                                            type="number"
                                            value={getSetting('smtp_port')}
                                            onChange={(e) => setSetting('smtp_port', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>
                                </div>
                                
                                <div className="bg-blue-50 p-4 rounded-lg">
                                    <h4 className="text-sm font-medium text-blue-800 mb-2">测试邮件配置</h4>
                                    <p className="text-sm text-blue-600 mb-3">发送测试邮件验证配置是否正确</p>
                                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                                        发送测试邮件
                                    </button>
                                </div>
                            </>
                        )}

                        {activeTab === 'storage' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        最大文件大小（MB）
                                    </label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="1000"
                                        value={getSetting('max_file_size_mb')}
                                        onChange={(e) => setSetting('max_file_size_mb', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        允许的文件类型
                                    </label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['pdf', 'epub', 'mobi', 'mp4', 'zip', 'rar'].map(type => (
                                            <label key={type} className="flex items-center">
                                                <input
                                                    type="checkbox"
                                                    checked={getSetting('allowed_file_types').split(',').includes(type)}
                                                    onChange={(e) => {
                                                        const current = new Set(getSetting('allowed_file_types').split(',').filter(Boolean));
                                                        if (e.target.checked) {
                                                            current.add(type);
                                                        } else {
                                                            current.delete(type);
                                                        }
                                                        setSetting('allowed_file_types', Array.from(current).join(','));
                                                    }}
                                                    className="mr-2"
                                                />
                                                <span className="text-sm">{type.toUpperCase()}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                    )}
                </div>
            </div>
        </div>
    );
}
