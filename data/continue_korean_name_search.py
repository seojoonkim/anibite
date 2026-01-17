#!/usr/bin/env python3
"""
구글 검색으로 남은 캐릭터의 한국어 이름 매칭 (이어서 진행)
"""
import sys
import os
import re
import json
import time
import requests

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


def main():
    data_dir = os.path.dirname(os.path.abspath(__file__))

    # 기존 데이터 로드
    with open(os.path.join(data_dir, 'top2000_characters.json'), 'r') as f:
        all_characters = json.load(f)

    with open(os.path.join(data_dir, 'exact_korean_names.json'), 'r') as f:
        matched = json.load(f)

    matched_ids = set(matched.keys())

    # 아직 매칭 안 된 캐릭터
    remaining = [c for c in all_characters if str(c['id']) not in matched_ids]

    log(f"=" * 60)
    log(f"한국어 이름 매칭 이어서 진행")
    log(f"=" * 60)
    log(f"전체: {len(all_characters)}개")
    log(f"완료: {len(matched)}개")
    log(f"남음: {len(remaining)}개")
    log(f"=" * 60)

    success = 0
    fail = 0

    for i, char in enumerate(remaining):
        char_id = str(char['id'])
        name_full = char['name_full']

        korean_name = search_korean_name(name_full)

        if korean_name:
            matched[char_id] = korean_name
            success += 1
            log(f"[{i+1}/{len(remaining)}] ✓ {name_full} → {korean_name}")

            # 10개마다 저장
            if success % 10 == 0:
                with open(os.path.join(data_dir, 'exact_korean_names.json'), 'w') as f:
                    json.dump(matched, f, ensure_ascii=False, indent=2)
        else:
            fail += 1
            log(f"[{i+1}/{len(remaining)}] ✗ {name_full}")

        # 구글 차단 방지
        time.sleep(1.5)

    # 최종 저장
    with open(os.path.join(data_dir, 'exact_korean_names.json'), 'w') as f:
        json.dump(matched, f, ensure_ascii=False, indent=2)

    log(f"\n" + "=" * 60)
    log(f"완료!")
    log(f"성공: {success}개")
    log(f"실패: {fail}개")
    log(f"총 매칭: {len(matched)}개")
    log(f"=" * 60)


if __name__ == "__main__":
    main()
