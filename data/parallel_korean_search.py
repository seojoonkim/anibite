#!/usr/bin/env python3
"""
병렬 3개 워커로 한국어 이름 검색
중간 저장 및 복구 지원
"""
import sys
import os
import re
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_FILE = os.path.join(DATA_DIR, 'exact_korean_names.json')
PROGRESS_FILE = os.path.join(DATA_DIR, 'search_progress.json')

# 결과 저장용 Lock
save_lock = Lock()


def log(msg):
    print(msg, flush=True)


def search_korean_name(english_name):
    """구글 검색으로 한국어 이름 찾기"""
    query = f"{english_name} 이름"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=ko"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        html = response.text

        # 패턴 1: "English Name (한국어 이름)" 형태
        if english_name.split():
            pattern1 = re.compile(
                re.escape(english_name.split()[0]) + r'[^(]*\(([가-힣]+\s*[가-힣]*)\)',
                re.IGNORECASE
            )
            match = pattern1.search(html)
            if match:
                korean_name = match.group(1).strip()
                if 2 <= len(korean_name.replace(' ', '')) <= 10:
                    return korean_name

        # 패턴 2: 일반적인 괄호 안 한국어 이름 (성 이름 형태)
        pattern2 = r'\(([가-힣]{2,4}\s+[가-힣]{2,6})\)'
        matches = re.findall(pattern2, html)
        if matches:
            for korean_name in matches[:5]:
                exclude_words = ['등장인물', '캐릭터', '애니메이션', '만화', '작품']
                if not any(w in korean_name for w in exclude_words):
                    return korean_name

        # 패턴 3: 붙어있는 한국어 이름
        pattern3 = r'\(([가-힣]{3,8})\)'
        matches = re.findall(pattern3, html)
        if matches:
            for korean_name in matches[:5]:
                exclude_words = ['등장인물', '캐릭터', '애니메이션', '만화', '작품', '시리즈', '주인공']
                if not any(w in korean_name for w in exclude_words):
                    if 3 <= len(korean_name) <= 8:
                        return korean_name

        return None

    except Exception as e:
        return None


def process_character(char, worker_id, matched, processed_ids):
    """단일 캐릭터 처리"""
    char_id = str(char['id'])
    name_full = char['name_full']

    # 이미 처리됨
    if char_id in matched or char_id in processed_ids:
        return None

    korean_name = search_korean_name(name_full)

    # 워커별 딜레이 (차단 방지)
    time.sleep(2)

    return {
        'id': char_id,
        'name': name_full,
        'korean': korean_name,
        'worker': worker_id
    }


def save_results(matched, processed_ids, total, success, fail):
    """결과 저장"""
    with save_lock:
        with open(RESULT_FILE, 'w') as f:
            json.dump(matched, f, ensure_ascii=False, indent=2)

        progress = {
            'processed_ids': list(processed_ids),
            'total_target': total,
            'success': success,
            'fail': fail,
            'matched_count': len(matched),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)


def main():
    log("=" * 60)
    log("병렬 한국어 이름 검색 (3 워커)")
    log("=" * 60)

    # 기존 데이터 로드
    with open(os.path.join(DATA_DIR, 'top2000_characters.json'), 'r') as f:
        all_characters = json.load(f)

    with open(RESULT_FILE, 'r') as f:
        matched = json.load(f)

    # 진행 상황 복구
    processed_ids = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            processed_ids = set(progress.get('processed_ids', []))
            log(f"이전 진행 상황 복구: {len(processed_ids)}개 처리됨")

    matched_ids = set(matched.keys())

    # 아직 처리 안 된 캐릭터
    remaining = [c for c in all_characters
                 if str(c['id']) not in matched_ids and str(c['id']) not in processed_ids]

    log(f"전체: {len(all_characters)}개")
    log(f"매칭 완료: {len(matched)}개")
    log(f"이미 처리: {len(processed_ids)}개")
    log(f"남음: {len(remaining)}개")
    log(f"예상 시간: 약 {len(remaining) * 2 // 3 // 60}분 (병렬 3개)")
    log("=" * 60)

    if not remaining:
        log("모든 캐릭터 처리 완료!")
        return

    success = 0
    fail = 0
    total = len(remaining)

    # 3개 워커로 분할
    chunks = [[], [], []]
    for i, char in enumerate(remaining):
        chunks[i % 3].append((char, i % 3))

    def worker_task(char_worker):
        char, worker_id = char_worker
        return process_character(char, worker_id, matched, processed_ids)

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=3) as executor:
        all_tasks = []
        for chunk in chunks:
            for item in chunk:
                all_tasks.append(item)

        futures = {executor.submit(worker_task, task): task for task in all_tasks}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result is None:
                continue

            char_id = result['id']
            name = result['name']
            korean = result['korean']
            worker = result['worker']

            processed_ids.add(char_id)

            if korean:
                matched[char_id] = korean
                success += 1
                log(f"[{i+1}/{total}] W{worker} ✓ {name} → {korean}")
            else:
                fail += 1
                log(f"[{i+1}/{total}] W{worker} ✗ {name}")

            # 20개마다 저장
            if (success + fail) % 20 == 0:
                save_results(matched, processed_ids, total, success, fail)
                log(f"    💾 중간 저장 (매칭: {len(matched)}개)")

    # 최종 저장
    save_results(matched, processed_ids, total, success, fail)

    log("\n" + "=" * 60)
    log("완료!")
    log(f"성공: {success}개")
    log(f"실패: {fail}개")
    log(f"총 매칭: {len(matched)}개")
    log("=" * 60)


if __name__ == "__main__":
    main()
