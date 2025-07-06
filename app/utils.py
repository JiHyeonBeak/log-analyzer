import re
from collections import Counter, defaultdict
from datetime import datetime

def parse_log_line(line):
    # 예시: 2025-06-03 08:12:34 GET 192.168.0.12 /api/login 200 123
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\d+\.\d+\.\d+\.\d+) (\S+) (\d{3}) (\d+)$'
    match = re.match(pattern, line.strip())
    if match:
        timestamp, method, ip, url, status, resp_time = match.groups()
        return {
            'timestamp': timestamp,
            'method': method,
            'ip': ip,
            'url': url,
            'status': status,
            'resp_time': int(resp_time)
        }
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
            dt = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
            hour = dt.strftime('%Y-%m-%d %H:00')
            hour_counter[hour] += 1
        except Exception:
            continue
    # 시간순 정렬
    return sorted(hour_counter.items())

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
                dt = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
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
            dt = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
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