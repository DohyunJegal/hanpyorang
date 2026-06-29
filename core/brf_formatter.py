"""BRF 파일 구성"""

_MARGIN = 24   # 좌측 공백 칸 수
_HEAD_W = 22   # 선거명, 선거구, 하단멘트 최대 칸 수
_CAND_W = 18   # 후보자 최대 칸 수
_LINE_W = 46   # 전체 줄 길이

_FOOTER_LINES = ['투표보조용구', '선거관리위원회']


def make_default_rows(num_candidates: int) -> list[str]:
    """후보자 수에 맞는 기본 행 목록 생성"""
    rows = ['공백', '선거명', '선거구', '공백']
    for i in range(1, num_candidates + 1):
        rows.append(f'후보자{i}')
        if i < num_candidates:
            rows.append('공백')
    target = 13 if num_candidates <= 4 else 22
    while len(rows) < target:
        rows.append('공백')
    rows.append('하단멘트')
    return rows


def format_brf(
    title: str,
    district: str,
    candidates: list,
    footer_braille: list,
    layout: dict | None = None,
) -> str:
    """
    layout = {'rows': ['공백', '선거명', '선거구', '후보자1', ..., '하단멘트']}
    layout이 없으면 기본 형식 사용
    """
    row_defs = (layout or {}).get('rows') or make_default_rows(len(candidates))

    lines = []
    for token in row_defs:
        if token == '공백':
            lines.append('')
        elif token == '선거명':
            lines.append(_center(title))
        elif token == '선거구':
            lines.append(_center(district) if district else '')
        elif token == '하단멘트':
            for ft in footer_braille:
                lines.append(_center(ft))
        elif token.startswith('후보자'):
            n = _parse_n(token, '후보자')
            if n is not None and 1 <= n <= len(candidates):
                c = candidates[n - 1]
                lines.append(_right(c['text']))
            else:
                lines.append('')
        else:
            lines.append('')

    return '\r\n'.join(l.rstrip() for l in lines) + '\r\n'


def _parse_n(token: str, prefix: str) -> int | None:
    try:
        return int(token[len(prefix):])
    except ValueError:
        return None


def _center(text: str) -> str:
    if len(text) > _HEAD_W:
        text = text[:_HEAD_W]
    pad = (_HEAD_W - len(text)) // 2
    return (' ' * _MARGIN + ' ' * pad + text).ljust(_LINE_W)


def _right(text: str) -> str:
    if len(text) > _CAND_W:
        text = text[:_CAND_W]
    pad = _CAND_W - len(text)
    return (' ' * _MARGIN + ' ' * pad + text).ljust(_LINE_W)
