'use client';

import { useState } from 'react';
import { 
    CogIcon, 
    GlobeAltIcon, 
    ShieldCheckIcon, 
    BellIcon,
    PaintBrushIcon,
    ServerIcon
} from '@heroicons/react/24/outline';

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('basic');
    const [loading, setLoading] = useState(false);
    const [saved, setSaved] = useState(false);

    const tabs = [
        { id: 'basic', name: '基本设置', icon: CogIcon },
        { id: 'appearance', name: '外观设置', icon: PaintBrushIcon },
        { id: 'features', name: '功能设置', icon: GlobeAltIcon },
        { id: 'security', name: '安全设置', icon: ShieldCheckIcon },
        { id: 'email', name: '邮件设置', icon: BellIcon },
        { id: 'storage', name: '存储设置', icon: ServerIcon },
    ];

    const handleSave = async () => {
        setLoading(true);
        try {
            await new Promise(resolve => setTimeout(resolve, 1000));
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (error) {
            console.error('保存设置失败:', error);
            alert('保存失败，请重试');
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
                    disabled={loading}
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
                    
                    <div className="space-y-6">
                        {activeTab === 'basic' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        网站名称
                                    </label>
                                    <input
                                        type="text"
                                        defaultValue="资源市场"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        网站描述
                                    </label>
                                    <textarea
                                        defaultValue="发现并获取高质量的电子书、视频课程、技术文档等数字资源"
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
                                        defaultValue="admin@example.com"
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
                                    <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
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
                                            defaultValue="#6366f1"
                                            className="w-12 h-12 border border-gray-300 rounded-lg cursor-pointer"
                                        />
                                        <input
                                            type="text"
                                            defaultValue="#6366f1"
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
                                        <input type="checkbox" defaultChecked className="sr-only peer" />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                    </label>
                                </div>
                                
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-700">评论功能</h3>
                                        <p className="text-sm text-gray-500">允许用户对资源进行评论</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" defaultChecked className="sr-only peer" />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                    </label>
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
                                        defaultValue="5"
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
                                        defaultValue="30"
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
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            SMTP端口
                                        </label>
                                        <input
                                            type="number"
                                            defaultValue="587"
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
                                        defaultValue="10"
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
                                                <input type="checkbox" defaultChecked className="mr-2" />
                                                <span className="text-sm">{type.toUpperCase()}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}