import os
from flask import Blueprint, render_template, request, current_app
from .utils import parse_log_line, search_pattern, traffic_by_hour

bp = Blueprint('views', __name__)

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

@bp.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # logs 디렉토리의 파일 목록
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_files = [f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))]

    result = None
    chart_data = None
    pattern_results = None
    keyword = request.form.get('keyword', '')
    selected_file = request.form.get('logfile')
    logs = []
    if request.method == 'POST' and selected_file:
        file_path = os.path.join(LOG_DIR, selected_file)
        if os.path.exists(file_path):
            with open(file_path, encoding='utf-8') as f:
                lines = f.read().splitlines()
            logs = [parse_log_line(line) for line in lines]
            logs = [log for log in logs if log]
            # 패턴 검색
            if keyword:
                pattern_results = search_pattern(logs, keyword)
            # 시간대별 트래픽
            chart_data = traffic_by_hour(logs)
            result = True
    return render_template('analyze.html', result=result, chart_data=chart_data, pattern_results=pattern_results, keyword=keyword, log_files=log_files, selected_file=selected_file) 