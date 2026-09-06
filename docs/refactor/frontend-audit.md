# AniBite 프런트엔드 읽기 전용 감사

## 범위와 판정 기준

- 대상: `/tmp/anibite-review`, 커밋 `cd63637a68d76771bf588f00279780ef14d9e9e1`. 아래 소스 경로는 저장소 루트 기준이다.
- 실제 React/Vite 소스, API 계약 일부, 빌드·린트를 확인했다. README의 성능 목표는 실측으로 취급하지 않았다.
- **확정**은 코드 또는 도구 출력으로 확인한 구조·계약·규칙 위반이다. 실제 사용자 발생 빈도, 브라우저에서의 재현, 운영 API 영향은 별도 표기한다.
- 브라우저·로그인·운영 데이터 변경·서버 실행은 하지 않았다. LCP/INP/CLS, 모바일 탭 동작, 색 대비, 네트워크 지연은 미측정이다. 시각 QA는 상위 담당자 범위다.
- 소스 및 Git 조작은 하지 않았다. npm 설치의 `node_modules/`, 빌드의 `dist/`만 생성되며 작업 후 `git status --short` 출력은 비어 있었다.

## 1. 실행 결과

| 명령 | 결과 | 근거 |
|---|---|---|
| `npm ci` | 종료 0 | `/tmp/anibite-install.log:2-17` |
| `npm run build` | 종료 0, Vite 7.3.1, 796 모듈 | `/tmp/anibite-build.log:5-10` |
| `npm run lint` | 종료 1, **169건: 오류 151 / 경고 18** | `/tmp/anibite-lint.log` 마지막 요약 |
| `npm audit --json` | 종료 1, 취약성 보고 20건: low 2 / moderate 6 / high 12 / critical 0 | `/tmp/anibite-npm-audit.json`, `/tmp/anibite-install.log:7` |

환경은 Node `v25.2.1`, npm `11.19.1`이다. 빌드 로그의 `built in 1.83s`는 이 머신의 한 번 빌드 소요이지 웹 로딩 성능이 아니다. Browserslist 데이터 오래됨 경고가 있었다. 설치 로그에는 esbuild/fsevents 설치 스크립트 승인 관련 경고가 있으나 빌드는 성공했다. 자동 `audit fix`는 실행하지 않았다.

실제 산출물 크기(Vite 표기 kB, gzip은 압축 결과이며 실제 전송 측정 아님):

| 청크 | minified | gzip | 로그 |
|---|---:|---:|---|
| 엔트리 JS | 309.84 | 98.41 | `/tmp/anibite-build.log:43` |
| MyAniPass JS | 422.69 | 120.42 | `/tmp/anibite-build.log:44` |
| AdminEditor JS | 93.98 | 32.52 | `/tmp/anibite-build.log:42` |
| 엔트리 CSS | 59.25 | 11.14 | `/tmp/anibite-build.log:14` |

**빌드 성공은 런타임 정상 또는 린트 통과를 의미하지 않는다.** `package.json:6-10`의 build는 Vite 변환뿐이며 테스트 스크립트·타입 검사 게이트가 없다. 린트에는 단순 미사용 변수 외에 조건부 Hook, 정의되지 않은 식별자도 포함된다. audit의 high 수를 곧바로 브라우저에서 악용 가능한 취약점 수로 해석하면 안 된다. 런타임 직접 의존 axios, 개발 도구 vite/postcss, react-router-dom 및 전이 의존성을 구분해 advisory 적용 조건을 후속 검토해야 한다.

## 2. 실제 라우트 맵

모든 경로는 `frontend/src/App.jsx`에 선언된다. 최초 `/`는 Home이 아니라 Rate다. Home.jsx와 Profile.jsx는 이 라우트 표에 연결되지 않는다.

