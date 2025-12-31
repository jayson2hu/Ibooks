'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ChatBubbleLeftRightIcon,
    XMarkIcon,
    PhoneIcon,
    EnvelopeIcon,
    ChatBubbleOvalLeftEllipsisIcon,
    DevicePhoneMobileIcon
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import CopyButton from './CopyButton';

interface Contact {
    id: number;
    type: string;
    value: string;
    label: string;
    is_clickable: boolean;
    is_copyable: boolean;
    link_url?: string;
    qr_code_url?: string;
    description?: string;
}

export default function FloatingContact() {
    const [isOpen, setIsOpen] = useState(false);
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [loading, setLoading] = useState(true);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchContacts = async () => {
            try {
                const response = await api.contacts.list(true);
                setContacts(response.data || []);
            } catch (error) {
                console.error('Failed to fetch contacts:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchContacts();
    }, []);

    // Group contacts by type to avoid duplicates in main view if desired, 
    // or just list them. For the widget, a compact list is better.
    // Let's filter for primary contact methods.

    const getIcon = (type: string) => {
        switch (type) {
            case 'phone': return <PhoneIcon className="w-5 h-5" />;
            case 'email': return <EnvelopeIcon className="w-5 h-5" />;
            case 'wechat': return <ChatBubbleOvalLeftEllipsisIcon className="w-5 h-5" />;
            case 'qq': return <span className="font-bold text-sm">QQ</span>;
            case 'telegram': return <span className="font-bold text-sm">TG</span>;
            default: return <ChatBubbleLeftRightIcon className="w-5 h-5" />;
        }
    };

    if (loading || contacts.length === 0) return null;

    return (
        <motion.div
            ref={containerRef}
            drag
            dragMomentum={false}
            dragConstraints={{ left: -1000, right: 0, top: -1000, bottom: 0 }}
            className="fixed bottom-8 right-8 z-[100]"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
        >
            <div className="relative">
                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: -16, scale: 1 }}
                            exit={{ opacity: 0, y: 20, scale: 0.95 }}
                            className="absolute bottom-full right-0 mb-4 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden w-72 origin-bottom-right"
                        >
                            <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600">
                                <h3 className="text-white font-semibold">联系我们</h3>
                                <p className="text-blue-100 text-xs mt-1">工作时间: 9:00 - 21:00</p>
                            </div>

                            <div className="max-h-[400px] overflow-y-auto p-2 space-y-2">
                                {contacts.map((contact) => (
                                    <div key={contact.id} className="p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group">
                                        <div className="flex items-start gap-3">
                                            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                                                {getIcon(contact.type)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-medium text-gray-800 mb-0.5">{contact.label}</div>

                                                {contact.type === 'wechat_qr' && contact.qr_code_url ? (
                                                    <div className="mt-2 text-center bg-white p-2 rounded border border-gray-200">
                                                        <img src={contact.qr_code_url} alt={contact.label} className="w-24 h-24 mx-auto" />
                                                        <p className="text-xs text-gray-400 mt-1">扫码添加</p>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2">
                                                        {contact.link_url && contact.is_clickable ? (
                                                            <a href={contact.link_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline truncate">
                                                                {contact.value}
                                                            </a>
                                                        ) : (
                                                            <CopyButton
                                                                value={contact.value}
                                                                className="text-xs text-gray-600 truncate hover:text-blue-600 cursor-pointer text-left"
                                                                label={contact.value}
                                                            />
                                                        )}

                                                        {/* Always show copy icon for clarity */}
                                                        <CopyButton value={contact.value} className="text-gray-400 hover:text-blue-600 shrink-0" />
                                                    </div>
                                                )}

                                                {contact.description && (
                                                    <p className="text-xs text-gray-400 mt-1">{contact.description}</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setIsOpen(!isOpen)}
                    className="w-14 h-14 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-lg hover:shadow-blue-500/30 transition-shadow cursor-pointer"
                >
                    <AnimatePresence mode="wait">
                        {isOpen ? (
                            <motion.div
                                key="close"
                                initial={{ rotate: -90, opacity: 0 }}
                                animate={{ rotate: 0, opacity: 1 }}
                                exit={{ rotate: 90, opacity: 0 }}
                            >
                                <XMarkIcon className="w-7 h-7" />
                            </motion.div>
                        ) : (
                            <motion.div
                                key="chat"
                                initial={{ rotate: 90, opacity: 0 }}
                                animate={{ rotate: 0, opacity: 1 }}
                                exit={{ rotate: -90, opacity: 0 }}
                            >
                                <ChatBubbleLeftRightIcon className="w-7 h-7" />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.button>
            </div>
        </motion.div>
    );
}
