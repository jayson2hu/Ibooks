import { fireEvent, render, screen } from '@testing-library/react';

import CategoryDetailError from '@/app/categories/[slug]/error';
import ResourceDetailError from '@/app/resources/[slug]/error';

describe('detail route error boundaries', () => {
    it.each([
        ['资源详情加载失败', ResourceDetailError],
        ['分类详情加载失败', CategoryDetailError],
    ])('renders %s with a working retry action', (heading, ErrorComponent) => {
        const reset = jest.fn();

        render(<ErrorComponent error={new Error('failed')} reset={reset} />);
        expect(screen.getByRole('alert')).toHaveTextContent(heading);

        fireEvent.click(screen.getByRole('button', { name: '重新加载' }));
        expect(reset).toHaveBeenCalledTimes(1);
    });
});
