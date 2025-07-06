#!/usr/bin/env python3
"""
views 모듈 테스트 스위트

이 모듈은 Flask 애플리케이션의 뷰 함수들을 테스트합니다.
- 라우트 접근 테스트
- 로그 분석 기능 테스트
- 그래프 생성 기능 테스트
"""

import sys
import os
import tempfile
import shutil

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app

# Flask 앱 fixture
def app():
    """Flask 앱 fixture - 테스트용 앱 생성"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['LOG_DIR'] = tempfile.mkdtemp()  # 임시 로그 디렉토리
    return app

def client(app):
    """테스트 클라이언트 fixture"""
    return app.test_client()

def test_log_file(app):
    """테스트용 로그 파일 fixture"""
    test_log_file = os.path.join(app.config['LOG_DIR'], 'test.log')
    with open(test_log_file, 'w', encoding='utf-8') as f:
        f.write("2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100\n")
        f.write("2025-06-03 08:01:00 POST 192.168.0.2 /api/login 201 150\n")
        f.write("2025-06-03 08:02:00 GET 192.168.0.3 /api/data 200 80\n")
    yield test_log_file
    # 테스트 후 임시 디렉토리 정리
    if os.path.exists(app.config['LOG_DIR']):
        shutil.rmtree(app.config['LOG_DIR'])

# 메인 페이지 라우트 테스트
def test_index_route(client):
    """메인 페이지 라우트 테스트"""
    response = client.get('/')
    assert response.status_code == 200
    assert '로그 분석기'.encode('utf-8') in response.data
    assert 'Magpie'.encode('utf-8') in response.data

# 분석 페이지 GET 요청 테스트
def test_analyze_route_get(client):
    """분석 페이지 GET 요청 테스트"""
    response = client.get('/analyze')
    assert response.status_code == 200
    assert '로그 파일'.encode('utf-8') in response.data
    assert '분석'.encode('utf-8') in response.data

# 파일 없이 POST 요청 테스트
def test_analyze_route_post_without_file(client):
    """파일 없이 POST 요청 테스트"""
    response = client.post('/analyze', data={})
    assert response.status_code == 200
    assert '분석 결과'.encode('utf-8') not in response.data

# 파일과 함께 POST 요청 테스트
def test_analyze_route_post_with_file(client, test_log_file):
    """파일과 함께 POST 요청 테스트"""
    data = {
        'logfile': 'test.log',
        'keyword': '/api'
    }
    response = client.post('/analyze', data=data)
    assert response.status_code == 200
    assert '분석 결과'.encode('utf-8') in response.data

# 키워드와 함께 POST 요청 테스트
def test_analyze_route_post_with_keyword(client, test_log_file):
    """키워드와 함께 POST 요청 테스트"""
    data = {
        'logfile': 'test.log',
        'keyword': 'GET'
    }
    response = client.post('/analyze', data=data)
    assert response.status_code == 200
    assert '패턴 검색 결과'.encode('utf-8') in response.data

# 키워드 없이 POST 요청 테스트
def test_analyze_route_post_without_keyword(client, test_log_file):
    """키워드 없이 POST 요청 테스트"""
    data = {
        'logfile': 'test.log'
    }
    response = client.post('/analyze', data=data)
    assert response.status_code == 200
    assert '분석 결과'.encode('utf-8') in response.data

# 트래픽 그래프 생성 테스트
def test_plot_image_traffic(client, test_log_file):
    """트래픽 그래프 생성 테스트"""
    response = client.get('/analyze/plot/traffic?logfile=test.log')
    assert response.status_code == 200
    assert 'image/png' in response.headers.get('Content-Type', '')

# 엔드포인트 그래프 생성 테스트
def test_plot_image_endpoint(client, test_log_file):
    """엔드포인트 그래프 생성 테스트"""
    response = client.get('/analyze/plot/endpoint?logfile=test.log')
    assert response.status_code == 200
    assert 'image/png' in response.headers.get('Content-Type', '')

# 상태 코드 그래프 생성 테스트
def test_plot_image_status(client, test_log_file):
    """상태 코드 그래프 생성 테스트"""
    response = client.get('/analyze/plot/status?logfile=test.log')
    assert response.status_code == 200
    assert 'image/png' in response.headers.get('Content-Type', '')

# 잘못된 그래프 타입 테스트
def test_plot_image_invalid_type(client, test_log_file):
    """잘못된 그래프 타입 테스트"""
    response = client.get('/analyze/plot/invalid?logfile=test.log')
    assert response.status_code == 404

# 파일 없이 그래프 요청 테스트
def test_plot_image_no_file(client):
    """파일 없이 그래프 요청 테스트"""
    response = client.get('/analyze/plot/traffic')
    assert response.status_code == 404

# 존재하지 않는 파일로 그래프 요청 테스트
def test_plot_image_nonexistent_file(client):
    """존재하지 않는 파일로 그래프 요청 테스트"""
    response = client.get('/analyze/plot/traffic?logfile=nonexistent.log')
    assert response.status_code == 404

# 에러 로그 페이지 테스트
def test_errors_route(client, test_log_file):
    """에러 로그 페이지 테스트"""
    response = client.get('/errors/test.log')
    assert response.status_code == 200
    assert '에러'.encode('utf-8') in response.data

# 존재하지 않는 파일로 에러 페이지 요청 테스트
def test_errors_route_nonexistent_file(client):
    """존재하지 않는 파일로 에러 페이지 요청 테스트"""
    response = client.get('/errors/nonexistent.log')
    assert response.status_code == 404

# 통합 테스트용 fixture
def mixed_log_file(app):
    """혼합 형식 테스트용 로그 파일 fixture"""
    mixed_log_file = os.path.join(app.config['LOG_DIR'], 'mixed.log')
    with open(mixed_log_file, 'w', encoding='utf-8') as f:
        f.write("2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100\n")
        f.write("2025-06-03T08:01:00.123Z POST /api/login 201 150\n")
        f.write("[INFO] 2025-06-03 08:02:00.456 - Client 10.0.1.45 requested GET /api/v1/data with status 200 (response time: 80ms)\n")
    yield mixed_log_file
    if os.path.exists(app.config['LOG_DIR']):
        shutil.rmtree(app.config['LOG_DIR'])

# 혼합 형식 로그 분석 테스트
def test_mixed_format_analysis(client, mixed_log_file):
    """혼합 형식 로그 분석 테스트"""
    data = {'logfile': 'mixed.log'}
    response = client.post('/analyze', data=data)
    assert response.status_code == 200
    assert '분석 결과'.encode('utf-8') in response.data

# 혼합 형식 로그 그래프 생성 테스트
def test_mixed_format_plot(client, mixed_log_file):
    """혼합 형식 로그 그래프 생성 테스트"""
    response = client.get('/analyze/plot/traffic?logfile=mixed.log')
    assert response.status_code == 200
    assert 'image/png' in response.headers.get('Content-Type', '') 