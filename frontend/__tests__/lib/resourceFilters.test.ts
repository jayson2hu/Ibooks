import { filterHomepageResources } from '@/lib/resourceFilters';

const resources = [
    {
        id: 1,
        resource_type: 'ebook',
        is_free: false,
        price: 10,
        created_at: '2026-01-01T00:00:00Z',
    },
    {
        id: 2,
        resource_type: 'video',
        is_free: true,
        price: 20,
        created_at: '2026-03-01T00:00:00Z',
    },
    {
        id: 3,
        resource_type: '高薪课程',
        is_free: false,
        price: 0,
        created_at: '2026-02-01T00:00:00Z',
    },
    {
        id: 4,
        resource_type: '电子书',
        is_free: false,
        price: 15,
        created_at: null,
    },
];

describe('filterHomepageResources', () => {
    it('recognizes canonical and localized course/ebook resource types', () => {
        expect(filterHomepageResources(resources, 'course').map((item) => item.id)).toEqual([2, 3]);
        expect(filterHomepageResources(resources, 'ebook').map((item) => item.id)).toEqual([1, 4]);
    });

    it('treats both free flags and zero prices as free resources', () => {
        expect(filterHomepageResources(resources, 'free').map((item) => item.id)).toEqual([2, 3]);
    });

    it('sorts newest resources without mutating the source array', () => {
        expect(filterHomepageResources(resources, 'new').map((item) => item.id)).toEqual([2, 3, 1, 4]);
        expect(resources.map((item) => item.id)).toEqual([1, 2, 3, 4]);
    });
});
