import re
from collections import Counter, defaultdict
from datetime import datetime

def parse_log_line(line):
    # 예시: 2025-05-01T10:15:30Z GET /api/user/list 200 123ms
    pattern = r'^(\S+)\s+(\S+)\s+(\S+)\s+(\d{3})\s+(\d+)ms$'
    match = re.match(pattern, line.strip())
    if match:
        timestamp, method, url, status, resp_time = match.groups()
        return {
            'timestamp': timestamp,
            'method': method,
            'url': url,
            'status': status,
            'resp_time': int(resp_time)
        }
    return None

def search_pattern(logs, keyword):
    # URL, 상태코드 등에서 keyword가 포함된 로그만 반환
    return [log for log in logs if keyword in log['url'] or keyword in log['status']]

def traffic_by_hour(logs):
    # 시간대별 트래픽(요청 수) 집계
    hour_counter = Counter()
    for log in logs:
        try:
            dt = datetime.strptime(log['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            hour = dt.strftime('%Y-%m-%d %H:00')
            hour_counter[hour] += 1
        except Exception:
            continue
    # 시간순 정렬
    return sorted(hour_counter.items()) 