| 경로 | 화면 | 접근/근거 |
|---|---|---|
| `/login` | Login | 공개, 90행 |
| `/register` | Register | 공개, 91행 |
| `/verify-email` | VerifyEmail | 공개, 92행 |
| `/email-sent` | EmailSent | 공개, 93행 |
| `/resend-verification` | ResendVerification | 공개, 94행 |
| `/` | Rate | 로그인 필요, 95-102행 |
| `/feed` | Feed | 로그인 필요, 103-110행 |
| `/rate` | Rate | 로그인 필요, 111-118행 |
| `/rate-characters` | RateCharacters | 로그인 필요, 119-126행 |
| `/write-reviews` | WriteReviews | 로그인 필요, 127-134행 |
| `/browse` | Browse | 로그인 필요, 135-142행 |
| `/leaderboard` | Leaderboard | 로그인 필요, 143-150행 |
| `/anime/:id` | AnimeDetail | 로그인 필요, 151-158행 |
| `/character/:id` | CharacterDetail | 로그인 필요, 159-166행 |
| `/my-anipass` | MyAniPass | 로그인 필요, 167-174행 |
| `/settings` | Settings | 로그인 필요, 175-182행 |
| `/admin` | AdminEditor | 일반 ProtectedRoute만 적용, 183-190행 |
| `/admin/backup` | BackupLogs | 일반 ProtectedRoute만 적용, 191-198행 |
| `/user/:userId` | MyAniPass | 로그인 필요, 199-206행 |

- 공개 경로 및 정확히 `/admin`에서만 Navbar를 숨긴다(`App.jsx:52-55`). `/admin/backup`은 관리자 화면이지만 Navbar가 나온다. 댓글의 “authenticated pages”와 달리 Navbar 표시 판단에는 인증 상태가 없다(82-86행).
- `path="*"`가 없다(89-207행). 잘못된 SPA 경로에 전용 Not Found 화면이 없다. 운영 HTTP 404 원인은 이 사실만으로 단정할 수 없다.
- Feed는 `filter` 쿼리를 사용하고 URL 변경을 따라간다(`pages/Feed.jsx:27-29,116-137`). MyAniPass는 `tab=feed|anipass|anime|character`를 검증하고 뒤로/앞으로 가기를 동기화한다(`pages/MyAniPass.jsx:49-53,140-153`).

## 3. 구조 평가

### 현재 구성

`main.jsx → GoogleOAuthProvider → App → Auth/Language/LogoWiggle Provider → BrowserRouter → AppRoutes → lazy pages`다(`main.jsx:42-48`, `App.jsx:213-224`). 도메인별 service 모듈이 Axios 인스턴스를 공유하고, 페이지가 로컬 상태·데이터 요청·정규화·뮤테이션·모달 표시를 직접 조율한다.

큰 파일의 실제 줄 수는 MyAniPass **2,313**, AnimeDetail **1,528**, CharacterDetail **1,403**, ActivityCard **908**, Feed **894**였다(파일을 Python으로 직접 집계). 줄 수 자체가 결함은 아니지만 프로필의 API/차트/피드/댓글/컬렉션/모달 결합이 변경 범위를 키운다. 근거: `MyAniPass.jsx:1-38`의 광범위한 import, `68-134`의 중복·파생 상태, `503-558`의 탭별 데이터 조율.

### 유지할 좋은 패턴

1. **라우트 단위 lazy + Suspense**가 이미 적용돼 있다(`App.jsx:11-28,88`). SPA 전체를 다시 쓰기보다 MyAniPass 내부 탭 경계를 추가 분할하는 편이 작은 변화다.
2. **도메인 service 경계와 공통 API 설정**이 있다(`services/animeService.js:7-21`, `services/api.js:14-33`, `config/api.js:4-5`). 설정 중복을 제거하고 계약 검증을 여기에 추가할 수 있다.
3. **URL 기반 탭 복원**, **검색 디바운스**, **IntersectionObserver cleanup**이 있다(`MyAniPass.jsx:140-153`, `Browse.jsx:86-93,132-154`). 이를 지우지 말고 stale response/페이지 계약을 보완해야 한다.
4. **낙관적 좋아요 + 실패 롤백**이 명시적이다(`hooks/useActivity.js:113-137`). 공통 mutation 패턴으로 확장할 수 있다.
5. 이미지 영역 비율·fallback·lazy loading이 일부 화면에 있다(`Browse.jsx:23-43,361-369`). 모든 이미지가 미최적화된 것은 아니다.
6. 디자인 토큰, 안정적인 스크롤바 영역, 해시 asset의 immutable 캐시 설정이 있다(`index.css:15-135,149-153`, `vercel.json:29-35`). 중복 색상 계층을 정리하면서 보존할 기반이다.
7. 청크 갱신 오류의 재로드 억제 장치가 있다(`main.jsx:10-40`). 다만 ErrorBoundary를 대체하지는 않는다.

## 4. 우선순위별 확정 문제와 영향

### P1 — 데이터 정확성·핵심 조작·출시 품질

#### F1. Browse 목록 API 계약 불일치와 이전 페이지 재요청 — 확정

