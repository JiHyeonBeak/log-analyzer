#!/usr/bin/env python3
"""
통합 테스트 스위트

이 모듈은 전체 애플리케이션의 통합 테스트를 수행합니다.
- 전체 워크플로우 테스트
- 실제 로그 파일 분석 테스트
- 성능 테스트
"""

import sys
import os
import tempfile
import shutil
import time
import threading

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.utils import parse_log_line, detect_log_format, convert_log_format

# Flask 앱 fixture
def app():
    """Flask 앱 fixture - 테스트용 앱 생성"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['LOG_DIR'] = tempfile.mkdtemp()
    return app

def client(app):
    """테스트 클라이언트 fixture"""
    return app.test_client()

def large_log_file(app):
    """대용량 테스트 로그 파일 fixture"""
    large_log_file = os.path.join(app.config['LOG_DIR'], 'large.log')
    with open(large_log_file, 'w', encoding='utf-8') as f:
        for i in range(1000):  # 1000개 로그 엔트리
            hour = (i % 24)
            minute = (i % 60)
            method = ['GET', 'POST', 'PUT', 'DELETE'][i % 4]
            status = ['200', '201', '404', '500'][i % 4]
            resp_time = 50 + (i % 200)
            f.write(f"2025-06-03 {hour:02d}:{minute:02d}:00 {method} 192.168.1.{i % 255} /api/endpoint{i % 10} {status} {resp_time}\n")
    yield large_log_file
    if os.path.exists(app.config['LOG_DIR']):
        shutil.rmtree(app.config['LOG_DIR'])

# 전체 워크플로우 테스트
def test_full_workflow(client, large_log_file):
    """전체 워크플로우 테스트"""
    # 1. 메인 페이지 접근
    response = client.get('/')
    assert response.status_code == 200
    
    # 2. 분석 페이지 접근
    response = client.get('/analyze')
    assert response.status_code == 200
    
    # 3. 로그 파일 분석
    data = {'logfile': 'large.log'}
    response = client.post('/analyze', data=data)
    assert response.status_code == 200
    assert '분석 결과'.encode('utf-8') in response.data
    
    # 4. 그래프 생성
    response = client.get('/analyze/plot/traffic?logfile=large.log')
    assert response.status_code == 200
    assert 'image/png' in response.headers.get('Content-Type', '')

# 대용량 파일 성능 테스트
def test_performance_large_file(client, large_log_file):
    """대용량 파일 성능 테스트"""
    start_time = time.time()
    
    data = {'logfile': 'large.log'}
    response = client.post('/analyze', data=data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # 성능 검증 (1초 이내에 처리되어야 함)
    assert processing_time < 1.0
    assert response.status_code == 200

# 혼합 형식 로그 워크플로우 테스트
def test_mixed_format_workflow(client, app):
    """혼합 형식 로그 워크플로우 테스트"""
    # 혼합 형식 로그 파일 생성
    mixed_log_file = os.path.join(app.config['LOG_DIR'], 'mixed.log')
    with open(mixed_log_file, 'w', encoding='utf-8') as f:
        f.write("2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100\n")
        f.write("2025-06-03T08:01:00.123Z POST /api/login 201 150\n")
        f.write("[INFO] 2025-06-03 08:02:00.456 - Client 10.0.1.45 requested GET /api/v1/data with status 200 (response time: 80ms)\n")
    
    # 분석 실행
    data = {'logfile': 'mixed.log'}
    response = client.post('/analyze', data=data)
    
    assert response.status_code == 200
    assert '분석 결과'.encode('utf-8') in response.data
    
    # 정리
    if os.path.exists(app.config['LOG_DIR']):
        shutil.rmtree(app.config['LOG_DIR'])

# 에러 처리 테스트
def test_error_handling(client, app):
    """에러 처리 테스트"""
    # 존재하지 않는 파일로 분석 시도
    data = {'logfile': 'nonexistent.log'}
    response = client.post('/analyze', data=data)
    
    # 에러가 발생하지 않고 정상적으로 처리되어야 함
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(app.config['LOG_DIR']):
        shutil.rmtree(app.config['LOG_DIR'])

# 동시 요청 테스트
def test_concurrent_requests(client, large_log_file):
    """동시 요청 테스트"""
    results = []
    
    def make_request():
        data = {'logfile': 'large.log'}
        response = client.post('/analyze', data=data)
        results.append(response.status_code)
    
    # 5개의 동시 요청 생성
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # 모든 스레드 완료 대기
    for thread in threads:
        thread.join()
    
    # 모든 요청이 성공해야 함
    assert len(results) == 5
    for status_code in results:
        assert status_code == 200

# 데이터 검증 테스트용 fixture
def validation_app():
    """데이터 검증 테스트용 앱 fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['LOG_DIR'] = tempfile.mkdtemp()
    return app

def validation_client(validation_app):
    """데이터 검증 테스트용 클라이언트 fixture"""
    return validation_app.test_client()

