import { render, screen } from '@testing-library/react';
import ResourceCard from '@/components/resource/ResourceCard';
import type { Resource } from '@/types';

const resource: Resource = {
    id: 1,
    title: 'TypeScript 实战',
    slug: 'typescript-in-action',
    tags: ['TypeScript'],
    price: 19.9,
    coin_price: 30,
    is_free: false,
    is_published: true,
    is_featured: false,
    view_count: 12,
    download_count: 3,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

describe('ResourceCard', () => {
    it('renders the title, coin price and resource link', () => {
        render(<ResourceCard resource={resource} />);

        expect(screen.getByText('TypeScript 实战')).toBeInTheDocument();
        expect(screen.getByText('30 书币')).toBeInTheDocument();
        expect(screen.getByRole('link')).toHaveAttribute('href', '/resources/typescript-in-action');
    });

    it('renders the free badge and price for free resources', () => {
        render(<ResourceCard resource={{ ...resource, is_free: true, coin_price: 0 }} />);

        expect(screen.getAllByText('免费')).toHaveLength(2);
    });
});
