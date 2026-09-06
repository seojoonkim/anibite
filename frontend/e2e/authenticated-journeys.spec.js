import { test, expect } from '@playwright/test';

// TEST ONLY: synthetic identities, credentials and catalogue. No real backend,
// OAuth, production data or production traffic is used by these browser tests.
const TOKEN = 'synthetic-local-e2e-token-not-a-real-jwt';
const credentials = { username: 'fixtureuser', password: 'TestOnlyPassword42!' };
const user = {
  id: 900001, username: credentials.username, email: 'fixture@example.test',
  display_name: '합성 테스트 사용자', avatar_url: null, bio: null,
  preferred_language: 'ko', oauth_provider: 'local',
  created_at: '2025-01-01T00:00:00', otaku_score: 0,
};
const anime = {
  id: 900001, title_romaji: 'Synthetic Auth Fixture', title_korean: '인증 테스트 전용 작품',
  title_english: 'Synthetic Auth Fixture', title_native: 'Synthetic Auth Fixture',
  title_korean_official: 1, format: 'TV', type: 'ANIME', status: 'FINISHED',
  season: 'SPRING', season_year: 2025, episodes: 12, duration: 24,
  genres: [], description: '실제 작품이 아닌 로컬 테스트 데이터입니다.',
  cover_image_url: null, banner_image_url: null, average_score: 0, popularity: 0,
  site_rating_count: 0, site_average_rating: null, site_rating_distribution: [],
  tags: [], studios: [], characters: [], staff: [], recommendations: [], external_links: [],
};

async function fixtures(page, { rejectSession = false } = {}) {
  const state = { rating: null, writes: [], requests: [], unexpected: [], errors: [], failNextSave: false, holdSave: null };
  page.on('pageerror', error => state.errors.push(error.message));
  await page.addInitScript(() => localStorage.setItem('language', 'ko'));
  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    // Fail closed: only this page's Vite origin may pass through. Every API
    // response is fulfilled here, and all remote resources are aborted.
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
    const path = url.pathname.replace(/\/$/, '');
    const method = request.method();
    if (!path.startsWith('/api/')) {
      if (url.origin === new URL(page.url()).origin) return route.continue();
      if (request.isNavigationRequest() && page.url() === 'about:blank') return route.continue();
      return route.abort();
    }
    const record = { method, path, authorization: request.headers().authorization };
    state.requests.push(record);
    const json = (body, status = 200) => route.fulfill({ status, json: body });
    if (method === 'POST' && path === '/api/auth/login') {
      record.body = request.postDataJSON();
      if (JSON.stringify(record.body) !== JSON.stringify(credentials)) return json({ detail: 'Invalid test credentials' }, 401);
      return json({ access_token: TOKEN, token_type: 'bearer', user });
    }
    const privatePath = path === '/api/auth/me' || path.startsWith('/api/ratings') || path.endsWith('/my-review');
    if (privatePath && (record.authorization !== `Bearer ${TOKEN}` || rejectSession)) return json({ detail: 'Not authenticated (test fixture)' }, 401);
    if (method === 'GET' && path === '/api/auth/me') return json(user);
    if (method === 'GET' && path === '/api/anime') return json({ items: [anime], total: 1, page: 1, page_size: 50, has_more: false });
    if (method === 'GET' && path === `/api/anime/${anime.id}`) return json(anime);
    if (method === 'GET' && path === '/api/activities') return json({ items: [], total: 0, has_more: false });
    if (method === 'GET' && path === `/api/reviews/anime/${anime.id}/my-review`) return json(null);
    if (method === 'GET' && path === `/api/reviews/anime/${anime.id}`) return json({ items: [], total: 0, page: 1, page_size: 10 });
    if (method === 'GET' && path === `/api/ratings/anime/${anime.id}`) return json(state.rating);
    if (method === 'POST' && path === '/api/ratings') {
      const body = request.postDataJSON();
      state.writes.push({ method, body, authorization: record.authorization });
      if (state.holdSave) await state.holdSave;
      if (state.failNextSave) { state.failNextSave = false; return json({ detail: 'Synthetic save failure' }, 503); }
      if (Number(body.anime_id) !== anime.id || body.status !== 'RATED' || body.rating < 0.5 || body.rating > 5 || body.rating * 2 % 1) return json({ detail: 'Invalid rating contract' }, 422);
      state.rating = { id: 900002, user_id: user.id, anime_id: anime.id, rating: body.rating, status: body.status, created_at: '2025-01-01T00:00:00', updated_at: '2025-01-01T00:00:00' };
      return json(state.rating, 201);
    }
    if (method === 'DELETE' && path === `/api/ratings/anime/${anime.id}`) {
      state.writes.push({ method, authorization: record.authorization });
      state.rating = null;
      return route.fulfill({ status: 204 });
    }
    // The real FastAPI routes require integer activity_id values. Do not
    // invent successful responses for the UI's temporary my-activity-* IDs.
    if (method === 'GET' && (path === `/api/bookmarks/check/my-activity-${anime.id}` || path === `/api/activities/my-activity-${anime.id}/comments`)) {
      state.unexpected.push(`Invalid integer activity_id: ${method} ${path}`);
      return json({ detail: [{ type: 'int_parsing', loc: ['path', 'activity_id'], msg: 'Input should be a valid integer, unable to parse string as an integer', input: `my-activity-${anime.id}` }] }, 422);
    }
    state.unexpected.push(`${method} ${path}`);
    return json({ detail: 'Unimplemented test fixture' }, 418);
  });
  return state;
}

