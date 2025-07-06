
## 테스트 구조

### 1. `test_utils.py`
**유틸리티 함수 테스트**
- 로그 라인 파싱 테스트
- 로그 형식 감지 테스트
- 로그 형식 변환 테스트
- 에러 처리 테스트

### 2. `test_views.py`
**Flask 뷰 함수 테스트**
- 라우트 접근 테스트
- 로그 분석 기능 테스트
- 그래프 생성 기능 테스트
- 에러 페이지 테스트

### 3. `test_integration.py`
**통합 테스트**
- 전체 워크플로우 테스트
- 성능 테스트
- 동시 요청 테스트
- 엣지 케이스 테스트

## 테스트 실행 방법

### pytest 사용 (권장)
```bash
# 모든 테스트 실행
pytest tests/

# 특정 테스트 파일 실행
pytest tests/test_utils.py

# 특정 테스트 함수 실행
pytest tests/test_utils.py::test_parse_log_line

# 상세한 출력과 함께 실행
pytest -v tests/

# 실패한 테스트만 재실행
pytest --lf tests/
```

### Python 직접 실행
```bash
# 개별 테스트 파일 실행
python -m pytest tests/test_utils.py
python -m pytest tests/test_views.py
python -m pytest tests/test_integration.py
```

## 테스트 스타일

### pytest 함수 기반 테스트
- `unittest` 클래스 기반에서 `pytest` 함수 기반으로 변환
- `@pytest.fixture` 데코레이터로 테스트 데이터 관리
- `assert` 문을 사용한 간결한 검증

### 예시 코드
```python
def test_parse_log_line():
    """로그 라인 파싱 테스트"""
    line = "2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100"
    result = parse_log_line(line)
    assert result is not None
    assert result['method'] == 'GET'
    assert result['status'] == '200'
```

## 테스트 커버리지

### 현재 테스트 범위
- ✅ 로그 파싱 기능
- ✅ 로그 형식 감지
- ✅ 로그 형식 변환
- ✅ Flask 라우트
- ✅ 웹 인터페이스
- ✅ 그래프 생성
- ✅ 에러 처리
- ✅ 성능 테스트
- ✅ 엣지 케이스

### 추가 예정 테스트
- [ ] 데이터베이스 연동 테스트
- [ ] API 엔드포인트 테스트
- [ ] 보안 테스트
- [ ] 브라우저 자동화 테스트

## 테스트 데이터

### 로그 파일 형식
테스트에서는 다양한 형식의 로그 파일을 사용합니다:

1. **표준 형식**
   ```
   2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100
   ```

2. **ISO 형식**
   ```
   2025-06-03T08:01:00.123Z POST /api/login 201 150
   ```

3. **애플리케이션 로그 형식**
   ```
   [INFO] 2025-06-03 08:02:00.456 - Client 10.0.1.45 requested GET /api/v1/data with status 200 (response time: 80ms)
   ```

4. **시스템 에러 로그 형식**
   ```
   [ERROR] 2025-06-03 08:03:00.789 - SYSTEM: Database connection failed
   ```

## 테스트 환경 설정

### 필요한 패키지
```bash
pip install pytest
pip install pytest-cov  # 커버리지 테스트용
pip install pytest-html  # HTML 리포트용
```

### 환경 변수
```bash
export FLASK_ENV=testing
export LOG_DIR=./logs
```

## 테스트 결과 해석

### 성공적인 테스트
```
test_utils.py::test_parse_log_line PASSED
test_views.py::test_index_route PASSED
test_integration.py::test_full_workflow PASSED
```

### 실패한 테스트
```
test_utils.py::test_invalid_log_format FAILED
    assert result is None
    assert result is not None
```

## 문제 해결

### 일반적인 문제들

1. **Import 오류**
   ```bash
   # 프로젝트 루트에서 실행
   cd /path/to/log-analyzer
   pytest tests/
   ```

2. **Flask 앱 생성 오류**
   ```bash
   # 환경 변수 설정
   export FLASK_APP=run.py
   export FLASK_ENV=testing
   ```

3. **로그 파일 접근 오류**
   ```bash
   # 로그 디렉토리 권한 확인
   chmod 755 logs/
   ```

### 디버깅 팁
- `pytest -s` : 출력 캡처 비활성화
- `pytest -x` : 첫 번째 실패에서 중단
- `pytest --pdb` : 실패 시 디버거 실행

## 성능 테스트

### 대용량 파일 테스트
- 1000개 로그 엔트리 처리
- 1초 이내 처리 시간 요구
- 메모리 사용량 모니터링

### 동시 요청 테스트
- 5개 동시 요청 처리
- 스레드 안전성 검증
- 응답 시간 측정

## 커버리지 리포트

### 커버리지 측정
```bash
pytest --cov=app tests/
```

### HTML 리포트 생성
```bash
pytest --cov=app --cov-report=html tests/
```

## 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [Flask 테스트 가이드](https://flask.palletsprojects.com/en/2.0.x/testing/)
- [Python 테스트 모범 사례](https://realpython.com/python-testing/) 