import { serializeJsonLd } from '@/lib/jsonLd';

describe('serializeJsonLd', () => {
    it('preserves JSON data while preventing script-element termination', () => {
        const payload = {
            name: '</script><script>alert("stored-xss")</script>',
            description: 'A & B > C\u2028next line\u2029last line',
        };

        const serialized = serializeJsonLd(payload);

        expect(serialized).not.toContain('<');
        expect(serialized).not.toContain('>');
        expect(serialized).not.toContain('&');
        expect(serialized).not.toContain('\u2028');
        expect(serialized).not.toContain('\u2029');
        expect(serialized).toContain('\\u003c/script\\u003e');
        expect(JSON.parse(serialized)).toEqual(payload);
    });
});