# 잘못된 로그 형식 테스트
def test_invalid_log_format(validation_client, validation_app):
    """잘못된 로그 형식 테스트"""
    # 잘못된 형식의 로그 파일 생성
    invalid_log_file = os.path.join(validation_app.config['LOG_DIR'], 'invalid.log')
    with open(invalid_log_file, 'w', encoding='utf-8') as f:
        f.write("This is not a valid log line\n")
        f.write("Another invalid line\n")
        f.write("Random text here\n")
    
    # 분석 실행
    data = {'logfile': 'invalid.log'}
    response = validation_client.post('/analyze', data=data)
    
    # 정상적으로 처리되어야 함 (빈 결과)
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(validation_app.config['LOG_DIR']):
        shutil.rmtree(validation_app.config['LOG_DIR'])

# 빈 로그 파일 테스트
def test_empty_log_file(validation_client, validation_app):
    """빈 로그 파일 테스트"""
    # 빈 로그 파일 생성
    empty_log_file = os.path.join(validation_app.config['LOG_DIR'], 'empty.log')
    with open(empty_log_file, 'w', encoding='utf-8') as f:
        pass  # 빈 파일
    
    # 분석 실행
    data = {'logfile': 'empty.log'}
    response = validation_client.post('/analyze', data=data)
    
    # 정상적으로 처리되어야 함
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(validation_app.config['LOG_DIR']):
        shutil.rmtree(validation_app.config['LOG_DIR'])

# 잘못된 로그 라인 테스트
def test_malformed_log_lines(validation_client, validation_app):
    """잘못된 로그 라인 테스트"""
    # 일부만 올바른 형식인 로그 파일 생성
    malformed_log_file = os.path.join(validation_app.config['LOG_DIR'], 'malformed.log')
    with open(malformed_log_file, 'w', encoding='utf-8') as f:
        f.write("2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100\n")
        f.write("Invalid line here\n")
        f.write("2025-06-03 08:01:00 POST 192.168.0.2 /api/login 201 150\n")
        f.write("Another invalid line\n")
    
    # 분석 실행
    data = {'logfile': 'malformed.log'}
    response = validation_client.post('/analyze', data=data)
    
    # 올바른 라인들만 파싱되어야 함
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(validation_app.config['LOG_DIR']):
        shutil.rmtree(validation_app.config['LOG_DIR'])

# 엣지 케이스 테스트용 fixture
def edge_app():
    """엣지 케이스 테스트용 앱 fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['LOG_DIR'] = tempfile.mkdtemp()
    return app

def edge_client(edge_app):
    """엣지 케이스 테스트용 클라이언트 fixture"""
    return edge_app.test_client()

# 매우 긴 URL 테스트
def test_very_long_url(edge_client, edge_app):
    """매우 긴 URL 테스트"""
    # 매우 긴 URL을 가진 로그 파일 생성
    long_url_log_file = os.path.join(edge_app.config['LOG_DIR'], 'long_url.log')
    very_long_url = '/api/' + 'a' * 1000  # 1000자 URL
    
    with open(long_url_log_file, 'w', encoding='utf-8') as f:
        f.write(f"2025-06-03 08:00:00 GET 192.168.0.1 {very_long_url} 200 100\n")
    
    # 분석 실행
    data = {'logfile': 'long_url.log'}
    response = edge_client.post('/analyze', data=data)
    
    # 정상적으로 처리되어야 함
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(edge_app.config['LOG_DIR']):
        shutil.rmtree(edge_app.config['LOG_DIR'])

# 특수 문자 테스트
def test_special_characters(edge_client, edge_app):
    """특수 문자 테스트"""
    # 특수 문자가 포함된 로그 파일 생성
    special_log_file = os.path.join(edge_app.config['LOG_DIR'], 'special.log')
    with open(special_log_file, 'w', encoding='utf-8') as f:
        f.write('2025-06-03 08:00:00 GET 192.168.0.1 "/api/users?name=test&value=123" 200 100\n')
        f.write('2025-06-03 08:01:00 POST 192.168.0.2 "/api/data" 201 150\n')
    
    # 분석 실행
    data = {'logfile': 'special.log'}
    response = edge_client.post('/analyze', data=data)
    
    # 정상적으로 처리되어야 함
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(edge_app.config['LOG_DIR']):
        shutil.rmtree(edge_app.config['LOG_DIR'])

# 극단적인 응답 시간 테스트
def test_extreme_response_times(edge_client, edge_app):
    """극단적인 응답 시간 테스트"""
    # 극단적인 응답 시간을 가진 로그 파일 생성
    extreme_log_file = os.path.join(edge_app.config['LOG_DIR'], 'extreme.log')
    with open(extreme_log_file, 'w', encoding='utf-8') as f:
        f.write("2025-06-03 08:00:00 GET 192.168.0.1 /api/fast 200 1\n")  # 매우 빠름
        f.write("2025-06-03 08:01:00 GET 192.168.0.2 /api/slow 200 999999\n")  # 매우 느림
        f.write("2025-06-03 08:02:00 GET 192.168.0.3 /api/normal 200 100\n")  # 정상
    
    # 분석 실행
    data = {'logfile': 'extreme.log'}
    response = edge_client.post('/analyze', data=data)
    
    # 정상적으로 처리되어야 함
    assert response.status_code == 200
    
    # 정리
    if os.path.exists(edge_app.config['LOG_DIR']):
        shutil.rmtree(edge_app.config['LOG_DIR'])

# pytest로 실행할 때는 이 부분이 필요하지 않습니다
# if __name__ == '__main__':
#     pytest.main() 