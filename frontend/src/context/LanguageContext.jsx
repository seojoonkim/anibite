import { createContext, useContext, useState, useEffect } from 'react';

const translations = {
  ko: {
    // Navbar
    appName: 'AniPass',
    rate: '애니 평가',
    rateCharacter: '캐릭터 평가',
    writeReview: '리뷰 작성',
    browse: '애니 검색',
    leaderboard: '리더보드',
    myAnipass: '내 애니패스',
    logout: '로그아웃',

    // Rate page
    rateTitle: '애니 평가',
    rateDescription: '카드에 마우스를 올리고 별점을 클릭하세요 (0.5점 단위)',

    // Character Rate page
    characterRateTitle: '캐릭터 평가',
    characterRateDescription: '내가 본 애니메이션의 캐릭터들을 평가하세요',
    ratedBadge: '평가완료',
    loading: '로딩 중...',
    allLoaded: '모든 캐릭터를 불러왔습니다',

    // Browse page
    browseTitle: '애니 검색',
    browseDescription: '모든 애니메이션을 검색하고 필터링하세요',
    search: '검색',
    searchPlaceholder: '애니메이션 검색...',
    sort: '정렬',
    sortPopularity: '인기순',
    sortRatingDesc: '평점 높은순',
    sortRatingAsc: '평점 낮은순',
    sortTitle: '제목순',
    sortYearDesc: '최신순',
    sortYearAsc: '오래된순',
    status: '방영 상태',
    statusAll: '전체',
    statusAiring: '방영중',
    statusFinished: '완결',
    statusNotYetAired: '미방영',
    year: '연도',
    yearPlaceholder: '예: 2024',
    genre: '장르',
    genrePlaceholder: '예: Action',
    loadMore: '더 보기',
    noResults: '검색 결과가 없습니다.',
    episodes: '화',
    rated: '명 평가',
    noRating: '평점 없음',

    // My AniPass
    myAnipassTitle: '내 애니패스',
    summary: '요약',
    ratedAnime: '평가한 애니',
    watchlist: '관심 목록',
    totalRated: '평가한 애니메이션',
    averageRating: '평균 평점',
    otakuScore: '오타쿠 점수',

    // Auth
    login: '로그인',
    register: '회원가입',
    username: '아이디',
    email: '이메일',
    password: '비밀번호',
    displayName: '표시 이름',

    // Common
    error: '에러',
    success: '성공',

    // Status actions
    watchLater: '보고싶어요',
    watchLaterShort: '나중에',
    notInterested: '관심없어요',
    notInterestedShort: '패스',
  },
  en: {
    // Navbar
    appName: 'AniPass',
    rate: 'Rate Anime',
    rateCharacter: 'Rate Characters',
    writeReview: 'Write Review',
    browse: 'Search',
    leaderboard: 'Leaderboard',
    myAnipass: 'My AniPass',
    logout: 'Logout',

    // Rate page
    rateTitle: 'Rate Anime',
    rateDescription: 'Hover over cards and click stars to rate (0.5 increments)',

    // Character Rate page
    characterRateTitle: 'Rate Characters',
    characterRateDescription: 'Rate characters from anime you\'ve watched',
    ratedBadge: 'Rated',
    loading: 'Loading...',
    allLoaded: 'All characters loaded',

    // Browse page
    browseTitle: 'Search',
    browseDescription: 'Search and filter all anime',
    search: 'Search',
    searchPlaceholder: 'Search anime...',
    sort: 'Sort',
    sortPopularity: 'Popularity',
    sortRatingDesc: 'Rating (High)',
    sortRatingAsc: 'Rating (Low)',
    sortTitle: 'Title',
    sortYearDesc: 'Year (New)',
    sortYearAsc: 'Year (Old)',
    status: 'Status',
    statusAll: 'All',
    statusAiring: 'Airing',
    statusFinished: 'Finished',
    statusNotYetAired: 'Not Yet Aired',
    year: 'Year',
    yearPlaceholder: 'e.g. 2024',
    genre: 'Genre',
    genrePlaceholder: 'e.g. Action',
    loadMore: 'Load More',
    noResults: 'No results found.',
    episodes: 'eps',
    rated: 'ratings',
    noRating: 'No rating',

    // My AniPass
    myAnipassTitle: 'My AniPass',
    summary: 'Summary',
    ratedAnime: 'Rated',
    watchlist: 'Watchlist',
    totalRated: 'Rated Anime',
    averageRating: 'Average Rating',
    otakuScore: 'Otaku Score',

    // Auth
    login: 'Login',
    register: 'Register',
    username: 'ID',
    email: 'Email',
    password: 'Password',
    displayName: 'Display Name',

    // Common
    error: 'Error',
    success: 'Success',

    // Status actions
    watchLater: 'Watch Later',
    watchLaterShort: 'Later',
    notInterested: 'Not Interested',
    notInterestedShort: 'Pass',
  },
  ja: {
    // Navbar
    appName: 'AniPass',
    rate: 'アニメ評価',
    rateCharacter: 'キャラ評価',
    writeReview: 'レビュー作成',
    browse: 'アニメ検索',
    leaderboard: 'ランキング',
    myAnipass: 'マイAniPass',
    logout: 'ログアウト',

    // Rate page
    rateTitle: 'アニメ評価',
    rateDescription: 'カードにマウスを置いて星をクリック (0.5刻み)',

    // Character Rate page
    characterRateTitle: 'キャラクター評価',
    characterRateDescription: '視聴したアニメのキャラクターを評価',
    ratedBadge: '評価済み',
    loading: '読込中...',
    allLoaded: '全キャラクター読込完了',

    // Browse page
    browseTitle: 'アニメ検索',
    browseDescription: '全アニメを検索・フィルタリング',
    search: '検索',
    searchPlaceholder: 'アニメを検索...',
    sort: '並び替え',
    sortPopularity: '人気順',
    sortRatingDesc: '評価高い順',
    sortRatingAsc: '評価低い順',
    sortTitle: 'タイトル順',
    sortYearDesc: '新しい順',
    sortYearAsc: '古い順',
    status: '放送状況',
    statusAll: '全て',
    statusAiring: '放送中',
    statusFinished: '完結',
    statusNotYetAired: '未放送',
    year: '年',
    yearPlaceholder: '例: 2024',
    genre: 'ジャンル',
    genrePlaceholder: '例: Action',
    loadMore: 'もっと見る',
    noResults: '検索結果がありません',
    episodes: '話',
    rated: '評価',
    noRating: '評価なし',

    // My AniPass
    myAnipassTitle: 'マイAniPass',
    summary: '概要',
    ratedAnime: '評価済み',
    watchlist: 'ウォッチリスト',
    totalRated: '評価済みアニメ',
    averageRating: '平均評価',
    otakuScore: 'オタクスコア',

    // Auth
    login: 'ログイン',
    register: '新規登録',
    username: 'ユーザーID',
    email: 'メール',
    password: 'パスワード',
    displayName: '表示名',

    // Common
    error: 'エラー',
    success: '成功',

    // Status actions
    watchLater: '後で見る',
    watchLaterShort: '後で',
    notInterested: '興味なし',
    notInterestedShort: 'パス',
  }
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'ko';
  });

  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  const toggleLanguage = () => {
    setLanguage(prev => {
      if (prev === 'ko') return 'en';
      if (prev === 'en') return 'ja';
      return 'ko';
    });
  };

  const t = (key) => {
    return translations[language][key] || key;
  };

  const getAnimeTitle = (anime, returnBoth = false) => {
    if (!anime) return returnBoth ? { primary: '', secondary: '' } : '';

    let primaryTitle = '';
    let secondaryTitle = '';

    if (language === 'ko') {
      // 한국어 모드: 한국어 제목 우선, 영어 제목 병기
      primaryTitle = anime.title_korean || anime.title_romaji || anime.title_english;
      secondaryTitle = anime.title_english || anime.title_romaji;

      // 같은 제목이면 병기하지 않음
      if (primaryTitle === secondaryTitle) {
        secondaryTitle = '';
      }
    } else if (language === 'ja') {
      // 일본어 모드: 일본어 원제 우선, 로마자 제목 병기
      primaryTitle = anime.title_native || anime.title_romaji || anime.title_english;
      secondaryTitle = anime.title_romaji || anime.title_english;

      // 같은 제목이면 병기하지 않음
      if (primaryTitle === secondaryTitle) {
        secondaryTitle = '';
      }
    } else {
      // 영어 모드: 영어 제목만
      primaryTitle = anime.title_english || anime.title_romaji;
    }

    // 시즌 표시가 이미 제목에 있는지 확인
    const hasSeasonInTitle = /season|시즌|part|기|期|nd|rd|th|II|III|IV|V|VI|VII|VIII|IX|X|kai|shippuden|continued|second|third|fourth|fifth/i.test(primaryTitle);

    // 시즌 번호가 2 이상이고 제목에 시즌 표시가 없으면 추가
    if (anime.season_number && anime.season_number > 1 && !hasSeasonInTitle) {
      if (language === 'ko') {
        primaryTitle = `${primaryTitle} ${anime.season_number}기`;
      } else {
        primaryTitle = `${primaryTitle} Season ${anime.season_number}`;
      }
    }

    if (returnBoth) {
      return { primary: primaryTitle, secondary: secondaryTitle };
    }

    return primaryTitle;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t, getAnimeTitle }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
