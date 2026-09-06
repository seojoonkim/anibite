import { afterEach, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../src/context/AuthProvider';
import { LanguageProvider } from '../src/context/LanguageProvider';
import { LogoWiggleProvider } from '../src/context/LogoWiggleProvider';
import Feed from '../src/pages/Feed';
import api from '../src/services/api';
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
function mount(url) {
  vi.stubGlobal('IntersectionObserver', class { observe() {} disconnect() {} });
  return render(<MemoryRouter initialEntries={[url]}><AuthProvider><LanguageProvider><LogoWiggleProvider><Feed/></LogoWiggleProvider></LanguageProvider></AuthProvider></MemoryRouter>);
}
it('mobile filter control preserves unrelated URL parameters and fetches following', async () => {
  const get = vi.spyOn(api, 'get').mockResolvedValue({ data: { items: [], total: 0 } });
  mount('/feed?highlight=9');
  fireEvent.change(await screen.findByRole('combobox', { name: '피드 필터' }), { target: { value: 'following' } });
  await screen.findByText('아직 활동이 없습니다.');
  expect(get.mock.calls.some(call => call[0].includes('following_only=true'))).toBe(true);
});
it('saved feed failures expose retry rather than an empty success', async () => {
  localStorage.setItem('token', 'fixture-token');
  const bookmarks = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValue({ ok: true, json: async () => ({ items: [] }) });
  vi.stubGlobal('fetch', vi.fn(url => String(url).includes('/bookmarks') ? bookmarks() : Promise.resolve({ ok: true, json: async () => ({ id: 8, username: 'fixture' }) })));
  mount('/feed?filter=saved');
  await screen.findByRole('alert');
  expect(screen.queryByText('저장한 활동이 없습니다')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '다시 시도' }));
  await screen.findByText('저장한 활동이 없습니다');
});
it('failed posting keeps the draft and exposes an accessible notice', async () => {
  const user = { id: 8, username: 'fixture', otaku_score: 0 };
  localStorage.setItem('token', 'fixture-token'); localStorage.setItem('user', JSON.stringify(user));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => user }));
  vi.spyOn(api, 'get').mockResolvedValue({ data: { items: [], total: 0 } });
  vi.spyOn(api, 'post').mockRejectedValue(new Error('offline'));
  mount('/feed');
  const draft = await screen.findByRole('textbox', { name: '새 게시물' });
  fireEvent.change(draft, { target: { value: '지켜야 할 초안' } });
  fireEvent.click(screen.getByRole('button', { name: '게시' }));
  await screen.findByRole('alert');
  expect(draft).toHaveValue('지켜야 할 초안');
  expect(sessionStorage.getItem('feed_draft_8')).toBe('지켜야 할 초안');
});
