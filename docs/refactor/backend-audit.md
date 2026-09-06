# AniBite 백엔드·데이터·성능·신뢰성 감사

## 범위와 판정 기준
- 대상: `/tmp/anibite-review` 현재 소스. 아래 `파일:행`은 이 디렉터리 기준 상대 경로다.
- 소스와 SQL 정의만 읽었다. 애플리케이션 import/기동, startup, 마이그레이션, 기존 DB 열기, 운영 API 호출, `.env`·인증정보 접근은 하지 않았다. 소스 변경 없음.
- 검증: 테스트 파일 AST 검사 및 캐릭터 평점 함수만 AST로 분리해 가짜 DB에 전달되는 SQL 확인. 실제 DB/네트워크 없이 수행했다. 운영 노출 여부·데이터 손상 건수·지연 시간은 측정하지 않았다.
- P0: 공개 서비스 배포 전 차단. P1: 다음 기능/리팩터링 배포 전 수정. P2: 측정과 함께 단계적 개선.

## 핵심 발견

### B01 · P0 · 인증 없는 관리 API가 개인정보 조회와 데이터 변경을 제공
**확인된 근거:** `backend/api/admin.py:5-12`에는 인증 dependency 없는 router와 `/verify-all-users` POST가 있고 `:27-36`에서 전체 미인증 계정을 인증 처리한다. `/users-status`는 `:57-58`, `:78-98`에서 이메일 포함 사용자 샘플을 반환한다. `/add-activities-metadata`는 `:149-159`에서 DDL을 실행한다. `backend/main.py:461-464`는 관리·디버그 router를 환경 조건/추가 dependency 없이 등록한다.
**영향:** 이 앱의 관리 경로에 접근 가능한 호출자는 로그인 없이 인증 상태를 변경하거나 이메일을 조회할 수 있다. 외부 gateway가 막는지는 미확인이며 실제 공격/유출이 발생했다고 단정하지 않는다.
**조치:** 임시 migration/debug router를 공개 앱에서 제거하고 운영 작업은 별도 승인 CLI/job으로 이동. 필요한 관리 API에는 중앙 role dependency와 감사 로그, negative authorization 테스트 적용. `admin_editor.py:33-37`의 username 문자열 기반 관리자 판정도 불변 사용자 ID/role로 교체한다.

### B02 · P1 · 비밀키 누락을 허용하고 이메일 인증 정책이 실제로 강제되지 않음
**근거:** `backend/config.py:25-28`은 JWT 키 미설정 시 공개된 기본 문자열로 HS256 토큰을 발급하고 7일 유효기간을 사용한다. `backend/api/admin_fix.py:37-47`도 관리 키 기본값을 허용한다. `backend/services/auth_service.py:135-146`은 인증 여부 검사를 주석 처리하고 토큰을 발급한다. `backend/main.py:173-180`은 매 기동에 `verify_existing_users()`를 호출하고, `backend/scripts/verify_existing_users.py:34-44`는 가입 시점 제한 없이 미인증 계정을 모두 인증한다.
**영향:** 키가 미설정된 배포는 토큰/관리 요청 위조 위험(P0 승격 조건). 현재 환경의 키 설정은 확인하지 않았다. 이메일 인증은 API 설명과 달리 로그인 보안 경계로 동작하지 않는다.
**조치:** 프로덕션에서는 비밀키 누락/기본값이면 시작 실패. 키 교체와 기존 토큰 폐기 계획 마련. 이메일 인증의 제품 정책부터 확정하고 일회성 이전 대상만 migration version/가입 cutoff로 한정한다. 이미 자동 인증된 계정을 근거 없이 일괄 미인증으로 되돌리지 않는다.

### B03 · P1 · Google 계정 연동의 검증 누락과 OAuth 계정 비밀번호 로그인 오류
**근거:** `backend/services/google_oauth_service.py:44-59`는 `email_verified`를 읽지만 거부 조건에는 이메일 존재만 있다. `:121-149`는 이메일 일치만으로 기존 계정에 Google ID를 연결하고 인증 완료로 바꾼다. `:193-200`은 신규 OAuth 계정의 `password_hash`를 NULL로 저장한다. 반면 `backend/services/auth_service.py:126-133`은 NULL 검사 없이 `verify_password()`를 호출하고 `backend/utils/security.py:21-25`는 해시 값에 `.encode()`를 실행한다.
**영향:** 미검증 이메일 자동 연동 방어가 없고, OAuth-only 계정에 일반 비밀번호 로그인을 시도하면 제어된 401 대신 NULL 처리 오류 경로가 있다. 실제 Google token으로 계정 탈취가 가능한 조건까지 재현한 것은 아니다.
**조치:** 검증된 이메일만 허용하고 기존 계정 연결은 재인증/명시적 동의 정책 적용. OAuth-only 계정 로그인은 일반화된 인증 실패/올바른 로그인 방법 안내로 처리. 신규 계정·통계 생성도 하나의 transaction으로 묶는다.

