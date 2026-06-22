"""PyWebView용 Python API"""

import os
import sys
import re
import configparser
from datetime import date

# PyInstaller frozen 환경에서는 _MEIPASS, 개발 환경에서는 상위 디렉터리
if getattr(sys, 'frozen', False):
    _ROOT = sys._MEIPASS
else:
    _ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
_LIB_DIR = os.path.join(_ROOT, 'lib')

if os.path.isdir(_LIB_DIR):
    if sys.platform == 'win32':
        os.add_dll_directory(_LIB_DIR)
    if _LIB_DIR not in sys.path:
        sys.path.insert(0, _LIB_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.pdf_extractor import extract_ballot
from core.braille_converter import to_braille
from core.brf_formatter import format_brf, _FOOTER_LINES

# config는 실행 파일 옆에 유지 (frozen 시 _MEIPASS는 읽기 전용 임시 폴더)
if getattr(sys, 'frozen', False):
    _CONFIG_DIR = os.path.join(os.path.dirname(sys.executable), 'config')
else:
    _CONFIG_DIR = os.path.join(_ROOT, 'config')
_LAYOUT_INI = os.path.join(_CONFIG_DIR, 'layouts.ini')
_PARTIES_INI = os.path.join(_CONFIG_DIR, 'parties.ini')

_DIGIT = {'0': 'j', '1': 'a', '2': 'b', '3': 'c', '4': 'd',
          '5': 'e', '6': 'f', '7': 'g', '8': 'h', '9': 'i'}

_DEFAULT_LAYOUT_NAME = '기본'
_DEFAULT_ROWS = ['공백', '선거명', '선거구', '공백',
                 '후보자1', '공백', '후보자2', '공백', '후보자3', '공백', '후보자4',
                 '공백', '공백', '하단멘트']


def _brf_number(num_str: str) -> str:
    result = '#'
    for ch in str(num_str):
        if ch in _DIGIT:
            result += _DIGIT[ch]
        elif ch == '-':
            result += '-'
        else:
            result += to_braille(ch)
    return result


def _make_filename(title: str, district: str) -> str:
    today = date.today().strftime('%Y%m%d')
    t = re.sub(r'[\s/\\:*?"<>|]', '', title)[:10]
    d = re.sub(r'[\s/\\:*?"<>|]', '', district)[:8]
    prefix = f'{t}_{d}' if t or d else '투표용지'
    return f'{prefix}_{today}.brf'


class Api:
    # 파일 다이얼로그
    def open_file_dialog(self):
        import webview
        result = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN, file_types=('PDF 파일 (*.pdf)',))
        return result[0] if result else None

    def open_files_dialog(self):
        import webview
        result = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=True, file_types=('PDF 파일 (*.pdf)',))
        return list(result) if result else []

    def open_folder_dialog(self):
        import webview
        result = webview.windows[0].create_file_dialog(webview.FileDialog.FOLDER)
        return result[0] if result else None

    # PDF 처리
    def extract_pdf(self, path):
        try:
            ballot = extract_ballot(path)
            return {'ok': True, 'data': ballot}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def convert_single(self, ballot_data, output_dir, layout_name=None):
        try:
            os.makedirs(output_dir, exist_ok=True)

            parties = self._load_parties()
            layout = self._get_layout(layout_name)

            title    = ballot_data.get('title', '')
            district = ballot_data.get('district', '')
            candidates = ballot_data.get('candidates', [])

            processed = []
            for c in candidates:
                name = c['name']
                for full, abbr in parties.items():
                    name = name.replace(full, abbr)
                processed.append({'number': c['number'], 'name': name})

            brf_title    = to_braille(title)
            brf_district = to_braille(district)
            brf_cands    = [
                {'number': _brf_number(c['number']), 'name_brf': to_braille(c['name'])}
                for c in processed
            ]
            brf_footer = [to_braille(f) for f in _FOOTER_LINES]

            content = format_brf(brf_title, brf_district, brf_cands, brf_footer, layout)

            fname    = _make_filename(title, district)
            out_path = os.path.join(output_dir, fname)
            with open(out_path, 'wb') as f:
                f.write(content.encode('ascii', errors='replace'))

            return {'ok': True, 'path': out_path}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def convert_batch(self, paths, output_dir, layout_name=None):
        results = []
        for path in paths:
            r = self.extract_pdf(path)
            if not r['ok']:
                results.append({'file': os.path.basename(path), 'ok': False, 'error': r['error']})
                continue
            r2 = self.convert_single(r['data'], output_dir, layout_name)
            results.append({
                'file': os.path.basename(path),
                'ok':   r2['ok'],
                'path': r2.get('path', ''),
                'error': r2.get('error', ''),
            })
        return results

    # 번역
    def translate_to_braille(self, text):
        try:
            return {'ok': True, 'result': to_braille(text)}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def translate_from_braille(self, text):
        try:
            from core.brf_decoder import decode
            return {'ok': True, 'result': decode(text)}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # 레이아웃
    def get_layout_names(self):
        """저장된 레이아웃 이름 목록 반환"""
        layouts = self._load_all_layouts()
        return list(layouts.keys())

    def get_layout(self, name):
        """특정 레이아웃의 rows 반환"""
        return self._get_layout(name)

    def save_layout(self, name, rows):
        """레이아웃 저장"""
        try:
            os.makedirs(_CONFIG_DIR, exist_ok=True)
            layouts = self._load_all_layouts()
            layouts[name] = rows
            self._write_layouts(layouts)
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def delete_layout(self, name):
        if name == _DEFAULT_LAYOUT_NAME:
            return {'ok': False, 'error': '기본 레이아웃은 삭제할 수 없습니다.'}
        try:
            layouts = self._load_all_layouts()
            layouts.pop(name, None)
            self._write_layouts(layouts)
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # 정당 이름
    def get_party_names(self):
        return self._load_parties()

    def save_party_names(self, data):
        try:
            os.makedirs(_CONFIG_DIR, exist_ok=True)
            cfg = configparser.ConfigParser()
            cfg['parties'] = {k: v for k, v in data.items() if k and v}
            with open(_PARTIES_INI, 'w', encoding='utf-8') as f:
                cfg.write(f)
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # 내부 헬퍼
    def _get_layout(self, name):
        if not name or name == _DEFAULT_LAYOUT_NAME:
            return None  # format_brf가 make_default_rows로 후보자 수에 맞게 생성
        if not os.path.isfile(_LAYOUT_INI):
            return None
        layouts = self._load_all_layouts()
        rows = layouts.get(name)
        return {'rows': rows} if rows else None

    def _load_all_layouts(self) -> dict[str, list[str]]:
        if not os.path.isfile(_LAYOUT_INI):
            return {_DEFAULT_LAYOUT_NAME: list(_DEFAULT_ROWS)}
        try:
            cfg = configparser.ConfigParser()
            cfg.read(_LAYOUT_INI, encoding='utf-8')
            result = {}
            for section in cfg.sections():
                raw = cfg[section].get('rows', '')
                result[section] = [t.strip() for t in raw.split(',') if t.strip()]
            return result or {_DEFAULT_LAYOUT_NAME: list(_DEFAULT_ROWS)}
        except Exception:
            return {_DEFAULT_LAYOUT_NAME: list(_DEFAULT_ROWS)}

    def _write_layouts(self, layouts: dict[str, list[str]]):
        cfg = configparser.ConfigParser()
        for name, rows in layouts.items():
            cfg[name] = {'rows': ','.join(rows)}
        with open(_LAYOUT_INI, 'w', encoding='utf-8') as f:
            cfg.write(f)

    def _load_parties(self) -> dict[str, str]:
        if not os.path.isfile(_PARTIES_INI):
            return {}
        try:
            cfg = configparser.ConfigParser()
            cfg.read(_PARTIES_INI, encoding='utf-8')
            return dict(cfg['parties']) if 'parties' in cfg else {}
        except Exception:
            return {}
