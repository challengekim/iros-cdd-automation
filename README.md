# IROS 등기부등본 자동화

법인/부동산 **등기부등본**을 자동으로 장바구니에 담고, 결제 후 열람·저장까지 자동화합니다.
IROS(인터넷등기소, https://www.iros.go.kr)에서 제공하는 법인/부동산 등기부등본을 대량으로 발급받을 때 유용합니다.

> **로그인과 결제는 수동입니다.** 인증/카드 정보는 사람이 직접 입력해야 합니다.
> **본 도구는 자동 발급 이외의 기능(결제 자동화 등)을 제공하지 않습니다.**

---

## 5분 퀵스타트

```bash
# 1. 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 2. 설정 파일 준비
cp config.json.example config.json

# 3. 마법사 실행
python3 iros_wizard.py
```

실행하면 메뉴가 뜨고, 원하는 작업(법인/부동산 장바구니·다운로드)을 번호로 고르면 됩니다.

---

## TouchEn nxKey 사전 설치 (중요)

IROS는 보안 프로그램 **TouchEn nxKey**를 요구합니다. 설치되지 않은 채로 스크립트를 실행하면 중간에 설치 페이지가 뜨고, **설치 후 브라우저를 재시작하여 처음부터 다시 실행**해야 합니다.

- 사전 설치: IROS 로그인 페이지 접속 → 안내에 따라 TouchEn nxKey 설치 → PC 재시작
- 본 스크립트는 설치 페이지가 감지되면 자동으로 중단하고 안내 메시지를 출력합니다

---

## 사전 준비 체크리스트

| 항목 | 비고 |
|------|------|
| Chrome / Chromium 설치 | Playwright가 자동 관리 (`playwright install chromium`) |
| TouchEn nxKey 사전 설치 | 위 섹션 참고 — 반드시 **먼저** 설치 |
| iros.go.kr 회원가입 | https://www.iros.go.kr |
| 공동인증서 / 간편인증 | 로그인 시 사용 |
| 카드 | 결제(수동) 시 필요. **한 번에 최대 10건** |
| Python 3.10 이상 | |

---

## 두 가지 워크플로우

### 법인등기부등본

```
1) 상호명/법인등록번호 준비 → 2) 장바구니 → 3) 결제(수동, 10건/회) → 4) 열람·저장
```

- 장바구니: `iros_cart_by_corpnum.py` (법인등록번호 기반, 정확도 높음) 또는 `iros_cart.py` (상호명 기반)
- 열람·저장: `iros_download.py`

### 부동산등기부등본

```
1) 주소/동호수 JSON 준비 → 2) 장바구니 → 3) 결제(수동, 10건/회) → 4) 열람·저장
```

- 장바구니: `iros_cart_realty.py`
- 열람·저장: `iros_download_realty.py`

마법사(`iros_wizard.py`)에서 메뉴로 바로 실행 가능합니다.

---

## 부동산 입력 JSON 포맷

`data/iros_realties.json` (또는 `config.json`의 `realty_list` 경로) — JSON 배열:

```json
[
  {
    "label": "우리집_아파트",
    "address": "서초대로 219",
    "unit": "101동 1203호",
    "building_name": ""
  },
  {
    "label": "상가_건물",
    "address": "세종대로 110",
    "unit": "",
    "building_name": "시청별관"
  },
  {
    "label": "토지",
    "address": "종로 1",
    "unit": "",
    "building_name": ""
  }
]
```

| 필드 | 설명 | 필수 |
|------|------|------|
| `label` | 로그/파일명 식별자 | O |
| `address` | 지번 또는 도로명 주소 | O |
| `unit` | 동/호수 (집합건물) — 권장 | 아파트·오피스텔 등은 사실상 필수 |
| `building_name` | 건물명 | 선택 |

> 집합건물(아파트/오피스텔)인데 동·호수를 비우면 "검색결과가 많아 소재지번 확인이 어려울 수 있습니다" 팝업이 나와서 skip 처리됩니다. 이 경우 **동/호수 또는 건물명을 추가**해서 재실행하세요.

샘플: `data/iros_realties.example.json`

---

## 설정 (config.json)

| 키 | 설명 | 기본값 |
|----|------|--------|
| `companies_list` | 상호명 기반 검색 목록 | `./data/iros_companies.json` |
| `corpnum_list` | 법인등록번호 기반 검색 목록 | `./data/iros_corpnums.json` |
| `realty_list` | 부동산 검색 목록 | `./data/iros_realties.json` |
| `save_dir` | 법인 PDF 저장 경로 | `~/Downloads/등기부등본` |
| `realty_save_dir` | 부동산 PDF 저장 경로 | `~/Downloads/부동산등기부등본` |
| `report_output` | 법인정보 종합 리포트 엑셀 | `./output/법인정보_종합리포트.xlsx` |
| `excel_path` | bizno 조회용 원본 엑셀 | `./data/고객리스트.xlsx` |

---

## 마법사 메뉴

```
[1] 법인등기부등본 — 장바구니 담기
    └ 1-A: 상호명 기반
    └ 1-B: 법인등록번호 기반 (기본 권장)
[2] 법인등기부등본 — 결제 후 열람·저장
[3] 부동산등기부등본 — 장바구니 담기
[4] 부동산등기부등본 — 결제 후 열람·저장
[5] 사업자번호 → 법인정보 조회 (bizno 스크래핑)
[6] 다운로드된 법인등기 PDF → 종합 리포트 엑셀 생성
[q] 종료
```

각 메뉴 선택 시:
- 입력 파일이 없으면 경로/형식을 안내합니다 (부동산은 1건 직접 입력 옵션 제공).
- 브라우저가 뜨면 IROS에 수동 로그인 후 Enter.
- 결제 단계는 결제대상목록이 뜨면 사람이 직접 카드 결제.

---

## OS별 안내

macOS / Linux에서 개발·검증된 스크립트입니다. **Windows에서도 원칙적으로 동작할 것으로 예상**되지만 실제 테스트는 진행되지 않았습니다.

**Windows 실행 시 참고 사항** (미검증):

- Python 3.10+ 설치 후 동일하게 `pip install -r requirements.txt` / `playwright install chromium`
- 명령은 `python3` 대신 `python` 사용 권장
- `~/Downloads/등기부등본`은 Windows에선 `%USERPROFILE%\Downloads\등기부등본`으로 해석되므로 `config.json`에 `C:/Users/.../Downloads/등기부등본`처럼 명시적으로 지정 권장
- **법인정보 PDF 추출(`corp_info_extract.py`)에 필요한 도구**:
  - `pdftotext`: [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) 다운로드 → `bin` 폴더를 PATH에 추가
  - (선택) `tesseract`: [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) — 한국어 언어팩(`kor`) 포함
- 터미널은 **PowerShell** 또는 **Windows Terminal** 권장 (한글 출력)

---

## 고급 사용 (스크립트 직접 실행)

마법사를 거치지 않고 개별 스크립트를 직접 실행할 수 있습니다.

### 법인 장바구니 — 법인등록번호 기반 (권장)

```bash
python3 iros_cart_by_corpnum.py [config.json]
```

입력: `data/iros_corpnums.json` — `{"법인등록번호": "회사명", ...}` 형식.
로그: `logs/cart_corpnum_log.json`

### 법인 장바구니 — 상호명 기반

```bash
python3 iros_cart.py [config.json] [시작인덱스]
```

입력: `data/iros_companies.json` — `["회사A", "회사B"]` 형식.
사명변경/특수문자로 실패 가능 — 실패분은 법인등록번호 기반으로 재시도 권장.

### 법인 열람·저장

```bash
python3 iros_download.py [config.json] [건수]
```

저장: `~/Downloads/등기부등본/회사명.pdf` (파일명은 상호명 매칭).

### 부동산 장바구니

```bash
python3 iros_cart_realty.py [config.json] [시작인덱스]
```

### 부동산 열람·저장

```bash
python3 iros_download_realty.py [config.json] [건수]
```

저장: `~/Downloads/부동산등기부등본/realty_{순번}_{원본파일명}.pdf`

### bizno 스크래핑 (사업자등록번호 → 법인정보)

```bash
python3 bizno_scrape.py [config.json]
```

엑셀에서 사업자등록번호를 읽어 bizno.net에서 회사명/법인등록번호/휴폐업 상태를 조회합니다.
결과: `data/bizno_results.json`, `data/iros_companies.json`

### 법인정보 종합 리포트 생성

```bash
python3 corp_info_report.py [config.json]
```

bizno 결과 + 다운로드 상태 + 등기부등본 PDF 추출 내용을 엑셀로 종합합니다.
PDF 추출은 내부적으로 `corp_info_extract.py`를 사용합니다.

**사전 요구사항**: `pdftotext` (poppler). macOS: `brew install poppler` / Ubuntu: `sudo apt install poppler-utils`. 스캔 이미지 PDF는 자동으로 Tesseract OCR로 fallback — `pip install pytesseract pdf2image` + `brew install tesseract tesseract-lang` (또는 `sudo apt install tesseract-ocr tesseract-ocr-kor`).

---

## 중단 후 재개

모든 스크립트는 로그 파일에 진행 상황을 저장하므로 중단 후 재실행하면 이미 처리된 건을 건너뜁니다.

```bash
python3 iros_cart_by_corpnum.py       # 자동 이어하기
python3 iros_cart.py config.json 50   # 상호명 기반 — 50번부터
python3 iros_download.py 220          # 이미 받은 파일은 건너뜀
```

로그 초기화:

```bash
echo '{"completed":[],"failed":[],"skipped":[]}' > logs/cart_realty_log.json
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 중간에 "보안 프로그램 설치" 페이지 | TouchEn nxKey 미설치 | nxKey 설치 후 브라우저 재시작, 스크립트 재실행 |
| "검색결과가 많아..." 팝업 반복 | 주소만 입력, 동/호수 없음 | 동·호수 또는 건물명 추가 |
| 회사 검색 안됨 | 사명변경/특수문자 | 법인등록번호 기반으로 재시도 |
| 열람 버튼 못 찾음 | 결제 안 됨 | 결제대상목록에서 결제 확인 |
| 브라우저 멈춤 (약 100건마다) | IROS 서버 부하 | 브라우저 닫고 재실행 (이어하기 지원) |
| PermissionError: ~/Downloads | macOS 보안 정책 | 시스템 설정 > 개인정보 보호 > 전체 디스크 접근 허용 |

---

## 파일 구조

```
iros-registry-automation/
├── README.md
├── config.json.example
├── requirements.txt
├── iros_wizard.py                 # 인터랙티브 마법사 (일반 사용자용 진입점)
├── iros_cart.py                   # 법인 장바구니 (상호명 기반)
├── iros_cart_by_corpnum.py        # 법인 장바구니 (법인등록번호 기반, 권장)
├── iros_download.py               # 법인 열람/저장
├── iros_cart_realty.py            # 부동산 장바구니
├── iros_download_realty.py        # 부동산 열람/저장
├── bizno_scrape.py                # 사업자번호 → 법인정보 조회
├── corp_info_extract.py           # 법인등기 PDF 텍스트 추출
├── corp_info_report.py            # 법인정보 종합 리포트 엑셀
├── data/
│   ├── iros_realties.example.json
│   └── ... (개인 데이터, gitignore)
├── logs/                          # 진행 상황 (gitignore)
└── output/                        # 결과물 (gitignore)
```

---

## 주의사항

- `config.json`, `data/`, `logs/`, `output/`는 `.gitignore`에 포함됩니다. 개인 정보는 커밋되지 않습니다.
- IROS 결제는 반드시 사람이 직접 진행합니다. 한 번에 최대 10건.
- bizno.net 과부하 방지를 위해 요청 간 자동 대기합니다 (건당 약 2초).
- GitHub: https://github.com/challengekim/iros-registry-automation
