# pdf2brf

투표용지 PDF를 시각장애인용 BRF 점자 파일로 변환하는 도구입니다.

## 주요 기능

- **단일 변환** — PDF 파일을 BRF로 변환
- **다중 변환** — 여러 PDF 파일을 한 번에 BRF로 변환
- **번역 / 역번역** — 한국어 - BRF 점자 ASCII 변환 확인
- **레이아웃 편집** — BRF 행의 순서와 종류를 직접 구성하고 저장 가능
- **정당 이름 수정** — 긴 정당 이름은 줄여서 BRF에 표시 가능

## 사용 방법

### 실행

```bash
pip install -r requirements.txt
python gui.py
```

### 빌드 (PyInstaller)

```bash
pip install pyinstaller
pyinstaller gui.spec
```

결과물은 `dist/pdf2brf/` 폴더에 생성됩니다.

### 빌드 후 배포

`pdf2brf.exe`와 `_internal/` 폴더가 `dist/pdf2brf/` 내부에 생성됩니다.

배포 시 `_internal/` 폴더와 `pdf2brf.exe`를 함께 배포해주세요.

> Windows 10 이상에서 실행을 권장합니다. Edge WebView2 런타임이 필요할 수 있습니다.

## 사용 기술

| 항목      | 내용                                                      |
| --------- | --------------------------------------------------------- |
| GUI       | [pywebview](https://pywebview.flowrl.com/) + Tailwind CSS |
| PDF 파싱  | [pdfplumber](https://github.com/jsvine/pdfplumber)        |
| 점자 변환 | [liblouis](https://liblouis.io/) (Korean Grade 2)         |
| 패키징    | PyInstaller                                               |

## 프로젝트 구조

```
pdf2brf/
├── gui.py              # GUI 진입점
├── gui.spec            # PyInstaller 빌드 설정
├── gui/
│   ├── api.py          # pywebview에 사용되는 Python API
│   └── ui/             # 프론트엔드
├── core/
│   ├── pdf_extractor.py        # PDF에서 투표용지 정보 추출
│   ├── braille_converter.py    # 한국어 - BRF 변환
│   ├── brf_formatter.py        # BRF 레이아웃 포매터
│   └── brf_decoder.py          # BRF - 한국어 역번역
├── lib/
│   ├── louis.py        # liblouis ctypes 바인딩
│   ├── liblouis.dll    # liblouis 라이브러리
│   └── tables/         # 점자 변환 테이블
└── config/             # 레이아웃 및 정당 이름 설정값
```

## 라이선스

MIT

## 크레딧

아이콘 제작자: [Freepik](https://www.flaticon.com/authors/freepik) - [Flaticon](https://www.flaticon.com/)
