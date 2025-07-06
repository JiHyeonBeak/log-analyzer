#!/usr/bin/env python3
"""
utils 모듈 테스트 스위트

이 모듈은 app.utils의 핵심 기능들을 테스트합니다.
- 로그 파싱 함수 (다중 패턴 지원)
- 로그 형식 자동 감지
- 로그 형식 변환
- 기타 유틸리티 함수들
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils import (
    parse_log_line, 
    detect_log_format, 
    convert_log_format,
    search_pattern,
    traffic_by_hour,
    endpoint_stats,
    status_code_stats,
    slow_requests,
    slowest_endpoints,
    detect_anomalies,
    suggest_improvements
)

# 표준 형식 로그 파싱 테스트
def test_parse_log_line_standard():
    """표준 형식 로그 파싱 테스트"""
    test_line = "2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100"
    result = parse_log_line(test_line, 'standard')
    assert result is not None
    assert result['timestamp'] == '2025-06-03 08:00:00'
    assert result['method'] == 'GET'
    assert result['ip'] == '192.168.0.1'
    assert result['url'] == '/api/users'
    assert result['status'] == '200'
    assert result['resp_time'] == 100

# ISO 형식 로그 파싱 테스트
def test_parse_log_line_iso_format():
    test_line = "2025-06-03T08:12:34.123Z GET /api/login 200 123"
    result = parse_log_line(test_line, 'iso_format')
    assert result is not None
    assert result['timestamp'] == '2025-06-03 08:12:34'
    assert result['method'] == 'GET'
    assert result['url'] == '/api/login'
    assert result['ip'] == '0.0.0.0'  # 기본값
    assert result['status'] == '200'
    assert result['resp_time'] == 123

# 대괄호 형식 로그 파싱 테스트
def test_parse_log_line_bracket_format():
    test_line = "[2025-06-03 08:12:34] GET /api/login 200 123ms"
    result = parse_log_line(test_line, 'bracket_format')
    assert result is not None
    assert result['timestamp'] == '2025-06-03 08:12:34'
    assert result['method'] == 'GET'
    assert result['url'] == '/api/login'
    assert result['status'] == '200'
    assert result['resp_time'] == 123

# Apache 형식 로그 파싱 테스트
def test_parse_log_line_apache_format():
    test_line = '192.168.0.12 - - [03/Jun/2025:08:12:34 +0000] "GET /api/login HTTP/1.1" 200 123'
    result = parse_log_line(test_line, 'apache_format')
    assert result is not None
    assert result['ip'] == '192.168.0.12'
    assert result['timestamp'] == '2025-06-03 08:12:34'
    assert result['method'] == 'GET'
    assert result['url'] == '/api/login'
    assert result['status'] == '200'
    assert result['resp_time'] == 123

# 로그 형식 감지 테스트
def test_detect_log_format_standard():
    sample_lines = [
        "2025-06-03 08:00:00 GET 192.168.0.1 /api/users 200 100",
        "2025-06-03 08:01:00 POST 192.168.0.2 /api/login 201 150",
        "2025-06-03 08:02:00 GET 192.168.0.3 /api/data 200 80"
    ]
    detected_format = detect_log_format(sample_lines)
    assert detected_format == 'standard'

def test_detect_log_format_iso():
    sample_lines = [
        "2025-06-03T08:00:00.123Z GET /api/users 200 100",
        "2025-06-03T08:01:00.456Z POST /api/login 201 150",
        "2025-06-03T08:02:00.789Z GET /api/data 200 80"
    ]
    detected_format = detect_log_format(sample_lines)
    assert detected_format == 'iso_format'

def test_detect_log_format_bracket():
    sample_lines = [
        "[2025-06-03 08:00:00] GET /api/users 200 100ms",
        "[2025-06-03 08:01:00] POST /api/login 201 150ms",
        "[2025-06-03 08:02:00] GET /api/data 200 80ms"
    ]
    detected_format = detect_log_format(sample_lines)
    assert detected_format == 'bracket_format'

def test_detect_log_format_unknown():
    sample_lines = [
        "This is not a valid log line",
        "Another invalid line",
        "Random text here"
    ]
    detected_format = detect_log_format(sample_lines)
    assert detected_format is None

# 로그 형식 변환 테스트
def test_convert_log_format_application():
    app_log_line = "[INFO] 2025-06-10 09:15:23.456 - Client 10.0.1.45 requested GET /api/v1/users with status 200 (response time: 145ms)"
    converted = convert_log_format(app_log_line)
    expected = "2025-06-10 09:15:23 GET 10.0.1.45 /api/v1/users 200 145"
    assert converted == expected

def test_convert_log_format_json():
    json_log_line = '{"timestamp": "2025-06-10T09:15:23.456Z", "level": "INFO", "method": "GET", "url": "/api/users", "status": 200, "response_time": 145}'
    converted = convert_log_format(json_log_line)
    expected = "2025-06-10 09:15:23 GET 0.0.0.0 /api/users 200 145"
    assert converted == expected

def test_convert_log_format_csv():
    csv_log_line = "2025-06-10,09:15:23,GET,10.0.1.45,/api/users,200,145"
    converted = convert_log_format(csv_log_line)
    expected = "2025-06-10 09:15:23 GET 10.0.1.45 /api/users 200 145"
    assert converted == expected

def test_convert_log_format_invalid():
    invalid_line = "This is not a valid log line"
    converted = convert_log_format(invalid_line)
    assert converted is None

def test_convert_and_parse_workflow():
    """변환 후 파싱 워크플로우 테스트"""
    original_line = "[INFO] 2025-06-10 09:15:23.456 - Client 10.0.1.45 requested GET /api/v1/users with status 200 (response time: 145ms)"
    converted_line = convert_log_format(original_line)
    assert converted_line is not None
    assert converted_line == "2025-06-10 09:15:23 GET 10.0.1.45 /api/v1/users 200 145"
    parsed_result = parse_log_line(converted_line, 'standard')
    assert parsed_result is not None
    assert parsed_result['timestamp'] == '2025-06-10 09:15:23'
    assert parsed_result['method'] == 'GET'
    assert parsed_result['ip'] == '10.0.1.45'
    assert parsed_result['url'] == '/api/v1/users'
    assert parsed_result['status'] == '200'
    assert parsed_result['resp_time'] == 145

# 로그 분석 관련 테스트용 샘플 데이터 fixture
test_sample_logs = [
    {"timestamp": "2025-06-03 08:00:00", "method": "GET", "ip": "192.168.0.1", "url": "/api/users", "status": "200", "resp_time": 100},
    {"timestamp": "2025-06-03 08:01:00", "method": "POST", "ip": "192.168.0.2", "url": "/api/login", "status": "201", "resp_time": 150},
    {"timestamp": "2025-06-03 08:02:00", "method": "GET", "ip": "192.168.0.3", "url": "/api/data", "status": "200", "resp_time": 80},
]

# 패턴 검색 테스트
def test_search_pattern():
    result = search_pattern(test_sample_logs, 'api')
    assert len(result) == 3
    result2 = search_pattern(test_sample_logs, 'login')
    assert len(result2) == 1

# 시간대별 트래픽 집계 테스트
def test_traffic_by_hour():
    result = traffic_by_hour(test_sample_logs)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0][1] == 3

# 엔드포인트별 통계 테스트
def test_endpoint_stats():
    result = endpoint_stats(test_sample_logs)
    assert isinstance(result, list)
    assert any(ep['url'] == '/api/users' for ep in result)

# 상태 코드별 통계 테스트
def test_status_code_stats():
    result = status_code_stats(test_sample_logs)
    assert '200' in result['code_counter']
    assert '201' in result['code_counter']

# 느린 요청 상위 N개 테스트
def test_slow_requests():
    result = slow_requests(test_sample_logs, top_n=2)
    assert len(result) == 2
    assert result[0]['resp_time'] >= result[1]['resp_time']

# 느린 엔드포인트 테스트
def test_slowest_endpoints():
    result = slowest_endpoints(test_sample_logs, top_n=1)
    assert isinstance(result, list)
    assert len(result) == 1

# 이상 탐지 테스트
def test_detect_anomalies():
    result = detect_anomalies(test_sample_logs)
    assert 'spike_hours' in result
    assert 'top_ips' in result

# 개선 방안 제안 테스트
def test_suggest_improvements():
    result = suggest_improvements(test_sample_logs)
    assert isinstance(result, list) 