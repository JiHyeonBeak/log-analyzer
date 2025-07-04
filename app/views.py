import os
import io
import matplotlib
matplotlib.use('Agg')  # 서버 환경에서 Tkinter 없이 이미지 저장용 백엔드 사용
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Blueprint, render_template, request, current_app, send_file
from .utils import parse_log_line, search_pattern, traffic_by_hour, endpoint_stats, status_code_stats, slow_requests, slowest_endpoints, detect_anomalies, suggest_improvements

bp = Blueprint('views', __name__)

# 로그 파일이 저장된 디렉토리 경로
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

@bp.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # logs 디렉토리의 파일 목록을 가져옴 (없으면 생성)
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_files = [f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))]

    # 분석 결과 변수 초기화
    result = None
    chart_data = None
    pattern_results = None
    keyword = request.form.get('keyword', '')  # 검색 키워드
    selected_file = request.form.get('logfile')  # 선택된 로그 파일명
    logs = []
    # POST 요청 + 파일 선택 시 분석 시작
    if request.method == 'POST' and selected_file:
        file_path = os.path.join(LOG_DIR, selected_file)
        if os.path.exists(file_path):
            # 로그 파일 읽기
            with open(file_path, encoding='utf-8') as f:
                lines = f.read().splitlines()
            # 한 줄씩 파싱 (parse_log_line: utils.py)
            logs = [parse_log_line(line) for line in lines]
            logs = [log for log in logs if log]  # 파싱 실패(None) 제거
            # 키워드(패턴) 검색
            if keyword:
                pattern_results = search_pattern(logs, keyword)
            # 시간대별 트래픽 분석
            chart_data = traffic_by_hour(logs)
            # 엔드포인트별 통계 분석
            endpoint_data = endpoint_stats(logs)
            # 상태코드 분포 분석
            status_data = status_code_stats(logs)
            # 느린 요청 상위 10개
            slowreqs = slow_requests(logs, top_n=10)
            # 느린 엔드포인트 상위 5개
            slowest_eps = slowest_endpoints(logs, top_n=5)
            # 특이 패턴(이상 탐지)
            anomalies = detect_anomalies(logs)
            # 자동 개선 방안 제안
            improvements = suggest_improvements(logs)
            result = True  # 분석 성공 플래그
    # 분석 결과와 각종 데이터, 파일 목록을 템플릿에 전달
    return render_template(
        'analyze.html',
        result=result,
        chart_data=chart_data,
        pattern_results=pattern_results,
        keyword=keyword,
        log_files=log_files,
        selected_file=selected_file,
        endpoint_data=locals().get('endpoint_data'),
        status_data=locals().get('status_data'),
        slowreqs=locals().get('slowreqs'),
        slowest_eps=locals().get('slowest_eps'),
        anomalies=locals().get('anomalies'),
        improvements=locals().get('improvements')
    )

@bp.route('/analyze/plot/<plot_type>')
def plot_image(plot_type):
    # 분석 결과를 그래프로 그려 PNG 이미지로 반환하는 라우트
    logfile = request.args.get('logfile')  # 쿼리스트링에서 파일명 받기
    if not logfile:
        return '', 404  # 파일명 없으면 404
    file_path = os.path.join(LOG_DIR, logfile)
    if not os.path.exists(file_path):
        return '', 404  # 파일 없으면 404
    # 로그 파일 읽고 파싱
    with open(file_path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    logs = [parse_log_line(line) for line in lines]
    logs = [log for log in logs if log]
    buf = io.BytesIO()  # 이미지 임시 저장 버퍼
    plt.figure(figsize=(12,5))  # 그래프 크기 통일
    # 그래프 종류별 분기
    if plot_type == 'traffic':
        # 시간대별 트래픽 (Line Chart)
        data = traffic_by_hour(logs)
        x = [d[0] for d in data]
        y = [d[1] for d in data]
        sns.lineplot(x=x, y=y, marker='o')
        plt.title('Traffic by Hour')
        plt.xlabel('Hour')
        plt.ylabel('Requests')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    elif plot_type == 'endpoint':
        # 엔드포인트별 평균 응답시간 (Bar Chart)
        stats = endpoint_stats(logs)
        x = [s['url'] for s in stats]
        y = [s['avg_time'] for s in stats]
        sns.barplot(x=x, y=y)
        plt.title('Average Response Time by Endpoint')
        plt.xlabel('Endpoint')
        plt.ylabel('Avg Response (ms)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    elif plot_type == 'status':
        # 상태 코드 분포 (Pie Chart)
        from collections import Counter
        codes = [log['status'] for log in logs]
        counter = Counter(codes)
        labels = list(counter.keys())
        sizes = list(counter.values())
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('Status Code Ratio')
        plt.tight_layout()
    else:
        # 지원하지 않는 plot_type
        return '', 404
    # 그래프를 PNG로 저장 후 응답
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png') 