### B04 · P1 · 평점 수정이 activity ID를 보존하지 않아 소셜 연결을 끊을 수 있음
**근거:** `backend/services/rating_service.py:35-44`와 `backend/services/character_service.py:185-194`는 기존 평점 activity를 먼저 삭제한다. `backend/scripts/fix_railway_triggers.py:83-93`의 update trigger는 ID 없는 `INSERT OR REPLACE`를 사용한다. 좋아요는 `backend/services/activity_service.py:489-513`, 댓글은 `:575-583`에서 `activity_id`를 저장/조회한다. `backend/database.py:17-32,49-67`은 각 helper 호출에 별도 연결과 commit을 사용하며 `foreign_keys=ON` 설정은 없다.
**영향:** 동일 작품의 별점만 수정해도 activity ID 안정성이 보장되지 않는다. 기존 좋아요·댓글·북마크·알림의 참조 유지가 위험하며, 중간 오류 시 원본 평점과 activity 상태가 분리된다. 실제 orphan 수나 현재 배포의 추가 trigger 효과는 DB를 열지 않아 미확인이다.
**조치:** activity ID를 유지하는 UPSERT `ON CONFLICT ... DO UPDATE`와 요청 단위 transaction을 채택. 원본 평점/리뷰가 진실의 원천인지 activity가 원천인지 확정하고 동기화 주체를 service 또는 trigger 한 곳으로 제한. 기존 ID를 재생성하기 전에 모든 참조 관계를 매핑한다.

### B05 · P1 · 캐릭터 평점 상태 전환 시 기존 별점이 지워지지 않음
**근거:** `backend/api/character_ratings.py:59-66`은 `WANT_TO_KNOW`/`NOT_INTERESTED`에 `rating=None`을 전달하지만 `backend/services/character_service.py:199-223`은 `rating is not None`일 때만 rating 컬럼을 UPDATE한다. 따라서 기존 RATED 별점이 그대로 남고 status만 바뀐다. API 모델 `backend/api/character_ratings.py:21-24`는 status를 enum이 아닌 자유 문자열로 받고 RATED에서 rating 필수 조건도 없다.
**격리 검증 결과:** 기존 `{rating: 4.5, status: RATED}`를 가정한 fake DB에서 `(rating=None, status=WANT_TO_KNOW)` 호출 시 실제 생성 SQL은 `UPDATE character_ratings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND character_id = ?`였으며 rating 할당이 없었다. DB에는 실행하지 않았다.
**조치:** 필드 미전달과 명시적 NULL을 구분하고 상태 전이표를 적용. `RATED => 유효한 0.5 단위 별점`, `기타 허용 상태 => NULL`을 API 및 DB CHECK로 검증. 기존 모순 레코드는 승인된 migration에서 정리한다.

### B06 · P1 · 평점 동기화 trigger의 user_stats JOIN 조건이 잘못됨
**근거:** `backend/scripts/fix_railway_triggers.py:72-76,112-116`은 `LEFT JOIN user_stats us ON u.id = NEW.user_id`를 사용한다. 오른쪽 테이블 `us`의 키와 연결하지 않고 바로 다음 WHERE도 `u.id = NEW.user_id`다.
**영향:** 해당 사용자가 매칭되면 user_stats의 각 행이 JOIN 후보가 되어 다른 사용자의 점수로 반복 INSERT/REPLACE할 수 있다. 사용자 수에 비례하는 불필요한 write와 잘못된 denormalized 점수가 가능한 코드다. 활동 조회의 `COALESCE(us.otaku_score, a.otaku_score, 0)` (`backend/services/activity_service.py:95`)가 일부 표시 오류를 가릴 수 있지만 write 증폭을 해결하지는 않는다.
**조치:** `us.user_id = u.id`로 교정하는 versioned migration을 만들고, 서로 다른 통계를 가진 여러 사용자의 단일 평가에 activity가 정확히 하나 갱신되는 테스트 추가. 본 감사에서는 trigger 설치나 실행을 하지 않았다.

