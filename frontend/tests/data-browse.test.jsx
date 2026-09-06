import { afterEach, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { AuthProvider } from '../src/context/AuthProvider';
import { LanguageProvider } from '../src/context/LanguageProvider';
import Browse from '../src/pages/Browse';
import api from '../src/services/api';
import { browseCache } from '../src/services/queryCache';
afterEach(() => { vi.restoreAllMocks(); browseCache.clear(); });
it('restores appended results and scroll after detail back navigation', async () => {
  const get = vi.spyOn(api, 'get').mockRejectedValue(new Error('Unexpected fixture request')).mockResolvedValueOnce({ data: { items: [{ id: 1, title_korean: '첫 작품' }], has_more: true } }).mockResolvedValueOnce({ data: { items: [{ id: 2, title_korean: '둘째 작품' }], has_more: false } });
  const scroll = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  const view = mount();
  await screen.findByText('첫 작품');
  fireEvent.click(screen.getByRole('button', { name: '더 보기' }));
  await screen.findByText('둘째 작품');
  Object.defineProperty(window, 'scrollY', { configurable: true, value: 480 });
  fireEvent.scroll(window);
  view.unmount();
  mount();
  await screen.findByText('둘째 작품');
  expect(get).toHaveBeenCalledTimes(2);
  await waitFor(() => expect(scroll).toHaveBeenCalledWith(0, 480));
});
function Location() { const location = useLocation(); return <output data-testid="url">{location.search}</output>; }
function mount(url = '/browse') { vi.stubGlobal('IntersectionObserver', class { observe() {} disconnect() {} }); return render(<MemoryRouter initialEntries={[url]} future={{v7_startTransition:true,v7_relativeSplatPath:true}}><AuthProvider><LanguageProvider><Browse/><Location/></LanguageProvider></AuthProvider></MemoryRouter>); }
it('uses fixed page size, explicitly appends page 2 and retries it without duplicates', async () => {
  const get = vi.spyOn(api, 'get').mockRejectedValue(new Error('Unexpected fixture request')).mockResolvedValueOnce({ data: { items: [{ id: 1, title_korean: '첫 작품' }], has_more: true } }).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data: { items: [{ id: 1, title_korean: '첫 작품' }, { id: 2, title_korean: '둘째 작품' }], has_more: false } });
  mount();
  await screen.findByText('첫 작품');
  fireEvent.click(screen.getByRole('button', { name: '더 보기' }));
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button', { name: '다시 시도' }));
  await screen.findByText('둘째 작품');
  expect(screen.getAllByText('첫 작품')).toHaveLength(1);
  expect(get.mock.calls.map(call => call[1].params.page)).toEqual([1,2,2]);
  expect(get.mock.calls.map(call => call[1].params.page_size)).toEqual([20,20,20]);
});
it('preserves URL controls, labels and latest search response with character tabs', async () => {
  let finishOld;
  const get = vi.spyOn(api, 'get').mockImplementation((url, config) => {
    if (config?.params?.q === 'old') return new Promise(r => { finishOld = r; });
    return Promise.resolve({ data: { anime: [{ id: 3, title_korean: '최신 작품' }], characters: [{ id: 7, name_korean: '주인공' }] } });
  });
  mount('/browse?q=old&sort=title_asc&tab=anime');
  await waitFor(() => expect(finishOld).toBeTypeOf('function'));
  fireEvent.change(screen.getByRole('searchbox', { name: '작품·캐릭터 검색' }), { target: { value: 'new' } });
  await screen.findByText('최신 작품');
  await act(async () => finishOld({ data: { anime: [{ id: 9, title_korean: '오래된 작품' }], characters: [] } }));
  expect(screen.queryByText('오래된 작품')).not.toBeInTheDocument();
  expect(screen.getByTestId('url')).toHaveTextContent('q=new');
  expect(screen.getByTestId('url')).toHaveTextContent('sort=title_asc');
  fireEvent.click(screen.getByRole('tab', { name: /캐릭터/ }));
  expect(screen.getByRole('link', { name: /주인공/ })).toHaveAttribute('href', '/character/7');
  expect(get.mock.calls[0][1].signal.aborted).toBe(true);
});
