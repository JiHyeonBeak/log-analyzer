import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# 지원하는 로그 형식 패턴들
LOG_PATTERNS = {
    'standard': {
        'pattern': r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD|SYSTEM) (\d+\.\d+\.\d+\.\d+) (\S+) (\d{3}) (\d+)$',
        'example': '2025-06-03 08:12:34 GET 192.168.0.12 /api/login 200 123',
        'groups': ['timestamp', 'method', 'ip', 'url', 'status', 'resp_time']
    },
    'iso_format': {
        'pattern': r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?) (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) (\d{3}) (\d+)$',
        'example': '2025-06-03T08:12:34.123Z GET /api/login 200 123',
        'groups': ['timestamp', 'method', 'url', 'status', 'resp_time']
    },
    'bracket_format': {
        'pattern': r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) (\d{3}) (\d+)(?:ms)?$',
        'example': '[2025-06-03 08:12:34] GET /api/login 200 123ms',
        'groups': ['timestamp', 'method', 'url', 'status', 'resp_time']
    },
    'apache_format': {
        'pattern': r'^(\d+\.\d+\.\d+\.\d+) - - \[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\] "(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) [^"]*" (\d{3}) (\d+)$',
        'example': '192.168.1.100 - - [08/Jun/2025:09:00:01 +0900] "GET / HTTP/1.1" 200 1234',
        'groups': ['ip', 'timestamp', 'method', 'url', 'status', 'resp_time']
    },
    'nginx_format': {
        'pattern': r'^(\d+\.\d+\.\d+\.\d+) - - \[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\] "(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) [^"]*" (\d{3}) (\d+)',
        'example': '192.168.0.12 - - [03/Jun/2025:08:12:34 +0000] "GET /api/login HTTP/1.1" 200 123',
        'groups': ['ip', 'timestamp', 'method', 'url', 'status', 'resp_time']
    },
    'simple_format': {
        'pattern': r'^(\d{2}:\d{2}:\d{2}) (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) (\d{3}) (\d+)$',
        'example': '08:12:34 GET /api/login 200 123',
        'groups': ['time', 'method', 'url', 'status', 'resp_time']
    },
    'app_log_format': {
        'pattern': r'^\[(INFO|DEBUG|WARN|ERROR)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+ - (?:Client )?(\d+\.\d+\.\d+\.\d+) requested (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) with status (\d{3}) \(response time: (\d+)ms\)',
        'example': '[INFO] 2025-06-10 09:00:15.123 - Client 10.0.1.45 requested GET /api/v1/dashboard with status 200 (response time: 89ms)',
        'groups': ['level', 'timestamp', 'ip', 'method', 'url', 'status', 'resp_time']
    },
    'system_log_format': {
        'pattern': r'^\[(INFO|DEBUG|WARN|ERROR)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+ - (.+)$',
        'example': '[ERROR] 2025-06-10 09:05:12.890 - Database connection failed: timeout after 30 seconds',
        'groups': ['level', 'timestamp', 'message']
    },

}

def detect_log_format(sample_lines: List[str]) -> Optional[str]:
    """
    로그 파일의 형식을 자동으로 감지합니다.
    
    Args:
        sample_lines: 분석할 로그 라인들의 리스트 (보통 처음 10-20줄)
    
    Returns:
        감지된 로그 형식의 이름 또는 None
    """
    if not sample_lines:
        return None
    
    # 각 형식별로 매치되는 라인 수 계산
    format_scores = {}
    
    for format_name, format_info in LOG_PATTERNS.items():
        pattern = re.compile(format_info['pattern'])
        match_count = 0
        
        for line in sample_lines:
            line = line.strip()
            if line and pattern.match(line):
                match_count += 1
        
        # 매치율 계산 (매치된 라인 수 / 전체 라인 수)
        if sample_lines:
            match_rate = match_count / len(sample_lines)
            format_scores[format_name] = match_rate
    
    # 가장 높은 매치율을 가진 형식 선택 (80% 이상 매치)
    best_format = None
    best_score = 0
    
    for format_name, score in format_scores.items():
        if score > best_score and score >= 0.8:  # 80% 이상 매치
            best_format = format_name
            best_score = score
    
    return best_format