### B07 · P1 · 통합 API와 구 API가 아직 서로 다른 댓글/리뷰 원천 사용
**근거:** `backend/services/activity_comment_service.py:58-91,123-158`은 리뷰가 존재하면 `review_comments`만 반환한다. 없으면 `:190-214`에서 `activity_comments`를 조회한다. 새 통합 API는 `backend/services/activity_service.py:517-535`에서 `activity_comments`만 조회하고 `:149-153`에서도 그 테이블만 집계한다. 리뷰 수정은 `:409-421`에서 activity를 갱신하고 user_post에 한해 원본을 갱신하므로 anime/character 원본 리뷰에 반영하지 않는다. 반면 평점 trigger는 `backend/scripts/fix_railway_triggers.py:106-115`에서 `user_reviews` 내용을 다시 읽는다.
**영향:** 같은 대상이라도 API/리뷰 존재 여부에 따라 댓글 목록/수가 달라질 수 있고, 통합 API로 수정한 리뷰가 후속 평점 변경에 구 원본으로 덮일 수 있다. 실제 프론트엔드의 모든 호출 경로는 별도 frontend 감사와 연결해야 한다.
**조치:** 구 API를 canonical 서비스의 호환 adapter로 전환. 댓글 ID는 테이블별 충돌 가능성을 고려해 `(legacy_table, legacy_id) -> canonical_id` 매핑을 유지하고 parent/likes/notification까지 함께 이관한다.

### B08 · P1 · 댓글 parent 소속/깊이 미검증 및 비원자적 좋아요 toggle
**근거:** `backend/api/activities.py:94-97`은 댓글 내용/parent를 그대로 받는다. `backend/services/activity_service.py:569-583`은 대상 activity 존재만 확인하고 parent가 같은 activity인지/최대 깊이인지 확인하지 않는다. 답글 조회 `:539-554`는 parent ID만 조건으로 사용한다. 좋아요 `:488-513`은 SELECT 후 INSERT/DELETE 및 알림을 별도 helper로 수행한다.
**영향:** 다른 activity의 댓글에 답글을 붙이는 구조와 조회/알림 대상 불일치가 허용된다. 병렬 좋아요 요청은 중복 삽입 충돌 또는 toggle 의도 불일치가 가능하며 실제 경쟁 오류는 미재현이다.
**조치:** parent의 존재·같은 activity·깊이를 transaction 안에서 검증. 빈/과대 댓글 길이 제한. like/unlike를 idempotent PUT/DELETE로 분리하고 unique constraint/알림을 같은 transaction 또는 outbox로 보호한다.

### B09 · P1 · startup이 파괴적 복구까지 수행하고 실패해도 health는 성공
**근거:** `backend/main.py:50-59,74-83,182-200,202-287`은 schema, 중복 제거, trigger 교체, index, backfill을 시작 시 수행하고 실패를 출력 후 계속한다. `backend/scripts/ensure_unique_constraints.py:128-155`는 중복을 삭제한 뒤 index를 만들고 legacy `ratings` 테이블을 DROP한다. 같은 파일 `:79-96,108-124`의 activity 중복 삭제에는 소셜 참조 재매핑이 없다. `backend/scripts/fix_railway_triggers.py:30-35`는 trigger를 개별 commit으로 제거한다. `backend/main.py:123-128`의 OAuth DB 경로는 `DATABASE_PATH` 설정과 별도다. `/health`는 `backend/main.py:426-429`에서 DB와 무관한 고정 성공 응답이다. `docker-startup.sh:9-18`은 DB 부재에도 빈 파일을 생성한다.
**영향:** 배포/재시작이 데이터 변경 작업이며 중간 실패를 readiness가 잡지 못한다. 복수 worker/중복 배포 시 migration 경쟁은 가능성이며 현재 운영 topology는 미확인이다.
**조치:** migration version·checksum·단일 실행 lock을 가진 별도 release job으로 이동. 앱은 필요한 schema version을 읽어서 readiness를 결정하고 liveness와 분리한다. schema가 없거나 볼륨이 잘못 연결되면 명시적 실패. 모든 migration이 같은 설정 DB 경로를 사용해야 한다.