- `frontend/src/pages/Browse.jsx:167-174`는 `{page, limit, sort}`를 전달한다. `frontend/src/services/animeService.js:11-13`은 이름 변환 없이 그대로 전송한다.
- 실제 서버는 `page_size`(기본 50)와 `sort_by`(기본 popularity)를 받는다(`backend/api/anime.py:21-32,54-63`). 따라서 검색어가 없는 목록에서 “초기 12/후속 20개”, sort 드롭다운의 의도가 서버 계약에 반영되지 않는다.
- `Browse.jsx:206-209`는 `setPage(prev => prev + 1)` 직후 같은 렌더의 `loadAnime(false)`를 호출한다. 그 함수는 기존 `page`를 읽는다(167행). 첫 추가 로딩은 page 1을 다시 요청하며 결과를 중복 제거 없이 append한다(179-180행). 실제 데이터가 있을 때 중복 목록/key가 발생하는 코드 경로다.
- 수정 방향: 서버의 page_size/sort_by에 맞는 명시적 adapter, 일정한 page size 또는 cursor 계약, `nextPage`를 함수 인자로 전달하고 성공 후에만 commit. 정렬별 요청 파라미터와 다음 페이지 중복 없음에 회귀 테스트를 작성한다. 단순히 limit 이름만 고치면 12→20 가변 page-size offset 문제를 새로 만들 수 있으므로 함께 고쳐야 한다(`backend/services/anime_service.py:25-27`).

#### F2. 읽기·쓰기를 구분하지 않는 자동 재시도 — 확정, 중복 저장 발생은 미재현

- `services/api.js:47-60`의 재시도 조건에는 HTTP method/idempotency 조건이 없다. 네트워크·408·429·5xx에 POST도 재전송된다.
- 실제 게시물 생성이 이 client를 사용한다(`services/userPostService.js:4-9`). 서버가 성공 처리한 뒤 응답만 유실되면 중복 게시물, toggle류는 결과 역전 가능성이 있다. 운영 중복 발생이나 서버의 방지 장치는 이 감사에서 입증하지 않았다.
- client 설정에 timeout도 없다(`services/api.js:14-19`). 취소를 별도로 제외하지 않아 이후 AbortSignal 도입 시 취소 요청까지 retry 대상으로 처리할 수 있다.
- 권고: GET/HEAD의 제한적 retry, 429 Retry-After 고려, mutation 기본 retry 금지 또는 서버 idempotency key, 타임아웃/취소 공통 규칙. 서비스·UI가 실패를 빈 결과로 숨기지 않도록 한다.

#### F3. 피드 필터 전환 시 새 요청을 잃는 경로 — 확정 코드 결함, 타이밍 재현 필요

- `hooks/useActivity.js:264-265`는 기존 초기 요청 진행 중이면 새 `loadInitial`을 즉시 버린다.
- 그런데 필터 effect는 먼저 `filtersStringRef`를 새 값으로 바꾸고 loadInitial을 호출한다(330-341행). 따라서 요청 중 all→following 변경 시 새 필터는 처리됐다고 기록되지만 요청은 생략되고, 기존 응답을 그대로 set한다(286행). 완료 후 새 필터 요청 재실행 장치가 없다.
- `loadMore`도 취소·generation 검증 없이 append한다(311-320행). 빠른 전환 시 목록 혼합 위험이 있다.
- 권고: query key 기반 캐시/취소 또는 request generation guard. 느린 응답 중 필터 변경 테스트와 역순 응답 테스트를 작성한다.
- Browse 검색도 `Browse.jsx:95-129`에 요청 취소/순서 검증이 없어 오래된 검색 응답이 최신 결과를 덮을 수 있다. 디바운스만으로 해결되지 않는다.

#### F4. 별점 입력이 포인터 위치·hover에 종속 — 확정 접근성 결함

- 공통 별 버튼은 accessible name/선택 상태 없이 SVG만 표시한다(`components/common/StarRating.jsx:153-166`). 반점/정점 판단은 `e.clientX` 위치다(50-64행). 키보드 사용자에게 0.5 단위의 명시적 선택 방법이 없다.
- 핵심 Rate 카드의 조작부는 mouse enter/move/leave로만 노출된다(`pages/Rate.jsx:214-219,243-265`), focus로 표시하는 동작이 없다. Link 내부에 button이 들어가 interactive 요소 중첩도 있다. opacity 0 조작부는 키보드 포커스에서 자동 제외되지 않는다.
- 모바일 실제 실패 양상은 브라우저 검증 대상이나 hover 의존·의미 누락은 코드로 확정이다.
- 권고: 항상 접근 가능한 평가 버튼, radio group 또는 키보드 지원 slider(0~5, 0.5 step), 읽기 전용 평점은 텍스트/이미지 의미로 분리. Tab/Enter/Space/화살표와 터치로 동일 작업을 완료하는 기준을 둔다.

