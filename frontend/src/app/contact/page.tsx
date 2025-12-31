import { api } from '@/lib/api';
import type { Metadata } from 'next';
import CopyButton from '@/components/common/CopyButton';

export const metadata: Metadata = {
    title: '联系我们',
    description: '联系方式 - 随时与我们取得联系',
};

export default async function ContactPage() {
    let contacts = [];

    try {
        const response = await api.contacts.list(true);
        contacts = response.data || [];
    } catch (error) {
        console.error('Failed to fetch contacts:', error);
    }

    // Group contacts by type
    const groupedContacts: any = {};
    contacts.forEach((contact: any) => {
        if (!groupedContacts[contact.type]) {
            groupedContacts[contact.type] = [];
        }
        groupedContacts[contact.type].push(contact);
    });

    return (
        <div className="min-h-screen pt-20">
            <div className="container py-8">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold mb-4">联系我们</h1>
                    <p className="text-xl text-secondary">
                        我们随时为您服务，欢迎联系
                    </p>
                </div>

                {/* Contact Cards */}
                <div className="max-w-4xl mx-auto">
                    <div className="grid grid-2 gap-6 mb-12">
                        {/* WeChat */}
                        {groupedContacts.wechat && groupedContacts.wechat.map((contact: any) => (
                            <div key={contact.id} className="card text-center">
                                <div className="text-4xl mb-4">💬</div>
                                <h3 className="text-xl font-semibold mb-2">{contact.label}</h3>
                                {contact.is_copyable ? (
                                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded">
                                        <CopyButton
                                            value={contact.value}
                                            label={<code className="text-primary font-mono">{contact.value}</code>}
                                            className="text-primary font-mono cursor-pointer hover:bg-gray-200 rounded px-1 -mx-1 transition-colors"
                                        />
                                        <CopyButton
                                            value={contact.value}
                                            className="text-sm text-tertiary hover:text-primary ml-2"
                                        />
                                    </div>
                                ) : (
                                    <p className="text-secondary">{contact.value}</p>
                                )}
                                {contact.description && (
                                    <p className="text-sm text-tertiary mt-2">{contact.description}</p>
                                )}
                            </div>
                        ))}

                        {/* WeChat QR */}
                        {groupedContacts.wechat_qr && groupedContacts.wechat_qr.map((contact: any) => (
                            <div key={contact.id} className="card text-center">
                                <div className="text-4xl mb-4">📱</div>
                                <h3 className="text-xl font-semibold mb-4">{contact.label}</h3>
                                {contact.qr_code_url && (
                                    <div className="inline-block p-4 bg-white border-2 border-gray-200 rounded-lg">
                                        <img
                                            src={contact.qr_code_url}
                                            alt={contact.label}
                                            className="w-48 h-48"
                                        />
                                    </div>
                                )}
                                {contact.description && (
                                    <p className="text-sm text-tertiary mt-4">{contact.description}</p>
                                )}
                            </div>
                        ))}

                        {/* QQ */}
                        {groupedContacts.qq && groupedContacts.qq.map((contact: any) => (
                            <div key={contact.id} className="card text-center">
                                <div className="text-4xl mb-4">🐧</div>
                                <h3 className="text-xl font-semibold mb-2">{contact.label}</h3>
                                {contact.is_clickable && contact.link_url ? (
                                    <a
                                        href={contact.link_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary font-mono hover:underline"
                                    >
                                        {contact.value}
                                    </a>
                                ) : contact.is_copyable ? (
                                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded">
                                        <CopyButton
                                            value={contact.value}
                                            label={<code className="text-primary font-mono">{contact.value}</code>}
                                            className="text-primary font-mono cursor-pointer hover:bg-gray-200 rounded px-1 -mx-1 transition-colors"
                                        />
                                        <CopyButton
                                            value={contact.value}
                                            className="text-sm text-tertiary hover:text-primary ml-2"
                                        />
                                    </div>
                                ) : (
                                    <p className="text-secondary font-mono">{contact.value}</p>
                                )}
                            </div>
                        ))}

                        {/* Email */}
                        {groupedContacts.email && groupedContacts.email.map((contact: any) => (
                            <div key={contact.id} className="card text-center">
                                <div className="text-4xl mb-4">📧</div>
                                <h3 className="text-xl font-semibold mb-2">{contact.label}</h3>
                                <a
                                    href={`mailto:${contact.value}`}
                                    className="text-primary hover:underline"
                                >
                                    {contact.value}
                                </a>
                                {contact.description && (
                                    <p className="text-sm text-tertiary mt-2">{contact.description}</p>
                                )}
                            </div>
                        ))}

                        {/* Phone */}
                        {groupedContacts.phone && groupedContacts.phone.map((contact: any) => (
                            <div key={contact.id} className="card text-center">
                                <div className="text-4xl mb-4">📞</div>
                                <h3 className="text-xl font-semibold mb-2">{contact.label}</h3>
                                <a
                                    href={`tel:${contact.value}`}
                                    className="text-primary hover:underline text-lg"
                                >
                                    {contact.value}
                                </a>
                                {contact.description && (
                                    <p className="text-sm text-tertiary mt-2">{contact.description}</p>
                                )}
                            </div>
                        ))}

                        {/* Telegram */}
                        {groupedContacts.telegram && groupedContacts.telegram.map((contact: any) => (
                            <div key={contact.id} className="card text-center">
                                <div className="text-4xl mb-4">✈️</div>
                                <h3 className="text-xl font-semibold mb-2">{contact.label}</h3>
                                {contact.link_url ? (
                                    <a
                                        href={contact.link_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary hover:underline"
                                    >
                                        {contact.value}
                                    </a>
                                ) : (
                                    <p className="text-secondary">{contact.value}</p>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* FAQ or Additional Info */}
                    <div className="card bg-surface">
                        <h2 className="text-2xl font-bold mb-4">常见问题</h2>
                        <div className="space-y-4">
                            <div>
                                <h3 className="font-semibold mb-2">📮 如何获取资源？</h3>
                                <p className="text-secondary">
                                    浏览资源页面，点击"获取资源"按钮即可获得云盘链接和提取码。
                                </p>
                            </div>
                            <div>
                                <h3 className="font-semibold mb-2">💬 如何联系客服？</h3>
                                <p className="text-secondary">
                                    可以通过上方的微信、QQ或邮箱联系我们，我们将在24小时内回复。
                                </p>
                            </div>
                            <div>
                                <h3 className="font-semibold mb-2">⏰ 工作时间</h3>
                                <p className="text-secondary">
                                    周一至周日 9:00-21:00 (节假日正常服务)
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
