"""
liblouis ctypes 바인딩 (4바이트 widechar 빌드 대응)

이 DLL은 widechar = uint32 (4바이트) 로 컴파일되어 있어
Windows 기본 c_wchar (UTF-16, 2바이트) 를 쓰면 안 된다.
입출력 버퍼를 c_uint32 배열로 직접 처리한다.
"""

import ctypes
import os
import sys

_dir = os.path.dirname(os.path.abspath(__file__))
_dll_path = os.path.join(_dir, 'liblouis.dll')

if sys.platform == 'win32' and os.path.isdir(_dir):
    os.add_dll_directory(_dir)

_lib = ctypes.CDLL(_dll_path)

# lou_version() -> const char*
_lib.lou_version.restype = ctypes.c_char_p
_lib.lou_version.argtypes = []

# lou_setDataPath(const char*) -> void  (deprecated but harmless)
_lib.lou_setDataPath.restype = None
_lib.lou_setDataPath.argtypes = [ctypes.c_char_p]

# lou_translateString — widechar = uint32
_lib.lou_translateString.restype = ctypes.c_int
_lib.lou_translateString.argtypes = [
    ctypes.c_char_p,                   # tableList
    ctypes.POINTER(ctypes.c_uint32),   # inbuf  (widechar*)
    ctypes.POINTER(ctypes.c_int),      # inlen
    ctypes.POINTER(ctypes.c_uint32),   # outbuf (widechar*)
    ctypes.POINTER(ctypes.c_int),      # outlen
    ctypes.c_char_p,                   # typeform
    ctypes.c_char_p,                   # spacing
    ctypes.c_int,                      # mode
]

# lou_backTranslateString — widechar = uint32
_lib.lou_backTranslateString.restype = ctypes.c_int
_lib.lou_backTranslateString.argtypes = [
    ctypes.c_char_p,                   # tableList
    ctypes.POINTER(ctypes.c_uint32),   # inbuf  (widechar*)
    ctypes.POINTER(ctypes.c_int),      # inlen
    ctypes.POINTER(ctypes.c_uint32),   # outbuf (widechar*)
    ctypes.POINTER(ctypes.c_int),      # outlen
    ctypes.c_char_p,                   # typeform
    ctypes.c_char_p,                   # spacing
    ctypes.c_int,                      # mode
]

# lou_free() -> void
_lib.lou_free.restype = None
_lib.lou_free.argtypes = []

_BUF_SIZE = 4096


def version() -> str:
    return _lib.lou_version().decode('utf-8')


def setDataPath(path: str) -> None:
    _lib.lou_setDataPath(path.encode('utf-8'))


def _table_list(tables) -> bytes:
    if isinstance(tables, (list, tuple)):
        return ','.join(tables).encode('utf-8')
    return tables.encode('utf-8')


def _str_to_widechar(text: str) -> 'ctypes.Array':
    """Python str → uint32 배열 (UTF-32 코드포인트)"""
    arr = (ctypes.c_uint32 * len(text))(*[ord(c) for c in text])
    return arr


def _widechar_to_str(buf, length: int) -> str:
    """uint32 배열 → Python str"""
    return ''.join(chr(buf[i]) for i in range(length))


def backTranslateString(tables, inbuf: str, mode: int = 0) -> str:
    if not inbuf:
        return ''

    table_bytes = _table_list(tables)
    in_arr = _str_to_widechar(inbuf)
    in_len = ctypes.c_int(len(inbuf))

    out_arr = (ctypes.c_uint32 * _BUF_SIZE)()
    out_len = ctypes.c_int(_BUF_SIZE)

    ret = _lib.lou_backTranslateString(
        table_bytes,
        in_arr,
        ctypes.byref(in_len),
        out_arr,
        ctypes.byref(out_len),
        None,
        None,
        mode,
    )
    _lib.lou_free()

    if ret == 0:
        raise RuntimeError(f'liblouis 역번역 실패: {inbuf!r}')

    return _widechar_to_str(out_arr, out_len.value)


def translateString(tables, inbuf: str, mode: int = 0) -> str:
    if not inbuf:
        return ''

    table_bytes = _table_list(tables)
    in_arr = _str_to_widechar(inbuf)
    in_len = ctypes.c_int(len(inbuf))

    out_arr = (ctypes.c_uint32 * _BUF_SIZE)()
    out_len = ctypes.c_int(_BUF_SIZE)

    ret = _lib.lou_translateString(
        table_bytes,
        in_arr,
        ctypes.byref(in_len),
        out_arr,
        ctypes.byref(out_len),
        None,
        None,
        mode,
    )
    _lib.lou_free()

    if ret == 0:
        raise RuntimeError(f'liblouis 번역 실패: {inbuf!r}')

    return _widechar_to_str(out_arr, out_len.value)
