export type HomepageResourceFilter = 'all' | 'new' | 'course' | 'ebook' | 'free';

interface FilterableResource {
    resource_type?: string | null;
    is_free: boolean;
    price: number;
    created_at?: string | null;
}

function normalizedResourceType(resourceType?: string | null): string {
    return resourceType?.trim().toLowerCase() || '';
}

function isCourse(resourceType?: string | null): boolean {
    const normalized = normalizedResourceType(resourceType);
    return normalized === 'course'
        || normalized === 'video'
        || normalized.includes('课程');
}

function isEbook(resourceType?: string | null): boolean {
    const normalized = normalizedResourceType(resourceType);
    return normalized === 'ebook'
        || normalized === 'book'
        || normalized.includes('电子书');
}

function createdAtTimestamp(resource: FilterableResource): number {
    const timestamp = Date.parse(resource.created_at || '');
    return Number.isNaN(timestamp) ? 0 : timestamp;
}

export function filterHomepageResources<T extends FilterableResource>(
    resources: T[],
    filter: HomepageResourceFilter,
): T[] {
    if (filter === 'new') {
        return [...resources].sort(
            (left, right) => createdAtTimestamp(right) - createdAtTimestamp(left),
        );
    }

    if (filter === 'free') {
        return resources.filter((resource) => resource.is_free || resource.price === 0);
    }

    if (filter === 'course') {
        return resources.filter((resource) => isCourse(resource.resource_type));
    }

    if (filter === 'ebook') {
        return resources.filter((resource) => isEbook(resource.resource_type));
    }

    return resources;
}