def normalize_timestamp(timestamp: str, format_type: str) -> str:
    """
    다양한 형식의 타임스탬프를 표준 형식으로 변환합니다.
    
    Args:
        timestamp: 원본 타임스탬프
        format_type: 로그 형식 타입
    
    Returns:
        표준 형식의 타임스탬프 (YYYY-MM-DD HH:MM:SS)
    """
    try:
        if format_type == 'iso_format':
            # ISO 형식: 2025-06-03T08:12:34.123Z -> 2025-06-03 08:12:34
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1][:8]
            return timestamp
        
        elif format_type == 'apache_format' or format_type == 'nginx_format':
            # Apache/Nginx 형식: 03/Jun/2025:08:12:34 +0000 -> 2025-06-03 08:12:34
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            
            # 03/Jun/2025:08:12:34 +0000 형식 파싱
            parts = timestamp.split(':')
            if len(parts) >= 3:
                date_part = parts[0]  # 03/Jun/2025
                time_part = f"{parts[1]}:{parts[2]}"  # 08:12:34
                
                if '/' in date_part:
                    day, month, year = date_part.split('/')
                    month_num = month_map.get(month, '01')
                    return f"{year}-{month_num}-{day.zfill(2)} {time_part}"
            
            return timestamp
        
        elif format_type == 'simple_format':
            # 간단 형식: 08:12:34 -> 오늘 날짜 + 시간
            today = datetime.now().strftime('%Y-%m-%d')
            return f"{today} {timestamp}"
        
        elif format_type == 'app_log_format':
            # 애플리케이션 로그 형식: 밀리초 제거
            if '.' in timestamp:
                timestamp = timestamp.split('.')[0]
            return timestamp
        
        elif format_type == 'system_log_format':
            # 시스템 로그 형식: 밀리초 제거
            if '.' in timestamp:
                timestamp = timestamp.split('.')[0]
            return timestamp
        
        else:
            # 표준 형식은 그대로 반환
            return timestamp
            
    except Exception:
        return timestamp

def parse_log_line(line: str, format_type: str = 'standard') -> Optional[Dict]:
    """
    다양한 형식의 로그 라인을 파싱합니다.
    
    Args:
        line: 파싱할 로그 라인
        format_type: 로그 형식 타입 (detect_log_format으로 감지된 형식)
    
    Returns:
        파싱된 로그 데이터 딕셔너리 또는 None
    """
    if not line.strip():
        return None
    
    if format_type not in LOG_PATTERNS:
        # 알 수 없는 형식이면 표준 형식으로 시도
        format_type = 'standard'
    
    format_info = LOG_PATTERNS[format_type]
    pattern = re.compile(format_info['pattern'])
    match = pattern.match(line.strip())
    
    if not match:
        return None
    
    groups = match.groups()
    group_names = format_info['groups']
    
    # 그룹 이름과 매치된 값들을 딕셔너리로 변환
    log_data = {}
    for i, group_name in enumerate(group_names):
        if i < len(groups):
            log_data[group_name] = groups[i]
    
    # 타임스탬프 정규화
    if 'timestamp' in log_data:
        log_data['timestamp'] = normalize_timestamp(log_data['timestamp'], format_type)
    elif 'time' in log_data:
        log_data['timestamp'] = normalize_timestamp(log_data['time'], format_type)
        del log_data['time']
    
    # 응답 시간을 정수로 변환
    if 'resp_time' in log_data:
        try:
            log_data['resp_time'] = int(log_data['resp_time'])
        except ValueError:
            log_data['resp_time'] = 0
    
    # 시스템 로그 처리 (message가 있는 경우)
    if 'message' in log_data:
        # 시스템 로그는 가상의 API 요청으로 변환
        level = log_data.get('level', 'INFO')
        message = log_data['message']
        
        # 에러 레벨에 따라 가상 상태 코드 설정
        if level == 'ERROR':
            status = '500'
        elif level == 'WARN':
            status = '400'
        else:
            status = '200'
        
        # 가상의 API 엔드포인트 생성
        if 'database' in message.lower():
            url = '/api/system/database'
        elif 'memory' in message.lower():
            url = '/api/system/memory'
        elif 'network' in message.lower():
            url = '/api/system/network'
        elif 'file' in message.lower():
            url = '/api/system/file'
        elif 'ssl' in message.lower() or 'certificate' in message.lower():
            url = '/api/system/ssl'
        elif 'authentication' in message.lower() or 'auth' in message.lower():
            url = '/api/system/auth'
        elif 'session' in message.lower():
            url = '/api/system/session'
        elif 'backup' in message.lower():
            url = '/api/system/backup'
        elif 'cache' in message.lower():
            url = '/api/system/cache'
        elif 'email' in message.lower() or 'smtp' in message.lower():
            url = '/api/system/email'
        elif 'rate limit' in message.lower():
            url = '/api/system/ratelimit'
        elif 'service' in message.lower():
            url = '/api/system/service'
        elif 'configuration' in message.lower() or 'config' in message.lower():
            url = '/api/system/config'
        elif 'process' in message.lower():
            url = '/api/system/process'
        elif 'index' in message.lower():
            url = '/api/system/index'
        elif 'external' in message.lower():
            url = '/api/system/external'
        else:
            url = '/api/system/other'
        
        # 가상의 응답 시간 설정 (에러는 보통 빠르게 처리됨)
        resp_time = 50 if level == 'ERROR' else 30
        
        # 가상의 IP 주소 (시스템 로그이므로)
        ip = '127.0.0.1'
        
        # 가상의 HTTP 메소드
        method = 'SYSTEM'
        
        # 새로운 로그 데이터로 교체
        log_data = {
            'timestamp': log_data['timestamp'],
            'method': method,
            'ip': ip,
            'url': url,
            'status': status,
            'resp_time': resp_time
        }
    
    # IP 주소가 없는 경우 기본값 설정
    if 'ip' not in log_data:
        log_data['ip'] = '0.0.0.0'
    
    return log_data

