import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ResourceCover from '@/components/common/ResourceCover';

describe('ResourceCover', () => {
    it('renders a supported image URL', () => {
        render(<ResourceCover src="/images/python-guide.jpg" alt="Python 指南" />);

        expect(screen.getByRole('img', { name: 'Python 指南' })).toHaveAttribute(
            'src',
            '/images/python-guide.jpg',
        );
    });

    it('shows an accessible fallback after an image fails', () => {
        render(<ResourceCover src="https://images.example.com/missing.jpg" alt="缺失资源" />);

        fireEvent.error(screen.getByRole('img', { name: '缺失资源' }));

        expect(screen.getByRole('img', { name: '缺失资源（暂无封面）' })).toBeInTheDocument();
    });

    it('rejects unsupported image protocols and recovers when the source changes', async () => {
        const { rerender } = render(<ResourceCover src="javascript:alert(1)" alt="安全资源" />);

        expect(screen.getByRole('img', { name: '安全资源（暂无封面）' })).toBeInTheDocument();

        rerender(<ResourceCover src="/images/react-course.jpg" alt="安全资源" />);

        await waitFor(() => {
            expect(screen.getByRole('img', { name: '安全资源' })).toHaveAttribute(
                'src',
                '/images/react-course.jpg',
            );
        });
    });
});
