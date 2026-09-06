import { act, cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, Link } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import AnimeDetail from '../src/pages/AnimeDetail';
import { animeService } from '../src/services/animeService';

vi.mock('../src/context/AuthContext', () => ({ useAuth: () => ({ user: null }) }));
vi.mock('../src/context/LanguageContext', () => ({ useLanguage: () => ({ language: 'en', getAnimeTitle: anime => anime.title_romaji }) }));
vi.mock('../src/hooks/useActivity', () => ({ useActivities: () => ({ activities: [], refetch: vi.fn() }) }));
vi.mock('../src/hooks/usePrefetch', () => ({ getPrefetchedData: () => null }));
vi.mock('../src/components/anime/RatingWidget', () => ({ default: () => null }));
vi.mock('../src/components/activity/ActivityCard', () => ({ default: () => null }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it('does not let the previous detail request overwrite a newly selected title', async () => {
  let resolveFirst;
  vi.spyOn(animeService, 'getAnimeById').mockImplementation(id => id === '1'
    ? new Promise(resolve => { resolveFirst = resolve; })
    : Promise.resolve({ id: 2, title_romaji: 'Second title', genres: [], characters: [], studios: [] }));
  render(<MemoryRouter initialEntries={['/anime/1']}><Link to="/anime/2">Next title</Link><Routes><Route path="/anime/:id" element={<AnimeDetail />} /></Routes></MemoryRouter>);
  await act(async () => {});
  fireEvent.click(screen.getByText('Next title'));
  await screen.findAllByText('Second title');
  await act(async () => resolveFirst({ id: 1, title_romaji: 'First title', genres: [], characters: [], studios: [] }));
  expect(screen.queryAllByText('First title')).toHaveLength(0);
  expect(screen.getAllByText('Second title').length).toBeGreaterThan(0);
});