def parse_log_file(file_path: str) -> List[Dict]:
    """로그 파일을 파싱하여 로그 데이터 리스트를 반환합니다."""
    logs = []
    
    try:
        # 파일에서 샘플 라인들을 읽어서 형식 감지
        sample_lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 20:  # 처음 20줄만 샘플로 사용
                    break
                sample_lines.append(line.strip())
        
        # 로그 형식 감지
        format_type = detect_log_format(sample_lines)
        if not format_type:
            print(f"Warning: Could not detect log format for {file_path}")
            return []
        
        # 전체 파일 파싱
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # 로그 라인 파싱
                log_data = parse_log_line(line, format_type)
                if log_data:
                    logs.append(log_data)
                else:
                    print(f"Warning: Line {line_num} could not be parsed: {line[:50]}...")
        
        return logs
    
    except Exception as e:
        print(f"Error parsing log file {file_path}: {e}")
        return []

def convert_log_format(raw_line: str) -> Optional[str]:
    """
    다양한 로그 형식을 표준 형식으로 변환합니다.
    
    Args:
        raw_line: 원본 로그 라인
    
    Returns:
        표준 형식으로 변환된 로그 라인 또는 None (변환 불가능한 경우)
    """
    if not raw_line.strip():
        return None
    
    line = raw_line.strip()
    
    # 1. 애플리케이션 API 요청 로그 형식 변환
    # [INFO] 2025-06-10 09:15:23.456 - Client 10.0.1.45 requested GET /api/v1/users with status 200 (response time: 145ms)
    app_log_pattern = r'^\[(INFO|DEBUG|WARN|ERROR)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+ - (?:Client )?(\d+\.\d+\.\d+\.\d+) requested (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) with status (\d{3}) \(response time: (\d+)ms\)'
    app_match = re.match(app_log_pattern, line)
    if app_match:
        level, timestamp, ip, method, url, status, resp_time = app_match.groups()
        # 밀리초 제거하고 표준 형식으로 변환
        timestamp_clean = timestamp  # 이미 HH:MM:SS 형식
        return f"{timestamp_clean} {method} {ip} {url} {status} {resp_time}"
    
    # 2. 시스템 에러/경고 로그 형식 변환
    # [ERROR] 2025-06-10 09:05:12.890 - Database connection failed: timeout after 30 seconds
    # [WARN] 2025-06-10 09:12:03.012 - High memory usage detected: 85% of available RAM
    system_log_pattern = r'^\[(INFO|DEBUG|WARN|ERROR)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+ - (.+)$'
    system_match = re.match(system_log_pattern, line)
    if system_match:
        level, timestamp, message = system_match.groups()
        # 시스템 로그는 가상의 API 요청으로 변환 (에러 분석을 위해)
        timestamp_clean = timestamp
        # 에러 레벨에 따라 가상 상태 코드 설정
        if level == 'ERROR':
            status = '500'  # 서버 에러
        elif level == 'WARN':
            status = '400'  # 클라이언트 에러
        else:
            status = '200'  # 정상
        
        # 가상의 API 엔드포인트 생성
        if 'database' in message.lower():
            url = '/api/system/database'
        elif 'memory' in message.lower():
            url = '/api/system/memory'
        elif 'network' in message.lower():
            url = '/api/system/network'
        elif 'file' in message.lower():
            url = '/api/system/file'
        elif 'ssl' in message.lower() or 'certificate' in message.lower():
            url = '/api/system/ssl'
        elif 'authentication' in message.lower() or 'auth' in message.lower():
            url = '/api/system/auth'
        elif 'session' in message.lower():
            url = '/api/system/session'
        elif 'backup' in message.lower():
            url = '/api/system/backup'
        elif 'cache' in message.lower():
            url = '/api/system/cache'
        elif 'email' in message.lower() or 'smtp' in message.lower():
            url = '/api/system/email'
        elif 'rate limit' in message.lower():
            url = '/api/system/ratelimit'
        elif 'service' in message.lower():
            url = '/api/system/service'
        elif 'configuration' in message.lower() or 'config' in message.lower():
            url = '/api/system/config'
        elif 'process' in message.lower():
            url = '/api/system/process'
        elif 'index' in message.lower():
            url = '/api/system/index'
        elif 'external' in message.lower():
            url = '/api/system/external'
        else:
            url = '/api/system/other'
        
        # 가상의 응답 시간 설정 (에러는 보통 빠르게 처리됨)
        resp_time = '50' if level == 'ERROR' else '30'
        
        # 가상의 IP 주소 (시스템 로그이므로)
        ip = '127.0.0.1'
        
        # 가상의 HTTP 메소드
        method = 'SYSTEM'
        
        return f"{timestamp_clean} {method} {ip} {url} {status} {resp_time}"
    
    # 2. JSON 로그 형식 변환 (향후 확장용)
    # {"timestamp": "2025-06-10T09:15:23.456Z", "level": "INFO", "method": "GET", "url": "/api/users", "status": 200, "response_time": 145}
    json_pattern = r'^\s*\{.*"timestamp"\s*:\s*"([^"]+)".*"method"\s*:\s*"([^"]+)".*"url"\s*:\s*"([^"]+)".*"status"\s*:\s*(\d+).*"response_time"\s*:\s*(\d+).*\}\s*$'
    json_match = re.match(json_pattern, line, re.DOTALL)
    if json_match:
        timestamp, method, url, status, resp_time = json_match.groups()
        # ISO 형식을 표준 형식으로 변환
        if 'T' in timestamp:
            timestamp_clean = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1][:8]
        else:
            timestamp_clean = timestamp
        return f"{timestamp_clean} {method} 0.0.0.0 {url} {status} {resp_time}"
    
    # 3. CSV 로그 형식 변환 (향후 확장용)
    # 2025-06-10,09:15:23,GET,10.0.1.45,/api/users,200,145
    csv_pattern = r'^(\d{4}-\d{2}-\d{2}),(\d{2}:\d{2}:\d{2}),(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD),(\d+\.\d+\.\d+\.\d+),(\S+),(\d{3}),(\d+)$'
    csv_match = re.match(csv_pattern, line)
    if csv_match:
        date, time, method, ip, url, status, resp_time = csv_match.groups()
        timestamp_clean = f"{date} {time}"
        return f"{timestamp_clean} {method} {ip} {url} {status} {resp_time}"
    
    # 4. 기타 형식들 (향후 확장용)
    # 여기에 새로운 로그 형식 변환 패턴을 추가할 수 있습니다.
    
    # 변환할 수 없는 형식인 경우 None 반환
    return None