### B10 · P2 · API 쿼리 비용이 페이지 크기로 제한되지 않음
**근거:** `backend/services/activity_service.py:64-71`은 전체 COUNT, `:144-153`은 전체 좋아요/댓글 GROUP BY 파생 테이블, `:159-161`은 마지막 LIMIT/OFFSET과 timestamp 단독 정렬을 사용한다. `:539-554`는 각 최상위 댓글마다 답글 쿼리(N+1). 구 댓글 서비스도 `backend/services/activity_comment_service.py:95-117,162-184,218-239`에서 같은 패턴이다. `backend/api/character_ratings.py:70-97`의 `/me/all`은 pagination을 받지 않고, `:108-122`는 기본 limit이 None이다. `backend/database.py:20-24,38-47`은 쿼리마다 새 연결/PRAGMA/전체 fetch를 사용한다.
**영향:** 작은 페이지라도 engagement 전체량에 비례한 비용 가능성, 댓글 수에 비례하는 연결/쿼리 증가, 깊은 OFFSET 및 timestamp 동률 페이지의 중복/누락 위험. 실제 slow query/실행계획/지연 개선 배수는 측정하지 않았다.
**조치:** 먼저 activity ID 페이지를 정한 뒤 해당 ID의 engagement만 batch 집계. 댓글 두 번 조회 후 메모리 계층화 또는 제한된 재귀 CTE. `(activity_time,id)` keyset pagination과 해당 filter용 복합 index는 합성 fixture EXPLAIN/벤치마크로 검증 후 추가. 전체 목록은 cursor/summary API로 분리한다. 즉시 DB 교체부터 할 근거는 없다.

### B11 · P2 · async 이미지 API에서 동기 네트워크/DB I/O 실행
**근거:** `backend/routers/image_proxy.py:20-60`은 `async def` 안에서 동기 R2 확인, SQLite, `requests.get(timeout=10)`, upload를 직접 호출한다. staff 경로도 `:81-127`이 동일하다. `backend/main.py:456-457`에서 import 성공 시 활성화한다.
**영향:** 캐시 miss나 외부 지연 시 event loop를 막아 같은 worker의 다른 요청에 영향을 줄 수 있다. 배포 worker 수와 실제 빈도는 미확인이다. DB의 URL을 외부 fetch에 쓰므로 URL 신뢰 경계도 점검 대상이나 임의 사용자 URL SSRF가 가능하다고 확정하지 않는다.
**조치:** 단기적으로 sync route/threadpool 전환, 중기적으로 async HTTP와 백그라운드 캐싱 worker, 동시 다운로드 dedupe, 크기·content-type·host 검증. 외부 저장 실패를 일반 오류 응답과 내부 구조화 로그로 분리한다.

### B12 · P1 · 현재 backend 테스트는 회귀 검증 게이트가 아님
**확인:** backend의 `test*.py` 파일을 AST로 확인한 결과 아래 네 파일 모두 test 함수 0, assert 0이다.
- `backend/test_feed_performance.py:6-16,45-52`: import 시 기본 DB 서비스 실행, 측정값과 무관하게 `<0.01s` 성공 문구 출력.
- `backend/test_feed_activities_optimization.py:6-17,27-46`: 사용자 4 고정, 실행시간 출력 및 구 denormalized 설명.
- `backend/test_character_ratings_performance.py:6-16,28-35`: 사용자 4 고정, 추정 개선 문구.
- `backend/test_user_feed_performance.py:6-16,30-44`: 사용자 4 고정, import 시 실행.
**한계:** 이 네 파일을 실행하지 않았다. `data/test_*.py`는 crawler 관련 파일이 있으며 그것이 전혀 테스트가 아니라고 전체 저장소에 일반화하지 않는다.
**조치:** 기본/운영 DB를 절대 열지 않는 dependency override/격리 fixture 기반 pytest 구축. import 시 I/O 제거. 권한 부정 테스트, 평점 상태 전이, activity ID/소셜 유지, 실패 rollback, OAuth-only 로그인, parent 교차 참조, concurrent like, migration 재실행/실패 복구를 release gate로 둔다.

## 기존 REFACTORING_PLAN.md와 현재 차이
- 문서 `REFACTORING_PLAN.md:497-511`의 activities 생성/API 구현은 아직 미완료 체크박스지만 실제 `backend/api/activities.py:119-154`, `backend/main.py:437`에 통합 API가 존재한다. 이를 처음부터 다시 만들 계획은 부정확하다.
- 문서 `:65-108,154-163`은 denormalized 통합 및 원본 리뷰 제거를 제안하지만 현재 `backend/services/activity_service.py:97-140`은 작품/캐릭터 JOIN 정규화가 이미 일부 적용되어 있다. 반면 사용자 정보와 대표 anime 일부는 activity 값에 의존한다(`:92-95,123-127`).
- 남은 핵심은 **새 테이블 도입이 아니라 원천/쓰기 경로/ID 참조의 일관성 확립**이다. 구 댓글 테이블을 실제로 사용하는 코드가 남아 있으므로 문서 체크박스만 보고 DROP하면 안 된다.