#### F5. 리뷰 모달의 dialog·포커스·필드 연결 누락 — 확정

- `components/common/EditReviewModal.jsx:142-174`는 div overlay와 SVG 닫기 버튼이며 role=dialog, aria-modal, 제목 연결, 닫기 이름이 없다.
- 전체 effect(79-98행)는 폼 초기화와 body overflow 처리뿐이다. focus trap/초기 focus/복귀/Escape 대응이 없다.
- textarea label에 htmlFor/id 연결이 없고(240-255행), 오류 메시지에 live/alert 의미가 없다(179-183행). 5000자 카운터는 표시하지만 maxLength 또는 최대 길이 검사가 없다(100-122,249-258행).
- 권고: 검증된 공통 Dialog와 FormField/FieldError를 도입하고 모달 중 background inert, focus restore, 저장 중 닫힘 정책을 명시한다. 저장 실패 뒤 내용 보존과 오류 focus까지 테스트한다.

#### F6. 린트가 실제 Hook 위반과 미정의 참조를 발견 — 확정, 전부 사용자 장애로 간주 금지

- `components/common/ContentMenu.jsx:35-39`는 소유자 조건으로 return한 뒤 useEffect를 호출한다. 같은 instance에서 소유권 조건이 바뀌면 Hook 순서가 바뀐다. 린트 근거 `/tmp/anibite-lint.log:52-56`.
- `pages/AnimeDetail.jsx:247,284,311,315,320` 등의 미정의 참조가 검출됐다. 그중 사용되지 않는 이전 handler도 있어 “현재 모든 댓글 기능이 실패한다”로 일반화하면 안 된다. 실제 연결된 경로와 dead code를 나눠 정리할 필요가 있다.
- 권고: Hook 순서/no-undef 우선 복구 → 회귀 테스트 → 미사용 코드 정리. React compiler 계열 lint의 set-state-in-effect 등을 단순 unused와 섞어서 일괄 disable하지 않는다. CI에서 lint/build/핵심 계약 테스트를 독립 필수 게이트로 둔다.

#### F7. 관리자 화면은 프런트에서 로그인만 확인 — 확정 UX/권한 경계 문제

- `App.jsx:31-40,183-198`의 ProtectedRoute는 isAuthenticated만 확인한다. AdminEditor 초기 상태에도 역할 확인이 없다(`pages/AdminEditor.jsx:48-60`).
- 일반 로그인 사용자가 관리자 UI를 볼 수 있는 경로가 있으나, **서버의 권한 우회가 가능하다는 결론은 아니다**. API 권한 enforcement는 별도 보안 감사가 필요하다.
- 권고: 역할 기반 route/UI guard와 403 화면을 추가하되 서버 권한 검사를 유일한 보안 경계로 유지한다.

### P2 — 인증/회복 UX·공유·유지보수

#### F8. 인증 초기화 정책과 로그인 복귀 동선 불일치 — 확정

- `context/AuthContext.jsx:31-54`는 직접 fetch로 /auth/me를 호출한다. 실패 상태를 401과 네트워크 실패로 나누지 않고 기존 사용자로 fallback한다. 한편 Axios는 401에서 저장 토큰 제거와 전체 location 이동을 수행한다(`services/api.js:63-71`).
- ProtectedRoute는 init fetch가 끝날 때까지 loading으로 막는다(`App.jsx:34-38`). 저장 user를 빨리 set하더라도 loading gate는 풀리지 않으며 fetch timeout도 없다.
- 원래 URL을 로그인 state로 보존하지 않는다(`App.jsx:40`), 로그인 성공 후 무조건 `/`로 이동한다(`pages/Login.jsx:25-28`). 공유 상세 링크를 로그인 후 잃는 코드다.
- 권고: 인증 만료와 일시 장애를 구분하고 세션 초기화 단일 경로/최대 대기/재시도 UI를 정의한다. 목적 경로를 보존하되 내부 경로로 검증해 복귀한다.

#### F9. 한국어 기본값과 문서 언어·브랜딩 메타 불일치 — 확정

