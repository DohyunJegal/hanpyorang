"""
BRF ASCII → 한국어 역번역

1. G2 규칙 최장 매칭 (ko-g2-rules.cti) — 수축어/음절 디코딩
2. 자모 음절 조합 (ko-chars.cti, 초성/중성/종성 + Unicode 공식)
3. 숫자 지시자(#) 처리
"""

import os
import re
import unicodedata
from functools import lru_cache

_LIB_DIR  = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
_TABLES   = os.path.join(_LIB_DIR, 'tables')

# ─── 숫자 지시자 ───────────────────────────────────────────────────
_NUM_IND = frozenset({3, 4, 5, 6})
_NUM_MAP = {
    frozenset({1}):          '1',
    frozenset({1, 2}):       '2',
    frozenset({1, 4}):       '3',
    frozenset({1, 4, 5}):    '4',
    frozenset({1, 5}):       '5',
    frozenset({1, 2, 4}):    '6',
    frozenset({1, 2, 4, 5}): '7',
    frozenset({1, 2, 5}):    '8',
    frozenset({2, 4}):       '9',
    frozenset({2, 4, 5}):    '0',
}

# ─── 자모 테이블 (ko-chars.cti 기반) ──────────────────────────────
#  초성: U+1100–U+1112
_INITIAL_SINGLE = {
    frozenset({4}):           'ᄀ',
    frozenset({1, 4}):        'ᄂ',
    frozenset({2, 4}):        'ᄃ',
    frozenset({5}):           'ᄅ',
    frozenset({1, 5}):        'ᄆ',
    frozenset({4, 5}):        'ᄇ',
    frozenset({6}):           'ᄉ',
    frozenset({2, 3, 5, 6}):  'ᄋ',
    frozenset({4, 6}):        'ᄌ',
    frozenset({5, 6}):        'ᄎ',
    frozenset({1, 2, 4}):     'ᄏ',
    frozenset({1, 2, 5}):     'ᄐ',
    frozenset({1, 4, 5}):     'ᄑ',
    frozenset({2, 4, 5}):     'ᄒ',
}
# 복합 초성 (첫 셀이 {6})
_INITIAL_DOUBLE = {
    (frozenset({6}), frozenset({4})):        'ᄁ',
    (frozenset({6}), frozenset({2, 4})):     'ᄄ',
    (frozenset({6}), frozenset({4, 5})):     'ᄈ',
    (frozenset({6}), frozenset({6})):        'ᄊ',
    (frozenset({6}), frozenset({4, 6})):     'ᄍ',
}

#  중성: U+1161–U+1175
_VOWEL_SINGLE = {
    frozenset({1, 2, 6}):          'ᅡ',
    frozenset({1, 2, 3, 5}):       'ᅢ',
    frozenset({3, 4, 5}):          'ᅣ',
    frozenset({2, 3, 4}):          'ᅥ',
    frozenset({1, 3, 4, 5}):       'ᅦ',
    frozenset({1, 5, 6}):          'ᅧ',
    frozenset({3, 4}):             'ᅨ',
    frozenset({1, 3, 6}):          'ᅩ',
    frozenset({1, 2, 3, 6}):       'ᅪ',
    frozenset({1, 3, 4, 5, 6}):    'ᅬ',
    frozenset({3, 4, 6}):          'ᅭ',
    frozenset({1, 3, 4}):          'ᅮ',
    frozenset({1, 2, 3, 4}):       'ᅯ',
    frozenset({1, 4, 6}):          'ᅲ',
    frozenset({2, 4, 6}):          'ᅳ',
    frozenset({2, 4, 5, 6}):       'ᅴ',
    frozenset({1, 3, 5}):          'ᅵ',
}
_VOWEL_MULTI = {
    (frozenset({3, 4, 5}),    frozenset({1, 2, 3, 5})): 'ᅤ',
    (frozenset({1, 2, 3, 6}), frozenset({1, 2, 3, 5})): 'ᅫ',
    (frozenset({1, 3, 4}),    frozenset({1, 2, 3, 5})): 'ᅱ',
    (frozenset({1, 2, 3, 4}), frozenset({1, 2, 3, 5})): 'ᅰ',
}

