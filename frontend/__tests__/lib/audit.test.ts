import { formatAuditDetails } from '@/lib/audit';

describe('formatAuditDetails', () => {
    it('serializes structured audit details for safe text rendering', () => {
        expect(formatAuditDetails({ method: 'POST', resource: { id: 42 } })).toBe(
            '{"method":"POST","resource":{"id":42}}',
        );
    });

    it('handles missing details without rendering an empty cell', () => {
        expect(formatAuditDetails(null)).toBe('-');
        expect(formatAuditDetails(undefined)).toBe('-');
    });
});
