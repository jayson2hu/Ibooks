import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ShareButton from '@/components/resource/ShareButton';

describe('ShareButton', () => {
    afterEach(() => {
        Object.defineProperty(navigator, 'share', {
            configurable: true,
            value: undefined,
        });
        Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: undefined,
        });
    });

    it('uses the system share sheet when available', async () => {
        const share = jest.fn().mockResolvedValue(undefined);
        Object.defineProperty(navigator, 'share', {
            configurable: true,
            value: share,
        });

        render(<ShareButton title="Python 指南" />);
        fireEvent.click(screen.getByRole('button', { name: '分享' }));

        await waitFor(() => expect(share).toHaveBeenCalledWith({
            title: 'Python 指南',
            url: window.location.href,
        }));
        expect(await screen.findByText('分享面板已打开')).toBeInTheDocument();
    });

    it('copies the current URL when the share sheet is unavailable', async () => {
        const writeText = jest.fn().mockResolvedValue(undefined);
        Object.defineProperty(navigator, 'share', {
            configurable: true,
            value: undefined,
        });
        Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: { writeText },
        });

        render(<ShareButton title="Python 指南" />);
        fireEvent.click(screen.getByRole('button', { name: '分享' }));

        await waitFor(() => expect(writeText).toHaveBeenCalledWith(window.location.href));
        expect(await screen.findByText('链接已复制')).toBeInTheDocument();
    });
});
