import { StrictMode } from 'react';
import { render, waitFor } from '@testing-library/react';
import ResourceViewTracker from '@/components/resource/ResourceViewTracker';
import { api } from '@/lib/api';

jest.mock('@/lib/api', () => ({
    api: {
        resources: { recordView: jest.fn() },
    },
}));

describe('ResourceViewTracker', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.mocked(api.resources.recordView).mockResolvedValue({} as never);
    });

    it('records one mounted page view even when React replays effects', async () => {
        render(
            <StrictMode>
                <ResourceViewTracker slug="viewed-book" />
            </StrictMode>,
        );

        await waitFor(() => expect(api.resources.recordView).toHaveBeenCalledTimes(1));
        expect(api.resources.recordView).toHaveBeenCalledWith('viewed-book');
    });
});
