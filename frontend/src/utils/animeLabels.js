// Human-readable labels for AniList enum values (ko / ja / en).
const L = (ko, ja, en) => ({ ko, ja, en });

const STATUS = {
  FINISHED: L('완결', '放送終了', 'Finished'),
  RELEASING: L('방영 중', '放送中', 'Airing'),
  NOT_YET_RELEASED: L('방영 예정', '放送予定', 'Upcoming'),
  CANCELLED: L('방영 취소', '放送中止', 'Cancelled'),
  HIATUS: L('휴재', '休止中', 'Hiatus'),
};
const FORMAT = {
  TV: L('TV 시리즈', 'TVシリーズ', 'TV'),
  TV_SHORT: L('TV 단편', 'TVショート', 'TV Short'),
  MOVIE: L('극장판', '劇場版', 'Movie'),
  SPECIAL: L('스페셜', 'スペシャル', 'Special'),
  OVA: L('OVA', 'OVA', 'OVA'),
  ONA: L('웹 애니', 'ONA', 'ONA'),
  MUSIC: L('뮤직비디오', 'MV', 'Music'),
};
const SEASON = {
  WINTER: L('겨울', '冬', 'Winter'),
  SPRING: L('봄', '春', 'Spring'),
  SUMMER: L('여름', '夏', 'Summer'),
  FALL: L('가을', '秋', 'Fall'),
};
const SOURCE = {
  ORIGINAL: L('오리지널', 'オリジナル', 'Original'),
  MANGA: L('만화', '漫画', 'Manga'),
  LIGHT_NOVEL: L('라이트노벨', 'ライトノベル', 'Light novel'),
  NOVEL: L('소설', '小説', 'Novel'),
  WEB_NOVEL: L('웹소설', 'Web小説', 'Web novel'),
  VISUAL_NOVEL: L('비주얼노벨', 'ビジュアルノベル', 'Visual novel'),
  VIDEO_GAME: L('게임', 'ゲーム', 'Video game'),
  GAME: L('게임', 'ゲーム', 'Game'),
  WEBTOON: L('웹툰', 'Webtoon', 'Webtoon'),
  OTHER: L('기타', 'その他', 'Other'),
  MULTIMEDIA_PROJECT: L('미디어믹스', 'メディアミックス', 'Multimedia'),
  DOUJINSHI: L('동인지', '同人誌', 'Doujinshi'),
  ANIME: L('애니메이션', 'アニメ', 'Anime'),
  PICTURE_BOOK: L('그림책', '絵本', 'Picture book'),
  COMIC: L('코믹스', 'コミック', 'Comic'),
  LIVE_ACTION: L('실사', '実写', 'Live action'),
  NOVEL_LIGHT: L('라이트노벨', 'ライトノベル', 'Light novel'),
};
export const GENRES = {
  Action: L('액션', 'アクション', 'Action'),
  Adventure: L('모험', '冒険', 'Adventure'),
  Comedy: L('코미디', 'コメディ', 'Comedy'),
  Drama: L('드라마', 'ドラマ', 'Drama'),
  Ecchi: L('엣치', 'エッチ', 'Ecchi'),
  Fantasy: L('판타지', 'ファンタジー', 'Fantasy'),
  Horror: L('호러', 'ホラー', 'Horror'),
  'Mahou Shoujo': L('마법소녀', '魔法少女', 'Mahou Shoujo'),
  Mecha: L('메카', 'ロボット', 'Mecha'),
  Music: L('음악', '音楽', 'Music'),
  Mystery: L('미스터리', 'ミステリー', 'Mystery'),
  Psychological: L('심리', 'サイコ', 'Psychological'),
  Romance: L('로맨스', '恋愛', 'Romance'),
  'Sci-Fi': L('SF', 'SF', 'Sci-Fi'),
  'Slice of Life': L('일상', '日常', 'Slice of Life'),
  Sports: L('스포츠', 'スポーツ', 'Sports'),
  Supernatural: L('초자연', '超常', 'Supernatural'),
  Thriller: L('스릴러', 'スリラー', 'Thriller'),
};

const pick = (table, value, language) => {
  if (!value) return value;
  const entry = table[value];
  return entry ? entry[language] || entry.en : String(value).replaceAll('_', ' ');
};

export const statusLabel = (v, lang = 'ko') => pick(STATUS, v, lang);
export const formatLabel = (v, lang = 'ko') => pick(FORMAT, v, lang);
export const sourceLabel = (v, lang = 'ko') => pick(SOURCE, v, lang);
export const genreLabel = (v, lang = 'ko') => (GENRES[v] ? GENRES[v][lang] || v : v);
export const seasonLabel = (season, year, lang = 'ko') => {
  const s = pick(SEASON, season, lang);
  if (!year) return s;
  return lang === 'en' ? `${s} ${year}` : `${year} ${s}`;
};
