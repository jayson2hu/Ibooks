import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import EnhancedSearchBar from '@/components/home/EnhancedSearchBar';

describe('EnhancedSearchBar', () => {
    it('submits a trimmed non-empty query with the selected scope', async () => {
        const onSubmit = jest.fn();
        render(<EnhancedSearchBar onSubmit={onSubmit} />);

        fireEvent.change(screen.getByPlaceholderText('搜索优质资源...'), { target: { value: ' React ' } });
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'course' } });
        fireEvent.submit(screen.getByRole('button', { name: '搜索' }).closest('form')!);

        await waitFor(() => expect(onSubmit).toHaveBeenCalledWith(' React ', 'course'));
    });

    it('does not submit an empty query', () => {
        const onSubmit = jest.fn();
        render(<EnhancedSearchBar onSubmit={onSubmit} />);

        fireEvent.submit(screen.getByRole('button', { name: '搜索' }).closest('form')!);
        expect(onSubmit).not.toHaveBeenCalled();
    });
});
