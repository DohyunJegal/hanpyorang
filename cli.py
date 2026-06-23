"""
한표랑 CLI

실행방법:
    python cli.py

    python cli.py [pdf경로]
"""

import importlib
import os
import re
import subprocess
import sys
from datetime import date


_LIB_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'lib'))
if os.path.isdir(_LIB_DIR) and _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)


# 라이브러리 설치
def _ensure_deps() -> None:
    deps = [
        ('pypdf', 'pypdf'),
    ]
    installed_any = False
    for mod_name, pkg_name in deps:
        try:
            __import__(mod_name)
        except ImportError:
            print(f'[한표랑] {pkg_name} 설치 중...', flush=True)
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', pkg_name]
            )
            print(f'[한표랑] {pkg_name} 설치 완료')
            installed_any = True
    if installed_any:
        importlib.invalidate_caches()


_ensure_deps()

from core.pdf_extractor import extract_ballot
from core.braille_converter import to_braille
from core.brf_formatter import format_brf


def _brf_number(num_str: str) -> str:
    """'2-가' 같은 기호 번호를 BRF 숫자 표기로 변환"""
    _DIGIT = {'0':'j','1':'a','2':'b','3':'c','4':'d','5':'e','6':'f','7':'g','8':'h','9':'i'}
    result = '#'
    for ch in str(num_str):
        if ch in _DIGIT:
            result += _DIGIT[ch]
        elif ch == '-':
            result += '-'
        else:
            result += to_braille(ch)  # 한글 접미사
    return result


def _make_filename(title: str, district: str) -> str:
    """{선거종류}_{선거구}_{날짜}.brf 형식으로 파일 이름 지정"""
    today = date.today().strftime('%Y%m%d')
    t = re.sub(r'[\s/\\:*?"<>|]', '', title)[:10]
    d = re.sub(r'[\s/\\:*?"<>|]', '', district)[:8]
    prefix = f'{t}_{d}' if t or d else '투표용지'
    return f'{prefix}_{today}.brf'


def main() -> None:
    if len(sys.argv) >= 2:
        pdf_path = sys.argv[1]
    else:
        while True:
            pdf_path = input('\nPDF 파일 경로: ').strip().strip('"')
            if not pdf_path:
                print('경로를 입력해주세요.')
                continue
            if not os.path.isfile(pdf_path):
                print(f'해당 파일을 찾을 수 없습니다.')
                continue
            break

    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'output'

    if not os.path.isfile(pdf_path):
        print(f'파일을 찾을 수 없습니다: {pdf_path}')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 1. PDF 텍스트 추출
    print(f'\n텍스트를 추출합니다...')
    ballot = extract_ballot(pdf_path)
    if not ballot['candidates']:
        print('후보자를 찾지 못했습니다. PDF를 확인해주세요.')

    # 2. 점자 변환
    print('점자 변환 중...')
    brf_title = to_braille(ballot['title'])
    brf_district = to_braille(ballot['district'])
    brf_cands = [
        {'number': _brf_number(c['number']), 'name_brf': to_braille(c['name'])}
        for c in ballot['candidates']
    ]
    from core.brf_formatter import _FOOTER_LINES
    brf_footer = [to_braille(f) for f in _FOOTER_LINES]

    # 3. BRF 레이아웃 적용
    print('BRF 레이아웃 적용 중...')
    content = format_brf(brf_title, brf_district, brf_cands, brf_footer, layout=None)

    # 4. 파일 저장
    fname = _make_filename(ballot['title'], ballot['district'])
    out_path = os.path.join(output_dir, fname)
    with open(out_path, 'wb') as f:
        f.write(content.encode('ascii', errors='replace'))

    print(f'\n변환 완료: {out_path}\n')


if __name__ == '__main__':
    main()