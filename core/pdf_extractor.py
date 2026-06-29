"""PDF 투표용지에서 텍스트 추출"""

import re


# 노이즈 필터: CMYK 색상 마크, ASCII 특수문자만 있는 줄, 파일 메타데이터
_NOISE_RE = re.compile(
    r'^(C|M|Y|K|CM|MY|CY|CMY|[$.:,]+)$'
    r'|\.pdf\s+\d+\s+\d{4}-\d{2}-\d{2}'
)

# 기호 번호 ("1-가", "1 - 가", "2-나", "5" 등)
_NUM_RE = re.compile(r'^\d{1,2}\s*(-\s*[가-힣])?$')
# 선거명 패턴 (~선거)
_TITLE_RE = re.compile(r'^[가-힣]{2,}선거$')
# 선거구 패턴 (~선거구)
_DISTRICT_RE = re.compile(r'^\[([가-힣]+선거구)\]$')
# 푸터 노이즈
_FOOTER_NOISE_RE = re.compile(r'[가-힣]+\s+[가-힣]+\s*\d|투표보조용구')


def extract_ballot(pdf_path: str) -> dict:
    """
    pdf 내용 추출
    Returns:
        dict:
            title (str): 선거명
            district (str): 선거구
            candidates (list[dict]): [{'number': str, 'name': str}, ...]
            footer (list[str]): 문구
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    raw = reader.pages[0].extract_text() or ''

    lines = [l.strip() for l in raw.splitlines()]
    lines = [l for l in lines if l and not _NOISE_RE.search(l)]
    lines = [l for l in lines if _is_readable(l)]

    if not lines:
        return {'title': '', 'district': '', 'candidates': [], 'footer': []}

    return _parse_lines(lines)


def _is_readable(text: str) -> bool:
    """깨진 문자가 많은 줄 제거"""
    clean = re.sub(r'[가-힣ᄀ-ᇿ㄰-㆏\d\s()\[\]\-+.,]', '', text)
    return len(clean) <= len(text) * 0.3


def _is_num_line(text: str) -> bool:
    return bool(_NUM_RE.match(text))


def _parse_lines(lines: list) -> dict:
    num_indices = [i for i, t in enumerate(lines) if _is_num_line(t)]

    if not num_indices:
        return {'title': '', 'district': lines[0] if lines else '', 'candidates': [], 'footer': []}

    first_num = num_indices[0]
    last_num = num_indices[-1]
    num_count = len(num_indices)

    title = ''
    district = ''
    district_indices = set()
    for i, t in enumerate(lines):
        if not title and _TITLE_RE.match(t):
            title = t
            district_indices.add(i)
        elif m := _DISTRICT_RE.match(t):
            district = m.group(1)
            district_indices.add(i)

    after = [
        t for i, t in enumerate(lines[last_num + 1:], start=last_num + 1)
        if i not in district_indices and not _FOOTER_NOISE_RE.search(t)
    ]

    numbers = [re.sub(r'\s+', '', lines[i]) for i in num_indices]  # "1 - 가" → "1-가"

    parties: list = []
    names: list = []

    if len(after) >= num_count * 2:
        parties = after[:num_count]
        names = after[num_count:num_count * 2]
    elif len(after) >= num_count:
        names = after[:num_count]
    else:
        names = after

    candidates = []
    for i, num in enumerate(numbers):
        party = parties[i] if i < len(parties) else ''
        name = names[i] if i < len(names) else ''
        if party or name:
            candidates.append({'number': num, 'party': party, 'name': name})

    return {
        'title': title,
        'district': district,
        'candidates': candidates,
        'footer': ['투표보조용구', '선거관리위원회'],
    }
