import type { AuditLogDetails } from '@/types';

export function formatAuditDetails(details: AuditLogDetails | undefined): string {
    if (details === null || details === undefined || details === '') {
        return '-';
    }

    if (typeof details === 'string') {
        return details;
    }

    try {
        return JSON.stringify(details);
    } catch {
        return '[详情无法显示]';
    }
}