#  종성: U+11A8–U+11C2
_FINAL_SINGLE = {
    frozenset({1}):          'ᆨ',
    frozenset({2, 5}):       'ᆫ',
    frozenset({3, 5}):       'ᆮ',
    frozenset({2}):          'ᆯ',
    frozenset({2, 6}):       'ᆷ',
    frozenset({1, 2}):       'ᆸ',
    frozenset({3}):          'ᆺ',
    frozenset({2, 3, 5, 6}): 'ᆼ',
    frozenset({1, 3}):       'ᆽ',
    frozenset({2, 3}):       'ᆾ',
    frozenset({2, 3, 5}):    'ᆿ',
    frozenset({2, 3, 6}):    'ᇀ',
    frozenset({2, 5, 6}):    'ᇁ',
    frozenset({3, 5, 6}):    'ᇂ',
}
_FINAL_MULTI = {
    (frozenset({1}),    frozenset({1})):         'ᆩ',
    (frozenset({1}),    frozenset({3})):         'ᆪ',
    (frozenset({2, 5}), frozenset({1, 3})):      'ᆬ',
    (frozenset({2, 5}), frozenset({3, 5, 6})):   'ᆭ',
    (frozenset({2}),    frozenset({1})):          'ᆰ',
    (frozenset({2}),    frozenset({2, 6})):       'ᆱ',
    (frozenset({2}),    frozenset({1, 2})):       'ᆲ',
    (frozenset({2}),    frozenset({3})):          'ᆳ',
    (frozenset({2}),    frozenset({2, 3, 6})):    'ᆴ',
    (frozenset({2}),    frozenset({2, 5, 6})):    'ᆵ',
    (frozenset({2}),    frozenset({3, 5, 6})):    'ᆶ',
    (frozenset({1, 2}), frozenset({3})):          'ᆹ',
    (frozenset({3}),    frozenset({3})):          'ᆻ',
}

# Unicode 음절 결합에 쓰이는 순서 인덱스
_INIT_ORD = ['ᄀ','ᄁ','ᄂ','ᄃ','ᄄ','ᄅ','ᄆ','ᄇ','ᄈ','ᄉ','ᄊ','ᄋ','ᄌ','ᄍ','ᄎ','ᄏ','ᄐ','ᄑ','ᄒ']
_VOWEL_ORD = ['ᅡ','ᅢ','ᅣ','ᅤ','ᅥ','ᅦ','ᅧ','ᅨ','ᅩ','ᅪ','ᅫ','ᅬ','ᅭ','ᅮ','ᅯ','ᅰ','ᅱ','ᅲ','ᅳ','ᅴ','ᅵ']
_FINAL_ORD = ['','ᆨ','ᆩ','ᆪ','ᆫ','ᆬ','ᆭ','ᆮ','ᆯ','ᆰ','ᆱ','ᆲ','ᆳ','ᆴ','ᆵ','ᆶ','ᆷ','ᆸ','ᆹ','ᆺ','ᆻ','ᆼ','ᆽ','ᆾ','ᆿ','ᇀ','ᇁ','ᇂ']


def _jamo_to_syllable(init: str, vowel: str, final: str = '') -> str:
    """초성 + 중성 + 종성 → 완성형 Unicode 음절"""
    try:
        ii = _INIT_ORD.index(init)
        vi = _VOWEL_ORD.index(vowel)
        fi = _FINAL_ORD.index(final)
        return chr(0xAC00 + (ii * 21 + vi) * 28 + fi)
    except (ValueError, TypeError):
        return (init or '') + (vowel or '') + (final or '')


@lru_cache(maxsize=1)
def _load_nabcc() -> dict:
    """BRF ASCII → frozenset(점 번호, 6점 이하)"""
    result = {}
    with open(os.path.join(_TABLES, 'text_nabcc.dis'), encoding='utf-8') as f:
        for line in f:
            m = re.match(r'display \\x([0-9a-fA-F]{4})\s+([0-9]+)', line)
            if not m:
                continue
            ch   = chr(int(m.group(1), 16))
            dots = frozenset(int(d) for d in m.group(2) if d.isdigit() and 1 <= int(d) <= 6)
            result[ch] = dots
    result[' '] = frozenset()
    return result


@lru_cache(maxsize=1)
def _load_g2_rules() -> dict:
    """ko-g2-rules.cti → {tuple(frozenset,...): 한국어 문자열}"""
    rules = {}
    path = os.path.join(_TABLES, 'ko-g2-rules.cti')
    if not os.path.isfile(path):
        return rules
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(
                r'(?:noback\s+)?(?:always|sign|word)\s+(\S+)\s+([\d\-]+)\s*(?:#.*)?$',
                line
            )
            if not m:
                continue
            korean = m.group(1)
            if '?' in korean or '�' in korean:
                continue
            try:
                key = tuple(
                    frozenset(int(d) for d in seg if d.isdigit() and 1 <= int(d) <= 6)
                    for seg in m.group(2).split('-')
                )
            except ValueError:
                continue
            if key not in rules:
                rules[key] = unicodedata.normalize('NFC', korean)
    return rules


