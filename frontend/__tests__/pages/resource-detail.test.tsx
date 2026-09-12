import { notFound } from 'next/navigation';

import ResourceDetailPage from '@/app/resources/[slug]/page';
import { api, getApiErrorStatus } from '@/lib/api';

jest.mock('next/navigation', () => ({
    notFound: jest.fn(() => {
        throw new Error('NEXT_NOT_FOUND');
    }),
}));

jest.mock('@/lib/api', () => ({
    getApiErrorStatus: jest.fn(),
    api: {
        resources: { get: jest.fn() },
    },
}));

jest.mock('@/components/resource/ResourceAccessCard', () => () => null);
jest.mock('@/components/resource/ResourceViewTracker', () => () => null);
jest.mock('@/components/resource/ShareButton', () => () => null);
jest.mock('@/components/contact/SidebarContacts', () => () => null);
jest.mock('@/components/common/ResourceCover', () => () => null);

describe('ResourceDetailPage failure routing', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('uses the not-found route for a genuine 404', async () => {
        jest.mocked(api.resources.get).mockRejectedValue(new Error('missing resource'));
        jest.mocked(getApiErrorStatus).mockReturnValue(404);

        await expect(ResourceDetailPage({
            params: Promise.resolve({ slug: 'missing' }),
        })).rejects.toThrow('NEXT_NOT_FOUND');

        expect(notFound).toHaveBeenCalledTimes(1);
    });

    it('rethrows server and network failures for the route error boundary', async () => {
        const failure = new Error('upstream unavailable');
        jest.mocked(api.resources.get).mockRejectedValue(failure);
        jest.mocked(getApiErrorStatus).mockReturnValue(500);

        await expect(ResourceDetailPage({
            params: Promise.resolve({ slug: 'python-guide' }),
        })).rejects.toBe(failure);

        expect(notFound).not.toHaveBeenCalled();
    });
});