## 마이그레이션·롤아웃 실행 계획 (이번 감사에서는 실행하지 않음)

### 0. 긴급 차단과 정책 확정
1. 공개 admin/debug/migration 경로 제거 또는 중앙 deny-by-default 적용. 권한 없는 요청 401/403과 DB 무변경을 격리 테스트로 확인.
2. 기본 비밀키 배포 거부, 필요한 토큰 rotation 계획. 이메일 인증과 OAuth 연결 정책 합의.
3. 자동 verify/backfill/destructive startup 중단. 이미 필요한 schema가 있는지 승인된 staging에서 검증 후 배포하며, 단순히 startup 코드를 지워 초기 설치를 깨뜨리지 않는다.

### 1. 재현 가능한 안전 기반
1. 운영 데이터 대신 합성/명시적으로 승인된 비식별 fixture로 테스트 DB 생성. empty/이전/현재 schema 각각의 version contract와 expected trigger 정의 확보.
2. 사용자 두 명 이상, 작품/캐릭터/평점/리뷰/좋아요/댓글/답글/북마크/알림이 연결된 fixture 및 동시 수정 fixture 작성.
3. 운영 작업 담당자가 SQLite backup API 등 일관된 snapshot으로 백업하고 별도 환경 복원을 검증한다. WAL 사용 중 DB 파일 하나만 복사하는 방식은 피한다. 본 감사는 운영 백업에 접근하지 않았다.

### 2. 확장 단계: 계약과 transaction 먼저
1. 원본 평점/리뷰 + canonical activity projection 등의 모델을 확정하고 모든 write 경로를 단일 command 서비스로 유도. 원본 유지/제거 결정은 API 소비자 목록으로 근거화.
2. ID-preserving UPSERT, 상태 CHECK/enum, 요청 transaction, FK enforcement를 도입한다. FK 활성화 전 orphan inventory/정리 정책이 필요하며 바로 켜지 않는다.
3. trigger JOIN 교정 및 중복 동기화 제거를 versioned migration으로 관리. 참조 데이터는 삭제 대신 mapping/격리한다. migration 실패는 rollback 및 release 실패로 처리.
4. `(old_table,old_id)->new_id` 매핑을 보존하며 likes/comments/parents/bookmarks/notifications를 이관한다. 평점 변경 시 기존 activity ID는 유지한다.

### 3. 그림자 비교와 단계 배포
1. staging에서 구 API와 새 adapter 응답을 비교: 사용자/항목별 평점 상태, 리뷰 내용, 활동 수, 좋아요 수, 댓글 계층, 소유권, bookmark/notification 링크. 단순 행 총계 일치만으로 완료하지 않는다.
2. 한 요청 경로 또는 일부 사용자부터 feature flag로 read 전환. 불필요한 병렬 dual-write 대신 단일 canonical write와 구 API adapter를 선호한다.
3. 관찰 지표: API 오류율, DB locked/busy, transaction rollback, 쿼리 수, p50/p95, event-loop 지연, orphan/duplicate 검사, 인증 거부/관리 접근 로그. 기준선은 실제 계측 후 정하며 본 보고서에 가상의 목표 달성률은 없다.
4. 댓글 pagination, feed page-first 집계, index 최적화는 정확성 gate 통과 후 독립 flag로 배포한다.

### 4. 롤백과 축소 단계
- 읽기 전환은 flag로 즉시 되돌리되, 새 write 형식과 구 reader 호환성을 먼저 확보한다.
- schema는 expand/contract 방식으로 구 컬럼·테이블과 ID mapping을 관찰 기간 동안 유지. 참조 및 소비자 제거 확인 전 DROP 금지.
- migration 도중 실패하면 transaction rollback. 이미 새 쓰기가 시작된 후 오래된 snapshot으로 단순 복원하면 최신 사용자 쓰기를 잃으므로 쓰기 중단·변경분 보존/재적용 절차를 별도 승인한다.
- 최종 종료 기준: 권한 negative 테스트, 상태 전이/ID 보존/소셜 링크/동시성 테스트 통과; migration 두 번째 실행 무변경; 실패 후 복구 검증; readiness가 schema/DB 실패를 정확히 반영; old API 소비가 없어야 한다.

## 미확인 사항
운영 gateway의 경로 차단, 실제 키 설정, 운영 DB schema/trigger/index, 데이터 손상 건수, 실 사용자별 댓글 분기, 트래픽/latency, worker topology는 확인하지 않았다. 위 위험을 운영 사고가 이미 발생한 사실로 해석하면 안 된다.