- `index.html:2`는 lang=en, `context/LanguageContext.jsx:236-243`은 ko 기본이며 localStorage만 동기화한다. document lang 업데이트는 src 검색에서 발견되지 않았다.
- title은 Anibite인데 description/OG/Twitter는 AniPass/anipass.app이다(`index.html:11-30`). 사용자 제공 CNAME 정보(anibite.com)와도 불일치한다. 링크 이미지의 실제 HTTP 가용성은 미확인이다.
- 모든 콘텐츠 상세가 로그인 필요라는 라우팅은 공개 검색 유입/공유 미리보기 요구와 맞는지 제품 결정이 필요하다. CSR 자체를 결함으로 단정하거나 SSR 전체 전환을 선행할 이유는 없다.
- 권고: 브랜드/정식 도메인 일원화, document lang 동기화, 공개 상세 정책 결정 후 경로별 제목·description·OG 전략을 선택한다.

#### F10. 상태 회복/찾을 수 없음 UX가 약함 — 확정

- 라우트 wildcard 없음(`App.jsx:89-207`), React ErrorBoundary 없음(src 검색), Suspense는 로딩만 처리한다(44-48,88행).
- Feed의 알림/저장 로딩 실패는 목록을 빈 배열로 바꾼다(`Feed.jsx:207-224`). `useActivityPagination`도 초기 오류를 빈 목록+hasMore=false로 바꾸며 error를 반환하지 않는다(`useActivity.js:290-298,366-374`). “콘텐츠 없음”과 “실패”를 구분하기 어렵다.
- 권고: 공통 empty/error/offline/403/404 상태, 재시도 CTA, 경로 단위 ErrorBoundary, 목록의 더 보기 대체 수단을 제공한다.

## 5. 성능·설계 개선 후보

### 코드로 확인한 사실

- **프로필 탭 코드가 한 청크에 묶인다.** `MyAniPass.jsx:19-33`의 차트들이 정적 import된다. 초기 activeTab은 feed(49-53행)인데 차트 관련 코드도 프로필 라우트 청크에 포함되는 구조다. 실제 MyAniPass 청크 422.69 kB는 빌드로 확인했다. 우선 통계 탭/차트 lazy split을 검토한다. 그 절감량은 아직 측정하지 않았다.
- **useVirtualGrid는 엄밀한 windowing이 아니라 지연 마운트다.** visible set에 넣은 section을 제거하지 않는다(`hooks/useVirtualGrid.js:14-22`). 긴 스크롤 이후 DOM 수를 일정하게 제한하지 않는다. `MyAniPass.jsx:1267-1268`에서 사용 중이다. 장기 DOM 증가와 메모리 규모는 profiler로 확인 후 row windowing 도입 여부를 결정한다.
- **이미지 크기 정책이 중복된다.** 작은 Browse 썸네일에도 covers_large URL을 선택한다(`Browse.jsx:211-218,361-366`); Rate 이미지에는 loading=lazy가 없다(`Rate.jsx:221-228`). 공통 image helper가 있는데 EditReviewModal은 별도 URL 변환을 다시 구현한다(`EditReviewModal.jsx:29-77`). viewport 아래만 lazy, 첫 화면 주요 이미지는 우선 로드, srcset/sizes·fallback 정책을 공통화한다. 실제 이미지 byte 절감량/LCP 개선은 미측정이다.
- **폰트 stylesheet 의존이 여러 개다.** `index.css:2-6`의 SUIT/Pretendard variable/Inter/Nunito/Righteous와 `index.html:7-10`의 Pretendard static/Varela Round가 공존한다. CSS 요청은 확정, 모든 font 파일이 실제 다운로드된다는 주장은 하지 않는다. 실제 사용 폰트·언어 subset을 먼저 측정해 정리한다.
- **카드별 resize 측정**이 있다(`Rate.jsx:39-53`); 카드마다 listener와 offsetWidth 읽기를 만든다. CSS clamp/container sizing 또는 공유 ResizeObserver를 고려한다. 이것이 현재 INP 병목이라는 근거는 없다.
- **hover prefetch cache는 TTL 조회만 하고 자동 eviction은 없다**(`hooks/usePrefetch.js:8-10,21-26,45-49,153-168`). clear 함수는 선언 외 src 호출이 검색되지 않았다. in-flight dedupe/뮤테이션 invalidation이 없어 중복 요청과 stale 데이터 후보가 된다. 지속 메모리 증가 규모는 미측정이다.
- **토큰이 여러 계층에 중복**된다(`index.css:15-135`, `styles/customColors.css:4-10`, `EditReviewModal.jsx:289-292`). inline 색상·important override를 의미 기반 token으로 수렴해야 변경 추적이 쉬워진다. 실제 computed contrast는 브라우저 QA 전까지 단정하지 않는다.

