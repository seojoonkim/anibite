import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import HoverStarInput from '../src/components/common/HoverStarInput';

afterEach(cleanup);

const rect = { left: 0, width: 40, top: 0, height: 40, right: 40, bottom: 40 };

it('rates in one click with half-star precision like character cards', () => {
  const change = vi.fn();
  render(<HoverStarInput value={0} onChange={change} />);
  const star4 = screen.getByRole('button', { name: '4점' });
  star4.getBoundingClientRect = () => rect;
  fireEvent.click(star4, { clientX: 30 });
  expect(change).toHaveBeenLastCalledWith(4);
  fireEvent.click(star4, { clientX: 5 });
  expect(change).toHaveBeenLastCalledWith(3.5);
});

it('previews the hovered value before click', () => {
  render(<HoverStarInput value={1} onChange={() => {}} />);
  const star3 = screen.getByRole('button', { name: '3점' });
  star3.getBoundingClientRect = () => rect;
  fireEvent.mouseMove(star3, { clientX: 35 });
  const filled = screen.getAllByRole('button').map(b => b.querySelectorAll('span span').length > 0);
  expect(filled).toEqual([true, true, true, false, false]);
});