async function login(page) {
  await page.getByLabel('아이디 또는 이메일', { exact: true }).fill(credentials.username);
  await page.getByLabel('비밀번호', { exact: true }).fill(credentials.password);
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('.account-menu summary')).toHaveText(user.display_name);
}

function assertClean(state) {
  expect(state.unexpected, 'Every API request must have an explicit synthetic fixture').toEqual([]);
  expect(state.errors, 'No uncaught browser errors').toEqual([]);
}

async function loginToRating(page) {
  await page.goto(`/login?returnTo=${encodeURIComponent(`/anime/${anime.id}`)}`);
  await login(page);
  await expect(page.getByRole('slider', { name: '내 평점', exact: true }).first()).toHaveValue('0');
}

test('login restores a guarded path including its query and fragment, then validates session on reload', async ({ page }) => {
  const state = await fixtures(page);
  const target = '/settings?source=synthetic-auth#profile';
  await page.goto(target);
  await expect(page).toHaveURL(/\/login$/);
  await login(page);
  await expect(page).toHaveURL(url => url.pathname + url.search + url.hash === target);
  expect(state.requests.find(r => r.path === '/api/auth/login').body).toEqual(credentials);
  expect(await page.evaluate(() => localStorage.getItem('token'))).toBe(TOKEN);
  await page.reload();
  await expect(page.locator('.account-menu summary')).toHaveText(user.display_name);
  await expect(page).toHaveURL(url => url.pathname + url.search + url.hash === target);
  expect(state.requests.some(r => r.path === '/api/auth/me' && r.authorization === `Bearer ${TOKEN}`)).toBe(true);
  assertClean(state);
});

test('login refuses an external returnTo and stays in the local catalogue', async ({ page }) => {
  const state = await fixtures(page);
  await page.goto('/login?returnTo=%2F%2Fexample.invalid%2Fsynthetic-only');
  await login(page);
  await expect(page).toHaveURL(/\/browse$/);
  await expect(page.getByText(anime.title_korean, { exact: true })).toBeVisible();
  assertClean(state);
});