def _try_jamo(cells: list, i: int) -> tuple:
    """
    cells[i]부터 자모 음절 하나 시도
    음절 문자열, 소비한 셀 수 반환

    ᄋ 초성은 BRF 인코딩에서 생략 -> 중성 셀로 시작하면 ᄋ+중성으로 처리
    """
    cell = cells[i]
    n    = len(cells)

    # 복합 초성 (6-X 패턴)
    init_jamo = None
    init_len  = 0
    if cell == frozenset({6}) and i + 1 < n:
        pair = (cell, cells[i + 1])
        if pair in _INITIAL_DOUBLE:
            init_jamo = _INITIAL_DOUBLE[pair]
            init_len  = 2
    # 단순 초성
    if init_jamo is None and cell in _INITIAL_SINGLE:
        init_jamo = _INITIAL_SINGLE[cell]
        init_len  = 1

    j = i + init_len

    # 중성 매칭 (2셀 > 1셀)
    vowel_jamo = None
    vowel_len  = 0
    if j + 1 < n and (cells[j], cells[j + 1]) in _VOWEL_MULTI:
        vowel_jamo = _VOWEL_MULTI[(cells[j], cells[j + 1])]
        vowel_len  = 2
    elif j < n and cells[j] in _VOWEL_SINGLE:
        vowel_jamo = _VOWEL_SINGLE[cells[j]]
        vowel_len  = 1

    # 초성 없음 + 중성 있음 → ᄋ 초성 묵시적 처리
    if init_jamo is None:
        if vowel_jamo is not None:
            init_jamo = 'ᄋ'  # 중성으로 시작하면 ᄋ 묵시적 처리
        else:
            return '', 0

    if vowel_jamo is None:
        return '', 0  # 초성 뒤 중성 없음 → 자모 음절 x

    j += vowel_len

    # 종성 매칭 (2셀 > 1셀, 단 다음이 초성+중성이면 무시)
    final_jamo = ''
    final_len  = 0

    if j + 1 < n and (cells[j], cells[j + 1]) in _FINAL_MULTI:
        # 2셀 종성 후보
        pair = (cells[j], cells[j + 1])
        # 다음 셀이 중성이면 종성+초성으로 분리 → 1셀만 종성
        final_jamo = _FINAL_MULTI[pair]
        final_len  = 2
    elif j < n and cells[j] in _FINAL_SINGLE:
        c = cells[j]
        # {2356} = ᄋ/ᆼ 중의성: 중성 뒤이므로 ᆼ 종성
        if c == frozenset({2, 3, 5, 6}):
            final_jamo = 'ᆼ'
            final_len  = 1
        elif c not in _INITIAL_SINGLE:
            # 순수 종성
            final_jamo = _FINAL_SINGLE[c]
            final_len  = 1
        else:
            # 초성과 겹치는 셀: 다음이 중성이면 새 음절로 판단 → 종성 없음
            if j + 1 < n and cells[j + 1] in _VOWEL_SINGLE:
                final_jamo = ''
                final_len  = 0
            else:
                final_jamo = _FINAL_SINGLE[c]
                final_len  = 1

    syllable = _jamo_to_syllable(init_jamo, vowel_jamo, final_jamo)
    return syllable, init_len + vowel_len + final_len


def decode(brf: str) -> str:
    """BRF ASCII 문자열 → 한국어"""
    nabcc    = _load_nabcc()
    g2_rules = _load_g2_rules()

    # CR은 제거, LF는 개행 마커(\x00)로 치환해 셀 디코딩에서 제외
    brf = brf.replace('\r', '').replace('\n', '\x00')

    cells = []
    newline_positions = set()
    for idx, ch in enumerate(brf):
        if ch == '\x00':
            newline_positions.add(len(cells))
            cells.append(None)  # 개행 마커
        else:
            cells.append(nabcc.get(ch, frozenset()))
    result    = []
    i         = 0
    in_number = False

    while i < len(cells):
        cell = cells[i]

        # 개행 마커
        if cell is None:
            result.append('\n')
            i += 1
            continue

        # 숫자 지시자
        if cell == _NUM_IND:
            in_number = True
            i += 1
            continue
        if in_number:
            if cell in _NUM_MAP:
                result.append(_NUM_MAP[cell])
                i += 1
                continue
            in_number = False

        # 공백
        if not cell:
            result.append(' ')
            i += 1
            continue

        # 1. G2 규칙 최장 매칭
        matched = False
        for length in range(min(6, len(cells) - i), 0, -1):
            key = tuple(cells[i:i + length])
            if key in g2_rules:
                # G2 수축이 초성(+모음) 패턴이면 자모 우선
                if length == 1 and cell in _INITIAL_SINGLE:
                    nxt = cells[i + 1] if i + 1 < len(cells) else frozenset()
                    nxt2 = cells[i + 2] if i + 2 < len(cells) else frozenset()
                    if nxt in _VOWEL_SINGLE or (nxt, nxt2) in _VOWEL_MULTI:
                        break
                if length == 2 and key[0] in _INITIAL_SINGLE and key[1] in _VOWEL_SINGLE:
                    break
                result.append(g2_rules[key])
                i += length
                matched = True
                break
        if matched:
            continue

        # 특수 ASCII 부호 처리
        if cell == frozenset({3, 6}):   # '-' (BRF 하이픈)
            result.append('-')
            i += 1
            continue

        # 2. 자모 음절 결합
        syllable, consumed = _try_jamo(cells, i)
        if consumed > 0:
            result.append(syllable)
            i += consumed
            continue

        # 3. 알 수 없는 경우
        dots_str = ''.join(str(d) for d in sorted(cell))
        result.append(f'[{dots_str}]')
        i += 1

    return ''.join(result)