def search_pattern(logs, keyword):
    # URL, 상태코드, 메소드, IP 등에서 keyword가 포함된 로그만 반환
    keyword_lower = keyword.lower()
    return [log for log in logs if 
            keyword_lower in log['url'].lower() or 
            keyword_lower in log['status'].lower() or 
            keyword_lower in log['method'].lower() or 
            keyword_lower in log['ip'].lower()]

def traffic_by_hour(logs):
    # 시간대별 트래픽(요청 수) 집계
    hour_counter = Counter()
    for log in logs:
        try:
            # 다양한 타임스탬프 형식 지원
            timestamp = log['timestamp']
            if len(timestamp) == 16:  # YYYY-MM-DD HH:MM 형식
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
            elif len(timestamp) == 19:  # YYYY-MM-DD HH:MM:SS 형식
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            else:
                continue
            
            hour = dt.strftime('%Y-%m-%d %H:00')
            hour_counter[hour] += 1
        except Exception:
            continue
    
    # 데이터가 있는 시간대만 반환하거나, 전체 24시간 범위 생성
    if hour_counter:
        # 데이터가 있는 시간대만 반환 (더 깔끔한 그래프)
        return sorted(hour_counter.items())
    else:
        return []

def endpoint_stats(logs):
    # 엔드포인트별 호출수, 평균 응답시간
    stats = {}
    for log in logs:
        url = log['url']
        if url not in stats:
            stats[url] = {'count': 0, 'total_time': 0, 'times': []}
        entry = stats[url]
        entry['count'] += 1
        entry['total_time'] += log['resp_time']
        entry['times'].append(log['resp_time'])
    result = []
    for url, data in stats.items():
        avg_time = data['total_time'] / data['count'] if data['count'] else 0
        result.append({
            'url': url,
            'count': data['count'],
            'avg_time': avg_time,
            'times': data['times']
        })
    # 호출수 내림차순 정렬
    return sorted(result, key=lambda x: x['count'], reverse=True)

