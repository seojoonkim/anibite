import { expect, it } from 'vitest';
import Home from '../src/pages/Home';
import Browse from '../src/pages/Browse';
import Profile from '../src/pages/Profile';
import MyAniPass from '../src/pages/MyAniPass';

it('legacy Home imports use the canonical discovery screen', () => {
  expect(Home).toBe(Browse);
});
it('legacy Profile imports use the canonical profile screen', () => {
  expect(Profile).toBe(MyAniPass);
});
