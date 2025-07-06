<div align="center">

# 🐦 Magpie Log Analyzer

![Magpie Logo](resources/magpie.png)

*스마트한 로그 분석 솔루션*

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>



## 📊 프로젝트 소개

웹 서버 로그를 쉽고 빠르게 분석하고, 다양한 시각화와 자동 개선 제안까지 제공하는 대시보드입니다. Flask, Matplotlib, Seaborn 등 최신 기술을 활용해, 로그 파일을 업로드/선택만 하면 트래픽, 엔드포인트, 상태코드, 성능 병목, 특이 패턴 등 다양한 인사이트를 한눈에 확인할 수 있습니다.

---

## 🚀 주요 기능
- **로그 파일 목록 조회 및 선택**
- **키워드(패턴) 검색**
- **시간대별 트래픽 분석** (Line Chart)
- **엔드포인트별 사용 현황/평균 응답시간** (Bar Chart)
- **상태 코드 분포** (Pie Chart)
- **느린 요청/엔드포인트 TOP N**
- **개선 방안 제안**
- **에러 로그 상세 보기** (4xx/5xx 상태코드 클릭 시)
- **모든 분석 결과 표+그래프 시각화**
- **반응형 UI/UX 디자인**

---

## 🎨 UI/UX 특징
- **모던한 파란색 테마**: 하늘색 그라데이션과 진한 파란색 네비게이션
- **반응형 디자인**: 모든 디바이스에서 최적화된 화면
- **야간 모드**: 야간 모드 지원
- **직관적인 통계 카드**: 한눈에 보는 핵심 지표
- **안정적인 그래프 표시**: matplotlib 기반 고품질 시각화
- **브랜드 아이덴티티**: Magpie 로고와 파비콘 통일

---

## ⚙️ 설치 및 실행 방법

1. **의존성 설치**
   ```bash
   python -m pip install -r requirements.txt
   ```
2. **로그 파일 준비**
   - `logs/` 폴더에 분석할 로그 파일들을 넣어주세요
   - **지원 포맷**: 다양한 웹/시스템 로그 포맷을 자동 감지하여 분석합니다.
     - 표준(기본) 포맷, Apache/Nginx 포맷, 단순 포맷, 애플리케이션/시스템 로그 등 혼합 사용 가능
   - 로그 파일은 아래 예시 중 하나 이상의 형식을 따라야 하며, 한 파일에 여러 형식이 섞여 있어도 자동 감지/분석됩니다.
3. **서버 실행**
   ```bash
   python run.py
   ```
4. **웹브라우저에서 접속**
   - [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📁 로그 파일 디렉토리 설정

로그 파일은 기본적으로 프로젝트 루트의 `logs/` 폴더에서 읽어옵니다.

### 기본 설정
```python
# app/views.py 파일의 15번째 줄
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
```

### 다른 디렉토리 사용하기
`app/views.py` 파일에서 `LOG_DIR` 변수를 수정하여 다른 경로를 지정할 수 있습니다:

```python
# 절대 경로 사용
LOG_DIR = '/path/to/your/logs'

# 상대 경로 사용
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'custom_logs')
```

### 자동 디렉토리 생성
- `logs/` 폴더가 존재하지 않으면 자동으로 생성됩니다
- 웹 인터페이스에서 로그 파일 목록을 자동으로 스캔합니다

---

## 📝 로그 파일 포맷 예시

아래와 같은 다양한 로그 포맷을 지원하며, 한 파일에 여러 형식이 섞여 있어도 자동 감지하여 분석합니다.

- **표준 포맷 (기본)**
  ```
  2025-06-03 12:34:56 GET 192.168.0.1 /api/v1/resource 200 123
  날짜 시간 HTTP메소드 IP URL 상태코드 처리시간(ms)
  ```
- **Apache/Nginx 포맷**
  ```
  192.168.1.100 - - [08/Jun/2025:09:00:01 +0900] "GET / HTTP/1.1" 200 1234
  IP - - [일/월/연:시:분:초 +TZ] "메소드 URL HTTP/버전" 상태코드 바이트수
  ```
- **ISO 포맷**
  ```
  2025-06-03T08:12:34.123Z GET /api/login 200 123
  ISO8601타임스탬프 메소드 URL 상태코드 처리시간(ms)
  ```
- **대괄호 포맷**
  ```
  [2025-06-03 08:12:34] GET /api/login 200 123ms
  [날짜 시간] 메소드 URL 상태코드 처리시간(ms)
  ```
- **단순 포맷**
  ```
  08:12:34 GET /api/login 200 123
  시간 메소드 URL 상태코드 처리시간(ms)
  ```
- **애플리케이션 로그 포맷**
  ```
  [INFO] 2025-06-10 09:00:15.123 - Client 10.0.1.45 requested GET /api/v1/dashboard with status 200 (response time: 89ms)
  [레벨] 날짜 시간 - Client IP requested 메소드 URL with status 상태코드 (response time: ms)
  ```
- **시스템 로그/이벤트 포맷**
  ```
  [ERROR] 2025-06-10 09:05:12.890 - Database connection failed: timeout after 30 seconds
  [레벨] 날짜 시간 - 메시지
  ```

> **참고:**
> - 한 로그 파일에 여러 포맷이 섞여 있어도 자동 감지 및 분석이 가능합니다.
> - 에러/경고/시스템 이벤트 로그도 트래픽, 에러 통계, 이상 탐지에 포함됩니다.
> - 테스트용 더미 데이터 생성 시 다양한 포맷을 혼합해도 무방합니다.

---

## 📈 분석/시각화 항목
- **시간대별 트래픽**: 시간별 요청 수 변화 (Line Chart)
- **엔드포인트별 통계**: 호출수, 평균 응답시간 (Bar Chart, 상위 20개)
- **상태코드 분포**: 2xx/4xx/5xx 비율 (Pie Chart)
- **느린 요청/엔드포인트**: TOP N 표
- **이상 탐지/특이 패턴**: 자동 탐지 결과
- **개선 방안 제안**: AI 기반 자동 리포트
- **에러 로그 상세**: 4xx/5xx 상태코드별 상세 로그

---

## 🛠️ 기술스택
- **Backend**: Python 3.x, Flask
- **데이터 시각화**: Matplotlib, Seaborn
- **프론트엔드**: HTML5, Bootstrap 5, JavaScript
- **이미지 처리**: PIL (Pillow)

## 🤖 개발 도구
- **Cursor AI**: 기능 구현, 디버깅, 리팩토링 전반
  - Flask 애플리케이션 구조 설계
  - matplotlib 그래프 생성 및 스타일링
  - HTML/CSS 템플릿 최적화
  - 코드 품질 개선 및 버그 수정
  - UI/UX 디자인 개선 및 색상 테마 적용
  - 그래프 안정성 및 성능 최적화
  - 테스트 코드 작성

---

## 📬 문의
- 깃허브 이슈 또는 이메일로 연락 주세요.


