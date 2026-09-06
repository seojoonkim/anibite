import { useState } from 'react';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import StarRating from '../src/components/common/StarRating';
afterEach(cleanup);
it('offers explicit half-step keyboard/touch adjustments and clear', () => {
 function Rating() { const [value, setValue] = useState(2); return <StarRating rating={value} onRatingChange={setValue}/>; }
 render(<Rating/>);
 fireEvent.click(screen.getByRole('button', {name: '0.5점 올리기'}));
 expect(screen.getByRole('slider').getAttribute('aria-valuenow')).toBe('2.5');
 fireEvent.keyDown(screen.getByRole('slider'), {key: 'ArrowRight'});
 expect(screen.getByRole('slider').getAttribute('aria-valuenow')).toBe('3');
 fireEvent.click(screen.getByRole('button', {name: '평가 지우기'}));
 expect(screen.getByRole('status').textContent).toContain('평가하지 않음');
});
it('renders read-only ratings without focusable buttons', () => {
 render(<StarRating rating={3.5} readonly/>);
 expect(screen.queryAllByRole('button')).toHaveLength(0);
 expect(screen.getByRole('img', {name: '5점 만점에 3.5점'})).toBeTruthy();
});
it('never clears by choosing the same value', () => {
 const change = vi.fn(); render(<StarRating rating={3} onRatingChange={change}/>);
 fireEvent.keyDown(screen.getByRole('slider'), {key: 'End'});
 expect(change).toHaveBeenCalledWith(5);
});