### 측정 후 결정할 가설

1. 프로필 통계 lazy split이 프로필 feed 최초 렌더의 parse/execute 비용을 줄일 가능성: chunk graph와 coverage 확인.
2. covers_large 및 다중 폰트가 모바일 네트워크 병목일 가능성: cold-cache waterfall, transferred bytes, LCP element 확인.
3. 지연 마운트 누적, per-card resize, 긴 피드 append가 긴 세션 메모리/INP 병목일 가능성: 고정 fixture로 스크롤 전후 DOM 수·heap·React commit 측정.
4. 빠른 검색/필터 전환에 stale 결과가 보일 가능성: 네트워크 응답 순서를 제어하는 테스트로 재현.
5. 터치 환경에서 hover overlay가 주요 평가 흐름을 방해할 가능성: 실제 iOS/Android 또는 브라우저 touch emulation과 키보드 검증.

## 6. 권장 리팩터링 순서와 완료 기준

| 순서 | 작업 단위 | 완료 기준 |
|---|---|---|
| 1 | Browse 계약/페이지 상태와 피드 request race 수정 | 요청 파라미터 계약 테스트, 첫 페이지 중복 없음, 실패 후 재시도에서 page 유지, 역순 응답에서 최신 filter만 반영 |
| 2 | 네트워크·인증 정책 일원화 | POST 자동 재시도 제한, 취소는 retry 제외, 401/403/오프라인 구분, 로그인 후 deep link 복귀 |
| 3 | 공통 StarRating/Dialog/FormField 접근성 | 포인터 없이 반점 포함 평가, 보이지 않는 버튼 focus 없음, 모달 focus trap/복귀/Escape, 이름·오류 안내 |
| 4 | 출시 게이트 복원·의존성 보안 정리 | Hook/no-undef 우선 해결, lint/build 필수 통과, advisory 적용 조건에 맞춘 업데이트 및 재빌드 |
| 5 | MyAniPass/Detail의 기능별 분할 | profile feed/collection/stats 모듈과 query key 분리, service adapter 계약 명확화, 중복 상태와 dead handler 제거 |
| 6 | 이미지/폰트/통계 청크/목록 최적화 | 같은 fixture·기기 조건의 전후 bundle/network/DOM·Web Vitals 자료 확보; 추정 개선치 금지 |
| 7 | URL/메타·에러·디자인 토큰 일원화 | 404/403/error 재시도, 브랜드/언어 일치, 공유 정책 합의, 키보드/터치/반응형 QA 통과 |

프레임워크 전면 교체보다 현재 service·lazy route·공통 activity 컴포넌트를 살리는 점진적 분리가 타당하다. 추천 경계는 `features/catalog`, `features/ratings`, `features/activity`, `features/profile`과 `shared/api`, `shared/ui`, `shared/i18n`이다. 새 폴더 구조 자체가 목표가 아니라 **계약 테스트와 같은 변경 단위의 응집**이 목표다.

## 7. 상위 시각 QA 담당자에게 넘길 체크리스트

- 비로그인 상세 진입 → 로그인 → 원래 상세 복귀, 404/403/세션 만료/네트워크 차단.
- Browse 정렬별 요청 파라미터, 연속 스크롤 첫 append 중복, 검색→삭제→정렬 전환 중 늦은 응답.
- 느린 all 피드 요청 중 following/notifications/saved 전환, 오류와 빈 상태 구분.
- Rate 카드: Tab focus가 보이는지, 터치로 평가 가능한지, 반점 선택, 상세 링크와 별 버튼 충돌.
- 모달: 초기/복귀 focus, Escape, background interaction, 저장 중 닫힘, 긴 리뷰/오류 읽힘.
- 프로필 feed와 통계 탭 cold-load 청크/network; 긴 컬렉션 스크롤 이후 DOM/heap.
- 확대 200%, 좁은 viewport의 Browse 표, 토큰 적용 후 computed contrast, reduced-motion 설정.

## 산출물

- 본 보고서: `/tmp/anibite-frontend-audit.md`
- 빌드: `/tmp/anibite-build.log`
- 린트: `/tmp/anibite-lint.log`
- 설치: `/tmp/anibite-install.log`
- npm advisory 원본: `/tmp/anibite-npm-audit.json`
