"""liblouis를 사용한 한국어 -> BRF ASCII 변환"""

import os
import sys

# lib/ DLL 먼저 탐색, louis.py 바인딩도 lib/ 에서 로드
_LIB_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
if os.path.isdir(_LIB_DIR):
    if sys.platform == 'win32':
        os.add_dll_directory(_LIB_DIR)
    if _LIB_DIR not in sys.path:
        sys.path.insert(0, _LIB_DIR)

import louis

# 테이블을 절대경로로 지정
_TABLES_DIR = os.path.join(_LIB_DIR, 'tables')
_TABLE = [os.path.join(_TABLES_DIR, 'ko-g2.ctb')]


def to_braille(text: str) -> str:
    """한국어 -> ASCII 문자열 변환"""
    if not text.strip():
        return ''
    result = louis.translateString(_TABLE, text)

    # 결과가 BRF ASCII인지 검증
    try:
        result.encode('ascii')
    except UnicodeEncodeError as exc:
        raise ValueError(
            f'변환 결과가 BRF ASCII가 아닙니다. 입력: {text!r}, 오류: {exc}'
        ) from exc
    return result