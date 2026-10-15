import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const checkBookmark = vi.fn(async () => false);
const getComments = vi.fn(async () => []);
vi.mock('../src/services/bookmarkService', () => ({
  bookmarkService: { checkBookmark, addBookmark: vi.fn(), removeBookmark: vi.fn() },
  default: { checkBookmark },
}));
vi.mock('../src/services/activityService', async (orig) => {
  const real = await orig();
  const svc = { ...(real.activityService || real.default), getComments };
  return { ...real, activityService: svc, default: svc };
});
vi.mock('../src/context/AuthContext', () => ({ useAuth: () => ({ user: { id: 2, username: 'demo2' }, isAuthenticated: true }) }));
vi.mock('../src/context/LogoWiggleContext', () => ({ useLogoWiggle: () => ({ triggerWiggle: () => {} }) }));
vi.mock('../src/context/LanguageContext', () => ({ useLanguage: () => ({ language: 'ko', t: k => k }) }));

const { default: ActivityCard } = await import('../src/components/activity/ActivityCard');

const base = { id: 7, activity_type: 'anime_rating', user_id: 1, username: 'demo1', display_name: 'Demo 1', item_id: 1, item_title: '합성 작품', rating: 4, likes_count: 0, user_liked: false, activity_time: '2026-10-15T00:00:00Z', created_at: '2026-10-15T00:00:00Z' };

describe('menu navigation speed: feed cards do not fan out requests', () => {
  beforeEach(() => { checkBookmark.mockClear(); getComments.mockClear(); });

  it('uses user_bookmarked from the feed payload instead of calling /bookmarks/check', async () => {
    render(<MemoryRouter><ActivityCard activity={{ ...base, comments_count: 0, user_bookmarked: true }} /></MemoryRouter>);
    await screen.findByText('합성 작품');
    await new Promise(r => setTimeout(r, 30));
    expect(checkBookmark).not.toHaveBeenCalled();
    expect(getComments).not.toHaveBeenCalled();
  });

  it('still loads comments when the card has comments to show', async () => {
    render(<MemoryRouter><ActivityCard activity={{ ...base, comments_count: 2, user_bookmarked: false }} /></MemoryRouter>);
    await waitFor(() => expect(getComments).toHaveBeenCalledWith(7));
    expect(checkBookmark).not.toHaveBeenCalled();
  });

  it('falls back to /bookmarks/check for payloads without the flag', async () => {
    render(<MemoryRouter><ActivityCard activity={{ ...base, comments_count: 0 }} /></MemoryRouter>);
    await waitFor(() => expect(checkBookmark).toHaveBeenCalledWith(7));
  });
});
