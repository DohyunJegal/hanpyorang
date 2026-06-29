"""
한표랑 GUI

실행방법:
    python gui.py

패키징:
    pyinstaller gui.spec
"""

import os
import sys

# lib/ 경로 설정
_ROOT = os.path.dirname(__file__)
_LIB_DIR = os.path.join(_ROOT, 'lib')
if os.path.isdir(_LIB_DIR):
    if sys.platform == 'win32':
        os.add_dll_directory(os.path.abspath(_LIB_DIR))
    if _LIB_DIR not in sys.path:
        sys.path.insert(0, _LIB_DIR)


def resource(rel: str) -> str:
    """PyInstaller 패키지 내부 경로 해석"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(_ROOT, rel)


if __name__ == '__main__':
    import webview
    from gui.api import Api

    api = Api()
    window = webview.create_window(
        title='한표랑',
        url=resource('gui/ui/index.html'),
        js_api=api,
        width=1280,
        height=720,
        min_size=(860, 560),
        background_color='#f0f4f8',
    )
    debug = not getattr(sys, 'frozen', False)
    webview.start(debug=debug)