def status_code_stats(logs):
    # 상태 코드별 빈도, 에러 집중 시간/엔드포인트
    code_counter = Counter()
    error_by_time = defaultdict(int)
    error_by_url = defaultdict(int)
    for log in logs:
        code = log['status']
        code_counter[code] += 1
        if code.startswith('4') or code.startswith('5'):
            # 시간대별 에러
            try:
                timestamp = log['timestamp']
                if len(timestamp) == 16:  # YYYY-MM-DD HH:MM 형식
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
                elif len(timestamp) == 19:  # YYYY-MM-DD HH:MM:SS 형식
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                else:
                    continue
                
                hour = dt.strftime('%Y-%m-%d %H:00')
                error_by_time[hour] += 1
            except Exception:
                pass
            # 엔드포인트별 에러
            error_by_url[log['url']] += 1
    return {
        'code_counter': dict(code_counter),
        'error_by_time': dict(error_by_time),
        'error_by_url': dict(error_by_url)
    }

def slow_requests(logs, top_n=10):
    # 처리시간이 긴 상위 N개 요청
    return sorted(logs, key=lambda x: x['resp_time'], reverse=True)[:top_n]

def slowest_endpoints(logs, top_n=5):
    # 평균 응답시간이 느린 엔드포인트 top N, 90퍼센타일 등
    stats = endpoint_stats(logs)
    for s in stats:
        times = sorted(s['times'])
        n = len(times)
        if n > 0:
            p90_idx = int(n * 0.9) - 1 if n > 1 else 0
            s['p90'] = times[p90_idx]
        else:
            s['p90'] = 0
    return sorted(stats, key=lambda x: x['avg_time'], reverse=True)[:top_n]

def detect_anomalies(logs):
    # 응답시간 급증 시간대, 비정상적 요청 IP 등
    # 1. 시간대별 평균 응답시간이 평소보다 2배 이상 급증한 구간 탐지
    hour_resp = defaultdict(list)
    for log in logs:
        try:
            timestamp = log['timestamp']
            if len(timestamp) == 16:  # YYYY-MM-DD HH:MM 형식
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
            elif len(timestamp) == 19:  # YYYY-MM-DD HH:MM:SS 형식
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            else:
                continue
            
            hour = dt.strftime('%Y-%m-%d %H:00')
            hour_resp[hour].append(log['resp_time'])
        except Exception:
            continue
    hour_avg = {h: (sum(v)/len(v) if v else 0) for h, v in hour_resp.items()}
    if hour_avg:
        global_avg = sum(hour_avg.values()) / len(hour_avg)
    else:
        global_avg = 0
    spike_hours = [h for h, avg in hour_avg.items() if avg > 2 * global_avg and avg > 200]
    # 2. IP별 요청수 상위 5개 (비정상적 요청 탐지)
    ip_counter = Counter([log['ip'] for log in logs])
    top_ips = ip_counter.most_common(5)
    return {
        'spike_hours': spike_hours,
        'top_ips': top_ips
    }

def suggest_improvements(logs):
    # 느린 엔드포인트, 에러 많은 엔드포인트에 대한 개선 제안
    suggestions = []
    # 느린 엔드포인트
    slow_eps = slowest_endpoints(logs, top_n=3)
    for ep in slow_eps:
        if ep['avg_time'] > 300:
            suggestions.append(f"'{ep['url']}' 엔드포인트는 평균 응답시간이 {ep['avg_time']:.1f}ms로 느립니다. DB 인덱스 최적화, 캐싱, 쿼리 개선을 검토하세요.")
    # 에러 많은 엔드포인트
    status_stats = status_code_stats(logs)
    error_urls = sorted(status_stats['error_by_url'].items(), key=lambda x: x[1], reverse=True)[:3]
    for url, cnt in error_urls:
        if cnt > 0:
            suggestions.append(f"'{url}' 엔드포인트에서 에러가 {cnt}회 발생했습니다. 입력값 검증, 예외처리, 버그 수정이 필요할 수 있습니다.")
    if not suggestions:
        suggestions.append("특별히 개선이 필요한 엔드포인트가 발견되지 않았습니다.")
    return suggestions 