import { useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { animeService } from '../services/animeService';
import api from '../services/api';
import { browseCache, syncCacheSession } from '../services/queryCache';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { usePrefetch } from '../hooks/usePrefetch';
import { usePagedResource } from '../hooks/usePagedResource';
import { IMAGE_BASE_URL } from '../config/api';
import { getCharacterImageUrl } from '../utils/imageHelpers';

const PAGE_SIZE = 20;
const searchSorts = ['popularity_desc', 'rating_desc', 'rating_asc', 'title_asc'];
const pack = (items, type) => items.map(item => ({ ...item, originalId: item.id, id: `${type}:${item.id}`, type }));
const imageUrl = url => !url ? '/placeholder-anime.svg' : url.startsWith('http') ? url : `${IMAGE_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`;

export default function Browse() {
  const { user } = useAuth();
  const { t, getAnimeTitle, language } = useLanguage();
  const text = (ko, en, ja) => language === 'ko' ? ko : language === 'ja' ? ja : en;
  const [params, setParams] = useSearchParams();
  const query = params.get('q') || '';
  const requestedSort = params.get('sort') || 'popularity_desc';
  const sort = searchSorts.includes(requestedSort) && (query.trim() || requestedSort !== 'rating_asc') ? requestedSort : 'popularity_desc';
  const tab = query.trim() && params.get('tab') === 'character' ? 'character' : 'anime';
  const year = params.get('year') || '';
  const genre = params.get('genre') || '';
  const { handleAnimeMouseEnter, handleCharacterMouseEnter, handleMouseLeave } = usePrefetch();
  const update = (name, value, replace = false) => {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value); else next.delete(name);
    setParams(next, { replace, preventScrollReset: true });
  };
  const loadPage = useCallback(async (page, signal) => {
    if (query.trim()) {
      await new Promise((resolve, reject) => {
        const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
        const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, 300);
        signal.addEventListener('abort', abort, { once: true });
        if (signal.aborted) abort();
      });
      const { data } = await api.get('/api/search', { params: { q: query.trim(), sort, limit: 30 }, signal });
      return { items: [...pack(data.anime || [], 'anime'), ...pack(data.characters || [], 'character')], hasMore: false };
    }
    const data = await animeService.getAnimeList({ page, page_size: PAGE_SIZE, sort, ...(year ? { year } : {}), ...(genre ? { genre } : {}) }, { signal });
    return { items: pack(data.items || [], 'anime'), total: data.total, hasMore: data.has_more ?? page * PAGE_SIZE < data.total };
  }, [query, sort, year, genre]);
  syncCacheSession();
  const cacheKey = JSON.stringify([query, sort, year, genre, user?.id || 'guest']);
  const results = usePagedResource(loadPage, false, { cache: browseCache, cacheKey });
  const items = results.items.filter(item => item.type === tab);

  return <main className="max-w-[1180px] mx-auto px-4 py-8">
    <h1 className="text-2xl font-bold mb-6">{text('발견', 'Discover', '見つける')}</h1>
    <div className="flex flex-wrap gap-3 mb-5">
      <label className="flex-1 min-w-0">{text('작품·캐릭터 검색', 'Search anime and characters', 'アニメ・キャラクター検索')}
        <input type="search" className="w-full min-h-11 px-3 rounded-lg border" value={query} onChange={event => update('q', event.target.value, true)} />
      </label>
      <label>{text('정렬', 'Sort', '並び順')}
        <select className="block min-h-11 rounded-lg border px-3" value={sort} onChange={event => update('sort', event.target.value)}>
          <option value="popularity_desc">{t('sortPopularity')}</option>
          <option value="rating_desc">{t('sortRatingDesc')}</option>
          {query.trim() && <option value="rating_asc">{t('sortRatingAsc')}</option>}
          <option value="title_asc">{t('sortTitle')}</option>
        </select>
      </label>
      <button className="min-h-11 px-3 self-end" onClick={() => setParams({}, { preventScrollReset: true })}>{text('검색·필터 초기화', 'Clear search and filters', '検索・絞り込みをリセット')}</button>
    </div>
    <div className="flex flex-wrap gap-3 mb-5">
      <label>{text('연도', 'Year', '年')}<input className="block border rounded-lg min-h-11 px-3 w-28" type="number" min="1960" max="2030" value={year} disabled={Boolean(query.trim())} onChange={e => update('year', e.target.value, true)} /></label>
      <label>{text('장르', 'Genre', 'ジャンル')}<input className="block border rounded-lg min-h-11 px-3 max-w-full" value={genre} disabled={Boolean(query.trim())} onChange={e => update('genre', e.target.value, true)} /></label>
    </div>
    {query.trim() && <>
      <p className="text-sm mb-3">{text('검색은 종류별 최대 30개입니다. 연도·장르 필터는 전체 작품 목록에서 적용됩니다.', 'Search returns up to 30 per type. Year and genre apply to the catalog only.', '検索は種類別に最大30件です。年・ジャンルは作品一覧のみ適用されます。')}</p>
      <div role="tablist" aria-label={text('검색 결과 종류', 'Result type', '検索結果の種類')} className="flex gap-3 mb-4">
        {['anime', 'character'].map(type => <button key={type} role="tab" aria-selected={tab === type} aria-controls="browse-results" className="min-h-11 px-4 border rounded-lg" onClick={() => update('tab', type)}>{type === 'anime' ? text('애니메이션', 'Anime', 'アニメ') : text('캐릭터', 'Characters', 'キャラクター')} ({results.items.filter(item => item.type === type).length})</button>)}
      </div>
    </>}
    {(results.loading || results.loadingMore) && <p role="status" className="py-3">{t('loading')}</p>}
    {results.error && <div role="alert" className="border rounded-lg p-4 mb-4"><p>{text('불러오지 못했습니다. 검색어와 기존 결과는 유지됩니다.', 'Could not load results. Your search and previous results are preserved.', '読み込めませんでした。検索語と以前の結果は保持されます。')}</p><button className="min-h-11 px-3" onClick={results.retry}>{text('다시 시도', 'Retry', '再試行')}</button></div>}
    {!results.loading && !results.error && items.length === 0 && <p role="status">{t('noResults')}</p>}
    <div id="browse-results" role={query.trim() ? 'tabpanel' : undefined} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" aria-busy={results.loading}>
      {items.map(item => {
        const title = item.type === 'anime' ? getAnimeTitle(item, true) : { primary: language === 'ko' ? item.name_korean || item.name_full : language === 'ja' ? item.name_native || item.name_full : item.name_full };
        const count = item.site_rating_count ?? item.rating_count;
        const rating = item.site_average_rating ?? item.rating;
        return <Link key={item.id} to={`/${item.type}/${item.originalId}`} className="flex min-w-0 gap-3 border rounded-xl p-3 bg-surface hover:bg-surface-hover" onMouseEnter={() => item.type === 'anime' ? handleAnimeMouseEnter(item.originalId, user) : handleCharacterMouseEnter(item.originalId, user)} onMouseLeave={handleMouseLeave}>
          <img className="w-20 h-28 object-cover rounded shrink-0" src={item.type === 'anime' ? imageUrl(item.cover_image_url) : getCharacterImageUrl(item.originalId, item.image_large)} alt="" loading="lazy" onError={e => { if (!e.currentTarget.src.endsWith('/placeholder-anime.svg')) e.currentTarget.src = '/placeholder-anime.svg'; }} />
          <div className="min-w-0"><h2 className="font-semibold break-words">{title.primary}</h2>{title.secondary && <p className="text-sm text-text-secondary">{title.secondary}</p>}
            <p className="text-sm">{item.season_year} {item.format}</p>
            {item.type === 'anime' && <p className="text-sm">{count > 0 && rating != null ? `${Number(rating).toFixed(1)} / 5 · ${count}` : t('noRating')}</p>}
          </div>
        </Link>;
      })}
    </div>
    {!query.trim() && results.hasMore && !results.error && <button className="min-h-11 px-6 my-6 border rounded-lg" disabled={results.loading || results.loadingMore} onClick={results.loadMore}>{text('더 보기', 'Load more', 'もっと見る')}</button>}
  </main>;
}
