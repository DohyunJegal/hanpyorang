"""BRF 파일 구성"""

_MARGIN = 24    # 좌측 여백
_HEAD_W = 22    # 헤더/푸터 최대 칸 수 (25~46)
_CAND_W = 18    # 후보자 최대 칸 수 (25~42)
_LINE_W = 46    # 전체 라인

# 점자 숫자 표기용 자릿수(a=1, b=2, ...)
_BRAILLE_DIGIT = {
    '0': 'j', '1': 'a', '2': 'b', '3': 'c', '4': 'd',
    '5': 'e', '6': 'f', '7': 'g', '8': 'h', '9': 'i',
}


def format_brf(
    title: str,
    district: str,
    candidates: list,
    footer: list,
) -> str:
    """
    BRF 점자 문자열 배치

    Args:
        title: 선거명 (BRF 점자 문자열)
        district: 선거구 (BRF 점자 문자열)
        candidates: 후보자 [{'number': int, 'name_brf': str}, ...]
        footer: 문구 [BRF 점자 문자열, ...]
    """
    rows = []

    # 헤더
    rows.append('')
    rows.append(_center(title, _HEAD_W))
    rows.append(_center(district, _HEAD_W))
    rows.append('')

    # 후보자
    for i, cand in enumerate(candidates):
        num_str = cand['number']
        content = f"{num_str} {cand['name_brf']}"
        rows.append(_right(content, _CAND_W))
        if i < len(candidates) - 1:
            rows.append('')

    # 푸터
    # ~4명 → 14-15번째 줄
    # 5명~ → 23-24번째 줄
    target = 13 if len(candidates) <= 4 else 22
    while len(rows) < target:
        rows.append('')

    for line in footer:
        rows.append(_center(line, _HEAD_W))

    return '\r\n'.join(rows) + '\r\n'


def _center(text: str, width: int) -> str:
    """text를 width 칸 안에서 가운데 정렬, 전체 46칸으로 패딩"""
    if len(text) > width:
        text = text[:width]
    pad = (width - len(text)) // 2
    return (' ' * _MARGIN + ' ' * pad + text).ljust(_LINE_W)


def _right(text: str, width: int) -> str:
    """text를 width 칸 안에서 오른쪽 정렬, 전체 46칸으로 패딩"""
    if len(text) > width:
        text = text[:width]
    pad = width - len(text)
    return (' ' * _MARGIN + ' ' * pad + text).ljust(_LINE_W)


def _num_to_brf(n) -> str:
    """기호 번호를 BRF 점자 숫자 표기로 변환 ('2-가' 형태 포함)"""
    s = str(n)
    result = '#'
    for ch in s:
        if ch in _BRAILLE_DIGIT:
            result += _BRAILLE_DIGIT[ch]
        elif ch == '-':
            result += '-'
        else:
            # 가나다 등 한글 접미사는 점자 변환 필요 — caller에서 처리
            result += ch
    return result