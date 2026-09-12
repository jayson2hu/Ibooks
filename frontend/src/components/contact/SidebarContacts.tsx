'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Contact } from '@/types';
import CopyButton from '@/components/common/CopyButton';

export default function SidebarContacts() {
    const [contacts, setContacts] = useState<Contact[]>([]);
    useEffect(() => {
        api.contacts.list(true)
            .then((response) => setContacts((response.data || []).filter((contact: Contact) => contact.show_in_sidebar)))
            .catch((error) => console.error('Failed to load sidebar contacts:', error));
    }, []);

    if (!contacts.length) return null;
    return <section className="mt-6 border-t border-gray-200 pt-6" aria-label="联系方式">
        <h2 className="text-lg font-semibold mb-3">需要帮助？</h2>
        <div className="space-y-3">{contacts.map((contact) => <div key={contact.id} className="rounded-lg bg-gray-50 p-3">
            <div className="text-sm font-medium text-gray-800">{contact.label}</div>
            <div className="mt-1 flex items-center gap-2 min-w-0">
                {contact.link_url && contact.is_clickable ? <a href={contact.link_url} target="_blank" rel="noopener noreferrer" className="truncate text-sm text-primary hover:underline">{contact.value}</a> : <span className="truncate text-sm text-gray-600">{contact.value}</span>}
                {contact.is_copyable && <CopyButton value={contact.value} className="shrink-0 text-gray-400 hover:text-primary" />}
            </div>
            {contact.description && <p className="mt-1 text-xs text-tertiary">{contact.description}</p>}
        </div>)}</div>
    </section>;
}