test('rating half-step buttons, keyboard bounds and clear persist through API readback', async ({ page }) => {
  const state = await fixtures(page);
  await loginToRating(page);
  const editor = page.locator('.rating-editor');
  const slider = editor.getByRole('slider');
  await expect(editor.getByRole('button', { name: '0.5점 내리기' })).toBeDisabled();
  await editor.getByRole('button', { name: '0.5점 올리기' }).click();
  await expect(editor).toContainText('저장됨');
  await expect(slider).toHaveValue('0.5');
  await slider.press('End');
  await expect(slider).toHaveValue('5');
  await expect(editor).toHaveAttribute('aria-busy', 'false');
  await expect(editor.getByRole('button', { name: '0.5점 올리기' })).toBeDisabled();
  await editor.getByRole('button', { name: '0.5점 내리기' }).click();
  await expect(editor).toHaveAttribute('aria-busy', 'false');
  await expect(slider).toHaveValue('4.5');
  await page.reload();
  await expect(slider).toHaveValue('4.5');
  await editor.getByRole('button', { name: '평가 지우기' }).click();
  await expect(editor).toContainText('저장됨');
  await expect(slider).toHaveValue('0');
  await expect(editor.getByRole('button', { name: '평가 지우기' })).toBeDisabled();
  await page.reload();
  await expect(slider).toHaveValue('0');
  expect(state.writes.map(w => w.method === 'POST' ? w.body.rating : w.method)).toEqual([0.5, 5, 4.5, 'DELETE']);
  for (const write of state.writes) expect(write.authorization).toBe(`Bearer ${TOKEN}`);
  for (const write of state.writes.filter(w => w.method === 'POST')) expect(write.body).toEqual({ anime_id: String(anime.id), rating: write.body.rating, status: 'RATED' });
  expect(state.rating).toBeNull();
  assertClean(state);
});

test('a failed rating save keeps the draft, reports failure and retries only on request', async ({ page }) => {
  const state = await fixtures(page);
  await loginToRating(page);
  const editor = page.locator('.rating-editor');
  let release;
  state.holdSave = new Promise(resolve => { release = resolve; });
  state.failNextSave = true;
  await editor.getByRole('button', { name: '0.5점 올리기' }).click();
  try {
    await expect(editor).toHaveAttribute('aria-busy', 'true');
    await expect(editor.getByRole('slider')).toBeDisabled();
    await expect(editor.getByRole('button', { name: '0.5점 올리기' })).toBeDisabled();
  } finally { release(); state.holdSave = null; }
  await expect(editor.getByRole('alert')).toContainText('저장하지 못했습니다');
  await expect(editor.getByRole('slider')).toHaveValue('0.5');
  await expect(editor).not.toContainText('저장됨');
  expect(state.rating).toBeNull();
  expect(state.writes).toHaveLength(1);
  await editor.getByRole('button', { name: '다시 저장' }).click();
  await expect(editor.getByRole('alert')).toHaveCount(0);
  await expect(editor).toContainText('저장됨');
  expect(state.writes).toHaveLength(2);
  expect(state.writes[1]).toEqual(state.writes[0]);
  await page.reload();
  await expect(editor.getByRole('slider')).toHaveValue('0.5');
  assertClean(state);
});

test('logout clears the session and guards private routes after history navigation and reload', async ({ page }) => {
  const state = await fixtures(page);
  await page.goto('/settings');
  await login(page);
  await expect(page).toHaveURL(/\/settings$/);
  await page.locator('.account-menu summary').click();
  await page.getByRole('button', { name: '로그아웃', exact: true }).click();
  await expect(page).toHaveURL(/\/browse$/);
  expect(await page.evaluate(() => [localStorage.getItem('token'), localStorage.getItem('user')])).toEqual([null, null]);
  await expect(page.locator('.account-menu')).toHaveCount(0);
  await page.goBack();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto('/settings?source=after-logout#profile');
  await expect(page).toHaveURL(/\/login$/);
  await page.reload();
  await expect(page.getByLabel('비밀번호', { exact: true })).toBeVisible();
  await expect(page.locator('.account-menu')).toHaveCount(0);
  assertClean(state);
});

test('a rejected stored session cannot unlock a guarded page using cached user claims', async ({ page }) => {
  const state = await fixtures(page, { rejectSession: true });
  await page.addInitScript(({ token, cachedUser }) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(cachedUser));
  }, { token: TOKEN, cachedUser: user });
  await page.goto('/settings');
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByLabel('비밀번호', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => [localStorage.getItem('token'), localStorage.getItem('user')])).toEqual([null, null]);
  expect(state.requests.some(r => r.path === '/api/auth/me')).toBe(true);
  await expect(page.locator('.account-menu')).toHaveCount(0);
  assertClean(state);
});
