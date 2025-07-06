import os
import io
import matplotlib
matplotlib.use('Agg')  # 서버 환경에서 Tkinter 없이 이미지 저장용 백엔드 사용
import matplotlib.pyplot as plt
import seaborn as sns


from flask import Blueprint, render_template, request, current_app, send_file
from .utils import parse_log_line, detect_log_format, convert_log_format, search_pattern, traffic_by_hour, endpoint_stats, status_code_stats, slow_requests, slowest_endpoints, detect_anomalies, suggest_improvements

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
            
            # 로그 형식 자동 감지 (처음 20줄 사용)
            sample_lines = [line for line in lines[:20] if line.strip()]
            detected_format = detect_log_format(sample_lines)
            print(f"DEBUG: Detected format: {detected_format}")
            print(f"DEBUG: Sample lines: {sample_lines[:3]}")
            
            # 로그 파싱
            logs = []
            parsed_count = 0
            for i, line in enumerate(lines):
                if line.strip():
                    # 감지된 형식으로 직접 파싱
                    if detected_format:
                        log_entry = parse_log_line(line, detected_format)
                    else:
                        log_entry = parse_log_line(line, 'standard')
                    
                    if log_entry:
                        logs.append(log_entry)
                        parsed_count += 1
                    else:
                        print(f"DEBUG: Failed to parse line {i+1}: {line[:100]}...")
            
            print(f"DEBUG: Total lines: {len(lines)}, Parsed: {parsed_count}, Logs: {len(logs)}")
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
    try:
        # 분석 결과를 그래프로 그려 PNG 이미지로 반환하는 라우트
        logfile = request.args.get('logfile')  # 쿼리스트링에서 파일명 받기
        print(f"DEBUG: Plot request - type: {plot_type}, logfile: {logfile}")  # 디버깅
        
        if not logfile:
            print("DEBUG: No logfile provided")
            return '', 404  # 파일명 없으면 404
        

            
        file_path = os.path.join(LOG_DIR, logfile)
        if not os.path.exists(file_path):
            print(f"DEBUG: File not found - {file_path}")
            return '', 404  # 파일 없으면 404
            
        # 로그 파일 읽고 파싱
        with open(file_path, encoding='utf-8') as f:
            lines = f.read().splitlines()
        
        # 로그 형식 자동 감지 (처음 20줄 사용)
        sample_lines = [line for line in lines[:20] if line.strip()]
        detected_format = detect_log_format(sample_lines)
        
        # 로그 파싱
        logs = []
        for line in lines:
            if line.strip():
                # 감지된 형식으로 직접 파싱
                if detected_format:
                    log_entry = parse_log_line(line, detected_format)
                else:
                    log_entry = parse_log_line(line, 'standard')
                
                if log_entry:
                    logs.append(log_entry)
        
        print(f"DEBUG: Parsed {len(logs)} valid log entries")  # 디버깅
        
        buf = io.BytesIO()  # 이미지 임시 저장 버퍼
        
        # matplotlib 설정 초기화
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, ax = plt.subplots(figsize=(12, 6))
        plt.style.use('default')  # 기본 스타일 사용
        
        # 그래프 종류별 분기
        if plot_type == 'traffic':
            # 시간대별 트래픽 (Line Chart)
            data = traffic_by_hour(logs)
            print(f"DEBUG: Traffic data - {len(data)} points")  # 디버깅
            if data:
                x = [d[0] for d in data]
                y = [d[1] for d in data]
                
                # 시간 라벨을 더 간단하게 표시 (HH:MM 형식)
                x_labels = []
                for hour in x:
                    if ' ' in hour:
                        # "2025-06-10 09:00" -> "09:00"
                        time_part = hour.split(' ')[1]
                        x_labels.append(time_part)
                    else:
                        x_labels.append(hour)
                
                # 데이터 포인트가 적을 때는 더 큰 마커와 선 사용
                marker_size = 8 if len(data) <= 5 else 6
                line_width = 3 if len(data) <= 5 else 2
                
                ax.plot(range(len(x)), y, marker='o', linewidth=line_width, markersize=marker_size, color='#0d6efd')
                ax.fill_between(range(len(x)), y, alpha=0.3, color='#0d6efd')
                
                # 제목에 데이터 범위 표시
                if len(data) == 1:
                    title = f'Traffic at {x_labels[0]}'
                else:
                    title = f'Traffic from {x_labels[0]} to {x_labels[-1]}'
                
                ax.set_title(title, fontsize=16, fontweight='bold', pad=30)
                ax.set_xlabel('Time', fontsize=12)
                ax.set_ylabel('Number of Requests', fontsize=12)
                ax.set_xticks(range(len(x)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
                ax.grid(True, alpha=0.3)
                
                # Y축 범위 조정 (0부터 시작하되 최대값에 여유 추가)
                if max(y) > 0:
                    ax.set_ylim(0, max(y) * 1.1)
                
                plt.subplots_adjust(top=0.9, bottom=0.15)
            else:
                plt.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                plt.title('Traffic by Hour', fontsize=16, fontweight='bold', pad=30)
                plt.subplots_adjust(top=0.9)
        elif plot_type == 'endpoint':
            # 엔드포인트별 평균 응답시간 (Bar Chart)
            stats = endpoint_stats(logs)
            print(f"DEBUG: Endpoint data - {len(stats)} endpoints")  # 디버깅
            if stats:
                # 상위 20개만 표시 (너무 많으면 그래프가 복잡해짐)
                stats = sorted(stats, key=lambda x: x['avg_time'], reverse=True)[:20]
                x = [s['url'] for s in stats]
                y = [s['avg_time'] for s in stats]
                
                # 엔드포인트 이름을 간단하게 표시
                x_labels = []
                for url in x:
                    parts = url.split('/')
                    if parts[-1]:
                        x_labels.append(parts[-1])
                    elif len(parts) > 1:
                        x_labels.append(parts[-2])
                    else:
                        x_labels.append(url)
                
                bars = ax.bar(range(len(x)), y, color='#198754', alpha=0.7, edgecolor='#0f5132', linewidth=1)
                ax.set_title('Average Response Time by Endpoint (Top 20)', fontsize=16, fontweight='bold', pad=30)
                ax.set_xlabel('Endpoint', fontsize=12)
                ax.set_ylabel('Average Response Time (ms)', fontsize=12)
                ax.set_xticks(range(len(x)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
                ax.grid(True, alpha=0.3, axis='y')
                
                # 막대 위에 값 표시
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(y)*0.01,
                            f'{height:.0f}ms', ha='center', va='bottom', fontsize=10)
                
                plt.subplots_adjust(top=0.9, bottom=0.2)
            else:
                plt.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                plt.title('Average Response Time by Endpoint', fontsize=16, fontweight='bold', pad=30)
                plt.subplots_adjust(top=0.9)
        elif plot_type == 'status':
            # 상태 코드 분포 (Pie Chart)
            from collections import Counter
            codes = [log['status'] for log in logs]
            counter = Counter(codes)
            if counter:
                labels = list(counter.keys())
                sizes = list(counter.values())
                
                # 색상 설정 (상태 코드별로 다른 색상)
                colors = []
                for code in labels:
                    if code.startswith('2'):
                        colors.append('#198754')  # 성공 - 초록
                    elif code.startswith('4'):
                        colors.append('#fd7e14')  # 클라이언트 에러 - 주황
                    elif code.startswith('5'):
                        colors.append('#dc3545')  # 서버 에러 - 빨강
                    else:
                        colors.append('#6c757d')  # 기타 - 회색
                
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                       colors=colors, explode=[0.05]*len(sizes), shadow=True)
                ax.set_title('Status Code Distribution', fontsize=16, fontweight='bold', pad=30)
                plt.subplots_adjust(top=0.9)
            else:
                plt.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                plt.title('Status Code Distribution', fontsize=16, fontweight='bold', pad=30)
                plt.subplots_adjust(top=0.9)
        else:
            # 지원하지 않는 plot_type
            return '', 404
            
        # 그래프를 PNG로 저장 후 응답
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        response = send_file(buf, mimetype='image/png')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        print(f"DEBUG: Error generating plot - {e}")  # 디버깅
        return '', 500

@bp.route('/errors/<logfile>')
def show_errors(logfile):
    # 에러 로그를 보여주는 라우트
    file_path = os.path.join(LOG_DIR, logfile)
    if not os.path.exists(file_path):
        return '', 404
    
    # 로그 파일 읽고 파싱
    with open(file_path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    
    # 로그 형식 자동 감지 (처음 20줄 사용)
    sample_lines = [line for line in lines[:20] if line.strip()]
    detected_format = detect_log_format(sample_lines)
    
    # 로그 파싱
    logs = []
    for line in lines:
        if line.strip():
            # 감지된 형식으로 직접 파싱
            if detected_format:
                log_entry = parse_log_line(line, detected_format)
            else:
                log_entry = parse_log_line(line, 'standard')
            
            if log_entry:
                logs.append(log_entry)
    
    # 4xx, 5xx 에러만 필터링
    error_logs = [log for log in logs if log['status'].startswith('4') or log['status'].startswith('5')]
    
    # 에러별로 그룹화
    error_stats = {}
    error_4xx_count = 0
    error_5xx_count = 0
    
    for log in error_logs:
        status = log['status']
        if status not in error_stats:
            error_stats[status] = []
        error_stats[status].append(log)
        
        # 4xx, 5xx 카운트
        if status.startswith('4'):
            error_4xx_count += 1
        elif status.startswith('5'):
            error_5xx_count += 1
    
    return render_template(
        'errors.html',
        logfile=logfile,
        error_logs=error_logs,
        error_stats=error_stats,
        total_errors=len(error_logs),
        error_4xx_count=error_4xx_count,
        error_5xx_count=error_5xx_count
    ) 