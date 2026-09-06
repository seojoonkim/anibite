-- =====================================================
-- 애니 평가 플랫폼 DB 스키마
-- 인기작 3,000개 + 캐릭터/성우/스태프 완전체
-- =====================================================

-- 애니메이션 기본 정보
CREATE TABLE anime (
    id INTEGER PRIMARY KEY,                    -- AniList ID
    id_mal INTEGER,                            -- MyAnimeList ID
    
    -- 제목
    title_romaji TEXT,
    title_english TEXT,
    title_native TEXT,
    
    -- 기본 정보
    type TEXT,                                 -- ANIME, MANGA
    format TEXT,                               -- TV, MOVIE, OVA, ONA, SPECIAL, MUSIC
    status TEXT,                               -- FINISHED, RELEASING, NOT_YET_RELEASED, CANCELLED, HIATUS
    description TEXT,
    
    -- 방영 정보
    season TEXT,                               -- WINTER, SPRING, SUMMER, FALL
    season_year INTEGER,
    episodes INTEGER,
    duration INTEGER,                          -- 분 단위
    
    -- 날짜
    start_date TEXT,                           -- YYYY-MM-DD
    end_date TEXT,
    
    -- 이미지 (커버는 로컬 저장, 나머지는 URL)
    cover_image_local TEXT,                    -- 로컬 저장 경로
    cover_image_url TEXT,                      -- 원본 URL (large)
    cover_image_color TEXT,                    -- 평균 색상 (#hex)
    banner_image_url TEXT,                     -- CDN URL
    
    -- 평점/인기도
    average_score INTEGER,                     -- 0-100
    mean_score INTEGER,
    popularity INTEGER,
    favourites INTEGER,
    trending INTEGER,
    
    -- 메타 정보
    source TEXT,                               -- ORIGINAL, MANGA, LIGHT_NOVEL 등
    country_of_origin TEXT,                    -- JP, KR, CN
    is_adult BOOLEAN DEFAULT 0,
    is_licensed BOOLEAN DEFAULT 1,
    
    -- 외부 링크
    site_url TEXT,                             -- AniList URL
    trailer_url TEXT,
    trailer_site TEXT,                         -- youtube, dailymotion
    
    -- 타임스탬프
    updated_at INTEGER,                        -- AniList 업데이트 시간
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 장르
CREATE TABLE genre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE anime_genre (
    anime_id INTEGER REFERENCES anime(id),
    genre_id INTEGER REFERENCES genre(id),
    PRIMARY KEY (anime_id, genre_id)
);

-- 태그 (더 세부적인 분류)
CREATE TABLE tag (
    id INTEGER PRIMARY KEY,                    -- AniList tag ID
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,                             -- Themes, Setting, Cast 등
    is_adult BOOLEAN DEFAULT 0
);

CREATE TABLE anime_tag (
    anime_id INTEGER REFERENCES anime(id),
    tag_id INTEGER REFERENCES tag(id),
    rank INTEGER,                              -- 태그 관련도 (0-100)
    is_spoiler BOOLEAN DEFAULT 0,
    PRIMARY KEY (anime_id, tag_id)
);

-- 스튜디오
CREATE TABLE studio (
    id INTEGER PRIMARY KEY,                    -- AniList studio ID
    name TEXT NOT NULL,
    is_animation_studio BOOLEAN DEFAULT 1,
    site_url TEXT,
    favourites INTEGER DEFAULT 0
);

CREATE TABLE anime_studio (
    anime_id INTEGER REFERENCES anime(id),
    studio_id INTEGER REFERENCES studio(id),
    is_main BOOLEAN DEFAULT 0,
    PRIMARY KEY (anime_id, studio_id)
);

-- 캐릭터
CREATE TABLE character (
    id INTEGER PRIMARY KEY,                    -- AniList character ID
    
    -- 이름
    name_first TEXT,
    name_last TEXT,
    name_full TEXT,
    name_native TEXT,
    name_alternative TEXT,                     -- JSON array
    
    -- 정보
    description TEXT,
    gender TEXT,
    age TEXT,
    date_of_birth TEXT,                        -- MM-DD or YYYY-MM-DD
    blood_type TEXT,
    
    -- 이미지 (URL만 저장, 나중에 로컬 저장 가능)
    image_url TEXT,
    image_local TEXT,                          -- 나중에 로컬 저장 시 사용
    
    -- 인기도
    favourites INTEGER DEFAULT 0,
    
    -- 타임스탬프
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 애니-캐릭터 연결
CREATE TABLE anime_character (
    anime_id INTEGER REFERENCES anime(id),
    character_id INTEGER REFERENCES character(id),
    role TEXT,                                 -- MAIN, SUPPORTING, BACKGROUND
    PRIMARY KEY (anime_id, character_id)
);

-- 성우/스태프 (통합 테이블)
CREATE TABLE staff (
    id INTEGER PRIMARY KEY,                    -- AniList staff ID
    
    -- 이름
    name_first TEXT,
    name_last TEXT,
    name_full TEXT,
    name_native TEXT,
    
    -- 정보
    description TEXT,
    gender TEXT,
    age INTEGER,
    date_of_birth TEXT,
    date_of_death TEXT,
    home_town TEXT,
    blood_type TEXT,
    years_active_start INTEGER,
    years_active_end INTEGER,
    
    -- 직업
    primary_occupations TEXT,                  -- JSON array
    
    -- 언어 (성우인 경우)
    language TEXT,                             -- JAPANESE, ENGLISH 등
    
    -- 이미지
    image_url TEXT,
    image_local TEXT,
    
    -- 인기도
    favourites INTEGER DEFAULT 0,
    
    -- 타임스탬프
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 캐릭터-성우 연결
CREATE TABLE character_voice_actor (
    character_id INTEGER REFERENCES character(id),
    staff_id INTEGER REFERENCES staff(id),
    anime_id INTEGER REFERENCES anime(id),     -- 어떤 애니에서
    language TEXT DEFAULT 'JAPANESE',
    PRIMARY KEY (character_id, staff_id, anime_id)
);

-- 애니-스태프 연결 (감독, 작가 등)
CREATE TABLE anime_staff (
    anime_id INTEGER REFERENCES anime(id),
    staff_id INTEGER REFERENCES staff(id),
    role TEXT,                                 -- Director, Original Creator 등
    PRIMARY KEY (anime_id, staff_id, role)
);

-- 관계 작품 (시퀄, 프리퀄 등)
CREATE TABLE anime_relation (
    anime_id INTEGER REFERENCES anime(id),
    related_anime_id INTEGER,                  -- 관련 작품 ID (DB에 없을 수도 있음)
    relation_type TEXT,                        -- SEQUEL, PREQUEL, SIDE_STORY 등
    PRIMARY KEY (anime_id, related_anime_id)
);

-- 추천 작품
CREATE TABLE anime_recommendation (
    anime_id INTEGER REFERENCES anime(id),
    recommended_anime_id INTEGER,
    rating INTEGER,                            -- 추천 점수
    PRIMARY KEY (anime_id, recommended_anime_id)
);

-- 외부 스트리밍 링크
CREATE TABLE anime_external_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anime_id INTEGER REFERENCES anime(id),
    site TEXT,                                 -- Crunchyroll, Netflix 등
    url TEXT,
    type TEXT,                                 -- STREAMING, INFO, SOCIAL
    language TEXT
);

-- 스트리밍 에피소드 정보
CREATE TABLE anime_streaming_episode (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anime_id INTEGER REFERENCES anime(id),
    title TEXT,
    thumbnail_url TEXT,
    url TEXT,
    site TEXT
);

-- 통계 (점수 분포)
CREATE TABLE anime_score_distribution (
    anime_id INTEGER REFERENCES anime(id),
    score INTEGER,                             -- 10, 20, 30 ... 100
    amount INTEGER,
    PRIMARY KEY (anime_id, score)
);

-- 통계 (상태 분포)
CREATE TABLE anime_status_distribution (
    anime_id INTEGER REFERENCES anime(id),
    status TEXT,                               -- CURRENT, PLANNING, COMPLETED, DROPPED, PAUSED
    amount INTEGER,
    PRIMARY KEY (anime_id, status)
);

-- =====================================================
-- 인덱스
-- =====================================================

CREATE INDEX idx_anime_popularity ON anime(popularity DESC);
CREATE INDEX idx_anime_score ON anime(average_score DESC);
CREATE INDEX idx_anime_season ON anime(season_year, season);
CREATE INDEX idx_anime_format ON anime(format);
CREATE INDEX idx_anime_status ON anime(status);

CREATE INDEX idx_character_name ON character(name_full);
CREATE INDEX idx_character_favourites ON character(favourites DESC);

CREATE INDEX idx_staff_name ON staff(name_full);
CREATE INDEX idx_staff_language ON staff(language);

CREATE INDEX idx_anime_character_role ON anime_character(role);
CREATE INDEX idx_anime_tag_rank ON anime_tag(rank DESC);

-- =====================================================
-- 크롤링 메타 정보
-- =====================================================

CREATE TABLE crawl_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 초기 메타 정보
INSERT INTO crawl_meta (key, value) VALUES 
    ('version', '1.0'),
    ('total_anime', '0'),
    ('total_characters', '0'),
    ('total_staff', '0'),
    ('last_full_crawl', NULL),
    ('last_incremental_crawl', NULL);
