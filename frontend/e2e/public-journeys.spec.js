import { test, expect } from '@playwright/test';

// Synthetic catalogue fixtures for isolated browser regressions. These are NOT
// production data or backend performance measurements. All non-local traffic is blocked.
const catalogue = Array.from({ length: 48 }, (_, index) => ({
  id: index + 1,
  title_romaji: `Fixture Anime ${index + 1}`,
  title_korean: `테스트 작품 ${index + 1}`,
  title_native: `テスト作品 ${index + 1}`,
  title_english: `Fixture Anime ${index + 1}`,
  title_korean_official: 1,
  format: 'TV', type: 'ANIME', status: 'FINISHED', season: 'SPRING',
  season_year: 2025, episodes: 12, duration: 24,
  genres: ['Adventure'], description: '로컬 회귀 테스트 전용 작품입니다. 실제 작품 정보가 아닙니다.',
  cover_image_url: '/placeholder-anime.svg', cover_image_color: '#47B5FF',
  banner_image_url: null, average_score: 80, popularity: 100,
  favourites: 0, source: 'ORIGINAL', is_adult: false,
  site_rating_count: 2, site_average_rating: 4,
  tags: [], studios: [], characters: [], staff: [], recommendations: [],
  external_links: [], trailer_url: null, site_url: null,
  start_date: '2025-04-01', end_date: '2025-06-30', site_rating_distribution: [],
}));

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('language', 'ko'));
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
    if (url.port !== '8000') return route.continue();
    const path = url.pathname.replace(/\/$/, '');
    const json = (body, status = 200) => route.fulfill({ status, json: body });
    if (path === '/api/anime') {
      const current = Number(url.searchParams.get('page') || 1);
      const size = Number(url.searchParams.get('page_size') || 50);
      const items = catalogue.slice((current - 1) * size, current * size);
      return json({ items, total: catalogue.length, page: current, page_size: size, has_more: current * size < catalogue.length });
    }
    if (path === '/api/search') {
      const q = url.searchParams.get('q') || '';
      return json({ anime: catalogue.filter(item => item.title_korean.includes(q)), characters: [] });
    }
    if (/^\/api\/anime\/\d+$/.test(path)) return json(catalogue[Number(path.split('/').at(-1)) - 1]);
    if (path === '/api/characters/1') return json({
      id: 1, name_full: 'Fixture Character', name_korean: '테스트 캐릭터',
      name_native: 'テスト人物', description: 'Synthetic character fixture only.',
      image_url: '/placeholder-anime.svg', anime: [],
      site_rating_count: 0, site_average_rating: null, my_rating: null,
      site_rating_distribution: [],
    });
    if (path.startsWith('/api/character-reviews')) return json({ items: [], total: 0 });
    if (path === '/api/activities') return json({ items: [], total: 0, has_more: false });
    if (path.startsWith('/api/series')) return json([]);
    if (path.startsWith('/api/reviews')) return json({ items: [], total: 0 });
    if (path === '/placeholder-anime.svg') return route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="320"><rect width="240" height="320" fill="#1e2736"/><text x="20" y="160" fill="#47B5FF">TEST FIXTURE</text></svg>' });
    return json({ detail: 'Not authenticated in isolated public-page test' }, 401);
  });
});

test('public catalogue is useful before login and has no horizontal overflow', async ({ page }, info) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/browse');
  await expect(page).toHaveURL(/\/browse/);
  await expect(page.getByText('테스트 작품 1', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({ path: `test-results/catalogue-${info.project.name}.png`, fullPage: false });
});

test('a shared anime detail is readable without a session', async ({ page }, info) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/anime/1');
  await expect(page).toHaveURL(/\/anime\/1$/);
  await expect(page.getByRole('heading', { name: '테스트 작품 1', exact: true }).first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.screenshot({ path: `test-results/detail-${info.project.name}.png`, fullPage: false });
});

test('a shared character detail is readable without a session', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/character/1');
  await expect(page.getByRole('heading', { name: '테스트 캐릭터', exact: true }).first()).toBeVisible();
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('private library still requires authentication', async ({ page }) => {
  await page.goto('/my-anipass');
  await expect(page).toHaveURL(/\/login/);
  await expect(page.locator('input[type="password"]')).toBeVisible();
});

test('login fields have associated names and an enabled primary action', async ({ page }, info) => {
  await page.goto('/login');
  await expect(page.locator('input[type="password"]')).toBeVisible();
  const fields = await page.locator('input').evaluateAll(elements => elements.filter(el => ['text', 'email', 'password'].includes(el.type)).map(el => ({ labels: el.labels.length, autocomplete: el.autocomplete })));
  expect(fields.length).toBeGreaterThanOrEqual(2);
  for (const field of fields) {
    expect(field.labels).toBeGreaterThan(0);
    expect(field.autocomplete).not.toBe('');
  }
  expect(await page.locator('button[type="submit"]').evaluate(el => getComputedStyle(el).backgroundColor)).not.toBe('rgb(30, 39, 54)');
  await page.screenshot({ path: `test-results/login-${info.project.name}.png`, fullPage: false });
});

test('unknown route offers a visible recovery screen', async ({ page }) => {
  await page.goto('/this-route-does-not-exist');
  await expect(page.getByText(/404|찾을 수 없|찾을 수 없는|찾지 못|not found/i).first()).toBeVisible();
  await expect(page.locator('a[href="/browse"], a[href="/"]').first()).toBeVisible();
});
